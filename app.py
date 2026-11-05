import os

from flask import Flask, flash, redirect, render_template, request, url_for

from paciente import (
    agregar_paciente,
    atender_paciente,
    eliminar_paciente,
    obtener_pacientes_ordenados,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY", "hospital-dashboard-development-key"
)

URGENCY_LABELS = {
    1: "Crítica",
    2: "Muy alta",
    3: "Alta",
    4: "Media",
    5: "Baja",
}


def dashboard_context():
    pacientes = obtener_pacientes_ordenados()
    return {
        "pacientes": pacientes,
        "total_pacientes": len(pacientes),
        "pacientes_urgentes": sum(
            1 for paciente in pacientes if paciente.prioridad in (1, 2)
        ),
        "proximo_paciente": pacientes[0] if pacientes else None,
        "urgency_labels": URGENCY_LABELS,
    }


def validate_patient_form():
    nombre = request.form.get("nombre", "").strip()
    prioridad_input = request.form.get("prioridad", "").strip()

    if not nombre:
        return None, "Ingresa el nombre del paciente."

    try:
        prioridad = int(prioridad_input)
    except (TypeError, ValueError):
        return None, "Selecciona un nivel de urgencia válido del 1 al 5."

    if prioridad not in URGENCY_LABELS:
        return None, "Selecciona un nivel de urgencia válido del 1 al 5."

    return (nombre, prioridad), None


@app.route("/")
def index():
    return render_template("index.html", **dashboard_context())


@app.route("/agregar", methods=["POST"])
def agregar():
    patient_data, error = validate_patient_form()
    if error:
        flash(error, "error")
        return redirect(url_for("index", _anchor="register"))

    nombre, prioridad = patient_data
    agregar_paciente(nombre, prioridad)
    flash(
        f"{nombre} fue registrado con urgencia {prioridad} · "
        f"{URGENCY_LABELS[prioridad]}.",
        "success",
    )
    return redirect(url_for("index", _anchor="queue"))


@app.route("/atender", methods=["POST"])
def atender():
    paciente = atender_paciente()
    if paciente:
        flash(f"{paciente.nombre} fue atendido correctamente.", "success")
    else:
        flash("La cola está vacía. No hay pacientes por atender.", "info")
    return redirect(url_for("index", _anchor="queue"))


@app.route("/eliminar/", methods=["GET", "POST"])
def eliminar_default():
    return redirect(url_for("index", _anchor="queue"))


@app.route("/eliminar/<nombre>", methods=["GET", "POST"])
def eliminar(nombre):
    if eliminar_paciente(nombre):
        flash(f"{nombre} fue eliminado de la cola.", "success")
        print(f"Paciente {nombre} eliminado definitivamente.")
    else:
        flash(f"No se encontró a {nombre} en la cola.", "error")
        print(f"No se pudo eliminar al paciente {nombre}.")
    return redirect(url_for("index", _anchor="queue"))


if __name__ == "__main__":
    app.run(debug=True)
