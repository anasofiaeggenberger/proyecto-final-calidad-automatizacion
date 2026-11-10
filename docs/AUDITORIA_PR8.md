# Auditoría final del PR #8

> **Estado actualizado:** concurrencia y aislamiento entre builds corregidos y probados.
> Ver [cierre de correcciones](CIERRE_CORRECCIONES.md). Los estados anteriores se conservan como historial;
> quedan únicamente las comprobaciones externas de Jenkins/SMTP y la entrega del equipo.

**Informe histórico de ae5cab5. Los hallazgos de código se resolvieron tras autorización.**

Estado vigente y pruebas: [Cierre de correcciones](CIERRE_CORRECCIONES.md).

Se corrigieron los defectos SMTP dentro del alcance del PR. Quedan un defecto de concurrencia
en dominio y una condición insegura de aislamiento entre jobs, además de la validación real
de Jenkins/SMTP. No se declara el proyecto completamente validado.

## A. Defectos confirmados

| Archivo / línea | Causa e impacto | Acción y prueba |
|---|---|---|
| scripts/notificar_fallo.py:63 | Se ignoraba el diccionario de destinatarios rechazados de smtplib; un envío parcial se marcaba accepted_by_smtp | Se eleva SMTPRecipientsRefused, CLI devuelve 1 y escribe failed; regresión roja antes del arreglo y verde después |
| scripts/notificar_fallo.py:79 | JSON válido pero con raíz null/lista, host incorrecto o puerto null podía producir excepciones no manejadas | Validación explícita de objeto, host y puerto; pruebas CLI verifican exit=1, status y ausencia de secretos |
| domain/patient_queue.py:24 | Construcción, contadores y heap no se protegen como una sola operación | Dos altas intercaladas generan p-0001 y orden de llegada duplicados; FIFO deja de tener desempate único |
| domain/patient_queue.py:50 y :57 | Comprobar estado/buscar y luego retirar son operaciones separadas | Dos threads atendiendo o eliminando el único paciente producen IndexError en uno |
| Jenkinsfile:148 y :253 | Compose usa el proyecto hospital-queue y nombres/puertos fijos; down afecta al proyecto compartido | Confirmado por inspección de configuración; no se ejecutó un borrado cruzado real |

Los dos hallazgos de dominio se reprodujeron con threads reales y barreras mediante
sys.settrace en puntos concretos, sin cambiar el código de producción. El intercalado
demuestra falta de atomicidad; no mide su frecuencia bajo carga HTTP normal.
Se comprobaron IDs, llegadas, prioridad ordenada y retiro. El orden de prioridades no falló
en el caso reproducido; sí fallan unicidad, desempate FIFO y seguridad de eliminación/atención.

### Correcciones fuera de alcance y propuesta para aprobar

El prompt solicita: “No hagás un refactor del dominio desde el PR #8 sin autorización” y
“Si la solución implica modificar infraestructura compartida, reportala para aprobación”.
Por ello no se modificaron PatientQueue, Gunicorn, Dockerfile ni Compose.

Proponer un PR separado del responsable de dominio con un RLock por cola y bloqueo consistente
de todas las operaciones de lectura/escritura y compuestas, más tests concurrentes. No basta
con bloquear sólo el incremento del ID. Como contención de despliegue, evaluar servir un
solo thread; tampoco se aplica aquí sin acuerdo.

Para Compose, la solución mínima compatible con ci/staging es una exclusión global del
recurso hospital-queue en TODOS los jobs que comparten daemon, desde deploy hasta cleanup.
disableConcurrentBuilds sólo protege el mismo job. Ejemplo para aprobar, requiere el plugin
Lockable Resources y que todos los jobs adopten el mismo recurso:

```groovy
options {
    lock(resource: 'hospital-queue')
}
```

La exclusión debe abarcar también el post/cleanup; verificar ese alcance en Jenkins real.
Una alternativa es un agente/daemon exclusivo por job. El aislamiento por build requeriría
quitar container_name fijo y asignar proyecto/puertos únicos, preservando health ci/staging:
es una modificación mayor del contrato de infraestructura y no se implementa en este commit.
Mientras tanto no compartir el daemon entre jobs que usan este Compose. Incluso un fallo
antes de Deploy ejecuta actualmente el down de post: no correr el job junto a otra instancia.

## B. Diagnóstico descartado y riesgos no confirmados

- **Directorio JUnit: no es un defecto.** Desde un directorio sin reports, pytest 8.4.2
  creó reports/notifications/junit.xml y las 22 pruebas pasaron. Una prueba fallida controlada
  creó también el padre del reporte y devolvió 1. No se agregó un mkdir innecesario.
- P1: Jenkins real/Groovy Declarative, omisión de etapas tras fallo y timeout no ejecutados.
  Los 20 bloques shell pasan sh -n; esto no valida sintaxis Declarative ni plugins.
- P1: correo real y credenciales del agente no disponibles; sólo mocks y CLI local.
- P2 heredado: Flask usa una clave de sesión fija de desarrollo si FLASK_SECRET_KEY no se
  inyecta. Proponer configuración por secreto al responsable; no cambiar producción aquí.
- P2: E2E y las fixtures HTTP eliminan datos de la instancia seleccionada; usar sólo una
  instancia exclusiva y autorizar E2E_ALLOW_CLEANUP=1. Esto no habilita paralelismo de casos.

## C. Cambios del único commit

| Archivo | Cambio |
|---|---|
| scripts/notificar_fallo.py | Rechazo parcial tratado como fallo y validación de configuración |
| tests/notifications/test_failure_notification.py | Mock fiel a la respuesta vacía de smtplib y regresión de rechazo parcial |
| tests/notifications/test_notification_cli.py | 11 casos CLI: éxito, configuración, credenciales, errores y ejecución como proceso |
| scripts/auditar_concurrencia.py | Reproductor aislado; exit 1 indica defecto detectado, no test de aceptación |
| Jenkinsfile | regression por defecto, conservando smoke seleccionable, cobertura y Health Gate |
| .gitattributes | Whitespace de evidencia generada se conserva literalmente; código sí se revisa |
| README.md, DECISIONES.md, EVIDENCIA.md | Estado y enlace a esta auditoría, sin cambiar resultados históricos |
| docs/JENKINS.md, docs/ESTADO_PROYECTO.md | Base main actualizada, default regression, advertencia precisa de aislamiento |
| docs/AUDITORIA_PR8.md | Este informe A–G |
| evidencia/integracion/auditoria-pr8/ | Evidencia nueva, logs, JUnit, cobertura y manifiesto con hashes |

La selección regression como default cubre los 71 casos HTTP y los 17 E2E que smoke reduce
a 3 y 1. Se justifica para validar el conjunto antes de integrar a main. No cambia reglas de
negocio ni agrega parámetros de falla. Las opciones smoke y ambos navegadores siguen disponibles.

## D. Validación ejecutada

Todos los comandos usan .venv/bin/python desde la raíz; cada XML/log se conserva en la
carpeta de auditoría. HTTP real local en procesos/puertos aislados; no se modificó Docker.

| Comando resumido | Resultado |
|---|---|
| -m ruff check app.py api domain services tests scripts | Sin errores |
| -m pytest tests/unit -q --cov=domain --cov=services --cov-fail-under=90 | 59 aprobadas; 99.12 % |
| -m pytest tests/integration -q | 71 aprobadas |
| -m pytest tests/notifications -q | 22 aprobadas |
| scripts/ejecutar_e2e.py --suite smoke --browser chromium | 1 aprobada, 16 excluidas por selección |
| scripts/ejecutar_e2e.py --suite regression --browser chromium | 17 aprobadas |
| scripts/ejecutar_e2e.py --suite smoke --browser firefox | 1 aprobada, 16 excluidas por selección |
| scripts/ejecutar_e2e.py --suite regression --browser firefox | 17 aprobadas |
| scripts/auditar_concurrencia.py | Exit 1 esperado: defecto heredado reproducido |

Total: **188 ejecuciones aprobadas**, incluyendo smoke repetido dentro de regression; no son
188 casos únicos. Las regresiones controladas SMTP/concurrencia se registran aparte y no se
ocultan. HTML/JUnit de los cuatro recorridos E2E existen bajo reports/audit; los JUnit,
selección y target de cada combinación se conservan en evidencia.

POM, data-testid, fixtures de limpieza y matriz de recorridos se revisaron sin modificarlos.
El fallo E2E de demo ya conserva screenshot y trace históricos; se verifican sus archivos.
No se fabricó un fallo nuevo de aplicación sólo para regenerar evidencia visual.

El orden de etapas sigue siendo checkout, setup, lint, unitarias/cobertura, notificaciones,
build, deploy, health, integración, E2E. Ruff/pytest conservan su salida a Jenkins; no hay
catchError que los convierta en éxito. post conserva el estado original y captura errores SMTP.
El cuerpo operativo del Health Gate coincide con origin/main: captura el código, muestra el
log y sale con ese código. Sólo se excluye del cotejo la instrumentación env.FAILED_STAGE
que ya tenía PR8.

## E. Evidencia y trazabilidad

Base: 09ccc08f6a84f0ed8ee6a08ee5bbd7b1f7eb059d.
Main incorporado sin reescribir historial: 4dde2eb06f871eeecbf7d35c364826542a7434c5.
Las pruebas se ejecutaron sobre esa base más los cambios de este único commit, todavía sin
confirmar al probar. manifiesto.json registra hashes SHA-256 de los archivos ejecutados para
compararlos con el commit final. No se atribuyen estas pruebas a un SHA inexistente.

Los reportes históricos de otros SHAs se conservaron intactos. La evidencia nueva sustituye
el directorio personal por $REPO, sin cambiar los resultados. Ver:
- workspace-limpio.json: creación de JUnit y salida no cero del fallo controlado.
- smtp-rojo.xml: test de rechazo parcial que falla antes de la corrección.
- notificaciones.xml y notificaciones.txt: 22 casos posteriores en verde.
- concurrencia.txt: duplicados e IndexError reproducibles.
- pipeline.json: validación shell y comparación del Health Gate.
- unitarias.xml / coverage.xml, integracion.xml y e2e-*/: resultados de cada capa.
- manifiesto.json: fecha Guatemala, base/main, fuente exacta y resultados.

## F. Pendientes externos

Jenkins/agente real, plugins/validador Declarative, pruebas de timeout/gates end-to-end y
credenciales SMTP. No se enviaron correos. Docker sólo se consultó para buscar Jenkins:
no había un contenedor Jenkins; no se detuvo ni eliminó ningún recurso.

## G. Estado del PR #8

**REQUIERE CORRECCIONES ADICIONALES:** SMTP corregido y suites locales verdes; el dueño del
dominio debe resolver o acordar la contención de concurrencia, y el equipo debe aprobar el
aislamiento entre jobs. Jenkins real y recepción SMTP siguen pendientes.
No se modificó main ni se hizo merge del PR. La actualización desde main y la auditoría
se agrupan en un solo commit sobre la rama existente.

Fuentes primarias:
[pytest JUnit](https://docs.pytest.org/en/stable/_modules/_pytest/junitxml.html),
[Python smtplib](https://docs.python.org/3.12/library/smtplib.html).
