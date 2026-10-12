# Revisor LLM de etiquetas de transacciones

Un motor de palabras clave etiqueta transacciones bancarias en formato Plaid. Un LLM lee esas
etiquetas, marca las que le parecen dudosas y sugiere la correcta con una razón que un analista
puede leer en cinco segundos. El código decide qué sugerencias se aplican, y después mido cuánto
valen en una decisión de crédito.

Lo hice como prueba técnica de AI Engineer para Fundo, que da adelantos basados en ingresos a
negocios pequeños.

[English version](README.md)

## Requisitos

Necesitas Python 3.10 o superior. La única dependencia es boto3:

```bash
pip install -r requirements.txt
```

## Reproducir los resultados sin API key

Las respuestas del LLM están guardadas en reviewer/cache/, así que este comando las vuelve a
usar y regenera todos los resultados sin llamar a ningún proveedor:

```bash
pip install -r requirements.txt
python run.py --use-cache
```

Muestra, por cada negocio, el ingreso mensual y la oferta según la verdad, el motor y el
revisor, junto con el error en dólares, la precisión de los flags, los casos engañosos y lo que
se gastó en el LLM. Tarda unos 30 segundos, casi todo en la simulación de errores.

| Archivo | Qué tiene |
|---|---|
| outputs/nova-lite/reviews.json | Por transacción: etiqueta del motor, sugerencia, etiqueta final, estado, confianza, razón y evidencia |
| outputs/nova-lite/metrics.json | Error de ingreso mensual por negocio, precisión y recall de los flags, casos engañosos, inyecciones |
| outputs/credit/report.md | Parte 2: features y ofertas antes y después, simulación de errores al 2, 5 y 10% |

## Correrlo con un LLM

El proveedor depende de lo que tengas en las variables de entorno:

| Variables | Proveedor | Modelo |
|---|---|---|
| AWS_BEARER_TOKEN_BEDROCK y AWS_REGION | Amazon Bedrock (por defecto) | Nova Lite |
| ANTHROPIC_API_KEY, sin credenciales de AWS | API de Anthropic | Claude Haiku 4.5 |
| Ninguna | Solo cache, con un aviso | |

```bash
export AWS_BEARER_TOKEN_BEDROCK=...   # API key de Bedrock
export AWS_REGION=us-east-1
python run.py
```

Bedrock también funciona con cualquier credencial estándar de AWS (AWS_PROFILE, o
AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY). El perfil de inferencia de Nova Lite sigue a tu
región (us., eu. o apac.). MODEL_ID cambia el modelo: los IDs que empiezan con claude- van a la
API de Anthropic y el resto a Bedrock. Las respuestas nuevas se agregan al cache, y lo que ya
está guardado no se vuelve a pedir.

## Otros conjuntos de datos

```bash
python run.py --use-cache --data data/holdout2   # también data/holdout, data/holdout3, data/holdout4
```

Corre el mismo pipeline sobre otro conjunto etiquetado y escribe los resultados en outputs/ con
el nombre del conjunto. El holdout 1 lo escribí después de congelar el revisor; los holdouts 2
a 4 los escribió un agente separado que nunca lo vio (los detalles están en SOLUTION.es.md).
python -m data.holdout, y lo mismo con holdout2 a holdout4, los regenera.

## Revisar tus propias transacciones

```bash
python run.py --input transacciones.json                         # solo revisar
python run.py --input transacciones.json --truth etiquetas.json  # revisar y medir
python run.py --input transacciones.json --assets asset_report.json --owner "Jane Doe" --name "Acme LLC"
```

La entrada puede ser una respuesta de /transactions/get o /transactions/sync de Plaid, una lista
simple de transacciones Plaid, o una carpeta armada como data/generated (businesses.json más los
archivos). Las transacciones pendientes se descartan, y los campos opcionales que falten se
llenan con los valores vacíos de Plaid. Por cada negocio muestra los grupos marcados como los
vería un analista, las features y la oferta con las etiquetas del motor y con las del revisor,
las señales del saldo y la decisión (prestar, rechazar o referir). El asset report agrega los
saldos diarios, y el dueño y el nombre del negocio activan las verificaciones que los
necesitan. Sin ellos, esas verificaciones se omiten y los cambios de negocio a personal van a un
analista.

Si pasas un archivo de verdad, la corrida se mide igual que con los conjuntos incluidos (error
en dólares, precisión y recall de los flags, correcciones dañinas, decisiones equivocadas) y se
listan los errores más caros que quedan. Puede ser un diccionario de transaction_id a etiqueta,
o una lista de objetos con transaction_id. Una etiqueta puede ser un nombre de grupo, el mío
(hr_gambling) o el del enunciado (High risk, gambling), o un objeto con group, label o
category, is_business y opcionalmente revenue. También funciona una verdad que solo diga
ingreso sí o no. Los resultados quedan en outputs/input/ con el nombre del archivo.

## Paso a paso

run.py encadena estos pasos, y cada uno también corre por separado:

```bash
python -m data.generate      # datos sintéticos Plaid: 10 negocios, 61-90 días, la verdad aparte
python -m engine.keywords    # etiquetas del motor y su error contra la verdad
python -m reviewer.review    # revisor LLM (--offline solo cache, --model, --input)
python -m reviewer.evaluate  # evalúa el revisor contra la verdad
python -m credit.simulate    # Parte 2
```

Los datos generados ya están en data/generated/. Si los regeneras con otra semilla, cambian las
transacciones y el cache deja de coincidir.

## Estructura

| Ruta | Qué hace |
|---|---|
| data/ | Generadores de datos sintéticos en formato Plaid y el cargador |
| engine/ | El motor de palabras clave, imperfecto a propósito |
| reviewer/ | Prompt, cliente LLM con cache, guardas de evidencia, política y evaluación |
| credit/ | Features de crédito, regla de oferta, regla de decisión y simulación de errores |
| labels.py | Las 13 etiquetas y la regla de ingreso, compartidas por todo |
| run.py | El comando único |

Las decisiones, los resultados y las limitaciones están en [SOLUTION.es.md](SOLUTION.es.md)
([inglés](SOLUTION.md)).
