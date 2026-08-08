from .base import (
    SoftDeleteMixin,
    SoftDeleteManager,
    SoftDeleteQuerySet,
    TenantAwareModel,
    TenantAwareManager,
    TenantAwareSoftDeleteManager,
)
from .paciente import Paciente

# Models legados re-exportados para não quebrar migrations existentes.
# Remover após migração completa para a nova estrutura.
from apps.core.models_legacy import Endereco, Usuario

__all__ = [
    # Mixins base
    "SoftDeleteMixin",
    "SoftDeleteManager",
    "SoftDeleteQuerySet",
    "TenantAwareModel",
    "TenantAwareManager",
    "TenantAwareSoftDeleteManager",
    # Models novos
    "Paciente",
    # Legados (temporário)
    "Usuario",
    "Endereco",
]
