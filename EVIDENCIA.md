# Evidencia de ejecución

> **Estado documental:** `main` está en `299c7b3b41355606e6bf59670cf1ae3cf09ac5d1`.
> Este documento separa resultados locales recientes, evidencia histórica y comprobaciones aún
> pendientes. Un reporte, captura o archivo XML no demuestra por sí solo que el `HEAD` actual haya
> sido ejecutado por Jenkins.

## 1. Resultado local reciente

La siguiente validación se realizó después de corregir la eliminación HTML por ID, en el working
tree que posteriormente se consolidó en `299c7b3`. Los manifiestos `selection.json` disponibles
para Playwright registran el checkout `46c466259f958bb3976a8195c37109f043a47ded` (`46c4662`),
por lo que estos resultados no se atribuyen a la ejecución del commit final ni a Jenkins.

| Verificación | Resultado observado | Ambiente | SHA verificable en el artefacto | Evidencia disponible | Clasificación |
|---|---:|---|---|---|---|
| Ruff | OK | Local | No registrado en un manifiesto versionado | Comando de validación local | VERIFICADO LOCALMENTE |
| Unitarias | 72 aprobadas, 0 fallos, 0 omitidas | Local | No hay JUnit reciente versionado con ese conteo | Resultado de la ejecución local; `evidencia/unitarias/` contiene reportes históricos | VERIFICADO LOCALMENTE |
| Integración HTTP | 71 aprobadas, 0 fallos, 0 omitidas | Flask temporal en localhost | No hay JUnit reciente versionado con ese conteo | Resultado de la ejecución local; `tests/integration/` permite reconstruir la colección | VERIFICADO LOCALMENTE |
| E2E Chromium, regresión | 17 aprobadas, 0 fallos, 0 omitidas | Servidor HTTP local temporal | `reports/e2e/chromium-regression/selection.json` → `46c4662` | Reporte local ignorado por Git | VERIFICADO LOCALMENTE |
| E2E Chromium, smoke | 1 aprobada, 0 fallos, 16 deseleccionadas | Servidor HTTP local temporal | `reports/e2e/chromium-smoke/selection.json` → `46c4662` | Reporte local ignorado por Git | VERIFICADO LOCALMENTE |
| E2E Firefox, regresión | 17 aprobadas, 0 fallos, 0 omitidas | Servidor HTTP local temporal | `reports/e2e/firefox-regression/selection.json` → `46c4662` | Reporte local ignorado por Git | VERIFICADO LOCALMENTE |
| E2E Firefox, smoke | 1 aprobada, 0 fallos, 16 deseleccionadas | Servidor HTTP local temporal | `reports/e2e/firefox-smoke/selection.json` → `46c4662` | Reporte local ignorado por Git | VERIFICADO LOCALMENTE |

Los comandos de referencia para repetir estas capas son los definidos en `Jenkinsfile`,
`docs/E2E.md` y `README.md`. Las ejecuciones anteriores no iniciaron Jenkins ni constituyen un
build CI. La cobertura no se declara como resultado actual de esta tabla: los XML disponibles de
cobertura son históricos y se identifican en la sección 2.

### Composición reproducible de integración

La colección actual de `tests/integration/` contiene 71 casos ejecutables:

| Archivo | Casos coleccionados | Técnica o alcance |
|---|---:|---|
| `test_alta_pacientes.py` | 38 | Alta, validación, límites y JSON |
| `test_atender_pacientes.py` | 5 | Prioridad, FIFO y cola vacía |
| `test_contrato_http.py` | 12 | Métodos, rutas, esquemas, tipos y aislamiento |
| `test_eliminar_pacientes.py` | 7 | ID existente, inválido, repetido, homónimos y orden |
| `test_health.py` | 4 | Estado, ambiente, versión y media type |
| `test_listado_pacientes.py` | 5 | Cola vacía, prioridad, FIFO y no mutación |
| **Total** | **71** | `.venv/bin/python -m pytest --collect-only -q tests/integration` |

La matriz de técnicas y casos se encuentra en [DECISIONES.md](DECISIONES.md), sección “Matriz de
trazabilidad de integración”.

## 2. Evidencia histórica identificable

### Build #3 de Jenkins temporal

`docs/JENKINS.md` documenta un Build #3 exitoso de una instancia temporal con Ruff, 67 pruebas
unitarias, 35 pruebas de notificaciones/pipeline, 71 de integración, 17 E2E Chromium, cobertura de
`domain` y `services` de 99.19 %, despliegue/health/cleanup Docker y reportes publicados. Esa
referencia es **histórica**:
no acredita una ejecución del `HEAD` `299c7b3`, no aporta en este repositorio un enlace de consola
reconstruible y no prueba el envío o la recepción de un correo SMTP real.

El manifiesto [`evidencia/integracion/cierre-correcciones/manifiesto.json`](evidencia/integracion/cierre-correcciones/manifiesto.json)
identifica otra validación con `sha_base` `ae5cab5889cc7b318423b1cc76cfa7740df309d0`, cobertura de
`domain` y `services` de 99.19 %, 102 casos unitarias/pipeline, 71 de integración por ambiente y
E2E de 17 casos. El mismo manifiesto declara `declarative_jenkins` no validado y
`correo_real_enviado: false`. No debe
presentarse como el Build #3 del `HEAD` actual.

### Otros artefactos versionados

| Artefacto | Qué demuestra | Límite de uso |
|---|---|---|
| [`evidencia/integracion/auditoria-pr8/manifiesto.json`](evidencia/integracion/auditoria-pr8/manifiesto.json) | Validación local anterior: 71 integración, 59 unitarias, 22 notificaciones y E2E de ambos navegadores | `sha_base` `09ccc08f...`; declara `jenkins_ejecutado: false` y `correo_enviado: false` |
| [`evidencia/integracion/junit-local.xml`](evidencia/integracion/junit-local.xml) | Un reporte local de 71 pruebas de integración | Es histórico y no registra el `HEAD` actual |
| [`evidencia/unitarias/junit-local.xml`](evidencia/unitarias/junit-local.xml) | Un reporte local de 59 pruebas unitarias | No es el conteo reciente de 72 |
| [`evidencia/unitarias/coverage-local.xml`](evidencia/unitarias/coverage-local.xml) | Cobertura histórica de `domain`/`services`: 99.12 % | No es una medición nueva de `299c7b3` |
| `evidencia/e2e/local-chromium/` y `evidencia/e2e/local-firefox/` | Recorridos locales anteriores de 17 casos por navegador | Sus `selection.json` registran SHAs anteriores (`18801fa` y `8bc7719`) |
| `evidencia/e2e/deployed-ci/` y `evidencia/e2e/deployed-staging/` | Ensayos contra Docker con health, selección y JUnit | Son históricos; no prueban una ejecución Jenkins nueva |
| `evidencia/e2e/fallo-controlado/` y `evidencia/e2e/restauracion/` | Fallo y recuperación local de E2E | No prueban que Jenkins haya omitido etapas ni enviado correo |

Los artefactos históricos conservan valor como evidencia de los ensayos que describen, pero sus
SHAs, fechas y ambientes deben acompañarlos siempre. No se mezclan con los resultados locales de
la sección 1.

## 3. Afirmaciones implementadas pero aún no acreditadas operativamente

| Requisito | Implementación inspeccionable | Evidencia operativa faltante | Estado |
|---|---|---|---|
| Health Gate bloqueante | `Jenkinsfile` conserva stdout/stderr, código de `scripts/verificar_health.py`, `cat` y `exit` | Build Jenkins que demuestre health rojo y ausencia de `Integration Tests` | PENDIENTE DE VERIFICACIÓN |
| Orden y bloqueo del pipeline | Stages declarados en `Jenkinsfile`; comando fallido usa código distinto de cero | Build real desde checkout limpio | PENDIENTE DE VERIFICACIÓN |
| Dos ambientes con un artefacto | `Dockerfile`, `docker-compose.yml` y `scripts/gestionar_ambiente.py` | Build con SHA, URLs, image ID y logs vinculados al mismo build | PENDIENTE DE VERIFICACIÓN |
| Notificación SMTP | `scripts/notificar_fallo.py`, `withCredentials` y tests locales | Correo real recibido con build, SHA, ambiente, etapa y enlace | PENDIENTE DE VERIFICACIÓN |
| Demo verde → roja → verde | Guion y fallos reversibles en [`docs/DEMO.md`](docs/DEMO.md) | Tres builds Jenkins identificables y restauración posterior | PENDIENTE DE VERIFICACIÓN |
| Instalación Jenkins limpia | Requisitos descritos en [`docs/JENKINS.md`](docs/JENKINS.md) | Agente real preparado desde cero, plugins, Docker, navegadores y credenciales | PENDIENTE DE VERIFICACIÓN |

Los tests de notificaciones prueban formato, validaciones, TLS y manejo de credenciales sin enviar
mensajes reales. Por eso “tests SMTP en verde” no equivale a “correo recibido”.

## 4. Plantilla para completar con evidencia Jenkins real

No se rellenan celdas con números, enlaces o SHAs que no existan. Cada fila deberá conservar el
log/artefacto y el checkout exacto que la produjo.

| Build | Ambiente | Parámetros (`ENVIRONMENT`, `SUITE`, `BROWSER`) | SHA completo | Resultado/etapa | Prueba o fallo | Enlace de consola | Artefactos | SMTP recibido |
|---|---|---|---|---|---|---|---|---|
| pendiente | `ci` | `ci`, `regression`, `chromium` | pendiente | verde | — | pendiente | JUnit, coverage, health, E2E | no verificado |
| pendiente | `staging` | `staging`, `smoke`, `firefox` | pendiente | verde | — | pendiente | JUnit, health, E2E | no verificado |
| pendiente | `ci` | parámetros del build | pendiente | rojo | etapa/prueba real pendiente | pendiente | log y reportes del fallo | pendiente |
| pendiente | `ci` | parámetros del build | pendiente | verde restaurado | — | pendiente | reportes posteriores | no verificado |
| pendiente | `ci` o `staging` | parámetros del build | pendiente | abortado/timeout | etapa real pendiente | pendiente | log, cleanup, notificación | pendiente |

## 5. Fuentes y reproducibilidad

- Pipeline, orden de etapas, gate de cobertura, Health Gate, publicación y cleanup: [`Jenkinsfile`](Jenkinsfile).
- Requisitos del agente y límites de la evidencia Jenkins temporal: [`docs/JENKINS.md`](docs/JENKINS.md).
- Diseño y ejecución E2E: [`docs/E2E.md`](docs/E2E.md).
- Guion de fallos controlados y recuperación: [`docs/DEMO.md`](docs/DEMO.md).
- Decisiones, cobertura y matriz de técnicas: [`DECISIONES.md`](DECISIONES.md).
- Requisitos oficiales: [repositorio del profesor](https://github.com/danihrndzld/proyecto-final-calidad).

La próxima actualización de este archivo debe incorporar únicamente artefactos generados por el
entorno que se quiera acreditar, con fecha, SHA completo, parámetros, resultado y enlace
identificable. Hasta entonces, SMTP real, Jenkins verde → rojo → verde y la reproducibilidad desde
un Jenkins limpio permanecen sin verificar.
