import os
import secrets

from flask import Flask, flash, redirect, render_template, request, url_for

from api import api_bp, register_api_error_handlers
from services.patient_service import (
    InvalidPatientNameError,
    InvalidPriorityError,
    PatientService,
    PatientServiceError,
)

URGENCY_LABELS = {
    1: "Crítica",
    2: "Muy alta",
    3: "Alta",
    4: "Media",
    5: "Baja",
}


def create_app(config=None, service=None):
    """Crea una aplicación Flask con un servicio de pacientes por instancia."""

    flask_app = Flask(__name__)
    flask_app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
    # ambiente y versión del artefacto se inyectan por entorno y se exponen en /api/health
    flask_app.config["AMBIENTE"] = os.environ.get("APP_AMBIENTE", "local")
    flask_app.config["VERSION"] = os.environ.get("APP_VERSION", "desconocida")
    if config is not None:
        flask_app.config.update(config)

    patient_service = service if service is not None else PatientService()
    flask_app.extensions["patient_service"] = patient_service

    def get_patient_service():
        return flask_app.extensions["patient_service"]

    def dashboard_context():
        pacientes = get_patient_service().listar()
        return {
            "pacientes": pacientes,
            "total_pacientes": len(pacientes),
            "pacientes_urgentes": sum(
                1 for paciente in pacientes if paciente.prioridad in (1, 2)
            ),
            "proximo_paciente": pacientes[0] if pacientes else None,
            "urgency_labels": URGENCY_LABELS,
        }

    @flask_app.route("/")
    def index():
        return render_template("index.html", **dashboard_context())

    @flask_app.route("/agregar", methods=["POST"])
    def agregar():
        nombre = request.form.get("nombre", "")
        prioridad = request.form.get("prioridad", "")

        try:
            paciente = get_patient_service().registrar(nombre, prioridad)
        except InvalidPatientNameError:
            flash("Ingresa el nombre del paciente.", "error")
            return redirect(url_for("index", _anchor="register"))
        except InvalidPriorityError:
            flash(
                "Selecciona un nivel de urgencia válido del 1 al 5.",
                "error",
            )
            return redirect(url_for("index", _anchor="register"))
        except PatientServiceError as error:
            flash(str(error), "error")
            return redirect(url_for("index", _anchor="register"))

        flash(
            f"{paciente.nombre} fue registrado con urgencia {paciente.prioridad} · "
            f"{URGENCY_LABELS[paciente.prioridad]}.",
            "success",
        )
        return redirect(url_for("index", _anchor="queue"))

    @flask_app.route("/atender", methods=["POST"])
    def atender():
        paciente = get_patient_service().atender_siguiente()
        if paciente:
            flash(f"{paciente.nombre} fue atendido correctamente.", "success")
        else:
            flash("La cola está vacía. No hay pacientes por atender.", "info")
        return redirect(url_for("index", _anchor="queue"))

    @flask_app.route("/eliminar/", methods=["GET", "POST"])
    def eliminar_default():
        return redirect(url_for("index", _anchor="queue"))

    @flask_app.route("/eliminar/<patient_id>", methods=["GET", "POST"])
    def eliminar(patient_id):
        try:
            paciente = get_patient_service().eliminar_por_id(patient_id)
        except PatientServiceError as error:
            flash(str(error), "error")
            return redirect(url_for("index", _anchor="queue"))

        if paciente:
            flash(f"{paciente.nombre} fue eliminado de la cola.", "success")
        else:
            flash(f"No se encontró un paciente con ID {patient_id} en la cola.", "error")
        return redirect(url_for("index", _anchor="queue"))

    flask_app.register_blueprint(api_bp)
    register_api_error_handlers(flask_app)

    return flask_app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
