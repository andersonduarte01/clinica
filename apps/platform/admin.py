from django.contrib import admin

from apps.platform.models import Tenant, TenantUser
from apps.platform.modules import MODULE_REGISTRY


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "plan",
        "status",
        "modulos_ativos_count",
        "trial_ends_at",
        "created_at",
    ]
    list_filter = ["plan", "status"]
    search_fields = ["name", "slug", "cnpj", "email"]
    readonly_fields = ["id", "created_at", "updated_at", "modulos_ativos_display"]

    fieldsets = [
        ("Identificação", {
            "fields": ["id", "name", "slug", "cnpj", "logo"],
        }),
        ("Responsável Técnico", {
            "fields": ["responsible_name", "responsible_crm_crbm", "email", "phone"],
        }),
        ("Plano e Status", {
            "fields": ["plan", "status", "trial_ends_at"],
        }),
        ("Módulos", {
            "fields": [
                "modulos_extras",
                "modulos_desabilitados",
                "modulos_ativos_display",
            ],
            "description": (
                "Os módulos ativos são calculados como: "
                "(módulos do plano ∪ extras) − desabilitados ∪ {core}."
            ),
        }),
        ("Configurações", {
            "fields": ["settings"],
            "classes": ["collapse"],
        }),
        ("Auditoria", {
            "fields": ["created_at", "updated_at", "deleted_at"],
            "classes": ["collapse"],
        }),
    ]

    def modulos_ativos_count(self, obj: Tenant) -> int:
        return len(obj.modulos_ativos)
    modulos_ativos_count.short_description = "Módulos Ativos"

    def modulos_ativos_display(self, obj: Tenant) -> str:
        modulos = obj.modulos_ativos
        labels = sorted(
            MODULE_REGISTRY[m].label
            for m in modulos
            if m in MODULE_REGISTRY
        )
        return ", ".join(labels) if labels else "Nenhum"
    modulos_ativos_display.short_description = "Módulos Ativos (calculado automaticamente)"


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ["user", "tenant", "role", "is_active", "created_at"]
    list_filter = ["role", "is_active", "tenant__plan"]
    search_fields = ["user__username", "user__email", "tenant__name", "tenant__slug"]
    raw_id_fields = ["user", "tenant"]
