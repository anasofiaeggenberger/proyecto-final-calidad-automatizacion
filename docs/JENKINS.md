# Jenkins y notificaciones

> **Estado:** el pipeline conserva los gates de calidad, construcción, despliegue,
> health, integración y E2E. El cambio de Playwright de esta rama sólo evita instalar
> paquetes del sistema durante un build Jenkins sin privilegios root.

## Requisitos del agente

El agente que ejecute este job debe tener:

- Python 3.12 y python3 en PATH (el post de notificación usa python3).
- uv, Git, Docker Engine y el plugin Compose v2.
- Acceso controlado al daemon Docker, por socket o por la configuración aprobada del nodo.
- Un workspace exclusivo o aislado para este job. El Jenkinsfile usa agent any, por lo
  que la administración de Jenkins debe impedir que el job caiga en un nodo sin estos
  requisitos.
- Los plugins Pipeline/Declarative, Git, JUnit, Credentials Binding y HTML Publisher.

El Dockerfile de la raíz construye la aplicación, no una imagen de agente Jenkins. No hay
una imagen de agente Jenkins versionada en este repositorio. La solución mínima reproducible
es mantener una imagen de agente aprobada por Infraestructura, fijada por digest, que incluya
Python 3.12, uv, Docker/Compose y las bibliotecas del navegador. Durante la construcción
de esa imagen, con privilegios de build, debe ejecutarse el equivalente a:

~~~
COPY requirements-ci.txt requirements-e2e.txt /opt/deps/
RUN uv venv --python 3.12 /opt/venv \
 && uv pip sync --python /opt/venv/bin/python /opt/deps/requirements-ci.txt \
 && uv pip install --python /opt/venv/bin/python --require-hashes \
      -r /opt/deps/requirements-e2e.txt \
 && /opt/venv/bin/python -m playwright install --with-deps chromium firefox
~~~

La base concreta debe ser una imagen Jenkins compatible con el modelo de agente utilizado
(SSH, inbound o Docker cloud), y debe fijarse por digest en la infraestructura del equipo.
No se agrega una imagen incompleta al repositorio de la aplicación: elegir una base o un
modelo de conexión inexistente haría que la receta no fuera reproducible. La instalación
con --with-deps queda exclusivamente en la construcción de esa imagen, nunca en cada build.

En el job, Setup Python puede seguir creando .venv y sincronizando los requirements
hash-pinned del workspace. En E2E Tests, el Jenkinsfile ejecuta sólo:

~~~
python -m playwright install "$BROWSER"
~~~

Esto instala el navegador seleccionado para la versión de Playwright del proyecto; no intenta
instalar paquetes OS ni requiere root. Si la imagen precarga también los navegadores, se debe
conservar la misma versión de Playwright y comprobar el cache antes de presentar el build.

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

La evidencia aportada para el cierre informa un Build #3 exitoso con Ruff, 67 unitarias,
35 pruebas de notificaciones/pipeline, 71 de integración, 17 E2E Chromium, cobertura
99.19 %, deploy/health/cleanup Docker y reportes publicados. Ese dato es evidencia de una
instancia temporal y no una ejecución reproducida en este checkout. Tampoco prueba el envío
o la recepción de un correo SMTP real.

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
