# Pruebas E2E

## Operación

Instalar requirements-ci.txt y requirements-e2e.txt con uv y los navegadores con Playwright
como indica README.md. Ejecutar desde la raíz:

```bash
.venv/bin/python scripts/ejecutar_e2e.py --suite regression --browser chromium
.venv/bin/python scripts/ejecutar_e2e.py --suite smoke --browser firefox
```

17 casos por navegador; smoke selecciona uno y excluye 16. regression ejecuta los 17.
El runner devuelve el código de pytest sin convertir un fallo en éxito.
La selección (suite, navegador y commit) queda en selection.json; target.json registra URL
y health de la instancia que respondió. El HTML es generado por pytest-html y JUnit por pytest.

Sin URL se inicia un servidor HTTP real, con app factory y puerto asignado por el sistema,
que se apaga al terminar. En CI se exige E2E_BASE_URL de la instancia ya desplegada:

```bash
E2E_ALLOW_CLEANUP=1 EXPECTED_AMBIENTE=ci EXPECTED_VERSION="$APP_VERSION" \\
    .venv/bin/python scripts/ejecutar_e2e.py --base-url http://127.0.0.1:8001
```

Usar una instancia exclusiva de pruebas. La fixture limpia por GET/DELETE los pacientes antes
y después de cada caso, incluso ante fallo. El contexto del navegador también es nuevo.
La cola es compartida en memoria; estos recorridos se ejecutan serialmente. El permiso de
limpieza es obligatorio para URL externa y no crea un endpoint de reset.

## Page Object Model

HospitalDashboardPage compone PatientForm y PatientQueueView. Todos los selectores están en
esos objetos, principalmente data-testid. Los tests expresan acciones y expectativas de negocio.
QueueReader y QueueActions definen contratos separados y las fixtures exponen sólo el contrato
que consume cada recorrido. La justificación SRP/ISP está en DECISIONES.md.

## Matriz verificable

| ID | Caso / archivo en tests/e2e | Técnica | Resultado esperado | Casos |
|---|---|---|---|---:|
| E2E-01 | test_smoke_registration.py | Transición y equivalencia válida | Registro, fila/resumen y recarga conservan el paciente; smoke | 1 |
| E2E-02 | test_priority_fifo_attention.py: menor prioridad/FIFO | Decisión y transición | 3/1/1 se atiende 1/1/3, empate por llegada, hasta vacío | 1 |
| E2E-03 | Mismo archivo: todos los niveles | Particiones de equivalencia | Alta 5/3/1/4/2 produce orden 1/2/3/4/5 | 1 |
| E2E-04 | test_deletion_and_empty_state.py: eliminar | Transición | Eliminar intermedio, próximo y último actualiza resumen y vacío | 1 |
| E2E-05 | Mismo archivo: cancelar | Tabla de decisión | Rechazar confirmación conserva el paciente, incluso tras recargar | 1 |
| E2E-06 | Mismo archivo: atender vacío | Equivalencia y estado | Mensaje informativo sin mutación | 1 |
| E2E-07 | test_form_validation.py: urgencia válida | Valores límite | 1 y 5 se aceptan, nombre mínimo A | 2 |
| E2E-08 | Mismo archivo: fuera de rango | Valores límite | 0 y 6 manipulados desde el navegador se rechazan en servidor | 2 |
| E2E-09 | Mismo archivo: nombre vacío | Partición inválida | Validación nativa impide el alta | 1 |
| E2E-10 | Mismo archivo: espacios | Partición inválida | Servidor muestra error y conserva vacío | 1 |
| E2E-11 | Mismo archivo: prioridad vacía | Partición inválida | Select obligatorio impide el alta | 1 |
| E2E-12 | Mismo archivo: normalización | Partición válida | Quita espacios exteriores y conserva tildes | 1 |
| E2E-13 | Mismo archivo: duplicados | Equivalencia y transición | Dos pacientes homónimos se conservan; atender retira uno | 1 |
| E2E-14 | test_responsive_dashboard.py | Equivalencias móvil/tablet | Registro y atención operables sin desbordamiento a 390/768 px | 2 |

La eliminación HTML sigue siendo por nombre según la aplicación existente; eliminar un
homónimo específico por ID es un pendiente de UI que debe coordinarse, no una ruta inventada.

## Fallos y evidencia

reports/e2e contiene report.html, junit.xml, selection.json y target.json.
Cada fallo de recorrido conserva screenshot y trace.zip bajo artifacts/.
No hay sleeps fijos ni reintentos para ocultar fallos.

```bash
.venv/bin/python -m playwright show-trace reports/e2e/artifacts/<caso>/trace.zip
```

Los ensayos locales y las ejecuciones Docker constan en EVIDENCIA.md. Los archivos TXT
conservados de comandos están en evidencia/integracion/cierre/; las muestras visuales E2E
están en evidencia/e2e/. Jenkins debe archivar los reportes de cada build, también cuando
una prueba falla.
