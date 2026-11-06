import pytest

from services.patient_service import (
    InvalidPatientNameError,
    InvalidPriorityError,
    PatientService,
)


@pytest.mark.parametrize(
    "priority",
    [1, 2, 3, 4, 5],
    ids=[
        "U-01-prioridad-1",
        "U-02-prioridad-2",
        "U-03-prioridad-3",
        "U-04-prioridad-4",
        "U-05-prioridad-5",
    ],
)
def test_U01_U05_service_accepts_priorities_1_to_5(
    patient_service,
    priority: int,
) -> None:
    patient = patient_service.registrar("Paciente válido", priority)

    assert patient.prioridad == priority
    assert patient_service.listar() == [patient]


def test_service_normalizes_a_valid_string_priority(patient_service) -> None:
    patient = patient_service.registrar("Paciente", " 2 ")

    assert patient.prioridad == 2


@pytest.mark.parametrize(
    "priority",
    [0, -1],
    ids=["U-14-cero", "U-14-negativa"],
)
def test_U14_service_rejects_priorities_below_one(patient_service, priority: int) -> None:
    with pytest.raises(InvalidPriorityError):
        patient_service.registrar("Paciente", priority)

    assert patient_service.listar() == []


@pytest.mark.parametrize(
    "priority",
    [6, 999],
    ids=["U-15-seis", "U-15-999"],
)
def test_U15_service_rejects_priorities_above_five(
    patient_service,
    priority: int,
) -> None:
    with pytest.raises(InvalidPriorityError):
        patient_service.registrar("Paciente", priority)

    assert patient_service.listar() == []


@pytest.mark.parametrize(
    "priority",
    ["2x", None, "", "   ", 2.5, "2.5", True, False],
    ids=[
        "U-16-texto",
        "U-16-none",
        "U-16-vacio",
        "U-16-espacios",
        "U-16-decimal",
        "U-16-decimal-texto",
        "U-16-bool-true",
        "U-16-bool-false",
    ],
)
def test_U16_service_rejects_non_numeric_and_non_integer_priorities(
    patient_service,
    priority: object,
) -> None:
    with pytest.raises(InvalidPriorityError):
        patient_service.registrar("Paciente", priority)  # type: ignore[arg-type]

    assert patient_service.listar() == []


@pytest.mark.parametrize(
    ("raw_name", "normalized_name"),
    [
        ("  Ana López  ", "Ana López"),
        ("A", "A"),
        ("P" * 120, "P" * 120),
    ],
    ids=["U-17-trim", "U-17-minimo", "U-17-largo"],
)
def test_U17_service_validates_and_normalizes_names(
    patient_service,
    raw_name: str,
    normalized_name: str,
) -> None:
    patient = patient_service.registrar(raw_name, 3)

    assert patient.nombre == normalized_name


@pytest.mark.parametrize(
    "name",
    ["", "   ", None, 123],
    ids=["U-17-vacio", "U-17-espacios", "U-17-none", "U-17-no-texto"],
)
def test_U17_service_rejects_invalid_names(patient_service, name: object) -> None:
    with pytest.raises(InvalidPatientNameError):
        patient_service.registrar(name, 3)  # type: ignore[arg-type]

    assert patient_service.listar() == []


def test_U10_service_reports_empty_list_and_next_without_mutation(
    patient_service,
) -> None:
    assert patient_service.listar() == []
    assert patient_service.proximo() is None
    assert patient_service.atender_siguiente() is None
    assert patient_service.listar() == []


def test_U12_service_can_attend_and_remove_by_id(patient_service) -> None:
    first = patient_service.registrar("A", 2)
    second = patient_service.registrar("B", 1)

    assert patient_service.proximo() == second
    assert patient_service.atender_siguiente() == second
    assert patient_service.eliminar_por_id(first.id) == first
    assert patient_service.eliminar_por_id(first.id) is None
    assert patient_service.listar() == []


def test_U13_service_remove_unknown_id_does_not_change_state(patient_service) -> None:
    patient = patient_service.registrar("A", 1)
    before = patient_service.listar()

    assert patient_service.eliminar_por_id("p-9999") is None
    assert patient_service.listar() == before
    assert patient_service.proximo() == patient


def test_service_remove_by_name_normalizes_name_and_handles_absent_patient(
    patient_service,
) -> None:
    patient = patient_service.registrar("  Ana  ", 2)

    assert patient_service.eliminar_por_nombre(" Ana ") == patient
    assert patient_service.eliminar_por_nombre("Ana") is None
    assert patient_service.listar() == []


def test_U18_duplicate_names_are_removed_unambiguously_by_id(patient_service) -> None:
    first = patient_service.registrar("Ana", 3)
    second = patient_service.registrar("Ana", 3)

    assert first.id != second.id
    assert patient_service.eliminar_por_id(second.id) == second
    assert patient_service.listar() == [first]
    assert patient_service.eliminar_por_id(first.id) == first
    assert patient_service.listar() == []


def test_U19_remove_then_register_preserves_state_and_fifo(patient_service) -> None:
    removed = patient_service.registrar("Se retira", 2)
    urgent = patient_service.registrar("Urgente", 1)
    patient_service.eliminar_por_id(removed.id)

    re_registered = patient_service.registrar("Nuevo", 2)

    assert re_registered.id == "p-0003"
    assert re_registered.orden_llegada == 2
    assert [patient.nombre for patient in patient_service.listar()] == [
        "Urgente",
        "Nuevo",
    ]


def test_service_instances_are_isolated(patient_service: PatientService) -> None:
    another_service = PatientService()

    patient_service.registrar("Sólo en A", 1)
    patient_in_b = another_service.registrar("Sólo en B", 1)

    assert [patient.nombre for patient in patient_service.listar()] == ["Sólo en A"]
    assert [patient.nombre for patient in another_service.listar()] == ["Sólo en B"]
    assert patient_in_b.id == "p-0001"
