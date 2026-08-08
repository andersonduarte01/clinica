from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)

from apps.core.models.paciente import Paciente
from apps.core.serializers.paciente import (
    LgpdConsentimentoSerializer,
    PacienteCreateSerializer,
    PacienteDetailSerializer,
    PacienteListSerializer,
    PacienteUpdateSerializer,
)
from apps.platform.permissions import HasModulePermission


class PacienteViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    """
    API de Pacientes — consumida pelo app mobile.

    list:        GET  /api/v1/pacientes/
    create:      POST /api/v1/pacientes/
    retrieve:    GET  /api/v1/pacientes/{id}/
    update:      PUT  /api/v1/pacientes/{id}/
    partial:     PATCH /api/v1/pacientes/{id}/
    delete:      DELETE /api/v1/pacientes/{id}/    (soft delete)
    consentimento: POST /api/v1/pacientes/{id}/lgpd/
    buscar_cpf:  GET  /api/v1/pacientes/buscar/?cpf=000.000.000-00
    """

    permission_classes = [IsAuthenticated, HasModulePermission("core")]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["sexo"]
    search_fields = ["nome_completo", "email", "telefone"]
    ordering_fields = ["nome_completo", "data_nascimento", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # TenantAwareManager já filtra pelo tenant do request atual.
        # global_objects nunca deve ser usado aqui.
        return Paciente.objects.all().select_related("tenant")

    def get_serializer_class(self):
        if self.action == "create":
            return PacienteCreateSerializer
        if self.action in ("update", "partial_update"):
            return PacienteUpdateSerializer
        if self.action == "list":
            return PacienteListSerializer
        return PacienteDetailSerializer

    def destroy(self, request, *args, **kwargs):
        """Soft delete — o registro não é removido do banco."""
        paciente = self.get_object()
        paciente.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------------
    # Actions extras
    # ------------------------------------------------------------------

    @action(detail=False, methods=["get"], url_path="buscar")
    def buscar_cpf(self, request):
        """
        GET /api/v1/pacientes/buscar/?cpf=000.000.000-00

        Busca rápida por CPF. Retorna 404 se não encontrado.
        Usado pelo mobile antes de cadastrar para evitar duplicatas.
        """
        cpf = request.query_params.get("cpf", "").strip()
        if not cpf:
            return Response(
                {"detail": "Parâmetro 'cpf' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            paciente = Paciente.objects.por_cpf(cpf).get()
        except Paciente.DoesNotExist:
            return Response(
                {"detail": "Paciente não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(PacienteDetailSerializer(paciente, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="lgpd")
    def lgpd_consentimento(self, request, pk=None):
        """
        POST /api/v1/pacientes/{id}/lgpd/

        Registra ou atualiza o consentimento LGPD do paciente.
        Deve ser chamado quando o app exibe o termo e o paciente aceita.

        Body:
            { "lgpd_versao_termo": "2025-01", "aceite": true }
        """
        paciente = self.get_object()
        serializer = LgpdConsentimentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        paciente.lgpd_consentimento_at = timezone.now()
        paciente.lgpd_versao_termo = serializer.validated_data["lgpd_versao_termo"]
        paciente.save(update_fields=["lgpd_consentimento_at", "lgpd_versao_termo", "updated_at"])

        return Response(
            {
                "detail": "Consentimento registrado com sucesso.",
                "lgpd_consentimento_at": paciente.lgpd_consentimento_at,
                "lgpd_versao_termo": paciente.lgpd_versao_termo,
            },
            status=status.HTTP_200_OK,
        )
