# Evidencia de ejecución

Documento compartido del equipo. Cada integrante mantiene su propia sección y sus archivos en
`evidencia/`.

## Conteo de pruebas por capa

| Capa | Responsable | Casos | Estado |
|---|---|---:|---|
| Unitarias | Ana Sofía | 59 | verde (cobertura 99.12 %, umbral 90 %) |
| Integración HTTP | Juan Pablo | 71 (3 marcados `smoke`) | verde contra el contenedor desplegado |
| E2E Playwright | Víctor | 17 (1 marcado smoke) | verde en Chromium y Firefox; también contra Docker |
| Notificaciones | Víctor | 10 | verde, sin envío real |

---

## Juan Pablo — API, integración y ambientes

### Verificación local realizada

Ejecutada sobre el commit `d6822810b74b5efed0f8d79c85143fa5ccb228f7` (base de la rama
`feat/juan-api-integration`), con Docker 28.4.0 y Docker Compose v2.39.2 en macOS Apple Silicon.

| Archivo | Contenido |
|---|---|
| `evidencia/integracion/verificacion-local.txt` | SHA e id de la imagen, `/api/health` de `ci` y `staging`, prueba de aislamiento entre ambientes y requests/responses de cada caso del contrato |
| `evidencia/integracion/pytest-local.txt` | Salida de las 71 pruebas de integración contra el contenedor `ci` |
| `evidencia/integracion/junit-local.xml` | Reporte JUnit de esa misma ejecución |
| `evidencia/integracion/gate-health-negativo.txt` | El gate de health fallando con SHA incorrecto, ambiente incorrecto e instancia caída |

Resultados observados:

- Artefacto único: `hospital-queue:d6822810b74b5efed0f8d79c85143fa5ccb228f7`,
  image id `sha256:543255862dfbf0d7ce2169b1c39f53f1d64abf6dc4dda96a56c33f80672d736a`.
- `GET /api/health` en `ci` → `{"ambiente": "ci", "estado": "ok", "version": "d6822810…"}` (puerto 8001).
- `GET /api/health` en `staging` → `{"ambiente": "staging", "estado": "ok", "version": "d6822810…"}` (puerto 8002).
- Ambos ambientes corrieron **la misma imagen** y reportaron el SHA del artefacto.
- Aislamiento: un alta en `ci` dejó `total: 1` en `ci` y `total: 0` en `staging` al mismo tiempo.
- Integración: 71 pruebas en verde contra `ci`; 3 pruebas `smoke` en verde contra `staging`.
- Gate de health: salida distinta de cero en los tres escenarios negativos, con el motivo exacto en el log.

### Comandos para reproducirla

```bash
export APP_VERSION=$(git rev-parse HEAD)
docker build --build-arg APP_VERSION="$APP_VERSION" -t hospital-queue:"$APP_VERSION" .
docker compose --profile ci up -d --no-build
.venv/bin/python scripts/verificar_health.py \
    --url http://127.0.0.1:8001/api/health --ambiente ci --version "$APP_VERSION"
API_BASE_URL=http://127.0.0.1:8001 EXPECTED_AMBIENTE=ci EXPECTED_VERSION="$APP_VERSION" \
    .venv/bin/python -m pytest tests/integration -v
docker compose --profile ci --profile staging down -v --remove-orphans
```

### Pendiente: evidencia de builds de Jenkins

Las etapas `Build Artifact`, `Deploy`, `Health Gate` e `Integration Tests` están en el `Jenkinsfile`
y su lógica de shell fue ejecutada y verificada localmente, pero **todavía no existe un build de
Jenkins**: falta definir el host, el agente con Docker y el job. No se registran números de build,
enlaces de log ni correos que no se hayan producido.

Al tener el job disponible deben llenarse estas filas con capturas y logs reales:

| Build | Ambiente | Suite | SHA | Etapa fallida | Resultado |
|---|---|---|---|---|---|
| *(pendiente)* | `ci` | `regression` | | — | verde |
| *(pendiente)* | `ci` | `regression` | | `Integration Tests` | rojo |
| *(pendiente)* | `ci` | `regression` | | — | verde tras revertir |
| *(pendiente)* | `staging` | `smoke` | | — | verde |

### Falla controlada preparada para la demo (capa de integración)

Cambio real y reversible en código de aplicación, **sin desactivar ninguna prueba**: en
`api/routes.py`, dentro de `eliminar_paciente`, devolver `200` en lugar de `204`.

```python
    return "", 200   # rompe el contrato: la etapa Integration Tests queda roja
```

Efecto esperado: `test_eliminar_existente_responde_204_sin_cuerpo` falla, la etapa
`Integration Tests` queda roja, las etapas posteriores no se ejecutan y el `post` apaga los
contenedores. Se restaura devolviendo `204`.

Alternativa igual de válida para la misma capa: en `crear_paciente`, devolver `200` en lugar de
`201`, o eliminar la verificación de `CAMPOS_DESCONOCIDOS`.

---

## Víctor — E2E, pipeline, notificaciones y demo

### Comprobación final local

9 de noviembre de 2026, macOS Apple Silicon, Python 3.12.13, Playwright 1.65.0,
pytest 8.4.2. El commit de código/documentación al ejecutar el cierre fue
`bea1816`; el commit siguiente únicamente conserva esta evidencia.

- **157 aprobadas** en la ejecución conjunta: 59 unitarias, 71 integración HTTP,
  17 E2E Chromium y 10 notificaciones. Sin casos omitidos ni fallos.
- Cobertura de domain/services: **99.12 %**, frente al gate de 90 %.
- Ruff: sin errores para app.py, api, domain, services, tests y scripts.
- E2E local por separado: 17/17 Chromium y 17/17 Firefox.
- El reporte HTML completo queda en reports/final/report.html (generado, ignorado en Git).

La evidencia conservada no contiene builds ni correos inventados. Los ensayos locales
corren HTTP real y Playwright, pero no acreditan ejecución dentro de Jenkins.

### Artefacto y ambientes verificados

Se construyó la imagen identificada por el SHA completo
`4010a7e3a09e6d39605932355a226c5dacad7c2a`, una vez para esta validación.
Se desplegó el mismo image ID en ci:8001 y staging:8002 con --no-build.

| Ambiente | Integración | E2E | Health |
|---|---:|---:|---|
| ci | 71/71 regresión | 17/17 Chromium | estado ok, ambiente ci y SHA exacto |
| staging | 3/3 smoke | 1/1 Firefox smoke | estado ok, ambiente staging y mismo SHA |

El registro de un paciente en ci produjo total=1 allí y total=0 en staging.
El gate de health devolvió código 1 al exigir una versión incorrecta.
Ambos contenedores del proyecto se apagaron al terminar. Los cambios posteriores al
SHA de la imagen agregan demo/documentación/evidencia; no cambian la aplicación empaquetada.

### Fallas reales y recuperación

Ensayadas en un worktree temporal de la rama demo/validar-gates, sobre `fbe8565`
más el parche de aplicación sin commit. No se modificaron ni desactivaron pruebas.

| Capa | Rojo observado | Tras revertir el parche |
|---|---|---|
| Unitarias | 9 fallaron al invertir la prioridad | 59 aprobadas |
| Integración | 1 fallo y 2 aprobadas de smoke al responder alta 200 | 3 smoke aprobadas |
| E2E | 1 fallo de smoke por cambio de testid | 1 smoke aprobada |

La captura y la traza del fallo E2E se conservaron. Los códigos de salida y los diffs reales
están en los logs; esto verifica detección y reversibilidad local. Falta demostrar que
Jenkins omite etapas posteriores y envía el correo en su entorno.

### Archivos de evidencia

| Ruta | Contenido |
|---|---|
| evidencia/integracion/cierre/ | TXT de health, pytest, Docker/aislamiento y fallo SHA; JUnit ci/staging y cierre conjunto |
| evidencia/integracion/cierre/demo/ | TXT de rojo/verde y JUnit de unitarias/integración del ensayo |
| evidencia/e2e/local-chromium/ y local-firefox/ | JUnit, selección y target de las regresiones locales |
| evidencia/e2e/deployed-ci/ y deployed-staging/ | JUnit, selección y health de los recorridos contra Docker |
| evidencia/e2e/fallo-controlado/ | JUnit, selección, target, screenshot y trace.zip del fallo de interfaz |
| evidencia/unitarias/ | JUnit y XML de cobertura medidos en esta sesión |
| evidencia/notificaciones/ | JUnit de las 10 pruebas del módulo SMTP |
| evidencia/integracion/cierre/manifiesto.json | SHAs, fecha, comandos y conteos extraídos del JUnit final |

Los TXT de salida de comandos se guardan bajo evidencia/integracion, como se solicitó.
Los requirements*.txt permanecen en raíz porque son manifiestos de instalación usados por
Docker, uv y Jenkins.

### Validación operativa pendiente

No se proporcionó un Jenkins ni servidor/credenciales SMTP. El envío está implementado en
scripts/notificar_fallo.py y Jenkinsfile, con TLS y credenciales inyectadas, pero **no se ha
enviado ni recibido un correo real**. Las 10 pruebas no contactan buzones.

Completar estas filas en el entorno del equipo antes de presentar la entrega como cerrada:

| Build/enlace | SHA | Ambiente | Suite/navegador | Estado/etapa | Correo recibido |
|---|---|---|---|---|---|
| pendiente | | ci | regression/chromium | verde | — |
| pendiente | | staging | smoke/firefox | verde | — |
| pendiente | | ci | regression/chromium | rojo por capa | pendiente |
| pendiente | | ci | regression/chromium | verde restaurado | — |
| pendiente | | ci | cualquiera | timeout/aborto | pendiente |

El guion y la configuración están en docs/DEMO.md y docs/JENKINS.md.
El tag final y la entrega MIU corresponden al cierre integrado del equipo.
