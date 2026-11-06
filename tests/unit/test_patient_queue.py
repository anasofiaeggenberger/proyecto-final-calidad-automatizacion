import pytest

from domain.patient import Patient
from domain.patient_queue import PatientQueue


def patient_names(patients: list[Patient]) -> list[str]:
    return [patient.nombre for patient in patients]


def test_U06_queue_orders_distinct_priorities(patient_queue: PatientQueue) -> None:
    for priority in [5, 1, 3, 2, 4]:
        patient_queue.enqueue(f"P{priority}", priority)

    assert [patient.prioridad for patient in patient_queue.list_ordered()] == [
        1,
        2,
        3,
        4,
        5,
    ]


def test_U07_queue_preserves_fifo_for_equal_priorities(
    patient_queue: PatientQueue,
) -> None:
    for name in ["A", "B", "C"]:
        patient_queue.enqueue(name, 3)

    assert patient_names(patient_queue.list_ordered()) == ["A", "B", "C"]
    assert patient_names(
        [
            patient_queue.attend_next(),
            patient_queue.attend_next(),
            patient_queue.attend_next(),
        ]
    ) == ["A", "B", "C"]


def test_U08_queue_preserves_fifo_with_interleaved_priorities(
    patient_queue: PatientQueue,
) -> None:
    for name, priority in [("A", 2), ("B", 1), ("C", 2), ("D", 1)]:
        patient_queue.enqueue(name, priority)

    attended = [patient_queue.attend_next() for _ in range(4)]

    assert patient_names(attended) == ["B", "D", "A", "C"]


@pytest.mark.parametrize(
    "priority",
    [1, 5],
    ids=["U-09-prioridad-1", "U-09-prioridad-5"],
)
def test_U09_queue_preserves_strict_arrival_order_when_all_priorities_match(
    patient_queue: PatientQueue,
    priority: int,
) -> None:
    for name in ["A", "B", "C", "D"]:
        patient_queue.enqueue(name, priority)

    assert patient_names(
        [patient_queue.attend_next() for _ in range(4)]
    ) == ["A", "B", "C", "D"]


def test_U10_empty_queue_list_peek_and_attend_do_not_mutate(
    patient_queue: PatientQueue,
) -> None:
    assert patient_queue.is_empty()
    assert len(patient_queue) == 0
    assert patient_queue.list_ordered() == []
    assert patient_queue.peek() is None
    assert patient_queue.attend_next() is None
    assert patient_queue.list_ordered() == []
    assert patient_queue.is_empty()


def test_U11_attending_until_empty_returns_expected_patients_then_none(
    patient_queue: PatientQueue,
) -> None:
    for name, priority in [("A", 3), ("B", 1), ("C", 2)]:
        patient_queue.enqueue(name, priority)

    assert patient_names(
        [patient_queue.attend_next() for _ in range(3)]
    ) == ["B", "C", "A"]
    assert patient_queue.attend_next() is None
    assert patient_queue.is_empty()


def test_U12_remove_existing_id_keeps_heap_order_valid(
    patient_queue: PatientQueue,
) -> None:
    first = patient_queue.enqueue("A", 1)
    middle = patient_queue.enqueue("B", 2)
    last = patient_queue.enqueue("C", 3)

    assert patient_queue.remove_by_id(middle.id) == middle
    assert [patient.id for patient in patient_queue.list_ordered()] == [
        first.id,
        last.id,
    ]
    assert patient_queue.attend_next() == first
    assert patient_queue.attend_next() == last
    assert patient_queue.attend_next() is None


def test_U13_remove_nonexistent_id_leaves_queue_unchanged(
    patient_queue: PatientQueue,
) -> None:
    patient_queue.enqueue("A", 2)
    patient_queue.enqueue("B", 1)
    before = patient_queue.list_ordered()
    before_next = patient_queue.peek()

    assert patient_queue.remove_by_id("p-9999") is None
    assert patient_queue.list_ordered() == before
    assert patient_queue.peek() == before_next
    assert len(patient_queue) == 2


def test_list_ordered_does_not_modify_queue_state(
    patient_queue: PatientQueue,
) -> None:
    patient_queue.enqueue("A", 3)
    patient_queue.enqueue("B", 1)
    patient_queue.enqueue("C", 2)
    before_next = patient_queue.peek()
    before_length = len(patient_queue)

    ordered = patient_queue.list_ordered()

    assert patient_names(ordered) == ["B", "C", "A"]
    assert patient_queue.peek() == before_next
    assert len(patient_queue) == before_length
    assert patient_names(
        [patient_queue.attend_next() for _ in range(3)]
    ) == ["B", "C", "A"]


def test_queue_instances_are_isolated(patient_queue: PatientQueue) -> None:
    another_queue = PatientQueue()

    patient_queue.enqueue("Sólo en A", 1)
    patient_in_b = another_queue.enqueue("Sólo en B", 1)

    assert [patient.nombre for patient in patient_queue.list_ordered()] == [
        "Sólo en A"
    ]
    assert [patient.nombre for patient in another_queue.list_ordered()] == [
        "Sólo en B"
    ]
    assert patient_in_b.id == "p-0001"
    assert len(patient_queue) == 1
    assert len(another_queue) == 1
