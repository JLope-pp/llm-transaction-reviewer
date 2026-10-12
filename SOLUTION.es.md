# Solución

[English version](SOLUTION.md)

Un LLM revisa las etiquetas que un motor de palabras clave pone a transacciones en formato
Plaid. El código decide qué correcciones se aplican, y una regla de decisión usa el saldo de
la cuenta como segunda opinión, para que una etiqueta equivocada no pueda por sí sola hacer
que se fondee a un negocio. Todo se reproduce con `python run.py --use-cache` (otros
conjuntos con `--data`), sin API key.

**En resumen (Nova Lite, 36 negocios en cinco conjuntos, tres de ellos ciegos):** el
revisor nunca convirtió una etiqueta correcta en incorrecta, y nuestra regla de decisión no
fondeó a ninguno de los negocios que debían recibir $0. El motor solo fondea a 8 de ellos.

## Datos y motor

Respuestas sintéticas de `/transactions/get` y `/asset_report/get` (convención de signo de
Plaid, categorías PFC v2 validadas contra el CSV de la taxonomía de Plaid). La categoría de
Plaid es la que Plaid plausiblemente pondría, a veces equivocada. La verdad vive aparte, en
`truth.json`. Desarrollo (10 negocios) se usó para diseñar. El holdout 1 (5) se escribió con
el revisor ya congelado. Los holdouts 2 a 4 (16) los escribió un agente separado que nunca
vio el revisor, el prompt ni los resultados.

Los casos incluyen pagos de procesadores que parecen transferencias, MCAs apilados, cargos
NSF con muchas redacciones, un banco sin cargos NSF, dinero del dueño, hard negatives
(`ADVANCE AUTO PARTS`), inyecciones en memos y historias de 61 a 85 días. El motor
(`engine/keywords.py`) falla por precedencia, puntuación, `SQUARE` contra `SQUARE CAPITAL` y
palabras clave dentro de nombres: 21.7% de grupos mal en desarrollo.

## Parte 1: el revisor

Las transacciones se agrupan por dirección, contraparte, forma de la descripción y etiqueta
del motor. El modelo ve cada grupo con montos y fechas, la categoría y el tipo de contraparte
de Plaid, y **hechos calculados por código**: un desembolso seguido de cuotas fijas, el
pagador coincide con el dueño, la contraparte es un procesador, y créditos que devuelven un
débito anterior mientras el saldo estaba negativo. El texto del banco va dentro de
`<untrusted>`. El modelo devuelve un veredicto, una etiqueta (lista cerrada más el indicador
de negocio; el ingreso lo deriva el código), una confianza, una razón corta y un indicador de
inyección. Después el código hace tres cosas:

1. **Segunda lectura**, cuando la respuesta se contradice (un "flag" que repite la etiqueta
   del motor, porque Nova Lite se ancla en ella) o cuando los datos estructurados apoyan una
   etiqueta que ninguno de los dos eligió.
2. **Revisión ciega** de los grupos con texto escrito por el pagador: se vuelve a preguntar
   sin el texto *y* sin la etiqueta del motor. Si el texto cambia el resultado de crédito, un
   analista ve las dos lecturas. Así se detectan las inyecciones por su efecto, sin importar
   cómo estén redactadas: 9 de 9 en los conjuntos de prueba, una en español.
3. **Política** (`reviewer/guardrails.py`): una corrección se aplica solo si es material,
   supera 0.85 de confianza cuando agrega ingreso (0.70 en otro caso), no es sospechosa, y
   **cada campo cambiado tiene una señal estructurada que el modelo no escribió** (categoría
   de Plaid, tipo de contraparte o un hecho del código). Quitar un NSF, un sobregiro o un alto
   riesgo siempre va a una persona. Si no, queda la etiqueta del motor y el flag va a un
   analista.

**Resultados (MEDIDOS contra la verdad sintética):**

| | Dev | H1 | H2 | H3 | H4 |
|---|---|---|---|---|---|
| Error bruto de ingreso $/mes, motor → revisor | 148k → **16k** | 17k → **7k** | 48k → **33k** | 55k → **35k** | 39k → **19k** |
| Precisión de flags / errores materiales detectados | 94% / 96% | 99% / 93% | 91% / 77% | 88% / 90% | 95% / 92% |
| Correcciones que volvieron incorrecta una etiqueta correcta | 0 | 0 | 0 | 0 | 0 |
| Hard negatives enviados a un analista | 2/89 | 0/14 | 9/66 | 5/55 | 21/110 |

El error bruto cuenta cada dólar mal clasificado (el error neto deja que se cancelen).

**Medido con honestidad.** Cada conjunto ciego se corrió una vez antes de cualquier cambio, y
esas corridas salieron peor: en H2 un negocio quedó sin revisar por una falla del proveedor,
H3 tuvo 1 corrección dañina, y H4 tuvo 8 y fondeó a un negocio con 4 adelantos apilados. Los
arreglos son reglas del negocio, no casos (devoluciones detectadas por estructura, un
prestamista no cobra por Zelle, quitar una alarma va a una persona, carga de pagos), y cada
uno es neutro o mejor en los otros conjuntos. Las métricas de antes y después están en
`outputs/holdout2/`. Lo que falló: un prompt con los nombres de nuestros casos daba $12k en
desarrollo porque contenía las respuestas; quité todo nombre específico de los datos y
volví a empezar desde $31k. Dos reescrituras del prompt empeoraron, y el modelo copiaba una
razón de ejemplo hasta que la quité.

**Errores que revisé** (los más caros que el revisor todavía comete, `reviews.json` contra
`truth.json`):
- **Créditos que no son ventas y no tienen categoría clara en Plaid** son el grupo más grande:
  un subsidio de guardería de $22,000 (H3, Plaid `TRANSFER_IN_DEPOSIT`), subsidios estatales,
  pagos de seguros. El modelo los llama ingreso o coincide con el motor. Ingreso falso, así
  que la oferta sube.
- **Financiamiento del propio procesador que parece sus pagos:** los $22,000 de Lightspeed
  (H2) llegan con el mismo texto que las ventas diarias, así que quedan dentro de un grupo de
  47 pagos y el hecho de desembolso más cuotas (máximo 3 créditos grandes) nunca se activa. Los
  $16,000 de Payoneer (H3) se devuelven con una retención variable, no con débitos fijos.
  Ingreso falso.
- **Dinero del dueño por Zelle:** en B03 se mostró el hecho "el pagador coincide con el
  dueño", pero el memo decía "for payroll" y el modelo lo dejó como ingreso de clientes.
  Plaid apoya la etiqueta del motor, así que no hubo segunda lectura. Apodos y apellidos de
  casada (H3, H1) no coinciden en absoluto.
- **Evidencia de Plaid que también está mal:** Scratchpay le paga a una veterinaria (H4) por
  clientes que financiaron su cuenta. Plaid lo llama desembolso de préstamo, así que la guarda
  dejó que el modelo lo pasara de active_advance a not_revenue. Sigue mal, y sigue sin contar
  como ingreso.
- **Retenidos, no equivocados:** propuestas correctas que esperan a una persona por diseño
  (quitar la etiqueta de embargo a Levy Restaurant Supply, un pago de Brightwheel con 0.80 de
  confianza). Cuestan tiempo del analista, no dinero.

**Modelo contra código.** El modelo juzga qué es una contraparte y si un texto intenta
manipularlo. El código se encarga de lo que tiene que ser exacto o auditable: agrupar, los
hechos, el ingreso, la materialidad, la evidencia y la decisión. Nova Lite reporta 0.9 de
confianza para casi todo, así que la confianza sola nunca aplica un cambio. Una salida
inválida se reintenta una vez con los errores y después se parte el bloque; los errores del
proveedor se reintentan con espera. Lo que quede sin revisar mantiene la etiqueta del motor,
y el cache guarda también las fallas, así que una reproducción toma el mismo camino.

**Elección del modelo** (pipeline final, cinco conjuntos):

| | Nova Lite | Claude Haiku 4.5 | Nova Pro |
|---|---|---|---|
| Mal fondeados / correcciones dañinas | 0 / 0 | 0 / 0 | 0 / 2 |
| Error bruto de ingreso / error de oferta | $110k / $130k | **$88k** / $131k | $165k / $185k |
| Transacciones enviadas a un analista | **188** | 220 | 473 |
| Costo de una corrida en los cinco conjuntos | **$0.07** | $1.06 | $0.78 |

Haiku etiqueta mejor pero da las mismas ofertas a 16 veces el costo, y dejó 21 transacciones
sin revisar por salidas inválidas (ese negocio se refiere); Pro manda 2.5 veces más trabajo a
los analistas. **Por defecto: Nova Lite en Bedrock**, con la API de Anthropic como
respaldo y `MODEL_ID` para cambiar de modelo. **Gasto: unos $2.68 en total**, y `run.py`
imprime la parte guardada en cache por modelo: Nova Lite $0.11 (las corridas finales, $0.07,
más corridas anteriores del pipeline, incluidas las ciegas, que el cache conserva), Haiku
$1.06 y Pro $0.78. Los otros $0.74 fueron llamadas del desarrollo inicial cuyo cache se borró
junto con el prompt sobreajustado.

## Parte 2: impacto en el crédito

`credit/features.py` calcula, desde cualquier juego de etiquetas: ingreso mensual sobre los
días cubiertos, proporción de ingreso sobre los depósitos, conteos de NSF y sobregiros,
proporción de alto riesgo, pago diario a otros funders, y señales de saldo que no dependen
de etiquetas (días negativos, saldo promedio, carga de pagos).

En desarrollo, la regla del enunciado da una suma de errores de oferta de $219k con el motor
y **$8k** con el revisor, y fondea a 3 negocios que debían recibir $0 (B04, B07, B08) contra
**0**. El banco de B08 devuelve los débitos rebotados en vez de cobrar comisiones: el motor ve
0 NSF y ofrece $19,885; el revisor cuenta 14 devoluciones. En B04, el wire de un funder se
cuenta como ingreso y sus $395 diarios no se cuentan como pago.

**Simulación de errores** (ESTIMADO, 100 corridas, tasa de 5%, cambio medio de la oferta
cuando el error ocurre):

| Tipo de error | Por transacción | Por contraparte | Cambia la decisión |
|---|---:|---:|---:|
| NSF perdido | $8,120 | $19,765 | 69% |
| Ingreso perdido | $2,765 | $13,158 | 1% |
| Ingreso falso | $1,521 | $7,839 | 12% |
| Adelanto falso | $1,494 | $3,224 | 0% |

El NSF es un precipicio: el error más raro es el que más decisiones cambia. Los errores por
contraparte, que es como fallan los motores de palabras clave, cuestan unas 5 veces más que
los aleatorios.

**Ingreso falso contra adelanto falso.** El ingreso falso suma $1.20 a la oferta por cada
dólar y pone capital en riesgo, muchas veces con un negocio ya endeudado. Un adelanto falso
resta $20 por cada dólar diario; eso cuesta margen, no capital. El peor caso es un funder
nuevo: su desembolso cuenta como ingreso *y* sus cuotas desaparecen (B04).

**Nuestra regla de decisión** (`credit/decision.py`, junto a la regla del enunciado). Las
pérdidas son asimétricas, así que el resultado puede ser **referir**: rechazar con más de 5
NSF por 90 días; referir con menos de 60 días de historia, cuando los días negativos superan
el 10% de la ventana, cuando otros funders se llevan más del 25% del ingreso, o cuando la
decisión por NSF depende de etiquetas en duda. Nada se fondea automáticamente sin esa
verificación: si el revisor no pudo revisar todas las transacciones (caída del proveedor,
salida inválida) o no hay asset report, se refiere. La oferta usa las etiquetas más
conservadoras. En los cinco conjuntos no fondea por error ni rechaza por error a nadie. La
regla del enunciado con las etiquetas del revisor todavía fondearía a U04 y V02 (cargos que
nadie reconoció, pero 10 y 11 días en negativo). El costo: 5 de 36 referidos.

**Un banco que no cobra NSF.** El modelo nunca ve el evento de fondos insuficientes, solo la
comisión. En un banco sin comisión el evento ocurre pero no deja texto, así que cero NSF
significa "no medido", no "sano". B08 pasó 30 de 90 días en negativo, la peor cuenta del
conjunto, y aun así recibe $19,885. Un modelo entrenado con esto sobrefinancia a esos
negocios. Mi arreglo cuenta el evento, no la comisión: el código empareja un crédito con un
débito anterior del mismo monto a la misma contraparte mientras el saldo era negativo, lo
que encontró los 37 pagos rebotados sin falsos positivos, y los días negativos entran
directo a la decisión. Agregaría una feature por institución, "cobra NSF sí/no", para que el
cero se trate como dato faltante.

**61 días en vez de 90.** Las sumas y los conteos cambian de significado. El ingreso
sobrevive si se divide por los días cubiertos, como el nuestro; dividirlo entre tres lo
subestima en un tercio. Los conteos son peores: 5 NSF en 61 días son unos 7.4 en 90, así que
el solicitante parece más sano de lo que es, y el modelo puntúa fuera de distribución sin
fallar en voz alta. La cobertura sale del asset report y viaja con la solicitud, los NSF se
comparan por 90 días y menos de 60 días se refiere. En producción también monitorearía la
cobertura y reentrenaría con historias de 90 días recortadas a ventanas más cortas.

## Parte 3: producción

**Primero en sombra, luego una compuerta.** El revisor corre junto al motor y registra lo que
*cambiaría*. Los analistas etiquetan cada semana una muestra de desacuerdos y acuerdos. Un
tipo de corrección (por ejemplo, pago de procesador → ingreso) sale en vivo solo después de
una ventana fija con precisión sobre un umbral, cero correcciones dañinas y sin aumento de
mal fondeados. Los tipos que agregan ingreso o quitan una alarma necesitan un umbral mayor o
se quedan con aprobación humana.

**Drift.** Monitorear las features, no solo las etiquetas: en cada versión de motor, prompt o
modelo, correr un conjunto fijo de referencia y comparar la mezcla de etiquetas, la
proporción de ingreso, los NSF, los pagos a funders y la oferta (PSI por feature); en
producción, seguirlas por banco y cobertura, más las tasas de acuerdo, de referidos y de
correcciones del analista. Un salto después de un release es la alarma, meses antes de que
los resultados lo muestren.

**Reproducir una decisión.** Guardar los payloads crudos de Plaid, la versión del motor y de
las palabras clave, el prompt, el ID del modelo y sus parámetros, las respuestas del LLM en
cache (ya indexadas por un hash de todas sus entradas), las versiones de guardas y reglas, las
features, la oferta y las acciones del analista. Repetir el paquete da la decisión original;
correrlo con el código de hoy muestra la diferencia.

**Analistas.** Ven solo flags materiales con razón y evidencia, y deciden todo referido, toda
alarma quitada, todo ingreso agregado sin evidencia y toda inyección. Sus decisiones se
guardan por el ID de entidad de la contraparte en Plaid, no por nombre (`ADVANCE AUTO PARTS` y
`ADVANCE AMERICA`), y se vuelven evidencia para las guardas y el set etiquetado de la
compuerta.

## Omitido y límites conocidos

Omitido: datos reales del Sandbox de Plaid (los casos había que plantarlos), RAG (el
conocimiento cabe en el prompt; un corpus de entidades sería una lista de palabras clave
ajustada a nuestros datos), calibrar la confianza, consultas de UCC y burós, una interfaz
para el analista. El respaldo de Anthropic se validó mandando el mismo cuerpo de la petición
a través de Bedrock, no con una key de Anthropic. Límites: créditos que no son ventas y no
tienen categoría en Plaid (subsidios, seguros) a menudo se escapan; las etiquetas de alto
riesgo que Plaid no puede categorizar nunca se quitan automáticamente; los prestamistas
payday quedan como `active_advance`; todos los resultados son sobre datos sintéticos, así que
muestran que los mecanismos funcionan, no la exactitud en producción.

## Herramientas

Usé Claude Code como asistente de programación, principalmente para:
- **Crear los datos.** Escribió los generadores en formato Plaid a partir de los casos que
  definí (negocios, bancos, trampas). Los holdouts 2 a 4 los escribió un agente de Claude
  separado al que se le indicó no abrir el revisor, el prompt ni los resultados, para que
  fueran pruebas ciegas.
- **Simulaciones.** Implementó el Monte Carlo de errores de etiqueta y la comparación de
  ofertas antes/después que diseñé.
- **Comparaciones.** Corrió el mismo pipeline con Nova Lite, Claude Haiku 4.5 y Nova Pro y
  armó las tablas de resultados.


También usé Amazon Bedrock, la documentación de la API de Plaid y su taxonomía PFC, y la
práctica pública de underwriting de MCA.
