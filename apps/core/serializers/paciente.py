from django.utils import timezone
from rest_framework import serializers
from validate_docbr import CPF

from apps.core.models.paciente import Paciente

_cpf_validator = CPF()


class PacienteListSerializer(serializers.ModelSerializer):
    """Serializer leve para listagens — sem dados sensíveis desnecessários."""

    class Meta:
        model = Paciente
        fields = [
            "id",
            "nome_completo",
            "data_nascimento",
            "sexo",
            "telefone",
            "email",
            "lgpd_consentimento_ativo",
            "created_at",
        ]
        read_only_fields = fields


class PacienteDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhe, criação e atualização."""

    lgpd_consentimento_ativo = serializers.BooleanField(read_only=True)
    is_anonimizado = serializers.BooleanField(read_only=True)

    class Meta:
        model = Paciente
        fields = [
            "id",
            "nome_completo",
            "cpf",
            "data_nascimento",
            "sexo",
            "rg",
            "telefone",
            "email",
            "nome_mae",
            "lgpd_consentimento_at",
            "lgpd_versao_termo",
            "lgpd_consentimento_ativo",
            "anonimizado_at",
            "is_anonimizado",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "lgpd_consentimento_ativo",
            "anonimizado_at",
            "is_anonimizado",
            "created_at",
            "updated_at",
        ]

    def validate_cpf(self, value: str) -> str:
        normalizado = "".join(c for c in value if c.isdigit())
        if not _cpf_validator.validate(normalizado):
            raise serializers.ValidationError("CPF inválido.")
        # Armazena formatado: 000.000.000-00
        return (
            f"{normalizado[:3]}.{normalizado[3:6]}.{normalizado[6:9]}-{normalizado[9:]}"
        )

    def validate(self, attrs: dict) -> dict:
        tenant = self.context["request"].tenant
        cpf = attrs.get("cpf", getattr(self.instance, "cpf", None))

        if cpf:
            from apps.core.models.paciente import _hash_cpf
            cpf_hash = _hash_cpf(cpf)
            qs = Paciente.global_objects.filter(
                tenant=tenant,
                cpf_hash=cpf_hash,
                deleted_at__isnull=True,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"cpf": "Já existe um paciente com este CPF neste laboratório."}
                )

        return attrs


class PacienteCreateSerializer(PacienteDetailSerializer):
    """Criação exige consentimento LGPD explícito."""

    lgpd_aceite = serializers.BooleanField(
        write_only=True,
        help_text="O paciente deve consentir com a política de privacidade no momento do cadastro.",
    )
    lgpd_versao_termo = serializers.CharField(
        required=True,
        help_text="Versão do termo de consentimento exibido ao paciente. Ex: '2025-01'.",
    )

    class Meta(PacienteDetailSerializer.Meta):
        fields = PacienteDetailSerializer.Meta.fields + ["lgpd_aceite"]

    def validate_lgpd_aceite(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError(
                "O consentimento LGPD é obrigatório para cadastrar um paciente."
            )
        return value

    def create(self, validated_data: dict) -> Paciente:
        validated_data.pop("lgpd_aceite")
        validated_data["lgpd_consentimento_at"] = timezone.now()
        validated_data["tenant"] = self.context["request"].tenant
        return Paciente.global_objects.create(**validated_data)


class PacienteUpdateSerializer(PacienteDetailSerializer):
    """Atualização — CPF não pode ser alterado após o cadastro."""

    class Meta(PacienteDetailSerializer.Meta):
        read_only_fields = PacienteDetailSerializer.Meta.read_only_fields + ["cpf"]


class LgpdConsentimentoSerializer(serializers.Serializer):
    """Registra (ou atualiza) o consentimento LGPD de um paciente já cadastrado."""

    lgpd_versao_termo = serializers.CharField(
        help_text="Versão do termo exibido. Ex: '2025-01'.",
    )
    aceite = serializers.BooleanField(
        help_text="Deve ser true. False indica recusa — retorna erro.",
    )

    def validate_aceite(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("O paciente recusou o consentimento.")
        return value
