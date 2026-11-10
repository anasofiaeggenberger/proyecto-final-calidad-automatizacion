# Guía operativa para agentes de IA — Proyecto Final de Calidad y Automatización

**Fecha de preparación:** 5 de noviembre de 2026
**Repositorio:** https://github.com/anasofiaeggenberger/proyecto-final-calidad-automatizacion
**Fecha oficial publicada:** 10 de noviembre de 2026, 14:29 (hora de Guatemala).
**Equipo:** Ana Sofía, Juan Pablo y Víctor.

> **Importante:** Este documento conserva instrucciones operativas y decisiones de planificación de
> una etapa anterior. Para el estado vigente deben consultarse `README.md`, `DECISIONES.md`,
> `EVIDENCIA.md` y `docs/ESTADO_PROYECTO.md`. Si existe una contradicción, prevalecen las
> instrucciones oficiales de https://github.com/danihrndzld/proyecto-final-calidad y se debe
> informar al equipo.

> **Actualización de implementación — `main` en `299c7b3`.** El código vigente contiene dominio,
> unitarias, API/HTTP, Docker/ambientes y 17 E2E por navegador con POM, gate, SMTP y demo. El resto
> conserva la planificación original y sus estados “futuro” o “no existe” son históricos. Jenkins,
> SMTP real y entrega final siguen pendientes de acreditación.

## 1. Contexto y estado real

Se reutiliza, con autorización de los autores, un proyecto académico de cola de prioridad hospitalaria: https://github.com/anasofiaeggenberger/Proyecto-Priority-Queue. La aplicación actual usa Python y Flask, plantillas HTML y CSS. Permite registrar pacientes con urgencia 1–5, ver la cola, atender al paciente más urgente y eliminar pacientes. En empates debe respetar el orden de llegada (FIFO). Se retiró la interfaz antigua «Sin Estructura» y se creó un dashboard visual renovado. La cola se almacena en memoria: se reinicia con el proceso y no debe tratarse como almacenamiento persistente.

La migración, la API JSON, las suites por capas y el pipeline están implementados en la base actual.
Las validaciones locales recientes y sus límites se registran en `EVIDENCIA.md`; eso no equivale a
un build Jenkins actual ni a SMTP real.

Los documentos de planificación son la referencia compartida para los tres integrantes una vez aprobada su PR. Cada responsable debe crear su propia rama a partir de la última versión aprobada de `main` y respetar el contrato API aprobado y las responsabilidades establecidas.

## 2. Archivos de la base conocida

```text
app.py                    # Rutas y lógica web Flask (actualmente acopladas)
paciente.py               # Implementación usada por la web; verificar API exacta
priority_queue.py         # Implementación de cola del flujo CLI; no confundir con la web
paciente1.py              # Archivo legado; inspeccionar antes de retirar
main.py                   # Entrada CLI heredada
simulacion.py             # Simulación heredada
utils.py                  # Utilidades heredadas
requirements.txt          # Dependencias de ejecución
static/css/styles.css     # Diseño del dashboard
templates/index.html      # UI del dashboard con data-testid
README.md                 # Instalación y contexto
.gitignore
```

Las clases `PatientQueue`, `PatientService`, la app factory y los endpoints `/api/*` existen en la
base actual. Sus contratos y límites se documentan en `docs/PLAN_TECNICO.md` y `DECISIONES.md`.

## 3. Instalación y ejecución local

```bash
git clone https://github.com/anasofiaeggenberger/proyecto-final-calidad-automatizacion.git
cd proyecto-final-calidad-automatizacion
uv python install 3.12
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
python app.py
```

Abrir `http://127.0.0.1:5000/`. Detener el servidor con `Ctrl+C`. Si ya existe `.venv`, no recrearlo. El repositorio base fue probado en macOS Apple Silicon con Python 3.12.14 y uv 0.12.17. En otros sistemas adaptar la activación del entorno. Las herramientas de pruebas, Docker y Jenkins requerirán configuración adicional aún por definir.

## 4. Objetivo de la entrega

Sistema web con API HTTP, lógica separable, pruebas unitarias con cobertura como gate, integración de caja negra contra una API desplegada, al menos tres recorridos E2E con Playwright/POM, pipeline con gates, dos ambientes seleccionables, parámetros observables, correo real de fallo, documentación, evidencias y demo controlada. La fuente oficial confirma además el artefacto único identificado por SHA, el registro de ambiente/versión por HTTP, los entregables `DECISIONES.md`, `EVIDENCIA.md` y `evidencia/`, y tres commits por integrante. El contrato API aprobado está en la sección 4 de `docs/PLAN_TECNICO.md`; el umbral de cobertura sigue siendo una decisión del equipo.

Para la demo se debe mostrar un cambio real y reversible en código de aplicación que haga fallar la capa elegida, detenga las siguientes etapas y produzca el correo recibido. No simular éxito ni fabricar evidencia.

## 5. Decisiones técnicas y trabajo planificado

- Mantener Python 3.12, Flask y el dashboard existente; no introducir frameworks innecesarios.
- Refactorizar hacia servicio de dominio (`PatientService`) y cola aislable (`PatientQueue`) y una app factory (`create_app`) que reciba configuración/dependencias, **sin cambiar la semántica de prioridad/FIFO**.
- Usar IDs únicos para pacientes, especialmente para eliminación: los nombres pueden repetirse.
- **Contrato API aprobado para el desarrollo:** `GET /api/health`, `GET /api/pacientes`, `POST /api/pacientes`, `POST /api/pacientes/atender` y `DELETE /api/pacientes/<id>`. Los campos JSON, validaciones, códigos HTTP y formatos de respuesta se encuentran definidos en la sección 4 de `docs/PLAN_TECNICO.md` y son obligatorios para la implementación. Cualquier cambio debe acordarse y documentarse antes de modificar código o pruebas.
- `Patient` representa un `id` único y estable, `nombre`, `prioridad` y `orden_llegada`; `PatientQueue` mantiene prioridad/FIFO en una instancia; `PatientService` centraliza la validación 1–5 y los casos de uso sin depender de Flask. HTML y API deben usar el mismo servicio y la misma cola de la instancia, nunca colas separadas.
- Mantener el estado por instancia y ambiente. Las pruebas no deben depender de datos de ejecuciones anteriores ni compartir una cola global.
- Herramientas vigentes: pytest + pytest-cov, cliente HTTP contra una instancia real para integración, Playwright con Python + POM, Docker Compose y Jenkins. El cliente Flask puede complementar, pero no sustituye la integración de caja negra.
- Ambientes vigentes `ci` y `staging`, cada uno con instancia y datos propios. Nunca publicar secretos SMTP.

## 6. Distribución EXCLUSIVA de responsabilidades

Cada integrante tiene una responsabilidad principal, una parte específica de infraestructura/pipeline y una parte de documentación/evidencia. **Nadie debe asumir que “los tres” harán una tarea sin un dueño definido.**

### Ana Sofía — dominio, unitarias, cobertura y gate de calidad

**Código:** refactorizar lógica de cola y servicio, garantizar prioridad 1–5, FIFO y estado aislable; coordinar con Juan Pablo sólo las interfaces internas antes de cambiarlas. **Pruebas:** crear pruebas unitarias con fixtures, límites 0/1/5/6, cola vacía, empate FIFO, duplicados, orden de atención y eliminación; medir cobertura. **CI:** hacerse dueña del bloque `unit + coverage` y del gate unitario/calidad, con reportes JUnit y cobertura como artefactos. **Documentación/evidencia:** reglas de dominio, matriz unitaria, umbral justificado en `DECISIONES.md`, reporte de cobertura y build detenido por regresión o cobertura en `EVIDENCIA.md`/`evidencia/`. **No tocar:** rutas REST finales de Juan Pablo, páginas POM de Víctor ni SMTP sin acuerdo.

### Juan Pablo — API, integración y ambientes

**Código:** implementar el contrato REST JSON aprobado, respuestas/errores consistentes y health con ambiente/SHA, usando el servicio de Ana sin duplicar la lógica. **Pruebas:** integración HTTP contra la API desplegada, con particiones de equivalencia, valores límite, tabla de decisión, aislamiento y contrato. **Infraestructura/CI:** hacerse dueño de Docker/Compose o aislamiento equivalente, del artefacto único, los dos ambientes y el gate de integración. **Documentación/evidencia:** contrato API, matriz de caja negra, configuración de ambientes/Docker, requests/responses y logs de health en `DECISIONES.md`/`EVIDENCIA.md`. **No tocar:** CSS/POM ni gate unitario de Ana sin coordinación.

### Víctor — E2E, notificaciones y demo

**Código/pruebas:** crear suite Playwright con Page Object Model y al menos tres recorridos independientes, uno marcado como smoke: registro/listado, prioridad/FIFO/atención y eliminación/cola vacía; usar `data-testid`, datos aislados y capturas/trazas al fallar. **CI:** hacerse dueño del bloque E2E, publicación de reportes, parámetros de suite/navegador y notificación SMTP real. **Demo:** preparar una falla reversible por capa y su evidencia. **Documentación/evidencia:** matriz E2E, dos principios SOLID con clases/problemas, configuración segura de correo, guion y builds en `DECISIONES.md`/`EVIDENCIA.md`. Si se propone Interface Segregation, debe existir una implementación concreta de abstracciones/interfaces y evidencia de sus consumidores; dividir Page Objects por sí solo no cuenta. Si no se puede demostrar, sustituirlo por otro principio justificable. **No tocar:** implementación de dominio ni contrato REST sin coordinación.

### Regla de participación individual

Los tres deben **escribir pruebas**, **modificar el pipeline** y tener **al menos tres commits propios** en el historial del commit entregado. El nombre y correo Git de cada commit deben corresponder a quien lo escribió. Para cumplir la participación, Ana agrega unitarias y gate de calidad, Juan integración y gate de integración, y Víctor E2E, notificaciones y gate E2E. Los cambios se hacen desde cuentas y ramas propias; no se crean commits a nombre de otra persona.

## 7. Orden histórico de ejecución y dependencias

La siguiente secuencia conserva cómo se planificó y coordinó la implementación. El estado actual y
las verificaciones pendientes se encuentran en `docs/ESTADO_PROYECTO.md` y `EVIDENCIA.md`.

**Bloque 0 — Documentación:** la guía operativa y el plan técnico deben mantenerse alineados mediante PR. El contrato API ya está aprobado; antes de implementar componentes dependientes, el equipo debe registrar únicamente las decisiones internas y operativas que siguen abiertas.

**Bloque 1 — Dominio e implementación:** Ana define la semántica interna de `PatientQueue` y sus fixtures respetando `id`, `nombre`, `prioridad`, `orden_llegada`, validación 1–5 y FIFO; Juan implementa la API aprobada sobre el mismo `PatientService`/`PatientQueue`. Sólo deben acordar detalles internos de inyección, DTOs y mapeo de errores, sin cambiar el contrato REST. Ninguno debe inventar interfaces públicas nuevas por separado.

**Bloque 2 — Paralelo:** Juan implementa API, integración, Docker y ambientes; Víctor crea POM y puede preparar E2E sobre la interfaz HTML estable; Ana termina cobertura y gate unitario. Víctor ejecuta el E2E final cuando exista una instancia desplegada y los selectores estén congelados.

**Bloque 3 — CI coordinado:** Ana Sofía crea el `Jenkinsfile` inicial con el gate unitario y de cobertura. Juan Pablo incorpora posteriormente las etapas de build, despliegue, ambientes y gate de integración. Víctor agrega al final las etapas E2E, reportes y notificaciones SMTP. La integración de cambios al pipeline se realiza mediante PRs en el orden Ana → Juan Pablo → Víctor. Cada integrante debe modificar personalmente el pipeline y realizar commits propios. El resto del desarrollo puede avanzar en paralelo.

**Bloque 4 — Integración:** PRs con revisión, pruebas locales, merge ordenado a `main`, pipeline end-to-end, evidencias, ensayos de fallas, tag y preparación del archivo MIU. No mezclar cambios incompatibles ni hacer force-push a `main`.

## 8. Convenciones Git

Cada persona clona el repo y trabaja desde `main` actualizado:

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/<nombre-de-tarea>
# trabajar, probar y revisar
git status
git diff --check
git add <archivos-de-su-tarea>
git commit -m "test: describe la prueba o funcionalidad"
git push -u origin feat/<nombre-de-tarea>
```

Ramas sugeridas: `feat/ana-domain-unit`, `feat/juan-api-integration` y `feat/victor-e2e-demo`. Reservar bloques del `Jenkinsfile` en ese orden y actualizar la siguiente rama desde `main` después de cada PR aprobado. Abrir PR contra `main`, explicar cambios, comandos, evidencia y riesgos. Nunca sobrescribir cambios ajenos, borrar tests para lograr verde, ni agregar secretos al repositorio.

## 9. Contrato mínimo de pruebas

| Capa | Escenarios clave | Evidencia |
|---|---|---|
| Unitarias (Ana) | prioridad 1–5, límites 0 y 6, FIFO en empate, cola vacía, orden, eliminar | pytest, cobertura, JUnit |
| Integración (Juan Pablo) | API HTTP desplegada, JSON válido/inválido, códigos del contrato, equivalencia, límites, decisión, aislamiento y health/SHA | reportes, requests/responses y logs de ambiente |
| E2E (Víctor) | tres recorridos mínimos con Playwright/POM, uno smoke; prioridad/FIFO, atención, eliminar y estado vacío | Playwright HTML, trazas/screenshots |
| Pipeline | lint/unit antes de build; artefacto único; deploy; integración y E2E contra instancia; gates y correo | logs, builds, artifacts y correo recibido |

El porcentaje de cobertura lo decide el grupo y se justifica en `DECISIONES.md`; no se inventa un valor oficial. La fuente oficial sí fija el mínimo de tres commits por integrante, tres E2E con uno smoke, integración contra API desplegada, artefacto identificado por SHA, dos ambientes, ambiente más dos parámetros adicionales, correo con datos del build y los entregables documentales.

## 10. Criterios de finalización

- Aplicación se instala desde README y funciona con datos de prueba.
- Registro, listado, prioridad, FIFO, atención y eliminación funcionan y están cubiertos.
- API JSON documentada y validada con integración.
- Tres recorridos E2E o más con POM, uno smoke, y dos principios SOLID justificados.
- Pipeline parametrizado construye una sola vez, despliega el artefacto con SHA y bloquea etapas posteriores al fallar.
- Dos ambientes diferenciados, seleccionables y demostrables con health que exponga ambiente y versión.
- Correo real con número de build, SHA, ambiente, etapa y enlace al log, sin credenciales en Git.
- Los tres tienen al menos tres commits propios, pruebas propias y cambios de pipeline propios.
- README, `DECISIONES.md`, `EVIDENCIA.md`, `evidencia/`, matrices, instrucciones y demo actualizados. `DECISIONES.md` incluye alternativas, conceptos, evidencia, fuentes IEEE y tres sugerencias de IA aceptadas/rechazadas; `EVIDENCIA.md` traza builds verde/rojo/verde, SHA, ambientes, cobertura, etapa fallida y conteo por capa.
- Repo público, tag y archivo MIU con URL, nombre del tag y SHA completo del commit entregado.

## 11. Guion base de demostración

La fuente oficial asigna 15 minutos de demo y 5 de preguntas. El flujo debe ser:

1. Mostrar app funcionando, repositorio, tag y commit entregado.
2. Lanzar el pipeline con los dos ambientes y parámetros configurables.
3. Ejecutar pipeline sano; enseñar gates, reportes, artefacto/health y builds por ambiente.
4. Introducir un defecto **real y reversible en código de aplicación**, nunca desactivar un test, para la capa que escoja el catedrático; llevar una falla preparada por capa.
5. Mostrar build fallido, etapa detenida, logs, evidencia y correo SMTP real en el buzón indicado.
6. Restaurar código, repetir ejecución sana y explicar decisiones técnicas.

El commit de ruptura de demo no se califica y el build automático que dispara su push tampoco. No provocar fallas sobre `main` sin un procedimiento reversible; preferir rama/ambiente de demo y documentar pasos exactos.

## 12. Instrucción lista para pegar al agente de cada integrante

> Lee íntegramente `docs/GUIA_AGENTES_PROYECTO_FINAL.md`, `docs/PLAN_TECNICO.md`, `README.md`, el código del repositorio y las instrucciones oficiales enlazadas. Identifica mi rol en la sección 6 y trabaja **solo en mis responsabilidades**. Antes de escribir código, resume arquitectura real, contratos compartidos, dependencias y archivos a modificar. Si una dependencia no está lista, prepara componentes independientes y pregunta por el contrato, sin inventarlo. Implementa de manera incremental, ejecuta pruebas, conserva compatibilidad y reporta resultados verificables. No hagas commit/push/merge sin autorización expresa. No modifiques trabajo de los demás ni almacenes credenciales. Mi nombre/rol es: [REEMPLAZAR POR ANA SOFÍA / JUAN PABLO / VÍCTOR].

## 13. Riesgos y preguntas pendientes

- El contrato JSON, `id`, campos y códigos HTTP ya están aprobados y deben respetarse. Los IDs únicos ya están implementados en `domain/patient_queue.py`; queda conservar la evidencia correspondiente a cada ejecución.
- El porcentaje de cobertura no lo fija la fuente oficial: debe justificarse en `DECISIONES.md`, junto con módulos excluidos.
- Docker/Compose está implementado y cuenta con evidencia histórica de ejecución; queda confirmar su disponibilidad en el agente Jenkins que se utilice para un build del `HEAD` actual.
- La integración debe probar una API desplegada y el health debe exponer ambiente y SHA; el cliente Flask aislado no basta como única evidencia.
- Definir Jenkins host, puertos, navegador y SMTP; el correo real requiere credenciales inyectadas y un destino autorizado.
- Evitar que todos modifiquen simultáneamente `app.py` o `Jenkinsfile`; establecer bloques reservados, orden de integración y revisión de PRs.
- Confirmar si el CLI continúa en alcance antes de retirar `main.py` y sus módulos.

**Regla final:** no basta con que Codex diga «completado». Cada responsable debe mostrar comandos, resultados, cambios, commits, evidencia y cumplimiento de la consigna oficial.
