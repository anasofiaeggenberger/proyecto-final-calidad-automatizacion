# Jenkins y notificaciones

> **Estado actualizado:** concurrencia y aislamiento entre builds corregidos y probados.
> Ver [cierre de correcciones](CIERRE_CORRECCIONES.md). Los estados anteriores se conservan como historial;
> quedan únicamente las comprobaciones externas de Jenkins/SMTP y la entrega del equipo.

## Requisitos del agente

Python 3.12, python3 en PATH para el correo, uv, Git, Docker Engine y Compose v2.
Usar un agente dedicado al proyecto, con acceso al daemon Docker. En Linux, preparar las
bibliotecas de Playwright o permitir que playwright install --with-deps las instale.
El timeout E2E incluye la preparación del navegador; conviene precargar navegadores para la demo.

Plugins: Pipeline/Declarative, Git, JUnit, Credentials Binding y HTML Publisher.
Configurar un job Pipeline from SCM que lea Jenkinsfile de la rama elegida. No crear etapas
a mano en la UI. pollSCM revisa cambios cada dos minutos; la primera ejecución registra
parámetros y activa el trigger. La rama de entrega es feat/victor-e2e-playwright; la demo
de fallos usa otro job/rama demo/ para no romperla.

CI genera un proyecto hospital-build-<UUID> y puertos de loopback asignados por Docker.
El helper gestionar_ambiente.py devuelve la URL y el post sólo limpia ese proyecto tras
verificar etiquetas de propiedad. Los comandos manuales de Compose conservan 8001/8002.

## Parámetros y gates

ENVIRONMENT=ci/staging selecciona la instancia. SUITE=regression/smoke (default regression) selecciona
3/71 casos de integración y 1/17 casos E2E. BROWSER=chromium/firefox cambia el navegador.
NOTIFY_EMAILS toma el correo de Git como default y permite editar destinatarios al lanzar.

Orden: checkout, setup, lint, unitarias/cobertura 90 %, pruebas de notificación, build único
etiquetado con SHA completo, deploy --no-build, health con SHA/ambiente, integración y E2E.
Las etapas siguientes no corren si un comando falla. El timeout global es 30 minutos y el de
E2E 8 minutos. Los abortos por timeout también intentan notificar.

JUnit y cobertura se archivan; HTML Publisher publica reports/e2e/report.html.
También se conservan screenshots/traces, metadatos de selección y health.
Si Jenkins restringe JavaScript del HTML, descargar el artefacto para verlo localmente;
no es necesario relajar la política global de seguridad.

## Configuración SMTP pendiente

No existe un servidor ni credenciales SMTP proporcionados para esta entrega local.
No se afirma que un correo haya sido enviado o recibido.

Crear en Jenkins, dentro del ámbito del job:

1. Secret file con ID smtp-config: JSON según smtp-config.example.json, usando host, puerto,
   tls=starttls (587) o ssl (465), y sender autorizado.
2. Username with password con ID smtp-auth: usuario SMTP y contraseña/token del proveedor.
3. Seleccionar NOTIFY_EMAILS con los destinatarios autorizados para el build de demo.

El Jenkinsfile inyecta SMTP_CONFIG_FILE, SMTP_USERNAME y SMTP_PASSWORD sólo durante
la notificación. Los secretos no se escriben en el repositorio, argumentos o logs.
Se usa smtplib con certificados verificados y sin fallback a texto plano.
Email Extension no es necesario.

El correo incluye número de build, SHA, ambiente, etapa fallida y enlace a console.
unsuccessful cubre fallo y aborto. Un fallo SMTP no convierte el build original en verde.
reports/notifications/status.json diferencia accepted_by_smtp de failed cuando el script
llega a ejecutarse; credenciales ausentes en Jenkins se registran en el log del post.

## Validación final que requiere el entorno del equipo

Ejecutar un build sano, otro con cada falla de demo y otro restaurado; comprobar gates
y artifacts. Recibir el correo real y guardar captura del buzón. Registrar links y números
reales en EVIDENCIA.md, incluyendo un build en cada ambiente y un timeout.
Las pruebas locales de notificaciones sólo verifican el código; no acreditan la entrega SMTP.

Fuentes: [Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/),
[Credentials Binding](https://www.jenkins.io/doc/pipeline/steps/credentials-binding/) y
[HTML Publisher](https://www.jenkins.io/doc/pipeline/steps/htmlpublisher/).

## Actualización de auditoría PR #8

Ver [informe de auditoría](AUDITORIA_PR8.md).
La evidencia anterior conserva sus SHAs y conteos históricos. La auditoría actual registra
22 pruebas SMTP, cobertura 99.12 % y smoke/regression en ambos navegadores.
No se considera validado el aislamiento entre jobs: disableConcurrentBuilds sólo protege
el mismo job; Compose y su cleanup comparten nombres y puertos. La solución compartida
requiere aprobación. Dominio concurrente, Jenkins real y SMTP recibido siguen pendientes.
