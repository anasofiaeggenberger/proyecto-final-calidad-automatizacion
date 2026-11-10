"""Endpoints JSON del contrato aprobado en docs/PLAN_TECNICO.md (sección 4)."""

from flask import Blueprint, current_app, jsonify, request

from domain.patient import Patient
from services.patient_service import (
    InvalidPatientNameError,
    InvalidPriorityError,
    PatientServiceError,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")

CAMPOS_ALTA = frozenset({"nombre", "prioridad"})


def _service():
    return current_app.extensions["patient_service"]


def _serializar(paciente: Patient) -> dict:
    return {
        "id": paciente.id,
        "nombre": paciente.nombre,
        "prioridad": paciente.prioridad,
        "orden_llegada": paciente.orden_llegada,
    }


def _error(codigo: str, mensaje: str, status: int, detalles: dict | None = None):
    cuerpo = {
        "error": {
            "codigo": codigo,
            "mensaje": mensaje,
            "detalles": detalles if detalles is not None else {},
        }
    }
    return jsonify(cuerpo), status


@api_bp.get("/health")
def health():
    return jsonify(
        {
            "estado": "ok",
            "ambiente": current_app.config["AMBIENTE"],
            "version": current_app.config["VERSION"],
        }
    )


@api_bp.post("/pacientes")
def crear_paciente():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error(
            "JSON_INVALIDO",
            "se espera un cuerpo JSON con nombre y prioridad",
            400,
        )

    desconocidos = sorted(set(payload) - CAMPOS_ALTA)
    if desconocidos:
        return _error(
            "CAMPOS_DESCONOCIDOS",
            "el cuerpo solo admite los campos nombre y prioridad",
            400,
            {"campos": desconocidos},
        )

    # en JSON la prioridad llega tipada: se rechazan textos, decimales y booleanos
    prioridad = payload.get("prioridad")
    if isinstance(prioridad, bool) or not isinstance(prioridad, int):
        return _error(
            "PRIORIDAD_INVALIDA",
            "prioridad debe ser un entero entre 1 y 5",
            400,
        )

    try:
        paciente = _service().registrar(payload.get("nombre"), prioridad)
    except InvalidPatientNameError:
        return _error("NOMBRE_INVALIDO", "nombre debe ser una cadena no vacía", 400)
    except InvalidPriorityError:
        return _error(
            "PRIORIDAD_INVALIDA",
            "prioridad debe ser un entero entre 1 y 5",
            400,
        )
    except PatientServiceError as error:
        return _error("SOLICITUD_INVALIDA", str(error), 400)

    return jsonify({"paciente": _serializar(paciente), "posicion": _posicion(paciente)}), 201


@api_bp.get("/pacientes")
def listar_pacientes():
    pacientes = _service().listar()
    return jsonify(
        {
            "total": len(pacientes),
            "proximo": _serializar(pacientes[0]) if pacientes else None,
            "pacientes": [_serializar(paciente) for paciente in pacientes],
        }
    )


@api_bp.post("/pacientes/atender")
def atender_paciente():
    paciente = _service().atender_siguiente()
    if paciente is None:
        return jsonify(
            {
                "paciente": None,
                "mensaje": "La cola está vacía. No hay pacientes por atender.",
            }
        )
    return jsonify({"paciente": _serializar(paciente)})


@api_bp.delete("/pacientes/<patient_id>")
def eliminar_paciente(patient_id: str):
    if _service().eliminar_por_id(patient_id) is None:
        return _error(
            "PACIENTE_NO_ENCONTRADO",
            f"no existe un paciente con id {patient_id}",
            404,
        )
    return "", 204


def _posicion(paciente: Patient) -> int:
    """Lugar 1-based del paciente en el orden de atención vigente."""

    for posicion, candidato in enumerate(_service().listar(), start=1):
        if candidato.id == paciente.id:
            return posicion
    return 0


def register_api_error_handlers(flask_app) -> None:
    """Mantiene las respuestas de /api en JSON sin alterar las rutas HTML."""

    @flask_app.errorhandler(404)
    def _no_encontrado(error):
        if _es_peticion_api():
            return _error(
                "RECURSO_NO_ENCONTRADO", "la ruta solicitada no existe", 404
            )
        return error.get_response()

    @flask_app.errorhandler(405)
    def _metodo_no_permitido(error):
        if _es_peticion_api():
            return _error(
                "METODO_NO_PERMITIDO",
                "el método HTTP no está permitido para esta ruta",
                405,
                {"permitidos": sorted(error.valid_methods or [])},
            )
        return error.get_response()


def _es_peticion_api() -> bool:
    return request.path == "/api" or request.path.startswith("/api/")
