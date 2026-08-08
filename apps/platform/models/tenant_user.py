import uuid

from django.conf import settings
from django.db import models


class TenantUser(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin_clinica", "Administrador da Clínica"
        BIOMEDICO = "biomedico", "Biomédico"
        RECEPCIONISTA = "recepcionista", "Recepcionista"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "platform.Tenant",
        on_delete=models.CASCADE,
        related_name="tenant_users",
        verbose_name="Tenant",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_memberships",
        verbose_name="Usuário",
    )
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        db_index=True,
        verbose_name="Papel",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("tenant", "user")]
        indexes = [models.Index(fields=["tenant", "role"])]
        verbose_name = "Usuário do Tenant"
        verbose_name_plural = "Usuários dos Tenants"

    def __str__(self) -> str:
        return f"{self.user} @ {self.tenant.slug} ({self.get_role_display()})"

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_biomedico(self) -> bool:
        return self.role == self.Role.BIOMEDICO

    @property
    def is_recepcionista(self) -> bool:
        return self.role == self.Role.RECEPCIONISTA
