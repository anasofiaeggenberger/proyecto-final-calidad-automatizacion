# Guía operativa para agentes de IA — Proyecto Final de Calidad y Automatización

**Fecha de preparación:** 5 de noviembre de 2026
**Repositorio:** https://github.com/anasofiaeggenberger/proyecto-final-calidad-automatizacion
**Fecha oficial publicada:** 10 de noviembre de 2026, 14:29 (hora de Guatemala).
**Equipo:** Ana Sofía, Juan Pablo y Víctor.

> **Importante:** Este documento combina hechos observados en el repositorio, requisitos oficiales y decisiones **planificadas**. `docs/PLAN_TECNICO.md` es su documento técnico complementario; ambos se revisan juntos en `docs/test-strategy` y no implican que API, pruebas, Docker o Jenkins ya existan. Si existe una contradicción, prevalecen las instrucciones oficiales de https://github.com/danihrndzld/proyecto-final-calidad y se debe informar al equipo. No afirmar que algo está implementado si sólo está planificado.

## 1. Contexto y estado real

Se reutiliza, con autorización de los autores, un proyecto académico de cola de prioridad hospitalaria: https://github.com/anasofiaeggenberger/Proyecto-Priority-Queue. La aplicación actual usa Python y Flask, plantillas HTML y CSS. Permite registrar pacientes con urgencia 1–5, ver la cola, atender al paciente más urgente y eliminar pacientes. En empates debe respetar el orden de llegada (FIFO). Se retiró la interfaz antigua «Sin Estructura» y se creó un dashboard visual renovado. La cola se almacena en memoria: se reinicia con el proceso y no debe tratarse como almacenamiento persistente.

La migración y el rediseño ya están en la historia base de `main` (commit visible `1444470` en la revisión anterior). Las rutas HTML fueron comprobadas manualmente y Codex reportó validaciones básicas correctas. En la rama actual `docs/test-strategy` sólo se preparan documentos; **todavía no están implementadas las suites completas de pruebas, la API JSON ni el pipeline final.**

Ana Sofía creó la rama `docs/test-strategy`. Los documentos pueden revisarse mediante PR desde esta rama; no es necesario esperar a que se publiquen en `main` para que cada responsable prepare trabajo independiente, pero sí deben aprobarse los contratos antes de implementar dependencias.

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

No suponer que las clases `PatientQueue`, `PatientService`, la app factory o los endpoints `/api/*` existen: son **propuestas de evolución**.

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

Sistema web con API HTTP, lógica separable, pruebas unitarias con cobertura como gate, integración de caja negra contra una API desplegada, al menos tres recorridos E2E con Playwright/POM, pipeline con gates, dos ambientes seleccionables, parámetros observables, correo real de fallo, documentación, evidencias y demo controlada. La fuente oficial confirma además el artefacto único identificado por SHA, el registro de ambiente/versión por HTTP, los entregables `DECISIONES.md`, `EVIDENCIA.md` y `evidencia/`, y tres commits por integrante. Los nombres exactos de la API y el umbral de cobertura siguen siendo decisiones del equipo.

Para la demo se debe mostrar un cambio real y reversible en código de aplicación que haga fallar la capa elegida, detenga las siguientes etapas y produzca el correo recibido. No simular éxito ni fabricar evidencia.

## 5. Decisiones técnicas propuestas (pendientes de aprobación final)

- Mantener Python 3.12, Flask y el dashboard existente; no introducir frameworks innecesarios.
- Refactorizar hacia servicio de dominio (`PatientService`) y cola aislable (`PatientQueue`) y una app factory (`create_app`) que reciba configuración/dependencias, **sin cambiar la semántica de prioridad/FIFO**.
- Usar IDs únicos para pacientes, especialmente para eliminación: los nombres pueden repetirse.
- Exponer la API JSON provisional unificada del plan: `GET /api/health`, `GET /api/pacientes`, `POST /api/pacientes`, `POST /api/pacientes/atender`, `DELETE /api/pacientes/<id>`. Usar `nombre`, `prioridad`, `id`, `orden_llegada`, `pacientes`, `proximo` y `total` sólo después de aprobar el contrato. Códigos HTTP, esquemas y validaciones se deben registrar antes de que Juan Pablo implemente.
- Separar estado por instancia y ambiente. Las pruebas no deben depender de datos de ejecuciones anteriores; evitar que pruebas paralelas compartan la cola global.
- Herramientas propuestas: pytest + pytest-cov para unitarias, un cliente HTTP contra la instancia desplegada para integración, Playwright con Python + POM para E2E, Docker Compose si el entorno lo permite y Jenkins para pipeline. El cliente Flask puede complementar, pero no sustituye la integración de caja negra contra API en ejecución.
- Ambientes propuestos `ci` y `staging`, cada uno con puerto, instancia y datos propios. Nunca publicar secretos SMTP.

## 6. Distribución EXCLUSIVA de responsabilidades

Cada integrante tiene una responsabilidad principal, una parte específica de infraestructura/pipeline y una parte de documentación/evidencia. **Nadie debe asumir que “los tres” harán una tarea sin un dueño definido.**

### Ana Sofía — dominio, unitarias, cobertura y gate de calidad

**Código:** refactorizar lógica de cola y servicio, garantizar prioridad 1–5, FIFO y estado aislable; coordinar el contrato con Juan Pablo antes de cambiar interfaces. **Pruebas:** crear pruebas unitarias con fixtures, límites 0/1/5/6, cola vacía, empate FIFO, duplicados, orden de atención y eliminación; medir cobertura. **CI:** hacerse dueña del bloque `unit + coverage` y del gate unitario/calidad, con reportes JUnit y cobertura como artefactos. **Documentación/evidencia:** reglas de dominio, matriz unitaria, umbral justificado en `DECISIONES.md`, reporte de cobertura y build detenido por regresión o cobertura en `EVIDENCIA.md`/`evidencia/`. **No tocar:** rutas REST finales de Juan Pablo, páginas POM de Víctor ni SMTP sin acuerdo.

### Juan Pablo — API, integración y ambientes

**Código:** definir e implementar el contrato REST JSON provisional aprobado, respuestas/errores consistentes y health con ambiente/SHA, usando el servicio de Ana sin duplicar la lógica. **Pruebas:** integración HTTP contra la API desplegada, con particiones de equivalencia, valores límite, tabla de decisión, aislamiento y contrato. **Infraestructura/CI:** hacerse dueño de Docker/Compose o aislamiento equivalente, del artefacto único, los dos ambientes y el gate de integración. **Documentación/evidencia:** contrato API, matriz de caja negra, configuración de ambientes/Docker, requests/responses y logs de health en `DECISIONES.md`/`EVIDENCIA.md`. **No tocar:** CSS/POM ni gate unitario de Ana sin coordinación.

### Víctor — E2E, notificaciones y demo

**Código/pruebas:** crear suite Playwright con Page Object Model y al menos tres recorridos independientes, uno marcado como smoke: registro/listado, prioridad/FIFO/atención y eliminación/cola vacía; usar `data-testid`, datos aislados y capturas/trazas al fallar. **CI:** hacerse dueño del bloque E2E, publicación de reportes, parámetros de suite/navegador y notificación SMTP real. **Demo:** preparar una falla reversible por capa y su evidencia. **Documentación/evidencia:** matriz E2E, dos principios SOLID con clases/problemas, configuración segura de correo, guion y builds en `DECISIONES.md`/`EVIDENCIA.md`. **No tocar:** implementación de dominio ni contrato REST sin coordinación.

### Regla de participación individual

Los tres deben **escribir pruebas**, **modificar el pipeline** y tener **al menos tres commits propios** en el historial del commit entregado. El nombre y correo Git de cada commit deben corresponder a quien lo escribió. Para cumplir la participación, Ana agrega unitarias y gate de calidad, Juan integración y gate de integración, y Víctor E2E, notificaciones y gate E2E. Los cambios se hacen desde cuentas y ramas propias; no se crean commits a nombre de otra persona.

## 7. Orden de ejecución y dependencias

**Bloque 0 — Documentación:** revisar y aprobar conjuntamente esta guía y `docs/PLAN_TECNICO.md` por PR desde `docs/test-strategy`. No modificar `main` directamente; los agentes pueden preparar ramas independientes con los contratos marcados como provisionales.

**Bloque 1 — Contratos y dominio:** Ana define la semántica de `PatientQueue` y sus fixtures; Juan acuerda con ella el `id`, validaciones, campos y códigos HTTP de la API provisional. Acordar también cómo inyectar estado. Ninguno debe inventar por separado la interfaz del otro.

**Bloque 2 — Paralelo:** Juan implementa API, integración, Docker y ambientes; Víctor crea POM y puede preparar E2E sobre la interfaz HTML estable; Ana termina cobertura y gate unitario. Víctor ejecuta el E2E final cuando exista una instancia desplegada y los selectores estén congelados.

**Bloque 3 — CI coordinado:** Ana prepara gate unitario/calidad; Juan prepara artefacto, Docker/ambientes y gate de integración; Víctor prepara E2E, artifacts, SMTP y gate E2E. Cada uno modifica un bloque reservado del pipeline; se integran secuencialmente para evitar conflictos. Un script auxiliar cuenta sólo si el pipeline lo ejecuta.

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

- El contrato JSON, `id`, campos y códigos HTTP son decisiones del equipo; deben aprobarse antes de implementar API o integración.
- El porcentaje de cobertura no lo fija la fuente oficial: debe justificarse en `DECISIONES.md`, junto con módulos excluidos.
- Docker/Compose no es requisito explícito; Juan debe confirmar disponibilidad o documentar aislamiento equivalente.
- La integración debe probar una API desplegada y el health debe exponer ambiente y SHA; el cliente Flask aislado no basta como única evidencia.
- Definir Jenkins host, puertos, navegador y SMTP; el correo real requiere credenciales inyectadas y un destino autorizado.
- Evitar que todos modifiquen simultáneamente `app.py` o `Jenkinsfile`; establecer bloques reservados, orden de integración y revisión de PRs.
- Confirmar si el CLI continúa en alcance antes de retirar `main.py` y sus módulos.

**Regla final:** no basta con que Codex diga «completado». Cada responsable debe mostrar comandos, resultados, cambios, commits, evidencia y cumplimiento de la consigna oficial.
