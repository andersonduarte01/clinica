import uuid

from django.db import models
from django.utils import timezone

from apps.platform.modules import Module, get_effective_modules


class Tenant(models.Model):
    class Status(models.TextChoices):
        TRIAL = "TRIAL", "Trial"
        ACTIVE = "ACTIVE", "Ativo"
        SUSPENDED = "SUSPENDED", "Suspenso"
        CANCELLED = "CANCELLED", "Cancelado"

    class Plan(models.TextChoices):
        FREE_TRIAL = "FREE_TRIAL", "Trial Gratuito (30 dias)"
        BASIC = "BASIC", "Básico"
        PROFESSIONAL = "PROFESSIONAL", "Profissional"
        ENTERPRISE = "ENTERPRISE", "Enterprise"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Nome do Laboratório")
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Usado como subdomínio: slug.labsaas.com.br",
    )
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    responsible_name = models.CharField(
        max_length=200,
        verbose_name="Responsável Técnico",
    )
    responsible_crm_crbm = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="CRM / CRBM",
    )
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    logo = models.ImageField(
        upload_to="tenants/logos/",
        null=True,
        blank=True,
        verbose_name="Logotipo",
    )

    # Plano e status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TRIAL,
        db_index=True,
    )
    plan = models.CharField(
        max_length=20,
        choices=Plan.choices,
        default=Plan.FREE_TRIAL,
        verbose_name="Plano",
    )
    trial_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Trial expira em",
    )

    # Controle de módulos por tenant
    # Permite adicionar módulos avulsos além do plano (ex: TISS para cliente BASIC especial)
    # e desabilitar módulos incluídos no plano que o tenant não usa.
    modulos_extras = models.JSONField(
        default=list,
        verbose_name="Módulos extras",
        help_text=(
            "Módulos adicionados além do plano contratado. "
            "Ex: ['tiss', 'estoque']. "
            "Consulte Module em apps/platform/modules.py para os valores válidos."
        ),
    )
    modulos_desabilitados = models.JSONField(
        default=list,
        verbose_name="Módulos desabilitados",
        help_text=(
            "Módulos do plano que foram desabilitados para este tenant. "
            "O módulo 'core' nunca pode ser desabilitado."
        ),
    )

    # Configurações livres do tenant (timeout de sessão, 2FA, fuso horário, etc.)
    settings = models.JSONField(
        default=dict,
        verbose_name="Configurações",
        help_text=(
            "Configurações customizáveis do tenant. Chaves disponíveis: "
            "session_timeout_minutes (int), "
            "2fa_obrigatorio (bool), "
            "email_remetente (str), "
            "municipio_codigo_ibge (str), "
            "meses_para_anonimizacao (int)."
        ),
    )

    # Soft delete — tenant deletado não remove os dados, apenas oculta
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"

    # ------------------------------------------------------------------
    # Módulos
    # ------------------------------------------------------------------

    @property
    def modulos_ativos(self) -> frozenset[Module]:
        """
        Conjunto efetivo de módulos ativos para este tenant.
        Calculado em tempo de execução — não persiste em banco.
        Use `tenant.has_module('qc')` para verificações pontuais.
        """
        return get_effective_modules(self)

    def has_module(self, module: str | Module) -> bool:
        if isinstance(module, str):
            try:
                module = Module(module)
            except ValueError:
                return False
        return module in self.modulos_ativos

    # ------------------------------------------------------------------
    # Trial
    # ------------------------------------------------------------------

    @property
    def trial_expirado(self) -> bool:
        if self.status != self.Status.TRIAL:
            return False
        if self.trial_ends_at is None:
            return False
        return timezone.now() > self.trial_ends_at

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self):
        super().delete()
