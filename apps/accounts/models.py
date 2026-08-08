import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    User customizado da plataforma LabSaaS.

    Campos extras além do AbstractUser padrão:
    - is_superadmin: administrador da plataforma (acima dos tenants)
    - totp_secret:   segredo TOTP para 2FA (vazio até o usuário ativar 2FA)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    is_superadmin = models.BooleanField(
        default=False,
        verbose_name="Superadmin da plataforma",
        help_text="Acesso irrestrito a todos os tenants. Reservado para a equipe LabSaaS.",
    )

    totp_secret = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Segredo TOTP",
        help_text="Base32 gerado ao ativar 2FA. Vazio enquanto 2FA estiver desativado.",
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    @property
    def has_2fa(self) -> bool:
        return bool(self.totp_secret)
