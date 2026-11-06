import pytest

from domain.patient import Patient


def test_patient_exposes_immutable_domain_data_and_sort_key() -> None:
    patient = Patient(
        id="p-0001",
        nombre="Ana López",
        prioridad=2,
        orden_llegada=4,
    )

    assert patient.id == "p-0001"
    assert patient.nombre == "Ana López"
    assert patient.prioridad == 2
    assert patient.orden_llegada == 4
    assert patient.sort_key == (2, 4)

    with pytest.raises(AttributeError):
        patient.nombre = "Otro nombre"  # type: ignore[misc]


def test_patient_ordering_uses_priority_then_arrival_order() -> None:
    later = Patient("p-0002", "B", prioridad=2, orden_llegada=1)
    earlier = Patient("p-0001", "A", prioridad=2, orden_llegada=0)
    more_urgent = Patient("p-0003", "C", prioridad=1, orden_llegada=9)

    assert earlier < later
    assert sorted([later, more_urgent, earlier]) == [more_urgent, earlier, later]


@pytest.mark.parametrize(
    "field, value",
    [
        ("id", ""),
        ("id", None),
        ("nombre", None),
        ("prioridad", 0),
        ("prioridad", -1),
        ("prioridad", 6),
        ("prioridad", 999),
        ("prioridad", "2x"),
        ("prioridad", None),
        ("prioridad", ""),
        ("prioridad", 2.5),
        ("prioridad", True),
        ("orden_llegada", -1),
        ("orden_llegada", True),
    ],
    ids=[
        "id-vacio",
        "id-none",
        "nombre-none",
        "prioridad-cero",
        "prioridad-negativa",
        "prioridad-seis",
        "prioridad-999",
        "prioridad-no-numerica",
        "prioridad-none",
        "prioridad-vacia",
        "prioridad-decimal",
        "prioridad-bool",
        "orden-negativo",
        "orden-bool",
    ],
)
def test_patient_rejects_invalid_domain_values(field: str, value: object) -> None:
    values: dict[str, object] = {
        "id": "p-0001",
        "nombre": "Paciente",
        "prioridad": 1,
        "orden_llegada": 0,
    }
    values[field] = value

    with pytest.raises((TypeError, ValueError)):
        Patient(**values)  # type: ignore[arg-type]
