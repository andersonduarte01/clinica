from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Adiciona dados do tenant e papel do usuário ao payload do JWT.
    O app mobile usa esses campos para saber quais telas exibir sem
    fazer uma requisição extra ao servidor.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["is_superadmin"] = getattr(user, "is_superadmin", False)

        # Determina o tenant a partir do último acesso ou da única membership
        tenant = None
        memberships = user.tenant_memberships.filter(is_active=True).select_related("tenant")

        if memberships.count() == 1:
            membership = memberships.first()
            tenant = membership.tenant
            token["role"] = membership.role
        else:
            # Usuário em múltiplos tenants — tenant resolvido pelo subdomínio no middleware
            token["role"] = ""

        if tenant:
            token["tenant_id"] = str(tenant.id)
            token["tenant_slug"] = tenant.slug
            token["tenant_name"] = tenant.name
            token["tenant_plan"] = tenant.plan
            token["modulos_ativos"] = sorted(m.value for m in tenant.modulos_ativos)
        else:
            token["tenant_id"] = None
            token["tenant_slug"] = None
            token["tenant_name"] = None
            token["tenant_plan"] = None
            token["modulos_ativos"] = []

        return token
