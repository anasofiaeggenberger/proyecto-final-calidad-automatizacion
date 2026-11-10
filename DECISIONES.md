# Decisiones técnicas

> **Estado al documentar:** `main` está en `299c7b3` (`299c7b3b41355606e6bf59670cf1ae3cf09ac5d1`).
> La implementación y las validaciones locales recientes están documentadas por separado de la
> evidencia histórica de Docker/Jenkins. No se presenta como verificado un build Jenkins nuevo,
> una entrega SMTP real ni la secuencia verde → roja → verde.

Documento compartido del equipo. Cada integrante mantiene su propia sección.

- Ana Sofía: dominio, pruebas unitarias, cobertura y gate de calidad.
- Juan Pablo: API REST, integración, Docker, ambientes y gate de integración.
- Víctor: Playwright/POM, gate E2E, notificaciones SMTP y demo; validación operativa de Jenkins/SMTP pendiente.

## Matriz de decisiones y trazabilidad

La siguiente tabla resume decisiones efectivamente reflejadas en el código. “Evidencia” identifica
archivos o pruebas reproducibles; no implica que una ejecución local sustituya una ejecución de
Jenkins. La fuente oficial es el [repositorio de instrucciones del profesor](https://github.com/danihrndzld/proyecto-final-calidad).

| ID | Decisión | Alternativa considerada | Concepto técnico | Evidencia verificable | Fuente |
|---|---|---|---|---|---|
| DEC-01 | Crear la aplicación con `create_app` y un `PatientService` por instancia | Cola global compartida | SRP, inyección y aislamiento de estado | `app.py:create_app`; `tests/unit/test_patient_service.py::test_service_instances_are_isolated` | `docs/PLAN_TECNICO.md`, secciones 11.1–11.2 |
| DEC-02 | Mantener la API en el blueprint `api/` | Agregar las rutas REST dentro de `app.py` | Separación de responsabilidades y propiedad de archivos | `api/routes.py`; registro en `app.py`; `tests/integration/test_contrato_http.py` | `docs/PLAN_TECNICO.md`, sección 11.2 |
| DEC-03 | Ordenar la cola por `(prioridad, orden_llegada)` con heap | FIFO único o varios workers con colas separadas | Invariante de dominio y FIFO en empates | `domain/patient.py:sort_key`; `domain/patient_queue.py`; pruebas de listado/atención | `docs/PLAN_TECNICO.md`, secciones 2 y 7 |
| DEC-04 | Identificar y eliminar por `id` único en API y HTML | Buscar/eliminar por nombre | Identidad estable y contrato HTTP | `app.py:eliminar`; `templates/index.html`; `tests/unit/test_app_html_deletion.py`; `tests/integration/test_eliminar_pacientes.py::test_eliminar_por_id_distingue_homonimos` | Requisito funcional y corrección consolidada en `299c7b3` |
| DEC-05 | Probar la API de integración por HTTP real con `urllib` | `app.test_client()` o agregar `requests` | Caja negra y dependencia mínima | `tests/integration/api_client.py`; `tests/integration/conftest.py`; 71 casos coleccionados | Instrucciones oficiales, testing de caja negra |
| DEC-06 | Aplicar gate de cobertura de 90 % sobre `domain` y `services` | Medir toda la aplicación o no bloquear el build | Quality gate y feedback temprano | `Jenkinsfile`, etapa `Unit Tests + Coverage`, opciones `--cov=domain`, `--cov=services`, `--cov-fail-under=90` | `docs/JENKINS.md`; requisito oficial de cobertura |
| DEC-07 | Construir una imagen por SHA y desplegarla en perfiles `ci`/`staging` con `--no-build` | Construir una imagen distinta por ambiente | Artefacto inmutable y configuración como código | `Jenkinsfile`; `Dockerfile`; `docker-compose.yml`; `scripts/gestionar_ambiente.py` | `docs/PLAN_TECNICO.md`, secciones 8–9 |
| DEC-08 | Hacer que el Health Gate conserve salida y código de `verificar_health.py` | `curl | tee` sin propagar el código de salida | Fail-fast y observabilidad | `Jenkinsfile`, etapa `Health Gate`; `scripts/verificar_health.py`; corrección `d07d642` | `docs/JENKINS.md`, sección de Health Gate |
| DEC-09 | Usar POM y separar lectura/acciones con `QueueReader` y `QueueActions` | Selectores y acciones duplicados en cada test | SRP e ISP | `tests/e2e/pages/`; `tests/e2e/contracts.py`; `tests/e2e/conftest.py` | `docs/E2E.md`; documentación oficial de Playwright |
| DEC-10 | Implementar SMTP con `smtplib` y credenciales Jenkins inyectadas | Email Extension o secretos en el repositorio | Gestión de secretos y TLS explícito | `scripts/notificar_fallo.py`; `Jenkinsfile:withCredentials`; `tests/notifications/` | `docs/JENKINS.md`; fuente [8] al final |

### Gate de cobertura: alcance y límites

El gate vigente ejecuta `pytest tests/unit` con `--cov=domain --cov=services` y
`--cov-fail-under=90` (`Jenkinsfile`, etapa `Unit Tests + Coverage`). Por lo tanto, el porcentaje
del gate mide los módulos `domain/` y `services/`; no incluye como objetivos de cobertura a
`app.py`, `api/`, `tests/` ni `scripts/`. Esas áreas sí tienen pruebas de integración, unitarias o
de pipeline donde corresponde, pero no deben contarse dentro del porcentaje del gate. Los XML
históricos de cobertura se identifican en [EVIDENCIA.md](EVIDENCIA.md) y no se presentan como una
medición nueva de `299c7b3`.

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

**Técnicas aplicadas** (secciones 7.1–7.3 del plan): las particiones, límites y decisiones se
trazan en la matriz siguiente. No todos los casos usan las tres técnicas; cada fila identifica la
técnica primaria de los casos que agrupa.

### Matriz de trazabilidad de integración

La suite tiene 71 casos coleccionados: 38 de alta, 5 de atención, 12 de contrato HTTP, 7 de
eliminación, 4 de health y 5 de listado. Las parametrizaciones se indican explícitamente para no
confundir el número de funciones con el número de casos ejecutables.

| Casos pytest reales | Técnica primaria | Entrada o condición | Resultado esperado | Requisito/regla cubierta |
|---|---|---|---|---|
| `test_alta_acepta_todas_las_prioridades_del_rango` (parametrización `[1, 2, 3, 4, 5]`); `test_alta_rechaza_prioridades_fuera_del_rango` (`[0, -1, 6, 99]`); `test_alta_rechaza_prioridades_con_tipo_invalido` (`[\"2\", \"\", 2.5, None, True, [2], {\"valor\": 2}]`) | Partición de equivalencia + valores límite | Prioridades válidas, inmediatamente fuera del rango y tipos no enteros | `201` para válidas; `400/PRIORIDAD_INVALIDA` para inválidas | Prioridad entera de 1 a 5 |
| `test_alta_rechaza_nombres_invalidos` (parametrización `[\"\", \"   \", \"\\t\\n\", None, 123, [], {}]`); `test_alta_rechaza_nombre_ausente`; `test_alta_acepta_el_nombre_mas_corto`; `test_alta_normaliza_espacios_del_nombre` | Partición de equivalencia + valor límite | Vacío, espacios, tipos no texto, ausencia, un carácter y espacios laterales | `400/NOMBRE_INVALIDO`, o alta normalizada cuando corresponde | Validación y normalización de nombre |
| `test_alta_rechaza_cuerpo_ausente`; `test_alta_rechaza_json_no_valido` (parametrización `[\"{\", \"[]\", \"texto\", \"null\"]`); `test_alta_rechaza_content_type_incorrecto`; `test_alta_rechaza_campos_desconocidos` | Tabla de decisión de entrada HTTP | Cuerpo ausente, JSON inválido, media type incorrecto o campos extra | `400` con `JSON_INVALIDO` o `CAMPOS_DESCONOCIDOS`; la cola no muta | Contrato de alta y rechazo seguro |
| `test_alta_invalida_no_muta_la_cola`; `test_eliminar_inexistente_no_muta_la_cola`; `test_atender_cola_vacia_responde_200_sin_paciente`; `test_atender_cola_vacia_es_repetible_y_no_muta` | Tabla de decisión de estado | Operación inválida o cola vacía frente a cola con datos | Error sin mutación, o `200` con `paciente: null` | Estados vacíos y atomicidad observable |
| `test_listado_ordena_por_urgencia`; `test_listado_respeta_fifo_en_empate_de_urgencia`; `test_atender_entrega_al_paciente_mas_urgente`; `test_atender_respeta_fifo_en_empate`; `test_atender_agota_la_cola_en_el_orden_esperado` | Partición de equivalencia + tabla de decisión | Prioridades diferentes y empates con orden de llegada conocido | Menor número primero; empate FIFO; la atención retira el próximo | Prioridad, FIFO y atención |
| `test_eliminar_existente_responde_204_sin_cuerpo`; `test_eliminar_id_inexistente_responde_404`; `test_eliminar_id_mal_formado_responde_404`; `test_eliminar_dos_veces_el_mismo_id_responde_404`; `test_eliminar_inexistente_no_muta_la_cola`; `test_eliminar_mantiene_el_orden_de_los_demas`; `test_eliminar_por_id_distingue_homonimos` | Partición de equivalencia + tabla de decisión | ID existente, inexistente, mal formado, repetido y homónimos | `204` sin cuerpo para existente; `404/PACIENTE_NO_ENCONTRADO` sin borrar otro; orden restante intacto | Eliminación por identidad y conservación de cola |
| `test_metodos_no_permitidos_responden_405_en_json[GET-/api/pacientes/atender]` y sus casos `PUT`, `PATCH`, `DELETE`, `POST`; `test_ruta_api_inexistente_responde_404_en_json`; `test_el_esquema_del_paciente_no_expone_campos_extra`; `test_el_esquema_de_error_es_uniforme`; `test_las_respuestas_json_declaran_su_content_type` | Tabla de decisión de contrato HTTP | Métodos/rutas permitidos o no permitidos y esquemas de respuesta | `405`/`404` JSON, campos y media type del contrato | Contrato HTTP y errores uniformes |
| `test_health_responde_ok_con_ambiente_y_version`; `test_health_declara_json`; `test_health_expone_el_ambiente_desplegado`; `test_health_expone_la_version_del_artefacto` | Partición de contrato de despliegue | Health válido y variables esperadas cuando están declaradas | `200` JSON con estado, ambiente y versión; `skip` explícito si falta expectativa | Health Gate y trazabilidad del artefacto |

La fixture `api` limpia por HTTP antes y después de cada prueba y verifica `total == 0`; el
contador de `orden_llegada` no se reinicia y por eso las aserciones comparan orden relativo. La
fuente de cada caso es `tests/integration/`; la colección reproducible es
`.venv/bin/python -m pytest --collect-only -q tests/integration`.

### 4. Docker, artefacto único y ambientes

- `Dockerfile` basado en `python:3.12-slim`, sirviendo con **gunicorn** (`requirements-prod.txt`).
  Se usa **un solo worker** porque la cola vive en memoria del proceso: con dos workers el estado se
  partiría y la prioridad/FIFO dejaría de ser observable. La concurrencia se cubre con hilos.
- El artefacto se construye **una sola vez por build** en la etapa `Build Artifact` y se etiqueta
  `hospital-queue:<SHA completo>`. El despliegue usa `docker compose up --no-build`, así que es
  imposible que el ambiente corra una imagen distinta de la construida.
- `docker-compose.yml` define dos servicios con *profiles*: `api-ci` (puerto 8001) y `api-staging`
  (puerto 8002). Comparten imagen y difieren en `APP_AMBIENTE`, puerto y contenedor, por lo que cada
  ambiente tiene su propia cola en memoria. El aislamiento se verificó en una validación Docker
  histórica registrando un paciente en `ci` y comprobando que `staging` seguía vacío; esa ejecución
  no se presenta como un build del `HEAD` actual.
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

| # | Sugerencia | Decisión | Justificación y evidencia |
|---|---|---|---|
| 1 | Separar la API en un blueprint `api/` en vez de ampliar `app.py` | **Aceptada** | Reduce el conflicto previsto en `docs/PLAN_TECNICO.md:11.2`; se verifica en `api/routes.py` y el registro del blueprint en `app.py`. |
| 2 | Usar `requests` para el cliente de integración | **Rechazada** | Habría requerido regenerar `requirements-ci.txt`; `tests/integration/api_client.py` usa `urllib` y la suite funciona sin esa dependencia adicional. |
| 3 | Servir el contenedor con `gunicorn --workers 4` | **Rechazada** | La cola es estado en memoria; `Dockerfile` conserva un worker y threads para no partir prioridad/FIFO. La regla está cubierta por pruebas de dominio y del servicio. |
| 4 | Verificar el health con `curl` y `grep` | **Rechazada** | El gate debe comparar campos y conservar el código de salida; `scripts/verificar_health.py` y `Jenkinsfile` implementan esa comparación y propagación. |

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

| Sugerencia | Decisión | Justificación y evidencia |
|---|---|---|
| Reutilizar TypeScript exactamente como en la práctica | Rechazada | El equipo acordó Python y pytest; `tests/e2e/` implementa el mismo enfoque con POM sin introducir Node. |
| Separar lectura y acciones con Protocols | Aceptada | `tests/e2e/contracts.py` y sus fixtures muestran consumidores separados, lo que permite justificar ISP. |
| Añadir endpoint de reset para limpiar E2E | Rechazada | Cambiaría el contrato de la API; `tests/e2e/support/queue_state.py` limpia con GET/DELETE existentes. |
| Dar por probado SMTP con mocks | Rechazada | Los tests de `tests/notifications/` verifican el código, pero no la entrega a un buzón; `EVIDENCIA.md` mantiene esa prueba pendiente. |

### Fuentes complementarias

[6] Microsoft, “Page object models” y “Pytest Plugin Reference,” Playwright for Python.
[En línea]. Disponibles: https://playwright.dev/python/docs/pom y
https://playwright.dev/python/docs/test-runners. Consulta: 9 nov. 2026.

[7] Jenkins Project, “Pipeline Syntax” y “Credentials Binding Plugin.”
[En línea]. Disponibles: https://www.jenkins.io/doc/book/pipeline/syntax/ y
https://www.jenkins.io/doc/pipeline/steps/credentials-binding/. Consulta: 9 nov. 2026.

[8] Python Software Foundation, “smtplib — SMTP protocol client,” Python 3.12.
[En línea]. Disponible: https://docs.python.org/3.12/library/smtplib.html. Consulta: 9 nov. 2026.

## Estado de verificación y límites

La implementación de POM, el aislamiento por contexto de navegador, los gates y la notificación
SMTP se pueden inspeccionar en sus archivos fuente y pruebas. Los resultados locales recientes y
la evidencia histórica se detallan en [EVIDENCIA.md](EVIDENCIA.md). Sigue pendiente una ejecución
real de Jenkins que acredite builds verde → rojo → verde, la detención de etapas posteriores y la
recepción de un correo SMTP. Tampoco se debe convertir la existencia de XML, capturas o trazas en
prueba de que el `HEAD` actual fue ejecutado por Jenkins.
