"""Entidades y estructuras de dominio de la cola hospitalaria."""

from .patient import Patient
from .patient_queue import PatientQueue

__all__ = ["Patient", "PatientQueue"]
