# Cola hospitalaria

Dashboard Flask para gestionar la atención de pacientes mediante una cola de prioridad. La interfaz principal permite registrar, listar, atender y eliminar pacientes, mostrando primero los niveles de urgencia más altos y respetando el orden de llegada cuando existe empate.

## Funcionalidades actuales

- Registro de pacientes con urgencia del 1 al 5.
- Listado ordenado por urgencia y FIFO dentro del mismo nivel.
- Resumen de pacientes en espera, próximo paciente y atención prioritaria.
- Atención del siguiente paciente.
- Eliminación individual de pacientes.
- Mensajes visibles para operaciones exitosas, validaciones y cola vacía.
- Diseño responsive con HTML semántico y selectores `data-testid` preparados para futuras pruebas Playwright.

La interfaz antigua “Sin Estructura” y sus rutas ya no forman parte de la aplicación web.

## Estructura principal

```text
.
├── app.py
├── api/
├── domain/
├── services/
├── tests/
├── scripts/
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
├── paciente.py
├── main.py
├── paciente1.py
├── priority_queue.py
├── simulacion.py
├── utils.py
├── requirements.txt
├── static/css/styles.css
└── templates/index.html
```

`app.py` es la entrada del dashboard web. `main.py` conserva el menú de consola existente y utiliza sus módulos de apoyo.

## Requisitos e instalación en macOS

Se requiere Python 3.12 y [uv](https://docs.astral.sh/uv/). Desde la raíz del repositorio:

```bash
uv python install 3.12
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

Si Python 3.12 ya está disponible para `uv`, puede omitirse `uv python install 3.12`.

## Ejecución

Para iniciar el dashboard:

```bash
source .venv/bin/activate
python app.py
```

Abrir <http://127.0.0.1:5000/> en el navegador. Detener el servidor con `Ctrl+C`.

El menú de consola puede iniciarse con:

```bash
source .venv/bin/activate
python main.py
```

## API JSON

La API comparte el servicio y la cola de la misma instancia que el dashboard HTML. Prefijo `/api`.

| Método | Ruta | Éxito | Errores |
|---|---|---|---|
| `GET` | `/api/health` | `200` con `estado`, `ambiente` y `version` | — |
| `POST` | `/api/pacientes` | `201` con `paciente` y `posicion` | `400` |
| `GET` | `/api/pacientes` | `200` con `total`, `proximo` y `pacientes` | — |
| `POST` | `/api/pacientes/atender` | `200`; con cola vacía `paciente: null` | — |
| `DELETE` | `/api/pacientes/<id>` | `204` sin cuerpo | `404` |

```bash
curl -X POST -H 'Content-Type: application/json' \
     -d '{"nombre": "Ana López", "prioridad": 2}' \
     http://127.0.0.1:5000/api/pacientes
```

Los errores usan un formato único:

```json
{"error": {"codigo": "PRIORIDAD_INVALIDA", "mensaje": "prioridad debe ser un entero entre 1 y 5", "detalles": {}}}
```

El ambiente y la versión que reporta `/api/health` se inyectan por entorno con `APP_AMBIENTE` y
`APP_VERSION`; sin ellas la instancia responde `local` y `desconocida`.

## Ambientes con Docker

Un solo artefacto etiquetado con el SHA del commit sirve a los dos ambientes:

```bash
export APP_VERSION=$(git rev-parse HEAD)
docker build --build-arg APP_VERSION="$APP_VERSION" -t hospital-queue:"$APP_VERSION" .
docker compose --profile ci up -d --no-build        # http://127.0.0.1:8001
docker compose --profile staging up -d --no-build   # http://127.0.0.1:8002
docker compose --profile ci --profile staging down -v --remove-orphans
```

Cada ambiente es un contenedor y un puerto propios, así que su cola en memoria es independiente.

## Pruebas

```bash
source .venv/bin/activate
uv pip install -r requirements-dev.txt

python -m pytest tests/unit -q --cov=domain --cov=services   # unitarias
python -m pytest tests/integration -q                        # integración
```

Las pruebas de integración hablan HTTP real. Si `API_BASE_URL` está definida prueban esa instancia
desplegada; si no, levantan una propia en un puerto libre y la apagan al terminar:

```bash
API_BASE_URL=http://127.0.0.1:8001 EXPECTED_AMBIENTE=ci EXPECTED_VERSION="$APP_VERSION" \
    python -m pytest tests/integration -q
```

Con `-m smoke` se ejecuta el subconjunto mínimo. La verificación del health desplegado se hace con:

```bash
python scripts/verificar_health.py --url http://127.0.0.1:8001/api/health \
    --ambiente ci --version "$APP_VERSION"
```

## Procedencia y licencia

El código base fue migrado de forma conservadora desde [anasofiaeggenberger/Proyecto-Priority-Queue](https://github.com/anasofiaeggenberger/Proyecto-Priority-Queue), commit `89fa05b` de `main`. Se conservaron los autores y avisos presentes en el README original.

El repositorio original no contiene `LICENSE`, `LICENSE.md`, `COPYING` ni `NOTICE`, y no declara una licencia formal. No se infiere ni añade una licencia nueva; cualquier redistribución debe confirmarse con los titulares del código.

## Alcance

El dashboard, el dominio aislado, las unitarias con gate de cobertura, la API JSON, las pruebas de
integración de caja negra, el artefacto Docker y los ambientes `ci`/`staging` ya están implementados.
Quedan pendientes la suite E2E con Playwright, las notificaciones SMTP y el job de Jenkins.

## Estrategia técnica y colaboración

La estrategia futura de pruebas y automatización está documentada en:

- [Plan técnico](docs/PLAN_TECNICO.md): arquitectura propuesta, contrato API provisional, matrices de pruebas, aislamiento, Jenkins, ambientes y riesgos.
- [Guía operativa para agentes](docs/GUIA_AGENTES_PROYECTO_FINAL.md): responsabilidades, dependencias, ramas, evidencias y reglas de integración.
- [Decisiones técnicas](DECISIONES.md): alternativas evaluadas, decisiones cerradas y fuentes.
- [Evidencia de ejecución](EVIDENCIA.md): resultados verificados y lo que sigue pendiente.

Las secciones de esos planes marcadas como planificadas siguen siendo trabajo futuro; `EVIDENCIA.md` indica qué está verificado y qué no. Para colaborar, cada integrante debe trabajar en una rama propia, mantener su alcance, ejecutar las verificaciones de su cambio y abrir un PR con evidencia. Ana Sofía es responsable de lógica/unitarias/cobertura/gate de calidad; Juan Pablo de API/integración/Docker/ambientes/gate de integración; y Víctor de Playwright/POM/gate E2E/notificaciones/demo. No se deben hacer commits, pushes ni merges a nombre de otra persona ni guardar secretos en el repositorio.
