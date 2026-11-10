"""Capa HTTP JSON del sistema de cola hospitalaria."""

from .routes import api_bp, register_api_error_handlers

__all__ = ["api_bp", "register_api_error_handlers"]
