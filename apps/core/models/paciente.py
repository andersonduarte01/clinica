import hashlib
import uuid

from django.db import models

from apps.core.models.base import SoftDeleteMixin, TenantAwareModel, TenantAwareSoftDeleteManager


def _hash_cpf(cpf: str) -> str:
    """SHA-256 do CPF normalizado (apenas dígitos). Usado para busca sem expor o CPF."""
    digitos = "".join(c for c in cpf if c.isdigit())
    return hashlib.sha256(f"labsaas:{digitos}".encode()).hexdigest()


class PacienteManager(TenantAwareSoftDeleteManager):
    def por_cpf(self, cpf: str):
        return self.get_queryset().filter(cpf_hash=_hash_cpf(cpf))

    def por_cpf_e_nascimento(self, cpf: str, data_nascimento):
        """Usado no login do portal do paciente (sem senha)."""
        return self.get_queryset().filter(
            cpf_hash=_hash_cpf(cpf),
            data_nascimento=data_nascimento,
        )


class Paciente(TenantAwareModel, SoftDeleteMixin):
    class Sexo(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMININO = "F", "Feminino"
        NAO_INFORMADO = "N", "Não Informado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # CPF armazenado em texto puro por ora.
    # cpf_hash permite busca sem varredura completa da tabela.
    # Quando django-encrypted-fields for instalado, `cpf` vira EncryptedCharField.
    cpf = models.CharField(max_length=14, verbose_name="CPF")
    cpf_hash = models.CharField(
        max_length=64,
        db_index=True,
        editable=False,
        help_text="SHA-256 do CPF normalizado. Gerado automaticamente.",
    )

    nome_completo = models.CharField(max_length=200, db_index=True, verbose_name="Nome Completo")
    data_nascimento = models.DateField(db_index=True, verbose_name="Data de Nascimento")
    sexo = models.CharField(max_length=1, choices=Sexo.choices, default=Sexo.NAO_INFORMADO)

    rg = models.CharField(max_length=20, blank=True, verbose_name="RG")
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    nome_mae = models.CharField(max_length=200, blank=True, verbose_name="Nome da Mãe")

    # LGPD
    lgpd_consentimento_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Consentimento LGPD em",
    )
    lgpd_versao_termo = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Versão do Termo LGPD",
        help_text="Ex: '2025-01'. Atualizar quando o texto do termo mudar.",
    )
    anonimizado_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Anonimizado em",
        help_text="Preenchido pela task de retenção LGPD. Indica dados substituídos por hash.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PacienteManager()
    global_objects = models.Manager()

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        # CPF único por tenant — dois tenants diferentes podem ter o mesmo paciente
        unique_together = [("tenant", "cpf_hash")]
        indexes = [
            models.Index(fields=["tenant", "nome_completo"]),
            models.Index(fields=["tenant", "data_nascimento"]),
        ]

    def __str__(self) -> str:
        return f"{self.nome_completo} ({self.cpf})"

    def save(self, *args, **kwargs):
        self.cpf_hash = _hash_cpf(self.cpf)
        super().save(*args, **kwargs)

    @property
    def lgpd_consentimento_ativo(self) -> bool:
        return self.lgpd_consentimento_at is not None

    @property
    def is_anonimizado(self) -> bool:
        return self.anonimizado_at is not None
