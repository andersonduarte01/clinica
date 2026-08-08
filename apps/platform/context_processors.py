from apps.platform.modules import MODULE_REGISTRY


def tenant_context(request):
    """
    Injeta dados do tenant e módulos ativos em todos os templates.

    Disponível nos templates como:
        {{ tenant.name }}
        {% if modulos_ativos.qc %}
        {{ modulos_info.qc.label }}
    """
    tenant = getattr(request, "tenant", None)
    if tenant is None:
        return {"tenant": None, "modulos_ativos": frozenset(), "modulos_info": {}}

    modulos_ativos = tenant.modulos_ativos

    return {
        "tenant": tenant,
        # frozenset com os Module enums ativos — usado em checks diretos no template
        "modulos_ativos": modulos_ativos,
        # dict {module_key_str: ModuleInfo} apenas dos módulos ativos — para montar menus
        "modulos_info": {
            mod.value: MODULE_REGISTRY[mod]
            for mod in modulos_ativos
            if mod in MODULE_REGISTRY
        },
    }
