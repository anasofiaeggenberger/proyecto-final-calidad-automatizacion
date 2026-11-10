# Decisiones técnicas

Documento compartido del equipo. Cada integrante mantiene su propia sección.

- Ana Sofía: dominio, pruebas unitarias, cobertura y gate de calidad. *(pendiente)*
- Juan Pablo: API REST, integración, Docker, ambientes y gate de integración.
- Víctor: Playwright/POM, gate E2E, notificaciones SMTP y demo implementados; validación operativa pendiente.

---

## Juan Pablo — API REST, integración, Docker y ambientes

### 1. Implementación del contrato REST

El contrato aprobado en `docs/PLAN_TECNICO.md` (sección 4) se implementó sin modificaciones: cinco
endpoints bajo `/api`, campos en español, `id` estable por paciente, prioridad entera 1–5 y un
formato único de error.

| Método | Ruta | Éxito | Errores implementados |
|---|---|---|---|
| `GET` | `/api/health` | `200` con `estado`, `ambiente` y `version` | — |
| `POST` | `/api/pacientes` | `201` con `paciente` y `posicion` | `400` `JSON_INVALIDO`, `CAMPOS_DESCONOCIDOS`, `NOMBRE_INVALIDO`, `PRIORIDAD_INVALIDA` |
| `GET` | `/api/pacientes` | `200` con `total`, `proximo` y `pacientes` | — |
| `POST` | `/api/pacientes/atender` | `200` con `paciente`; vacío `200` con `paciente: null` y `mensaje` | — |
| `DELETE` | `/api/pacientes/<id>` | `204` sin cuerpo | `404` `PACIENTE_NO_ENCONTRADO` |

Adicionalmente, cualquier ruta `/api/*` inexistente responde `404` `RECURSO_NO_ENCONTRADO` y los
métodos no permitidos responden `405` `METODO_NO_PERMITIDO`, ambos en JSON. Esto no amplía el
contrato de negocio: evita que un error de cliente reciba una página HTML de error de Flask.

**Alternativas evaluadas**

- *Escribir las rutas dentro de `app.py`.* Descartada: el plan (sección 11.2) advierte sobre
  conflictos cuando varios integrantes editan `app.py`. La API vive en el paquete `api/` y `app.py`
  sólo gana tres líneas de registro.
- *Flask-RESTX / Flask-Smorest.* Descartada: agrega dependencias y una capa de esquemas para cinco
  endpoints, y el plan pide no introducir frameworks innecesarios.
- *Duplicar la validación en la capa HTTP.* Descartada: la validación de nombre y rango vive en
  `PatientService` (responsabilidad de Ana) y la API sólo traduce sus excepciones a códigos HTTP.

### 2. Detalles internos que el plan dejaba abiertos

| Decisión | Resolución | Motivo |
|---|---|---|
| Asignación del `id` | La genera `PatientQueue` (`p-0001`) y la API sólo la expone | Evita dos fuentes de verdad para el identificador |
| `posicion` en el alta | Se calcula como el lugar 1-based del paciente en `listar()` | El servicio no la expone y el cliente necesita saber dónde quedó |
| Inyección de ambiente/versión | Variables de entorno `APP_AMBIENTE` y `APP_VERSION`, leídas en `create_app` y expuestas en `/api/health` | El pipeline inyecta el SHA en el contenedor; nada se calcula desde fuera de la instancia |
| Tipo de `prioridad` en JSON | Se exige entero: se rechazan `"2"`, `2.5`, `true` y `null` | En JSON el tipo es explícito; aceptar texto escondería errores del cliente |
| Campos desconocidos | `400` con el listado de campos sobrantes en `detalles.campos` | Lo exige la sección 4.1 del plan |

### 3. Pruebas de integración de caja negra

Las pruebas viven en `tests/integration/` y hablan HTTP real contra la API; no usan el cliente de
pruebas de Flask ni importan el dominio. El cliente (`tests/integration/api_client.py`) está
construido sobre `urllib` de la biblioteca estándar.

- *Alternativa descartada:* `requests`. Habría obligado a regenerar `requirements-ci.txt`, que es un
  archivo bloqueado con hashes generado por `uv pip compile` y propiedad del bloque de Ana. Con
  `urllib` la suite de integración no agrega ninguna dependencia.
- *Alternativa descartada:* usar `app.test_client()`. La consigna oficial exige caja negra contra una
  API desplegada; el cliente de Flask no atraviesa la red ni el artefacto desplegado.

**Aislamiento de datos.** La fixture `api` vacía la cola por HTTP antes y después de cada prueba y
verifica que llegue en `total == 0`. El `orden_llegada` no se reinicia entre pruebas —`PatientQueue`
no reutiliza órdenes a propósito— por lo que las pruebas afirman que la secuencia sea creciente, no
valores absolutos.

**Instancia bajo prueba.** Si existe `API_BASE_URL`, la suite prueba esa instancia desplegada (es el
caso del pipeline). Si no existe, levanta un proceso propio en un puerto libre y lo apaga en
`finally`, de modo que la misma suite sirve para verificación local sin Docker.

**Técnicas aplicadas** (secciones 7.1–7.3 del plan): particiones de equivalencia de `nombre`,
`prioridad`, estado de la cola y eliminación; valores límite `0`, `1`, `5`, `6`, `""`, `"   "` y
`"A"`; y la tabla de decisión completa, incluyendo que un alta inválida no mute la cola.

### 4. Docker, artefacto único y ambientes

- `Dockerfile` basado en `python:3.12-slim`, sirviendo con **gunicorn** (`requirements-prod.txt`).
  Se usa **un solo worker** porque la cola vive en memoria del proceso: con dos workers el estado se
  partiría y la prioridad/FIFO dejaría de ser observable. La concurrencia se cubre con hilos.
- El artefacto se construye **una sola vez por build** en la etapa `Build Artifact` y se etiqueta
  `hospital-queue:<SHA completo>`. El despliegue usa `docker compose up --no-build`, así que es
  imposible que el ambiente corra una imagen distinta de la construida.
- `docker-compose.yml` define dos servicios con *profiles*: `api-ci` (puerto 8001) y `api-staging`
  (puerto 8002). Comparten imagen y difieren en `APP_AMBIENTE`, puerto y contenedor, por lo que cada
  ambiente tiene su propia cola en memoria. El aislamiento se verificó registrando un paciente en
  `ci` y comprobando que `staging` seguía vacío.
- *Alternativa descartada:* un solo contenedor con dos puertos o dos workers. No daría estados
  separados ni un `ambiente` distinguible en `/api/health`.
- *Alternativa descartada:* aislamiento por procesos sin Docker. Se mantiene como plan de respaldo si
  el agente de Jenkins no tiene Docker: las pruebas ya saben levantar su propia instancia, pero
  entonces habría que replicar a mano el etiquetado por SHA.

### 5. Pipeline: etapas propias y gates

Se agregaron después del bloque unitario de Ana, sin modificar sus etapas:

1. `Build Artifact` — registra el SHA, construye la imagen una vez y guarda `reports/build/artefacto.txt`.
2. `Deploy` — levanta el perfil del ambiente elegido con `--no-build`.
3. `Health Gate` — `scripts/verificar_health.py` exige `estado: ok`, el ambiente seleccionado y el
   SHA construido. Si la instancia no reporta ese SHA, el build se detiene antes de probar nada.
4. `Integration Tests` — ejecuta `tests/integration` contra la instancia desplegada y publica JUnit.

El bloque `post { always { ... } }` apaga los contenedores de ambos perfiles y guarda sus logs
incluso ante fallo o timeout. Se añadió `timeout(time: 30, unit: 'MINUTES')` para que un bloqueo
termine en build abortado en lugar de un job colgado.

**Parámetros.** `ENVIRONMENT` (`ci`/`staging`) selecciona instancia, puerto y configuración, y es lo
que el `Health Gate` verifica. `SUITE` (`smoke`/`regression`) cambia qué casos de integración se
ejecutan mediante el marcador `smoke`. Los parámetros `BROWSER` y `NOTIFY_EMAILS` corresponden a
Víctor. El umbral de cobertura se mantiene fijo en el pipeline y no se expone como parámetro para
que nadie pueda eludir el gate de Ana al lanzar un build.

### 6. Sugerencias de IA aceptadas y rechazadas

| # | Sugerencia | Decisión | Motivo |
|---|---|---|---|
| 1 | Separar la API en un blueprint `api/` en vez de ampliar `app.py` | **Aceptada** | Reduce el conflicto previsto en la sección 11.2 del plan y deja la propiedad del archivo clara |
| 2 | Usar `requests` para el cliente de integración | **Rechazada** | Obligaba a regenerar `requirements-ci.txt`, archivo bloqueado con hashes del bloque de Ana; `urllib` cubre el caso sin dependencias |
| 3 | Servir el contenedor con `gunicorn --workers 4` | **Rechazada** | La cola es estado en memoria del proceso; varios workers la partirían y romperían prioridad/FIFO. Se dejó `--workers 1 --threads 4` |
| 4 | Verificar el health desde el pipeline con `curl` y `grep` | **Rechazada** | Un `grep` del SHA pasa por coincidencia parcial; el script compara campo por campo y falla con un mensaje legible |

### 7. Fuentes

1. ISO/IEC/IEEE 29119-4:2021, *Software and systems engineering — Software testing — Part 4: Test techniques*, IEEE, Piscataway, NJ, USA, 2021.
2. G. J. Myers, C. Sandler y T. Badgett, *The Art of Software Testing*, 3.ª ed. Hoboken, NJ, USA: Wiley, 2011.
3. J. Humble y D. Farley, *Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation*. Boston, MA, USA: Addison-Wesley, 2010.
4. R. Fielding, M. Nottingham y J. Reschke, "HTTP Semantics," RFC 9110, IETF, jun. 2022. [En línea]. Disponible: https://www.rfc-editor.org/rfc/rfc9110
5. R. T. Fielding, "Architectural Styles and the Design of Network-based Software Architectures," tesis doctoral, Univ. of California, Irvine, CA, USA, 2000.

## Víctor — Playwright, gate E2E, SMTP y demo

### Pruebas de interfaz y técnicas

Se implementaron 17 casos independientes en Python con Playwright/pytest: uno smoke y el resto
de regresión. Cubren registro, recarga, prioridad 1–5, FIFO, atención, eliminación confirmada o
cancelada, vacío, límites 0/1/5/6, validación nativa y del servidor, nombres duplicados y móvil/tablet.
La [matriz E2E](docs/E2E.md) enlaza caso, técnica y resultado esperado.

Se tomó como referencia la práctica local practica-e2e-playwright: selectores en POM, casos
ISTQB y trazas/capturas al fallar. Se eligió Python frente a TypeScript para respetar el acuerdo
del equipo y reutilizar pytest/JUnit sin incorporar Node al agente.

El estado se prepara y limpia por HTTP mediante QueueState; el recorrido de negocio siempre
se realiza en el navegador. Cada prueba usa un contexto nuevo. En CI es obligatorio apuntar a
la instancia desplegada; no hay fallback local silencioso. El servidor HTTP en puerto dinámico
se reserva al desarrollo. La cola compartida exige ejecución serial y un ambiente exclusivo.

### Dos principios SOLID con implementación y consumidores

| Principio | Clases y consumidor concreto | Problema que evita |
|---|---|---|
| SRP | PatientForm concentra el formulario; PatientQueueView concentra tabla/resumen/acciones; HospitalDashboardPage los compone | Un cambio de formulario no obliga a modificar selectores de la cola ni duplicarlos en cada test |
| ISP | QueueReader y QueueActions son Protocols separados en contracts.py; la fixture queue entrega QueueReader a registro/validación y queue_actions entrega QueueActions a atención/eliminación | Las pruebas que sólo consultan no dependen de una interfaz que también obliga a implementar acciones destructivas |

PatientQueueView satisface ambas interfaces estructuralmente. La separación se encuentra en
código y en fixtures/consumidores, y no se justifica por mera inyección de constructor.

### Gate, parámetros y artefactos

Se conserva el gate de 90 % de Ana y las etapas de artefacto/ambientes/integración de Juan.
Lint revisa errores de sintaxis y nombres con Ruff antes de unitarias. Las herramientas E2E
tienen un lock separado con hashes, restringido por requirements-ci.txt para no cambiar el
entorno de dominio. El pipeline añade pruebas del correo antes del build y E2E después de
integración. El código de salida de pytest llega a Jenkins sin una tubería que lo oculte.

ENVIRONMENT selecciona ci/staging; SUITE smoke/regression cambia integración y E2E; BROWSER
chromium/firefox cambia el navegador y queda registrado en selection.json. NOTIFY_EMAILS
cambia destinatarios. JUnit, HTML, selección, health, trazas y capturas se archivan incluso al
fallar. Se evita concurrencia del mismo job por el estado y los nombres fijos de Compose.

### Correo y demo

Se eligió smtplib de la biblioteca estándar frente a Email Extension para que host, puerto,
TLS, usuario y contraseña se inyecten explícitamente por Credentials Binding desde el
Jenkinsfile. SMTP_CONFIG_FILE contiene servidor/puerto/remitente; smtp-auth aporta usuario y
contraseña. Sólo se permiten STARTTLS o TLS directo con validación de certificado.
No se publican secretos ni respuestas SMTP en logs.

El correo contiene build, SHA, ambiente, etapa fallida y enlace al log. unsuccessful cubre
fallo y aborto/timeout; si SMTP falla se conserva el resultado fallido original. Las pruebas
verifican formato, rechazo de cabeceras y TLS sin enviar mensajes reales. Un servidor que
acepta el mensaje no demuestra recepción en el buzón: esa evidencia sigue pendiente.

Los tres parches de demo modifican código de aplicación, no pruebas, y el asistente sólo los
aplica en ramas demo/. Se verifican en un worktree temporal y se revierten sin git reset.
El [guion](docs/DEMO.md) distingue los ensayos locales de los builds reales aún pendientes.

### Sugerencias de IA

| Sugerencia | Decisión | Motivo |
|---|---|---|
| Reutilizar TypeScript exactamente como en la práctica | Rechazada | El equipo acordó Python y pytest; se reutiliza el diseño, no otro stack |
| Separar lectura y acciones con Protocols | Aceptada | Permite demostrar ISP con contratos y consumidores reales |
| Añadir endpoint de reset para limpiar E2E | Rechazada | Cambiaría la API de Juan; la limpieza usa GET/DELETE existentes |
| Dar por probado SMTP con mocks | Rechazada | Los mocks prueban el código, no la entrega de correo; se deja el buzón pendiente |

### Fuentes complementarias

[6] Microsoft, “Page object models” y “Pytest Plugin Reference,” Playwright for Python.
[En línea]. Disponibles: https://playwright.dev/python/docs/pom y
https://playwright.dev/python/docs/test-runners. Consulta: 9 nov. 2026.

[7] Jenkins Project, “Pipeline Syntax” y “Credentials Binding Plugin.”
[En línea]. Disponibles: https://www.jenkins.io/doc/book/pipeline/syntax/ y
https://www.jenkins.io/doc/pipeline/steps/credentials-binding/. Consulta: 9 nov. 2026.

[8] Python Software Foundation, “smtplib — SMTP protocol client,” Python 3.12.
[En línea]. Disponible: https://docs.python.org/3.12/library/smtplib.html. Consulta: 9 nov. 2026.

## Actualización de auditoría PR #8

Ver [informe de auditoría](docs/AUDITORIA_PR8.md).
La evidencia anterior conserva sus SHAs y conteos históricos. La auditoría actual registra
22 pruebas SMTP, cobertura 99.12 % y smoke/regression en ambos navegadores.
No se considera validado el aislamiento entre jobs: disableConcurrentBuilds sólo protege
el mismo job; Compose y su cleanup comparten nombres y puertos. La solución compartida
requiere aprobación. Dominio concurrente, Jenkins real y SMTP recibido siguen pendientes.
