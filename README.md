# 🏥 Proyecto: Priority Queue en Hospital

**Integrantes:**
- Ana Sofía Eggenberger
- Jan Ricica

**Clase:** Estructura de Datos
**Tema:** Implementación de *Priority Queue* para hospital

## Descripción

Este proyecto simula la administración de pacientes en un hospital utilizando una **Priority Queue** como estructura de datos. También integra una interfaz web con Flask.

Cada paciente se registra con un nivel de urgencia del **1 al 5**, donde 1 es la máxima prioridad médica y 5 la mínima.

La aplicación conserva las interfaces existentes del proyecto original:

- Interfaz web Flask con cola de pacientes y versión sin estructura, mediante `app.py`.
- Menú de consola con priority queue, simulación y generación de reportes, mediante `main.py`.
- Menú de consola alternativo sin estructuras, mediante `main_sin_estructuras.py`.

## Estructura

```text
.
├── app.py
├── main.py
├── main_sin_estructuras.py
├── paciente.py
├── paciente1.py
├── pacientes_sin_estructura.py
├── priority_queue.py
├── simulacion.py
├── utils.py
├── requirements.txt
├── static/css/styles.css
└── templates/
    ├── index.html
    └── sinestructura.html
```

Los archivos `reporte_pacientes.txt` y `reporte_sin_estructuras.txt` son salidas generadas por la aplicación y no forman parte de los archivos fuente migrados.

## Requisitos e instalación en macOS

Se requiere Python 3.12 y [uv](https://docs.astral.sh/uv/). Desde la raíz del repositorio:

```bash
uv python install 3.12
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

`uv python install 3.12` puede omitirse si Python 3.12 ya está disponible para `uv`.

## Ejecución

Para iniciar la interfaz web Flask:

```bash
source .venv/bin/activate
python app.py
```

Abrir <http://127.0.0.1:5000/> en el navegador. La ruta de la versión sin estructura es <http://127.0.0.1:5000/sinestructura/>.

Para ejecutar los menús de consola:

```bash
source .venv/bin/activate
python main.py
python main_sin_estructuras.py
```

## Procedencia y licencia

El código fuente fue migrado de forma conservadora desde [anasofiaeggenberger/Proyecto-Priority-Queue](https://github.com/anasofiaeggenberger/Proyecto-Priority-Queue), clonado el 5 de noviembre de 2026 desde el commit `89fa05b` de `main`.

Se conservaron los autores y avisos presentes en el README original. El repositorio original no contiene un archivo `LICENSE`, `LICENSE.md`, `COPYING` ni `NOTICE`, y no declara una licencia formal; por tanto, este proyecto no infiere ni añade una licencia nueva. Si se requiere redistribución, debe confirmarse el permiso correspondiente con los titulares del código.

## Alcance de esta migración

Esta migración incorpora la base funcional existente sin refactorizar su arquitectura, cambiar sus rutas o agregar endpoints, pruebas o CI/CD. Las dependencias de ejecución declaradas son Flask, Werkzeug (fijado a una versión compatible con Flask 2.3.2) y colorama; `heapq` y `random` pertenecen a la biblioteca estándar de Python.
