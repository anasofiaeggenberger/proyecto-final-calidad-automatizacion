# Plan técnico de pruebas y CI/CD

## 0. Alcance, fuentes y estados

Este documento define una estrategia técnica para el sistema hospitalario Flask de este repositorio. En esta etapa es documentación: no implementa pruebas, API JSON, Docker, Jenkins ni cambios de producción.

Los estados se usan así:

- **Implementado:** existe en el código actual y fue observado directamente.
- **Planificado:** propuesta del equipo para una etapa posterior; no debe tratarse como código disponible.
- **Pendiente:** decisión, infraestructura o requisito que todavía debe cerrarse.
- **Oficial:** requisito publicado por el repositorio del curso.

La fuente oficial consultada y accesible es [danihrndzld/proyecto-final-calidad](https://github.com/danihrndzld/proyecto-final-calidad). El contrato REST de la sección 4 es una decisión aprobada del equipo, aunque su implementación sigue planificada. Las decisiones que la fuente oficial no fija y que aún no se han cerrado se identifican como pendientes.

## 1. Estado real de la aplicación

### 1.1 Archivos y dependencias observadas

| Archivo | Estado y responsabilidad observada | Dependencias |
|---|---|---|
| `app.py` | **Implementado.** Entrada Flask, validación del formulario, mensajes flash, dashboard y rutas HTML | Flask; funciones de `paciente.py` |
| `paciente.py` | **Implementado.** `Paciente`, heap global, alta, listado, atención y eliminación para la web | `heapq` |
| `templates/index.html` | **Implementado.** Dashboard, formulario, tabla/estado vacío, mensajes y `data-testid` | Contexto de `app.py` |
| `static/css/styles.css` | **Implementado.** Estilos responsive y estados visuales | Ninguna dependencia externa |
| `priority_queue.py` | **Implementado.** Segunda cola usada por el CLI | `heapq`, `paciente1.py` |
| `paciente1.py` | **Implementado.** Modelo de paciente del CLI | Ninguna |
| `main.py` | **Implementado.** Menú interactivo de consola | `priority_queue.py`, `utils.py`, `simulacion.py` |
| `simulacion.py` | **Implementado.** Simulación y reporte del CLI | `random`, `priority_queue.py` |
| `utils.py` | **Implementado.** Validación y colorama para el CLI | `colorama` |
| `requirements.txt` | **Implementado.** Flask 2.3.2, Werkzeug 2.3.7 y colorama 0.4.6 | No incluye dependencias de pruebas |
| `.gitignore` | **Implementado.** Ignora entornos, caches, secretos, logs y reportes generados | — |

Dependencias actuales:

```text
Navegador
  └── app.py
        ├── templates/index.html
        ├── static/css/styles.css
        └── paciente.py
              └── heapq

CLI opcional
  └── main.py
        ├── priority_queue.py ── paciente1.py
        ├── simulacion.py ────── priority_queue.py
        └── utils.py ─────────── colorama
```

La aplicación web no importa `priority_queue.py`, `paciente1.py`, `simulacion.py` ni `utils.py`. Una prueba de la cola del CLI no demostraría por sí sola el comportamiento de la cola utilizada por Flask.

### 1.2 Rutas HTML actuales

| Método | Ruta | Comportamiento observado |
|---|---|---|
| `GET` | `/` | Renderiza `templates/index.html` con la cola y el resumen |
| `POST` | `/agregar` | Valida `nombre` y `prioridad`, agrega y redirige a `/#queue`; ante error redirige a `/#register` |
| `POST` | `/atender` | Atiende el siguiente o muestra mensaje de cola vacía y redirige a `/#queue` |
| `GET`, `POST` | `/eliminar/` | Redirección de compatibilidad a la cola |
| `GET`, `POST` | `/eliminar/<nombre>` | Elimina por nombre, muestra flash y redirige a `/#queue` |

Estas rutas son **implementadas** y deben conservarse mientras se agregan pruebas. No existe actualmente ninguna ruta `/api/*` ni `/health`.

### 1.3 Funcionalidad existente y ausente

| Funcionalidad | Estado actual |
|---|---|
| Registrar, listar, atender y eliminar pacientes desde el dashboard | **Implementado** |
| Prioridad 1–5, con 1 como más urgente | **Implementado en la validación web y en `Paciente`** |
| FIFO cuando la prioridad es igual | **Implementado** mediante `Paciente._contador` y `orden` |
| Mensajes de éxito, validación y cola vacía | **Implementado** mediante `flash` |
| Interfaz «Sin Estructura» | **Eliminada de la aplicación web** |
| API REST JSON | **No implementada; planificada** |
| Suites unitarias, integración y E2E | **No implementadas; planificadas** |
| Docker y dos ambientes aislados | **No implementados; planificados** |
| Jenkins, gates y correo SMTP | **No implementados; planificados** |
| `DECISIONES.md`, `EVIDENCIA.md` y `evidencia/` | **No existen; entregables planificados** |

La cola web es un estado global en memoria. Se pierde al reiniciar el proceso y no debe confundirse con almacenamiento persistente.

## 2. Reglas de negocio y defectos preexistentes

| ID | Regla o hallazgo | Estado/evidencia |
|---|---|---|
| BR-01 | La web acepta prioridades enteras del 1 al 5 | Implementado en `validate_patient_form()` |
| BR-02 | Un número menor representa mayor urgencia | Implementado en `Paciente.__lt__()` |
| BR-03 | Con igual prioridad se respeta la llegada FIFO | Implementado con `Paciente._contador` |
| BR-04 | El listado se ordena por prioridad y llegada | Implementado con `heapq.nsmallest()` |
| BR-05 | Atender retira el primer paciente | Implementado con `heapq.heappop()` |
| BR-06 | Atender una cola vacía no modifica el estado | Implementado; Flask muestra mensaje informativo |
| BR-07 | Eliminar busca por nombre y repara el heap | Implementado; sólo elimina la primera coincidencia |
| BR-08 | La cola vive en memoria global | Limitación actual |
| BR-09 | No existe identificador único | Limitación actual; nombres duplicados son ambiguos |
| BR-10 | La validación está en Flask, no en `paciente.py` | Limitación actual que motiva la extracción |
| BR-11 | La web usa redirects y flashes, no JSON | Implementado |

El `return None` después de `heapq.heappop()` en `atender_paciente()` es inalcanzable, pero no cambia el comportamiento actual. Se documenta para una limpieza futura; no se modifica en este trabajo documental.

## 3. Separación de lógica propuesta

**Planificado, no implementado:** separar reglas de negocio de Flask sin alterar prioridad, FIFO ni las rutas HTML existentes.

```text
create_app / adaptadores web y API
              ↓
        PatientService
              ↓
        PatientQueue por instancia
              ↓
            Patient
```

Estructura futura sugerida: `domain/` para modelo y cola, `services/` para casos de uso, `web/` para adaptadores Flask y carpetas separadas de pruebas y automatización. No se debe crear esta estructura durante la presente tarea.

Responsabilidades acordadas: `Patient` representa un `id` único y estable, `nombre`, `prioridad` y `orden_llegada`; `PatientQueue` encapsula una cola por instancia y conserva prioridad/FIFO; `PatientService` centraliza la validación 1–5 y los casos de uso sin depender de Flask; los adaptadores HTML y API convierten los resultados del mismo servicio a redirects/flashes o JSON.

La cola debe inyectarse por instancia en la app de prueba y la instancia de aplicación debe compartir el mismo `PatientService`/`PatientQueue` entre HTML y API. No se deben crear una cola para la web y otra para la API. El estado global de `paciente.py` es una limitación actual que se reemplazará durante la extracción.

Secuencia futura: (1) encapsular cola y contador sin cambiar resultados, (2) agregar una app factory que permita inyectar el servicio/cola y la configuración de pruebas, sin fijar todavía su firma pública, (3) conservar URLs, campos y `data-testid`, (4) implementar API sobre el mismo servicio y (5) revisar la duplicidad del CLI tras confirmar su alcance.

## 4. Contrato API REST JSON aprobado por el equipo

El equipo adopta el siguiente contrato REST JSON como referencia común para el desarrollo. Los endpoints, métodos HTTP, campos, códigos de respuesta y formatos definidos en esta sección deben respetarse durante la implementación de la API y sus pruebas. Cualquier modificación posterior debe acordarse entre los integrantes y actualizarse en ambos documentos antes de implementarse.

### 4.1 Convenciones

- Prefijo: `/api`.
- Campos JSON en español para alinearlos con el formulario existente (`nombre`, `prioridad`).
- `id` estable por paciente, por ejemplo `p-0001`, para no eliminar por nombre duplicado.
- Prioridad válida: entero entre 1 y 5, donde 1 es la más urgente.
- Respuestas JSON con `Content-Type: application/json`.
- Campos desconocidos: `400`.

### 4.2 Endpoints aprobados

| Método | Ruta | Éxito | Errores principales |
|---|---|---|---|
| `GET` | `/api/health` | `200` con estado, ambiente y versión del artefacto | `503` sólo si existe una dependencia externa no disponible |
| `POST` | `/api/pacientes` | `201` con paciente creado y posición | `400` por JSON ausente, nombre o prioridad inválidos |
| `GET` | `/api/pacientes` | `200` con total, próximo y lista ordenada; vacío también `200` | — |
| `POST` | `/api/pacientes/atender` | `200` con paciente; en vacío, `200` con `paciente: null` | — |
| `DELETE` | `/api/pacientes/<id>` | `204` sin cuerpo | `404` si el id no existe |

El contrato aprobado contiene cinco endpoints, dentro de la orientación oficial de un sistema pequeño de 3 a 5 endpoints. Las rutas HTML actuales no se reemplazan.

### 4.3 Cuerpos aprobados

Alta:

```json
{"nombre": "Ana López", "prioridad": 2}
```

Paciente:

```json
{"id": "p-0001", "nombre": "Ana López", "prioridad": 2, "orden_llegada": 0}
```

Alta y listado responden, respectivamente, `{"paciente": {...}, "posicion": 1}` y `{"total": 2, "proximo": {...}, "pacientes": [...]}`.

Atender vacío responde `{"paciente": null, "mensaje": "La cola está vacía. No hay pacientes por atender."}`.

Error común:

```json
{
  "error": {
    "codigo": "PRIORIDAD_INVALIDA",
    "mensaje": "prioridad debe ser un entero entre 1 y 5",
    "detalles": {}
  }
}
```

Los nombres anteriores, `id`, el formato de error y el `200` para cola vacía son decisiones aprobadas del equipo, no requisitos impuestos por la fuente oficial. Ana debe implementar el modelo de dominio compatible; Juan Pablo debe implementar este contrato y probar sus respuestas JSON mediante integración HTTP; Víctor debe realizar los recorridos E2E sobre la interfaz web.

### 4.4 Salud de la instancia y SHA

El requisito oficial exige que el artefacto se construya una sola vez por build, se identifique con el SHA del commit o una versión, y que la instancia responda ese identificador por HTTP junto con su ambiente. La implementación futura de `/api/health` debe incluir, como mínimo:

```json
{"estado": "ok", "ambiente": "ci", "version": "<SHA-completo-del-commit>"}
```

Esto no existe en `app.py` todavía: la ruta y el cuerpo aprobados aún deben implementarse. La forma de inyectar la versión del artefacto sigue pendiente de implementación, aunque el requisito de exponerla sí es oficial.

## 5. Aislamiento de datos

### 5.1 Unitarias

- Crear una cola nueva por prueba una vez extraída la lógica.
- No reutilizar `cola_prioridad` ni `Paciente._contador` entre casos.
- Mientras exista el global, limpiar la lista y restaurar el contador en un fixture de transición.
- No depender del orden de ejecución de pytest.

### 5.2 Integración

- Levantar una instancia de la API por build/ambiente y usar HTTP real contra ella; el cliente Flask puede complementar, pero no sustituye la prueba de caja negra exigida.
- Usar una cola/estado nuevo por instancia y limpiar el proceso al terminar.
- Verificar que health indique el ambiente y el SHA que se está probando.
- No compartir datos entre casos: usar nombres únicos o reiniciar la instancia.

### 5.3 E2E y CI

- Cada ejecución Playwright debe crear su contexto y datos propios.
- Ejecutar la app en un proceso y puerto controlados, con limpieza en `finally`/`post` incluso ante timeout.
- Los ambientes `ci` y `staging` deben ser instancias distintas con la misma imagen/artefacto y configuración separada.
- Si Docker/Compose es elegido, cada ambiente tendrá contenedor, puerto, red y variables propios. Si no, se requiere aislamiento equivalente.

## 6. Matriz preliminar de pruebas unitarias

Las pruebas de Ana deben apuntar a dominio/servicio, no a Flask. Los casos U-14 a U-18 dependen de centralizar la validación.

| ID | Caso | Entrada | Resultado verificable |
|---|---|---|---|
| U-01 | Prioridad 1 | Paciente con `1` | Se acepta y queda antes que niveles mayores |
| U-02 | Prioridad 2 | Paciente con `2` | Se acepta en posición correcta |
| U-03 | Prioridad 3 | Paciente con `3` | Se acepta en posición correcta |
| U-04 | Prioridad 4 | Paciente con `4` | Se acepta en posición correcta |
| U-05 | Prioridad 5 | Paciente con `5` | Se acepta como menor urgencia |
| U-06 | Orden de prioridades | Insertar 5, 1, 3, 2, 4 | Atención/listado: 1, 2, 3, 4, 5 |
| U-07 | FIFO igual | A, B, C con prioridad 3 | Salen A, B, C |
| U-08 | FIFO intercalado | A(2), B(1), C(2), D(1) | Salen B, D, A, C |
| U-09 | Todos iguales | Varios con prioridad 1 o 5 | Se conserva llegada estricta |
| U-10 | Cola vacía | Listar, próximo y atender sin altas | Vacío, próximo nulo y sin mutación |
| U-11 | Atención hasta vaciar | Atender N+1 veces | N salidas correctas y última operación vacía |
| U-12 | Eliminar existente | Eliminar un elemento intermedio | Sólo ese elemento desaparece; heap válido |
| U-13 | Eliminar inexistente | Nombre/id ausente | Resultado negativo y cola sin cambios |
| U-14 | Límite inferior | `0`, `-1` | Rechazo de validación |
| U-15 | Límite superior | `6`, `999` | Rechazo de validación |
| U-16 | No numérico | `"2x"`, `None`, vacío | Rechazo controlado |
| U-17 | Nombre límite | Vacío, espacios, `A`, nombre largo | Sólo lo permitido se acepta |
| U-18 | Duplicados | Dos pacientes con mismo nombre | Comportamiento definido para eliminar por id |
| U-19 | Estado posterior | Insertar, eliminar, insertar | No se corrompe prioridad/FIFO |

## 7. Matriz preliminar de integración

Juan debe ejecutar estas pruebas de caja negra contra la API en ejecución. Cada caso debe registrar la técnica que lo originó y la partición, límite o regla de decisión cubierta.

### 7.1 Particiones de equivalencia

| Campo/estado | Partición válida | Particiones inválidas o especiales |
|---|---|---|
| `nombre` | Texto no vacío después de `strip` | Ausente, vacío, espacios, tipo no texto |
| `prioridad` | Enteros 1, 2, 3, 4 y 5 | Ausente, vacío, decimal, texto, menor que 1, mayor que 5 |
| Cola | Vacía, un paciente, varios | Repetir atención sobre cola vacía |
| Eliminación | `id` existente | `id` ausente, mal formado o inexistente |
| HTTP/JSON | Método, Content-Type y cuerpo válidos | Método no permitido, JSON inválido, Content-Type incorrecto |
| Health | Instancia activa con versión y ambiente | Proceso detenido o dependencia futura no disponible |

### 7.2 Valores límite

| Caso | Valores | Resultado esperado |
|---|---|---|
| Prioridad mínima | `1` | Aceptar |
| Debajo del mínimo | `0`, `-1` | Rechazar |
| Prioridad máxima | `5` | Aceptar |
| Encima del máximo | `6` | Rechazar |
| Nombre mínimo | `"A"` | Aceptar si no se acuerda otra longitud |
| Nombre vacío | `""`, `"   "` | Rechazar |
| Cola | 0, 1 y varios | Respuestas y orden consistentes |

### 7.3 Tabla de decisión

| Caso | Nombre válido | Prioridad válida | Cola con paciente | Objetivo existe | Resultado |
|---|---:|---:|---:|---:|---|
| Alta válida | Sí | Sí | Cualquiera | N/A | `201`, se registra y ordena |
| Alta inválida | No | Cualquiera | Cualquiera | N/A | `400`, sin mutación |
| Prioridad inválida | Sí | No | Cualquiera | N/A | `400`, sin mutación |
| Atender con pacientes | N/A | N/A | Sí | N/A | `200`, sale prioridad/FIFO correcta |
| Atender vacío | N/A | N/A | No | N/A | `200`, `paciente: null`, sin mutación |
| Eliminar existente | N/A | N/A | Sí | Sí | `204`, se retira el objetivo |
| Eliminar ausente | N/A | N/A | Cualquiera | No | `404`, sin mutación |
| Health normal | N/A | N/A | N/A | N/A | `200`, estado, ambiente y SHA |

La tabla usa el contrato aprobado de la sección 4. Si el equipo necesita cambiar un código o campo, debe acordarlo y actualizar ambos documentos y `DECISIONES.md` antes de modificar código o pruebas.

## 8. Estrategia E2E con Playwright y POM

**Planificado:** usar Playwright con Python, por coherencia con el proyecto, y Page Object Model. El requisito oficial pide al menos tres recorridos, uno de ellos marcado como smoke.

### 8.1 Estructura propuesta

```text
tests/e2e/pages/hospital_dashboard_page.py
tests/e2e/pages/patient_form.py
tests/e2e/pages/patient_queue_view.py
tests/e2e/test_smoke_registration.py
tests/e2e/test_priority_fifo_attention.py
tests/e2e/test_deletion_and_empty_state.py
tests/e2e/conftest.py
```

Los page objects deben usar los `data-testid` existentes: `register-form`, `patient-name-input`, `priority-select`, `register-patient-button`, `patient-row`, `attend-next-button`, `delete-patient-button` y `empty-state`. No depender de clases CSS decorativas.

### 8.2 Recorridos independientes

1. **Smoke: alta y listado.** Abrir dashboard limpio, registrar un paciente, verificar una fila y el resumen.
2. **Prioridad, FIFO y atención.** Registrar 3, 1, 1; verificar 1/1/3 y FIFO entre los dos niveles 1; atender hasta validar el orden.
3. **Eliminación y cola vacía.** Registrar varios, eliminar uno por `data-testid`, verificar reordenamiento, vaciar y verificar `empty-state` y mensaje.
4. **Opcional: validación y responsive.** Probar entrada inválida en desktop, tablet y móvil; la cola debe quedar sin cambios.

Cada recorrido crea un contexto y datos propios. Víctor debe guardar screenshots/traces cuando falle y registrar qué selector y estado verificó.

### 8.3 SOLID exigido para la justificación

Antes de implementar, registrar en `DECISIONES.md` dos principios y su evidencia. Propuesta:

- **Single Responsibility:** `PatientForm` sólo encapsula registro y `PatientQueueView` sólo lectura/acciones de la cola; evita un page object monolítico y duplicación de selectores.
- **Interface Segregation (candidato condicionado):** sólo puede justificarse si la implementación futura define abstracciones/interfaces concretas y cada consumidor depende de un subconjunto que necesita; dividir Page Objects no demuestra ISP por sí solo. Si no existe esa evidencia, el equipo debe sustituirlo por otro principio justificable y documentar la clase, la alternativa y el problema evitado.

La clase, el problema que evita y el test/build donde se observa deben quedar documentados. Recibir una dependencia por constructor, por sí solo, no cuenta como principio.

## 9. Jenkins, ambientes y gates

El proyecto selecciona Jenkins, aunque la fuente oficial permite otros sistemas de CI. Esta sección es una propuesta; no se crea un `Jenkinsfile` todavía.

### 9.1 Flujo y artefacto único

1. **Checkout:** registrar SHA completo.
2. **Lint/setup:** preparar Python y herramientas aprobadas.
3. **Unit + coverage:** ejecutar unitarias de Ana y fallar si falla la suite o se incumple el umbral fijado en `DECISIONES.md`.
4. **Build:** construir una sola vez el artefacto etiquetado con el SHA.
5. **Deploy:** desplegar ese mismo artefacto en el ambiente elegido.
6. **Integration:** Juan prueba la API HTTP desplegada.
7. **E2E:** Víctor ejecuta Playwright contra esa instancia.
8. **Artifacts/notification:** publicar reportes y enviar el correo del resultado.

Si una etapa falla, el build queda rojo y las siguientes no corren. Todos los procesos deben apagarse mediante bloques equivalentes a `post { always { ... } }`.

El endpoint de health debe demostrar que la instancia responde el mismo SHA del artefacto y el ambiente seleccionado. El pipeline no debe inventar esa respuesta desde fuera.

### 9.2 Dos ambientes aislados

| Ambiente | Propósito | Aislamiento propuesto |
|---|---|---|
| `ci` | Validación por build/PR | Instancia, puerto, workspace, estado y artifacts propios |
| `staging` | Smoke y demo | Otra instancia con la misma versión del artefacto, configuración, datos y puerto separados |

**Docker/Compose es la opción propuesta para Juan**, porque facilita empaquetar una vez y levantar dos instancias. No es un requisito oficial explícito ni está implementado; debe confirmarse con la infraestructura disponible. Un aislamiento equivalente por procesos también debe cumplir versión, ambiente y puertos distinguibles.

### 9.3 Parámetros

Al lanzar el job se deben elegir el ambiente y al menos dos parámetros adicionales, con efecto observable; uno debe cambiar la suite o el navegador:

| Parámetro | Valores/default propuesto | Efecto |
|---|---|---|
| `ENVIRONMENT` | `ci` / `staging`; default `ci` | Selecciona instancia y configuración |
| `SUITE` | `smoke` / `regression`; default `smoke` | Cambia qué pruebas se ejecutan |
| `BROWSER` | `chromium` (y otro aprobado); default `chromium` | Cambia el navegador E2E |
| `NOTIFY_EMAILS` | destinatario autorizado por defecto | Cambia destinatarios del correo |

El umbral de cobertura debe fijarse y justificarse en `DECISIONES.md`; no se recomienda convertirlo en un parámetro libre que permita eludir el gate.

Cada commit en la rama principal debe disparar un build con los valores por defecto. La configuración del pipeline debe vivir en el repositorio; en la interfaz de Jenkins sólo se configuran el job, plugins y secretos necesarios.

### 9.4 Correo SMTP

Víctor preparará el correo real usando el plugin aprobado, por ejemplo Email Extension, pero el pipeline debe leer servidor, puerto, usuario y contraseña desde variables/credenciales inyectadas por Jenkins. La configuración global por sí sola no satisface la guía oficial. La contraseña no puede aparecer en logs ni repositorio. `NOTIFY_EMAILS` se puede cambiar al lanzar el build y debe tener un valor por defecto autorizado.

El correo de fallo debe incluir número de build, SHA/commit, ambiente, etapa fallida y enlace al log. Debe enviarse también en timeout; si SMTP falla, se conservan artifacts y se registra el fallo operativo.

### 9.5 Fallas controladas

| Escenario | Gate esperado | Evidencia |
|---|---|---|
| Regresión real en lógica | Unitarias rojas; no avanzar | JUnit, cobertura, log y correo |
| API/status/schema incorrecto | Integración roja; no avanzar a E2E | Respuesta y assertion |
| `data-testid` ausente | E2E rojo; conservar trace/screenshot | Reporte Playwright |
| Health no responde o SHA incorrecto | No ejecutar integración/E2E | Log de despliegue y cleanup |
| Timeout | Build abortado y correo | Log, trace si existe y cleanup |
| Smoke de staging falla | No declarar éxito | Log y correo |

La demo debe romper código de aplicación, no desactivar una prueba. El cambio de demo es reversible y no se hace sobre `main` sin procedimiento aprobado.

## 10. Responsabilidades y evidencias

La distribución es exclusiva y debe mantenerse en los PRs. Los tres integrantes deben escribir pruebas, modificar una parte real del pipeline y tener al menos tres commits propios; la fuente oficial también exige que autor y correo Git correspondan a quien escribió cada commit.

### Ana Sofía — lógica, unitarias, cobertura y gate unitario/calidad

- **Código/pruebas:** extraer `Patient`/`PatientQueue`/servicio sin cambiar prioridad/FIFO; escribir unitarias U-01–U-19 y fixtures de aislamiento.
- **Pipeline:** agregar el bloque `unit + coverage`, reporte JUnit/cobertura y el gate de calidad.
- **Documentación:** sección de reglas de negocio, matriz unitaria, umbral y justificación en `DECISIONES.md`.
- **Evidencia:** reporte de cobertura, resultado unitario verde y build detenido por cobertura o regresión en `EVIDENCIA.md`/`evidencia/`.
- **No modificar:** Ana no debe modificar el contrato REST aprobado ni implementar los endpoints asignados a Juan Pablo; Docker corresponde a Juan Pablo, y POM y SMTP corresponden a Víctor.

### Juan Pablo — API REST, integración, Docker, ambientes y gate de integración

- **Código/pruebas:** implementar el contrato API aprobado sobre el servicio de Ana; escribir integración HTTP de caja negra con equivalencias, límites y tabla de decisión.
- **Infraestructura:** crear el Dockerfile/Compose o aislamiento equivalente, construir una vez por SHA y levantar `ci`/`staging` con configuración separada.
- **Pipeline:** agregar build/deploy, health con ambiente/SHA y gate de integración.
- **Documentación:** contrato API, matriz de integración, diseño de ambientes y decisión de Docker en `DECISIONES.md`.
- **Evidencia:** requests/responses, logs de health/versión, un build por ambiente y fallo controlado de integración.
- **No asumir:** cambios en reglas de dominio, selectores E2E ni configuración SMTP.

### Víctor — Playwright, POM, gate E2E, SMTP y demo

- **Código/pruebas:** escribir los tres recorridos mínimos con Playwright/POM, uno smoke; documentar dos principios SOLID con clases y problema evitado.
- **Pipeline:** agregar ejecución E2E, selección de suite/navegador, artifacts de screenshots/traces y gate E2E.
- **Notificaciones/demo:** configurar SMTP mediante variables inyectadas, correo de fallo y guion de demo con una falla por capa.
- **Documentación:** matriz E2E, POM, parámetros, correo y guion en `DECISIONES.md`; consignar builds/correos en `EVIDENCIA.md`/`evidencia/`.
- **No asumir:** modificar la cola, cambiar el contrato API o alterar Docker sin coordinación.

### Commits y participación

Cada integrante debe tener como mínimo tres commits propios en el historial del commit entregado. Al menos uno de esos commits debe modificar el pipeline de forma atribuible; el autor y correo Git deben estar configurados correctamente. No se deben crear commits a nombre de otra persona.

## 11. Dependencias y trabajo en ramas sin conflictos

### 11.1 Dependencias

1. Ana documenta y estabiliza la semántica interna de `Patient`/`PatientQueue`/`PatientService` y su fixture, respetando el contrato aprobado.
2. Juan implementa el contrato API aprobado sobre el servicio de Ana y define sólo los detalles internos de inyección, DTOs y mapeo de errores que no están fijados.
3. Víctor puede preparar POM sobre la UI actual, pero ejecuta E2E final cuando Juan exponga una instancia desplegada y los `data-testid` estén congelados.
4. Los tres mantienen congelados los endpoints y respuestas aprobados; antes de integrar el pipeline acuerdan nombres de parámetros, artifacts y demás detalles operativos pendientes.
5. La demo y las evidencias se generan sólo después de un build verde reproducible.

### 11.2 Ramas y archivos de propiedad

Partir de la última `main` aprobada, sin trabajar directamente sobre ella:

```text
feat/ana-domain-unit       -> domain/, tests/unit/, documentación de unitarias
feat/juan-api-integration  -> API, tests/integration/, Docker/ambientes
feat/victor-e2e-demo       -> tests/e2e/, POM, notificaciones/evidencias
```

El `Jenkinsfile` será integrado progresivamente para evitar conflictos entre las ramas de los tres integrantes.

1. **Ana Sofía:** crea la estructura inicial del `Jenkinsfile` y configura las etapas de pruebas unitarias, cobertura y calidad.
2. **Juan Pablo:** después de integrar la rama de Ana, actualiza su rama desde `main` y agrega las etapas de construcción del artefacto, despliegue, ambientes y pruebas de integración.
3. **Víctor:** después de integrar la rama de Juan Pablo, actualiza su rama desde `main` y agrega las etapas E2E, publicación de reportes y notificaciones SMTP.
4. Cada integrante debe realizar personalmente sus modificaciones, probar su etapa y generar commits propios.
5. Los cambios al pipeline se integran mediante Pull Requests en el orden Ana → Juan Pablo → Víctor. Nadie debe sobrescribir las etapas de otro integrante.

Los tres pueden desarrollar sus pruebas y componentes independientes en paralelo. Únicamente las modificaciones al `Jenkinsfile` se integrarán de manera secuencial.

## 12. Archivos antiguos: recomendación, no ejecución

Si el alcance final es sólo el dashboard Flask, se puede evaluar retirar en una tarea separada el conjunto CLI:

- `main.py`
- `priority_queue.py`
- `paciente1.py`
- `simulacion.py`
- `utils.py`

No se eliminan aquí: actualmente forman una interfaz de consola separada y retirarlos sería un cambio de alcance. Antes de hacerlo, confirmar si el profesor o el equipo requiere demostrarla. Tampoco se propone retirar `requirements.txt` hasta decidir cómo separar dependencias de runtime y desarrollo.

## 13. Matriz de requisitos verificables

| ID | Requisito | Evidencia futura | Estado |
|---|---|---|---|
| RQ-01 | Prioridad 1–5 | U-01–U-05, límites U-14–U-16 | Implementado en web; pruebas planificadas |
| RQ-02 | Menor número = mayor urgencia | U-06 y matriz de integración | Implementado |
| RQ-03 | FIFO en empate | U-07–U-09 y E2E 2 | Implementado; pruebas planificadas |
| RQ-04 | Cola vacía sin mutación | U-10/U-11, integración y E2E 3 | Implementado en web |
| RQ-05 | Eliminar objetivo | U-12/U-13 e integración | Implementado por nombre en HTML; API planificada con `id` aprobado |
| RQ-06 | Lógica aislable | `PatientQueue`, servicio y fixtures | Planificado |
| RQ-07 | API HTTP probada en ejecución | Contrato aprobado y tests de Juan | Planificado; implementación pendiente |
| RQ-08 | Tres E2E mínimo, uno smoke | Playwright/POM y artifacts | Requisito oficial; planificado |
| RQ-09 | Unitarias con cobertura y gate | JUnit, cobertura y build rojo | Requisito oficial; planificado |
| RQ-10 | Integración de caja negra con técnicas | Matrices y requests HTTP | Requisito oficial; planificado |
| RQ-11 | Artefacto único identificado por SHA | Log, health y build | Requisito oficial; planificado |
| RQ-12 | Dos ambientes seleccionables | Build en `ci` y `staging` con misma versión | Requisito oficial; nombres son propuesta |
| RQ-13 | Ambiente + dos parámetros, uno de suite/navegador | Parámetros y reportes | Requisito oficial; planificado |
| RQ-14 | Correo con build, SHA, ambiente, etapa y log | Correo real y evidencia | Requisito oficial; SMTP pendiente |
| RQ-15 | Tres commits por persona y autor verificable | Historial del SHA entregado | Requisito oficial; pendiente de ejecución |
| RQ-16 | `DECISIONES.md`, `EVIDENCIA.md`, `evidencia/` | Archivos y capturas | Requisito oficial; no existen todavía |
| RQ-17 | Tag y archivo de MIU con URL, tag y SHA completo | Entrega final | Requisito oficial; pendiente |
| RQ-18 | Demo con falla real y correo | Builds verde/rojo/verde y correo | Requisito oficial; pendiente |
| RQ-19 | Decisiones justificadas y uso transparente de IA | `DECISIONES.md` con alternativas, concepto, evidencia, fuente IEEE y tres sugerencias de IA aceptadas/rechazadas | Requisito oficial; pendiente |
| RQ-20 | Evidencia trazable | `EVIDENCIA.md` con builds verde/rojo/verde, SHA, ambos ambientes, gate de cobertura, etapa/prueba fallida y conteo por capa; capturas en `evidencia/` | Requisito oficial; pendiente |

## 14. Confirmaciones y preguntas abiertas

La fuente oficial confirma el objetivo general, pero no decide por el equipo:

1. ¿Qué interfaces internas de inyección, asignación del `id` único, DTOs y mapeo de errores necesita la implementación, sin alterar el contrato REST aprobado?
2. ¿Cómo se mapeará la eliminación HTML actual por nombre al `id` aprobado de la API sin cambiar las rutas existentes?
3. ¿Qué porcentaje de cobertura se justifica en `DECISIONES.md` y qué módulos quedan fuera?
4. ¿Docker/Compose estará disponible o se usará aislamiento equivalente?
5. ¿Qué servidor SMTP, credenciales inyectadas y dirección autorizada se usarán en la demo?
6. ¿Qué navegador adicional, si alguno, estará disponible en Jenkins?
7. ¿El CLI sigue en alcance o se retira después de la entrega?
8. La fuente oficial describe 2–3 pantallas como el tamaño orientativo de un sistema nuevo; ¿se espera alguna pantalla adicional o el dashboard actual es suficiente para esta base existente?

No se deben inventar respuestas para estas preguntas. Registrar la decisión y su evidencia antes de implementar las capas dependientes.

## 15. Entregables oficiales y orden futuro

La fuente oficial solicita, además del código, README con sistema/ambientes/parámetros, `DECISIONES.md`, `EVIDENCIA.md`, carpeta `evidencia/`, un tag público y un archivo en MIU con enlace, tag y SHA completo. `DECISIONES.md` debe justificar alternativas, conceptos del curso, evidencia y fuentes IEEE, además de tres sugerencias de IA aceptadas o rechazadas. `EVIDENCIA.md` debe trazar builds verde/rojo/verde, SHA, ambientes, cobertura, etapa/prueba fallida y cantidad de pruebas por capa. La demo parte del commit entregado, muestra un build verde, los dos ambientes, una falla real por capa y el correo recibido; el commit de ruptura de demo no se califica.

Orden recomendado:

1. Confirmar las preguntas internas/operativas abiertas sin modificar el contrato REST aprobado.
2. Extraer servicio/cola y escribir unitarias.
3. Implementar API, integración HTTP, Docker/ambientes y health con SHA.
4. Implementar POM, tres E2E y artifacts.
5. Integrar Jenkins con los gates y correo por variables inyectadas.
6. Generar builds verde, rojo y verde, evidencias y documentación oficial.
7. Crear el tag y preparar el archivo de MIU.

La fuente oficial marca como meta de tiempo, no como punto de calificación, que un build tarde menos de tres minutos con dependencias en caché.

Hasta entonces, este archivo y `docs/GUIA_AGENTES_PROYECTO_FINAL.md` son documentación de trabajo; no implican que alguna de esas piezas ya exista.
