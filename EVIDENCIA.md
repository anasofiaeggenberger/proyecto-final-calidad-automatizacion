# Evidencia de ejecución

Documento compartido del equipo. Cada integrante mantiene su propia sección y sus archivos en
`evidencia/`.

## Conteo de pruebas por capa

| Capa | Responsable | Casos | Estado |
|---|---|---:|---|
| Unitarias | Ana Sofía | 59 | verde (cobertura 99.12 %, umbral 90 %) |
| Integración HTTP | Juan Pablo | 71 (3 marcados `smoke`) | verde contra el contenedor desplegado |
| E2E Playwright | Víctor | 0 | pendiente |

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
