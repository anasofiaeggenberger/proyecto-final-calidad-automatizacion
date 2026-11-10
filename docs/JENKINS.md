# Jenkins y notificaciones

> **Estado:** el pipeline conserva los gates de calidad, construcción, despliegue,
> health, integración y E2E. Esta documentación distingue la infraestructura versionada
> de la evidencia histórica de Jenkins y de las verificaciones aún pendientes.

## Agente reproducible versionado

La aplicación usa el `Dockerfile` de la raíz para construir el artefacto Flask. El agente
Jenkins reproducible está separado en [`infra/jenkins/Dockerfile`](../infra/jenkins/Dockerfile)
y [`docker-compose.jenkins.yml`](../docker-compose.jenkins.yml). La receta está fijada para
`linux/arm64` y contiene:

- Jenkins `2.541.3-jdk21` fijado por digest.
- Python 3.12.12 administrado por uv, uv, Git y `python3`.
- Docker CLI `29.9.2` y Docker Compose plugin `5.7.0`, fijados por versión.
- Las bibliotecas de sistema necesarias para Firefox de Playwright 1.65.0.
- Firefox descargado en la imagen para que los paquetes del sistema no se instalen durante
  cada build.
- Los plugins utilizados por el Jenkinsfile, con sus versiones declaradas en
  [`infra/jenkins/plugins.txt`](../infra/jenkins/plugins.txt).

La receta es reproducible, pero no se debe presentar como un build limpio verificado hasta
construirla y validarla en un entorno separado. Esta documentación no reemplaza la evidencia
real de los Builds #4, #5 y #6.

Durante la construcción local de esta receta, `jenkins-plugin-cli` reportó advisories sobre las
versiones transitivas `workflow-multibranch:841.vec5b_9e1806ec` (SECURITY-3729) y
`pipeline-groovy-lib:798.v5cc688825312` (SECURITY-3815 y SECURITY-3796). La imagen se construyó
y validó funcionalmente, pero no se declara libre de vulnerabilidades; antes de usarla fuera de
esta entrega se deben actualizar los plugins afectados y repetir la validación.

### Construcción y arranque aislados

La instancia de ejemplo usa el puerto `8091`, el contenedor `hospital-jenkins-repro` y el
volumen nuevo `hospital-jenkins-repro-home`. No reutiliza `jenkins-hospital-review-home` ni
ningún otro volumen histórico. Se utiliza `network_mode: host` porque el pipeline despliega
la aplicación en loopback; el aislamiento de esta receta es de estado, contenedor, puerto y
volumen. En Docker Desktop, la compatibilidad del modo host debe estar habilitada.

Primero se debe obtener el socket y su GID numérico en el host. No se asume que el GID sea
`0`:

```bash
# Docker Desktop sobre macOS
export DOCKER_SOCKET_PATH=/run/host-services/docker.proxy.sock
test -S "$DOCKER_SOCKET_PATH"
export DOCKER_SOCKET_GID="$(stat -f '%g' "$DOCKER_SOCKET_PATH")"

# Linux (usar en lugar del bloque anterior)
# export DOCKER_SOCKET_PATH=/var/run/docker.sock
# test -S "$DOCKER_SOCKET_PATH"
# export DOCKER_SOCKET_GID="$(stat -c '%g' "$DOCKER_SOCKET_PATH")"

export JENKINS_HTTP_PORT=8091
docker compose -f docker-compose.jenkins.yml config --quiet
docker compose -f docker-compose.jenkins.yml build
docker compose -f docker-compose.jenkins.yml up -d
curl -fsS -o /dev/null -w 'HTTP %{http_code}\n' \
  "http://127.0.0.1:${JENKINS_HTTP_PORT}/login"
```

`group_add` agrega sólo el GID del socket al proceso `jenkins`. La pertenencia al grupo del
socket concede acceso equivalente a Docker y debe limitarse a este agente temporal; no se
debe reemplazar por `chmod 666`, `chmod 777` ni por ejecutar Jenkins como root. Si el host
utiliza otra ruta de socket, se debe cambiar únicamente la variable de entorno.

Validaciones no destructivas después del arranque:

```bash
docker compose -f docker-compose.jenkins.yml exec jenkins id -u
docker compose -f docker-compose.jenkins.yml exec jenkins id -g
docker compose -f docker-compose.jenkins.yml exec jenkins id -G
docker compose -f docker-compose.jenkins.yml exec jenkins docker version
docker compose -f docker-compose.jenkins.yml exec jenkins docker compose version
docker compose -f docker-compose.jenkins.yml exec jenkins \
  sh -c 'ldconfig -p | grep -E "lib(Xcursor|gtk-3|gdk-3|pangocairo|cairo-gobject|gdk_pixbuf)"'
```

Desde la interfaz de Jenkins se crea el primer usuario y luego un Pipeline from SCM con el
repositorio del proyecto, la rama `*/main` y el script `Jenkinsfile`. La configuración del
job no se incorpora al volumen ni a este archivo. Las credenciales SMTP se cargan sólo desde
Jenkins con los IDs documentados abajo; nunca se guardan en Compose, Git o argumentos.

Para detener la instancia sin borrar su volumen:

```bash
docker compose -f docker-compose.jenkins.yml down
```

No usar `down -v` como limpieza rutinaria: eliminaría el volumen `hospital-jenkins-repro-home`
y la configuración de esta instancia. La imagen y el volumen son independientes del Jenkins
histórico y de los contenedores `jenkins` y `jenkins-parcial-2`.

## Requisitos del agente

El agente que ejecute este job debe tener los requisitos incluidos en la receta anterior, o
una imagen equivalente aprobada:

- Python 3.12 y `python3` en PATH (el post de notificación usa `python3`).
- uv, Git, Docker Engine y el plugin Compose v2.
- Acceso controlado al daemon Docker, por socket o por la configuración aprobada del nodo.
- Un workspace exclusivo o aislado para este job. El Jenkinsfile usa `agent any`, por lo
  que la administración de Jenkins debe impedir que el job caiga en un nodo sin estos
  requisitos.
- Los plugins Pipeline/Declarative, Git, JUnit, Credentials Binding y HTML Publisher.

En el job, Setup Python sigue creando `.venv` y sincronizando los requirements hash-pinned del
workspace. En E2E Tests, el Jenkinsfile ejecuta sólo:

~~~
python -m playwright install "$BROWSER"
~~~

Esto comprueba o completa el navegador seleccionado para la versión de Playwright del
proyecto; no intenta instalar paquetes OS ni requiere root. La imagen versionada ya instala
las bibliotecas Linux y precarga Firefox durante su construcción.

## Job, polling y parámetros

Configurar un job Pipeline from SCM para leer el Jenkinsfile del commit o rama aprobados.
No crear etapas manualmente en la UI. Para la entrega, no usar la rama histórica
feat/victor-e2e-playwright; esta corrección se valida en fix/final-jenkins-playwright y
debe quedar seleccionada la referencia final aprobada por el equipo.

El trigger actual es pollSCM('H/2 * * * *'). Se conserva porque forma parte de la
configuración existente, pero puede provocar builds innecesarios por cada cambio de
documentación, evidencia o rama que observe el job. disableConcurrentBuilds() evita dos
ejecuciones simultáneas del mismo job, pero no deduplica otros jobs ni elimina builds ya
encolados. La opción preferible es webhook del SCM; si polling es obligatorio, acordar una
frecuencia menos agresiva y filtrar el alcance en la configuración del job. No deshabilitar
el trigger sin reemplazar el mecanismo de integración requerido.

Parámetros:

- ENVIRONMENT=ci|staging: instancia y ambiente verificados por health.
- SUITE=regression|smoke: regression es el valor predeterminado; smoke selecciona los
  casos marcados.
- BROWSER=chromium|firefox: motor de Playwright.
- NOTIFY_EMAILS: destinatarios autorizados, editables al lanzar el job.

Cada build crea un proyecto Compose hospital-build-<UUID>, despliega la única imagen
etiquetada con el SHA completo, obtiene una URL de loopback y limpia sólo su propio proyecto.
Los comandos manuales de Compose conservan los puertos 8001/8002.

## Orden, gates y reportes

El orden es:

1. Checkout y Setup Python.
2. Ruff.
3. Unit Tests + Coverage, con umbral de 90 %.
4. Notification Tests.
5. Build Artifact.
6. Deploy.
7. Health Gate.
8. Integration Tests.
9. E2E Tests.

Un comando con código distinto de cero detiene las etapas posteriores. El Health Gate conserva
la corrección de d07d642: redirige stdout y stderr al reporte, guarda el código de
verificar_health.py, publica el reporte con cat y termina con el mismo código. Por ello un
health inválido impide entrar a Integration Tests. El cleanup y la publicación de reportes
están en post y no convierten un build fallido en exitoso.

Se publican JUnit de unitarias, notificaciones, integración y E2E; cobertura, logs de build y
health; y el reporte HTML E2E junto con screenshots, traces y metadatos. Si Jenkins restringe
JavaScript del HTML, descargar el artefacto para verlo localmente; no relajar la seguridad
global.

## Ejecuciones Jenkins verificadas

Los Builds #4, #5 y #6 de la instancia temporal activa ejecutaron el commit
`fdceef069d2a2c33894f0982d1dde38b90330e1f`. Los artefactos `reports/build/artefacto.txt` de
cada build conservan el SHA, el ambiente y la suite; el resultado y los parámetros se
verificaron en la configuración de cada build.

| Build | Ambiente | Suite | Navegador | Resultado | Evidencia concreta |
|---:|---|---|---|---|---|
| #4 | `ci` | `regression` | Chromium | SUCCESS | Checkout y artefacto del SHA completo; el detalle numérico de pruebas no se replica aquí |
| #5 | `staging` | `smoke` | Firefox | FAILURE | Ruff, unitarias, notificaciones, cobertura, Docker, deploy, Health Gate e integración smoke superaron; Firefox falló por bibliotecas Linux ausentes |
| #6 | `staging` | `smoke` | Firefox | SUCCESS | 72 unitarias, 35 notificaciones/pipeline, 3 integración smoke, 1 E2E Firefox smoke y 99.19 % de cobertura de `domain`/`services` |

La cobertura `99.19 %` de #6 se limita a `domain` y `services`, tal como solicita el gate del
Jenkinsfile; no es cobertura de la aplicación Flask completa, la API, HTML ni scripts. Build
#6 confirma la corrección de infraestructura aplicada a la instancia temporal, pero no
demuestra una instalación Jenkins limpia desde cero porque conservó su volumen histórico.

Build #3 sigue siendo evidencia histórica de otra instancia temporal. No se debe mezclar con
#4–#6 ni presentarlo como ejecución del checkout actual. Ninguno de estos builds demuestra el
envío y la recepción de un correo SMTP real ni una secuencia intencional verde → roja → verde.

## Credenciales y notificaciones SMTP

No se incluyen secretos ni se afirma que SMTP real haya sido probado. Crear en Jenkins,
dentro del alcance del job:

1. Secret file, ID smtp-config, siguiendo la estructura de
   docs/smtp-config.example.json con host, puerto, tls=starttls (587) o ssl (465) y
   sender autorizado.
2. Username with password, ID smtp-auth, con usuario y contraseña/token del proveedor.
3. NOTIFY_EMAILS con destinatarios autorizados para la demo.

El Jenkinsfile inyecta SMTP_CONFIG_FILE, SMTP_USERNAME y SMTP_PASSWORD sólo dentro
del post fallido. set +x evita trazarlos; no deben aparecer en repositorio, argumentos ni
logs. scripts/notificar_fallo.py usa certificados verificados, STARTTLS o SMTPS, y no
degrada a texto plano. Email Extension no es necesario.

La notificación incluye build, SHA, ambiente, etapa y URL de consola. unsuccessful cubre
fallos y abortos; un error SMTP no vuelve verde el build original. El reporte
reports/notifications/status.json diferencia accepted_by_smtp de failed cuando el
script llega a ejecutarse. Las pruebas locales sólo verifican el código y no acreditan
entrega en un buzón.

## Validación pendiente

Antes de presentar el cierre como reproducible en el equipo:

- Ejecutar el job desde el agente aprobado y comprobar que Chromium y Firefox arrancan sin
  privilegios root y con las bibliotecas de la imagen.
- Ejecutar una falla controlada unitaria, de integración y E2E; verificar etapa roja,
  etapas posteriores omitidas, cleanup, artefactos y restauración.
- Configurar SMTP sólo con credenciales del administrador, verificar aceptación y recepción
  en el buzón autorizado, y registrar esa evidencia separadamente.
- Registrar número/enlace, SHA, ambiente, suite, navegador, etapa y artefactos reales en
  EVIDENCIA.md. Los archivos de evidencia por sí solos no sustituyen el build ejecutado.

Fuentes: [Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/),
[Credentials Binding](https://www.jenkins.io/doc/pipeline/steps/credentials-binding/) y
[HTML Publisher](https://www.jenkins.io/doc/pipeline/steps/htmlpublisher/).
