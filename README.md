# Cola hospitalaria

Dashboard Flask para gestionar la atención de pacientes mediante una cola de prioridad. La interfaz principal permite registrar, listar, atender y eliminar pacientes, mostrando primero los niveles de urgencia más altos y respetando el orden de llegada cuando existe empate.

## Funcionalidades actuales

- Registro de pacientes con urgencia del 1 al 5.
- Listado ordenado por urgencia y FIFO dentro del mismo nivel.
- Resumen de pacientes en espera, próximo paciente y atención prioritaria.
- Atención del siguiente paciente.
- Eliminación individual de pacientes.
- Mensajes visibles para operaciones exitosas, validaciones y cola vacía.
- Diseño responsive con HTML semántico y selectores `data-testid` preparados para futuras pruebas Playwright.

La interfaz antigua “Sin Estructura” y sus rutas ya no forman parte de la aplicación web.

## Estructura principal

```text
.
├── app.py
├── paciente.py
├── main.py
├── paciente1.py
├── priority_queue.py
├── simulacion.py
├── utils.py
├── requirements.txt
├── static/css/styles.css
└── templates/index.html
```

`app.py` es la entrada del dashboard web. `main.py` conserva el menú de consola existente y utiliza sus módulos de apoyo.

## Requisitos e instalación en macOS

Se requiere Python 3.12 y [uv](https://docs.astral.sh/uv/). Desde la raíz del repositorio:

```bash
uv python install 3.12
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

Si Python 3.12 ya está disponible para `uv`, puede omitirse `uv python install 3.12`.

## Ejecución

Para iniciar el dashboard:

```bash
source .venv/bin/activate
python app.py
```

Abrir <http://127.0.0.1:5000/> en el navegador. Detener el servidor con `Ctrl+C`.

El menú de consola puede iniciarse con:

```bash
source .venv/bin/activate
python main.py
```

## Procedencia y licencia

El código base fue migrado de forma conservadora desde [anasofiaeggenberger/Proyecto-Priority-Queue](https://github.com/anasofiaeggenberger/Proyecto-Priority-Queue), commit `89fa05b` de `main`. Se conservaron los autores y avisos presentes en el README original.

El repositorio original no contiene `LICENSE`, `LICENSE.md`, `COPYING` ni `NOTICE`, y no declara una licencia formal. No se infiere ni añade una licencia nueva; cualquier redistribución debe confirmarse con los titulares del código.

## Alcance

Esta etapa se limita a la limpieza visual y funcional del dashboard. No incluye API JSON, CI/CD, Docker ni una suite completa de pruebas.

## Estrategia técnica y colaboración

La estrategia futura de pruebas y automatización está documentada en:

- [Plan técnico](docs/PLAN_TECNICO.md): arquitectura propuesta, contrato API provisional, matrices de pruebas, aislamiento, Jenkins, ambientes y riesgos.
- [Guía operativa para agentes](docs/GUIA_AGENTES_PROYECTO_FINAL.md): responsabilidades, dependencias, ramas, evidencias y reglas de integración.

Estos documentos describen trabajo planificado; no significan que la API, las pruebas, Docker o Jenkins ya estén implementados. Para colaborar, cada integrante debe trabajar en una rama propia, mantener su alcance, ejecutar las verificaciones de su cambio y abrir un PR con evidencia. Ana Sofía es responsable de lógica/unitarias/cobertura/gate de calidad; Juan Pablo de API/integración/Docker/ambientes/gate de integración; y Víctor de Playwright/POM/gate E2E/notificaciones/demo. No se deben hacer commits, pushes ni merges a nombre de otra persona ni guardar secretos en el repositorio.
