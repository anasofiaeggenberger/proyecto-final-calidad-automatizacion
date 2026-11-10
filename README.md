# Hospital Priority Queue — Sistema de Gestión de Pacientes

Hospital Priority Queue es una aplicación web Flask para gestionar la atención de pacientes mediante una cola de prioridad. La prioridad <code>1</code> representa la mayor urgencia y la prioridad <code>5</code> la menor. Cuando dos pacientes tienen la misma prioridad, se conserva el orden de llegada (FIFO).

El proyecto incluye un dashboard web, una API REST, pruebas automatizadas por capas, ejecución con Docker y un pipeline Jenkins con gates de calidad, integración y E2E.

## Características principales

- Registro de pacientes con nombre y prioridad del <code>1</code> al <code>5</code>.
- Orden automático por urgencia y FIFO en empates.
- Visualización del total, el próximo paciente y la atención prioritaria.
- Atención del siguiente paciente y manejo explícito de la cola vacía.
- Eliminación de pacientes mediante la API y desde el dashboard.
- Validaciones de nombres, prioridades, JSON y campos desconocidos.
- Respuestas JSON uniformes para errores de la API.
- Dashboard responsive con selectores <code>data-testid</code> para pruebas E2E.
- Pruebas unitarias, integración HTTP, notificaciones y Playwright con Page Object Model.
- Cobertura como gate de calidad y Ruff como verificación estática.
- Construcción de un artefacto Docker identificado por el SHA del commit.
- Ambientes Docker independientes para <code>ci</code> y <code>staging</code>.
- Pipeline Jenkins parametrizado con publicación de reportes y cleanup controlado.

La cola se mantiene en memoria dentro de cada proceso. Reiniciar la aplicación o detener un contenedor elimina los pacientes de esa instancia; no se presenta como almacenamiento persistente.

## Tecnologías utilizadas

| Área | Tecnologías |
|---|---|
| Aplicación | Python 3.12, Flask 2.3.2, Jinja, HTML y CSS |
| Servidor del contenedor | Gunicorn 23.0.0 |
| Pruebas | pytest 8.4.2, pytest-cov 6.3.0, pytest-html 4.2.0 |
| E2E | Playwright 1.65.0, pytest-playwright 0.10.0 |
| Calidad | Ruff 0.17.4, cobertura de <code>domain</code> y <code>services</code> |
| Automatización | Jenkins Declarative Pipeline, <code>uv</code>, <code>smtplib</code> |
| Contenedores | Docker Engine y Docker Compose v2 |

Las versiones de las herramientas de pruebas están fijadas en <code>requirements-ci.txt</code> y <code>requirements-e2e.txt</code> mediante hashes.

## Arquitectura

~~~text
Dashboard HTML ─┐
                ├── Flask app factory ── PatientService ── PatientQueue
API REST ───────┘                                      └── Patient

tests/unit          → dominio y servicios
tests/integration   → API HTTP en ejecución
tests/e2e           → dashboard real con Playwright/POM
tests/notifications → correo y manejo de errores SMTP
tests/pipeline      → despliegue y cleanup controlado
~~~

- <code>app.py</code> crea una instancia Flask y un <code>PatientService</code> por aplicación.
- <code>PatientService</code> concentra los casos de uso y la validación.
- <code>PatientQueue</code> mantiene la prioridad y el orden FIFO con estado aislado por instancia.
- El dashboard y la API usan el mismo servicio cuando pertenecen al mismo proceso.
- Docker ejecuta <code>ci</code> y <code>staging</code> en contenedores separados, con colas independientes y la misma imagen etiquetada con el SHA.
- Jenkins genera un proyecto Compose exclusivo por build, publica la API en un puerto de loopback asignado y limpia únicamente recursos que puede atribuir a ese build.

## Estructura del proyecto

~~~text
.
├── app.py
├── api/routes.py
├── domain/
│   ├── patient.py
│   └── patient_queue.py
├── services/patient_service.py
├── templates/index.html
├── static/css/styles.css
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── notifications/
│   └── pipeline/
├── scripts/
│   ├── ejecutar_e2e.py
│   ├── gestionar_ambiente.py
│   ├── notificar_fallo.py
│   └── verificar_health.py
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
├── requirements*.txt
├── DECISIONES.md
├── EVIDENCIA.md
└── docs/
~~~

Los archivos <code>main.py</code>, <code>paciente.py</code>, <code>paciente1.py</code>, <code>priority_queue.py</code>, <code>simulacion.py</code> y <code>utils.py</code> corresponden a una interfaz de consola heredada y se mantienen separados del flujo web principal. El Dockerfile no los empaqueta.

## Requisitos previos

### Aplicación local

- Git.
- Python 3.12.
- [uv](https://docs.astral.sh/uv/).
- Un navegador para abrir el dashboard.

### Pruebas

Las pruebas unitarias, de integración, notificaciones y pipeline requieren las dependencias de <code>requirements-ci.txt</code>. Las pruebas E2E requieren además <code>requirements-e2e.txt</code> y los navegadores administrados por Playwright.

### Docker

Para ejecutar los ambientes locales se necesita Docker Engine con Docker Compose v2.

### Jenkins

El agente Jenkins necesita Python 3.12, <code>python3</code>, <code>uv</code>, Git, Docker Engine, Compose v2, acceso controlado al daemon Docker y un workspace aislado. También requiere los plugins Pipeline/Declarative, Git, JUnit, Credentials Binding y HTML Publisher.

El repositorio no contiene una imagen de agente Jenkins. Las bibliotecas del sistema necesarias para Chromium y Firefox deben estar preparadas en el agente o en una imagen de infraestructura aprobada. La configuración completa está en [docs/JENKINS.md](docs/JENKINS.md).

### SMTP

El envío de fallos está implementado, pero requiere configurar credenciales Jenkins <code>smtp-config</code> y <code>smtp-auth</code>. No se incluyen secretos en el repositorio y este README no afirma que SMTP real haya sido probado.

## Instalación paso a paso

### macOS y Linux

Desde la raíz del repositorio:

~~~bash
git clone https://github.com/anasofiaeggenberger/proyecto-final-calidad-automatizacion.git
cd proyecto-final-calidad-automatizacion

uv python install 3.12
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
~~~

Si Python 3.12 ya está disponible para <code>uv</code>, puede omitirse <code>uv python install 3.12</code>.

Para instalar las herramientas de calidad y pruebas:

~~~bash
uv pip sync --python .venv/bin/python requirements-ci.txt
~~~

Para agregar Playwright y pytest-html:

~~~bash
uv pip install --python .venv/bin/python --require-hashes -r requirements-e2e.txt
.venv/bin/python -m playwright install chromium firefox
~~~

En Linux, la instalación de las bibliotecas del sistema del navegador puede requerir permisos administrativos. Esa preparación corresponde al sistema operativo o al agente de CI; no se realiza durante cada build Jenkins.

### Windows PowerShell

~~~powershell
git clone https://github.com/anasofiaeggenberger/proyecto-final-calidad-automatizacion.git
cd proyecto-final-calidad-automatizacion

uv python install 3.12
uv venv --python 3.12
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
~~~

Para las pruebas:

~~~powershell
uv pip sync --python .venv\Scripts\python.exe requirements-ci.txt
uv pip install --python .venv\Scripts\python.exe --require-hashes -r requirements-e2e.txt
.\.venv\Scripts\python.exe -m playwright install chromium firefox
~~~

Docker Compose y los comandos <code>curl</code> de las secciones siguientes requieren Docker Desktop y una terminal compatible. Las variables de entorno de Bash deben expresarse en PowerShell con <code>$env:NOMBRE = "valor"</code>.

## Ejecución de la aplicación

Con el entorno activado:

~~~bash
python app.py
~~~

Abrir <http://127.0.0.1:5000/> en el navegador. Para detener el servidor local, presionar <code>Ctrl+C</code> en la terminal donde se ejecuta.

La aplicación local utiliza el servidor de desarrollo de Flask. El contenedor utiliza Gunicorn y no depende de este servidor para sus despliegues.

Para informar ambiente y versión explícitamente:

~~~bash
APP_AMBIENTE=local APP_VERSION=local python app.py
~~~

Sin esas variables, <code>/api/health</code> responde <code>ambiente: "local"</code> y <code>version: "desconocida"</code>.

## Uso del sistema

Desde el dashboard se puede registrar un paciente, seleccionar su prioridad, observar la cola y presionar **Atender siguiente**. Un escenario simple para demostrar prioridad y FIFO es:

1. Registrar <code>Paciente prioridad 3</code> con prioridad <code>3</code>.
2. Registrar <code>Paciente urgente A</code> con prioridad <code>1</code>.
3. Registrar <code>Paciente urgente B</code> con prioridad <code>1</code>.
4. Verificar que los pacientes de prioridad <code>1</code> aparecen primero.
5. Atender dos veces y comprobar que sale primero <code>Paciente urgente A</code> y luego <code>Paciente urgente B</code>.
6. Atender nuevamente para retirar el paciente de prioridad <code>3</code>.

La API elimina por ID. La acción de eliminación del dashboard actual identifica al paciente por nombre; para demostrar eliminación inequívoca de homónimos, usar la API o nombres distinguibles.

## API REST

La API usa el prefijo <code>/api</code> y comparte la cola de la instancia con el dashboard HTML.

| Método | Endpoint | Respuesta exitosa | Errores principales |
|---|---|---|---|
| <code>GET</code> | <code>/api/health</code> | <code>200</code> con <code>estado</code>, <code>ambiente</code> y <code>version</code> | — |
| <code>POST</code> | <code>/api/pacientes</code> | <code>201</code> con <code>paciente</code> y <code>posicion</code> | <code>400</code> por JSON, campos, nombre o prioridad inválidos |
| <code>GET</code> | <code>/api/pacientes</code> | <code>200</code> con <code>total</code>, <code>proximo</code> y <code>pacientes</code> | — |
| <code>POST</code> | <code>/api/pacientes/atender</code> | <code>200</code> con el paciente atendido | <code>200</code> con <code>paciente: null</code> si la cola está vacía |
| <code>DELETE</code> | <code>/api/pacientes/&lt;id&gt;</code> | <code>204</code> sin cuerpo | <code>404</code> si el paciente no existe |

Los errores tienen este formato:

~~~json
{
  "error": {
    "codigo": "PRIORIDAD_INVALIDA",
    "mensaje": "prioridad debe ser un entero entre 1 y 5",
    "detalles": {}
  }
}
~~~

### Health

~~~bash
curl -sS http://127.0.0.1:5000/api/health | python -m json.tool
~~~

### Registrar pacientes

~~~bash
curl -sS -X POST http://127.0.0.1:5000/api/pacientes \
  -H 'Content-Type: application/json' \
  -d '{"nombre":"Ana López","prioridad":2}' | python -m json.tool
~~~

La respuesta incluye un ID estable, por ejemplo <code>p-0001</code>, y la posición calculada en la cola.

### Listar y atender

~~~bash
curl -sS http://127.0.0.1:5000/api/pacientes | python -m json.tool

curl -sS -X POST http://127.0.0.1:5000/api/pacientes/atender \
  | python -m json.tool
~~~

### Eliminar por ID

Reemplazar <code>&lt;ID&gt;</code> por el identificador devuelto al registrar o listar el paciente:

~~~bash
curl -i -X DELETE http://127.0.0.1:5000/api/pacientes/<ID>
~~~

La respuesta esperada es <code>204 No Content</code> y sin cuerpo.

## Ejecución con Docker

El Dockerfile construye la aplicación con Python 3.12 y Gunicorn. Compose define dos perfiles:

| Perfil | Servicio | URL predeterminada | Ambiente |
|---|---|---|---|
| <code>ci</code> | <code>api-ci</code> | <http://127.0.0.1:8001> | <code>ci</code> |
| <code>staging</code> | <code>api-staging</code> | <http://127.0.0.1:8002> | <code>staging</code> |

Construir una imagen identificada con el SHA actual y levantar ambos perfiles:

~~~bash
export APP_VERSION="$(git rev-parse HEAD)"
export IMAGE_NAME=hospital-queue

docker build \
  --build-arg APP_VERSION="$APP_VERSION" \
  -t "$IMAGE_NAME:$APP_VERSION" .

docker compose --profile ci up -d --no-build
docker compose --profile staging up -d --no-build
~~~

Comprobar las dos instancias:

~~~bash
curl -sS http://127.0.0.1:8001/api/health | python -m json.tool
curl -sS http://127.0.0.1:8002/api/health | python -m json.tool
docker compose --profile ci --profile staging ps
~~~

La respuesta de health debe mostrar <code>estado: "ok"</code>, el ambiente correspondiente y <code>version</code> igual a <code>$APP_VERSION</code>.

Para detener los servicios sin solicitar eliminación explícita de volúmenes:

~~~bash
docker compose --profile ci --profile staging down --remove-orphans
~~~

<code>docker compose down -v</code> agrega la eliminación de volúmenes. No usarlo en ambientes compartidos ni cuando se necesiten conservar datos. En este proyecto la cola es en memoria, por lo que detener los contenedores igualmente elimina el estado de los pacientes.

## Pruebas automatizadas

Ejecutar los comandos desde la raíz con <code>.venv</code> preparado.

### Ruff

~~~bash
.venv/bin/ruff check app.py api domain services tests scripts
~~~

### Pruebas unitarias y cobertura

~~~bash
mkdir -p reports/unit
.venv/bin/python -m pytest tests/unit -q \
  --junitxml=reports/unit/junit.xml \
  --cov=domain \
  --cov=services \
  --cov-report=term-missing \
  --cov-report=xml:reports/unit/coverage.xml \
  --cov-fail-under=90
~~~

El gate mide los módulos <code>domain</code> y <code>services</code> y exige al menos 90% de cobertura.

### Notificaciones y pipeline

~~~bash
mkdir -p reports/notifications
.venv/bin/python -m pytest tests/notifications tests/pipeline -q \
  --junitxml=reports/notifications/junit.xml
~~~

Estas pruebas verifican el formato del correo, validaciones SMTP, manejo de credenciales, protección de secretos y la lógica de despliegue/cleanup. No envían un correo real.

### Integración HTTP

Sin <code>API_BASE_URL</code>, la fixture inicia una instancia Flask temporal en un puerto libre y la apaga al finalizar:

~~~bash
.venv/bin/python -m pytest tests/integration -q
~~~

Para probar una instancia ya desplegada y exclusiva:

~~~bash
API_BASE_URL=http://127.0.0.1:8001 \
EXPECTED_AMBIENTE=ci \
EXPECTED_VERSION="$APP_VERSION" \
.venv/bin/python -m pytest tests/integration -q
~~~

El subconjunto marcado como smoke se ejecuta con <code>-m smoke</code>.

### E2E con Playwright

Instalar los navegadores una vez:

~~~bash
.venv/bin/python -m playwright install chromium firefox
~~~

Regresión completa, 17 casos por navegador:

~~~bash
.venv/bin/python scripts/ejecutar_e2e.py \
  --suite regression --browser chromium

.venv/bin/python scripts/ejecutar_e2e.py \
  --suite regression --browser firefox
~~~

Smoke:

~~~bash
.venv/bin/python scripts/ejecutar_e2e.py \
  --suite smoke --browser chromium
~~~

Sin <code>--base-url</code>, las pruebas levantan un servidor HTTP local temporal. Para una instancia Docker exclusiva:

~~~bash
E2E_ALLOW_CLEANUP=1 \
EXPECTED_AMBIENTE=ci \
EXPECTED_VERSION="$APP_VERSION" \
.venv/bin/python scripts/ejecutar_e2e.py \
  --base-url http://127.0.0.1:8001 \
  --suite regression --browser chromium
~~~

Cada caso limpia la cola por HTTP antes y después de ejecutarse. No apuntar estas pruebas a una instancia compartida.

Los reportes quedan en <code>reports/e2e/</code>:

- <code>junit.xml</code>: resultados para Jenkins.
- <code>report.html</code>: reporte HTML de pytest-html.
- <code>selection.json</code> y <code>target.json</code>: suite, navegador, commit, URL y health.
- <code>artifacts/</code>: screenshots y traces de fallos.

Para inspeccionar una traza:

~~~bash
.venv/bin/python -m playwright show-trace reports/e2e/artifacts/<caso>/trace.zip
~~~

Las salidas de <code>reports/</code> están ignoradas por Git. Las evidencias seleccionadas y documentadas se conservan en [evidencia/](evidencia/) y se describen en [EVIDENCIA.md](EVIDENCIA.md).

## Jenkins CI/CD

El [Jenkinsfile](Jenkinsfile) automatiza estas etapas:

1. Checkout y preparación de Python.
2. Ruff.
3. Pruebas unitarias y cobertura.
4. Pruebas de notificaciones y pipeline.
5. Construcción del artefacto Docker.
6. Deploy en <code>ci</code> o <code>staging</code>.
7. Health Gate con ambiente y SHA.
8. Pruebas de integración contra la instancia desplegada.
9. Playwright E2E.

Un comando fallido detiene las etapas posteriores. El pipeline conserva stdout/stderr del Health Gate, publica JUnit, cobertura, reportes E2E, screenshots, traces y logs de despliegue. El bloque <code>post</code> intenta enviar la notificación de fallo y limpia únicamente el proyecto Compose propio del build.

Parámetros disponibles:

| Parámetro | Valores/configuración | Efecto |
|---|---|---|
| <code>ENVIRONMENT</code> | <code>ci</code>, <code>staging</code> | Selecciona instancia y ambiente validado por health |
| <code>SUITE</code> | <code>regression</code>, <code>smoke</code> | Selecciona la suite completa o los casos smoke |
| <code>BROWSER</code> | <code>chromium</code>, <code>firefox</code> | Cambia el navegador E2E |
| <code>NOTIFY_EMAILS</code> | Destinatarios editables | Define los destinatarios de la notificación |

El agente no puede asumirse como un Jenkins limpio: requiere las herramientas y librerías del navegador indicadas en [docs/JENKINS.md](docs/JENKINS.md). El repositorio no contiene una imagen versionada de agente Jenkins.

SMTP utiliza Credentials Binding (<code>smtp-config</code> y <code>smtp-auth</code>) y variables inyectadas. No almacenar credenciales en Git ni en argumentos o logs. La implementación y las pruebas locales no equivalen a una prueba de entrega en un buzón real.

El trigger actual es <code>pollSCM('H/2 * * * *')</code>. Puede generar builds por cambios que el job observe; su frecuencia y alcance deben revisarse en la configuración de Jenkins sin deshabilitar el mecanismo requerido de integración.

## Documentación adicional

- [Guía de Jenkins y SMTP](docs/JENKINS.md): agente, plugins, parámetros, reportes y credenciales.
- [Pruebas E2E](docs/E2E.md): POM, casos, aislamiento y evidencias.
- [Guion de demo](docs/DEMO.md): preparación, recorrido de 15 minutos y fallas controladas.
- [Decisiones técnicas](DECISIONES.md): arquitectura, pruebas, pipeline y alternativas evaluadas.
- [Evidencia de ejecución](EVIDENCIA.md): resultados disponibles, comandos y limitaciones.
- [Plan técnico](docs/PLAN_TECNICO.md): contrato API y estrategia completa del proyecto.

## Autores

- Ana Sofía Eggenberger
- Juan Pablo Madriz
- Víctor Saravia

## Contexto académico

Proyecto final del curso **Calidad y Automatización de Software** de la [Universidad Francisco Marroquín](https://www.ufm.edu/), Guatemala.

La consigna y los criterios originales están disponibles en el [repositorio oficial del profesor](https://github.com/danihrndzld/proyecto-final-calidad).

## Licencia y procedencia

El código base fue migrado de forma conservadora desde [anasofiaeggenberger/Proyecto-Priority-Queue](https://github.com/anasofiaeggenberger/Proyecto-Priority-Queue), commit <code>89fa05b</code> de <code>main</code>.

El repositorio original no contiene <code>LICENSE</code>, <code>LICENSE.md</code>, <code>COPYING</code> ni <code>NOTICE</code>, y no declara una licencia formal. Este proyecto no inventa ni concede una licencia nueva; cualquier redistribución del código heredado debe confirmarse con sus titulares.
