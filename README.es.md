# Revisor LLM de etiquetas de transacciones

Un motor de palabras clave etiqueta transacciones bancarias en formato Plaid. Un LLM revisa
esas etiquetas, marca las que le generan dudas y propone la etiqueta correcta con una razón
que un analista puede leer en cinco segundos. El código decide qué correcciones se aplican.
Después medimos qué valen esas correcciones en una decisión de crédito.

Hecho como prueba técnica de AI Engineer para Fundo, que da adelantos basados en ingresos a
negocios pequeños.

[English version](README.md)

## Requisitos

- Python 3.10 o superior
- `pip install -r requirements.txt` (solo `boto3`)

## Reproducir los resultados sin API key

Las respuestas del LLM están guardadas en `reviewer/cache/`. Este comando las lee y regenera
todos los resultados, sin key y sin llamar a ningún proveedor:

```bash
pip install -r requirements.txt
python run.py --use-cache
```

Muestra, por negocio, el ingreso mensual y la oferta según la verdad, el motor y el
revisor, además del error en dólares, la precisión de los flags, los hard negatives y el
gasto en LLM. Tarda unos 30 segundos, casi todo en la simulación de errores.

| Archivo | Contenido |
|---|---|
| `outputs/nova-lite/reviews.json` | Por transacción: etiqueta del motor, propuesta, final, estado, confianza, razón y evidencia |
| `outputs/nova-lite/metrics.json` | Error de ingreso mensual por negocio, precisión y recall de los flags, hard negatives, inyecciones |
| `outputs/credit/report.md` | Parte 2: features y oferta antes/después, simulación de errores al 2/5/10% |

## Correr con un LLM

El proveedor se elige según las variables de entorno:

| Variables | Proveedor | Modelo |
|---|---|---|
| `AWS_BEARER_TOKEN_BEDROCK` + `AWS_REGION` | Amazon Bedrock (por defecto) | Nova Lite |
| `ANTHROPIC_API_KEY` (sin credenciales AWS) | API de Anthropic | Claude Haiku 4.5 |
| Ninguna | Solo cache, con un aviso | |

```bash
export AWS_BEARER_TOKEN_BEDROCK=...   # API key de Bedrock
export AWS_REGION=us-east-1
python run.py
```

Bedrock también acepta cualquier credencial AWS estándar (`AWS_PROFILE`,
`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`). El perfil de inferencia de Nova Lite sigue a
la región (`us.`, `eu.`, `apac.`). `MODEL_ID` cambia el modelo: los IDs que empiezan con
`claude-` van a la API de Anthropic y el resto a Bedrock. Las respuestas nuevas se agregan
al cache y las ya guardadas no se vuelven a pedir.

## Otros conjuntos de datos

```bash
python run.py --use-cache --data data/holdout2   # también data/holdout, data/holdout3, data/holdout4
```

El mismo pipeline sobre otro conjunto etiquetado; los resultados quedan en
`outputs/<conjunto>/`. El holdout 1 se escribió con el revisor congelado; los holdouts 2 a 4,
un agente separado que nunca vio el revisor (ver SOLUTION.md). `python -m data.holdout` (y
`holdout2..4`) los regenera.

## Revisar transacciones propias

```bash
python run.py --input transacciones.json                         # solo revisar
python run.py --input transacciones.json --truth etiquetas.json  # revisar y medir
python run.py --input transacciones.json --assets asset_report.json --owner "Jane Doe" --name "Acme LLC"
```

`--input` acepta una respuesta de `/transactions/get` o `/transactions/sync` de Plaid, una
lista simple de transacciones Plaid, o una carpeta como `data/generated` (`businesses.json` +
archivos). Las transacciones pendientes se excluyen y los campos opcionales que falten se
llenan con los valores vacíos de Plaid. Por negocio muestra los grupos marcados como los
vería un analista (etiqueta del motor, propuesta, revenue sí/no, confianza, razón y
evidencia), las features y la oferta según el motor y según el revisor, las señales de saldo
y nuestra decisión (fondear / rechazar / referir). `--assets` agrega los saldos diarios;
`--owner` y `--name` agregan los datos de la solicitud que necesitan las verificaciones del
dueño y del nombre del negocio. Sin ellos esas verificaciones se omiten y los cambios de
negocio/personal van al analista.

`--truth` mide la corrida igual que en nuestros conjuntos (error en dólares, precisión y
recall de los flags, correcciones dañinas, decisiones equivocadas) y lista los errores más
caros que quedan. Acepta `{transaction_id: etiqueta}` o una lista de objetos con
`transaction_id`; una etiqueta es un nombre de grupo, el nuestro (`hr_gambling`) o el del
enunciado (`High risk — gambling`), o un objeto con `group`/`label`/`category`,
`is_business` y opcionalmente `revenue`. También funciona con una verdad que solo dice
ingreso sí/no. Los resultados quedan en `outputs/input/<nombre>/`.

## Paso a paso

`run.py` encadena estos pasos; cada uno también corre por separado:

```bash
python -m data.generate      # datos sintéticos Plaid: 10 negocios, 61-90 días, la verdad aparte
python -m engine.keywords    # etiquetas del motor y su error contra la verdad
python -m reviewer.review    # revisor LLM (--offline solo cache, --model, --input)
python -m reviewer.evaluate  # evalúa el revisor contra la verdad
python -m credit.simulate    # Parte 2
```

Los datos generados ya están en `data/generated/`. Regenerarlos con otra semilla cambia las
transacciones y el cache deja de coincidir.

## Estructura

| Ruta | Qué hace |
|---|---|
| `data/` | Generador de datos sintéticos en formato Plaid y cargador |
| `engine/` | Motor de palabras clave, imperfecto a propósito |
| `reviewer/` | Prompt, cliente LLM con cache, guardas de evidencia, política y evaluación |
| `credit/` | Features de crédito, regla de oferta y simulación de errores |
| `labels.py` | Las 13 etiquetas y la regla de ingreso, compartidas por todo |
| `run.py` | El comando único |

Decisiones, resultados y limitaciones en [SOLUTION.es.md](SOLUTION.es.md) ([inglés](SOLUTION.md)).
