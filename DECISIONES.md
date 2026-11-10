# Decisiones técnicas

Documento compartido del equipo. Cada integrante mantiene su propia sección.

- Ana Sofía: dominio, pruebas unitarias, cobertura y gate de calidad. *(pendiente)*
- Juan Pablo: API REST, integración, Docker, ambientes y gate de integración.
- Víctor: Playwright/POM, gate E2E, notificaciones SMTP y demo. *(pendiente)*

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
