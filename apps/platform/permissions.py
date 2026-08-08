from functools import wraps

from django.core.exceptions import PermissionDenied

from apps.platform.modules import Module


class ModuleRequiredMixin:
    """
    Mixin para class-based views Django.

    Uso:
        class ExameListView(ModuleRequiredMixin, ListView):
            required_module = 'exame'
            model = Exame
    """

    required_module: str | Module | None = None

    def dispatch(self, request, *args, **kwargs):
        if self.required_module:
            tenant = getattr(request, "tenant", None)
            if tenant is None or not tenant.has_module(self.required_module):
                raise PermissionDenied(
                    f"O módulo '{self.required_module}' não está disponível no plano contratado."
                )
        return super().dispatch(request, *args, **kwargs)


def module_required(module: str | Module):
    """
    Decorator para function-based views Django.

    Uso:
        @module_required('qc')
        def levey_jennings_view(request, exame_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            tenant = getattr(request, "tenant", None)
            if tenant is None or not tenant.has_module(module):
                raise PermissionDenied(
                    f"O módulo '{module}' não está disponível no plano contratado."
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class HasModulePermission:
    """
    Permission class para DRF ViewSets.

    Uso:
        class ExameViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, HasModulePermission('exame')]

    Não herda de BasePermission do DRF intencionalmente — é instanciada
    via fábrica para receber o módulo como argumento.
    """

    def __init__(self, module: str | Module):
        self.module = module

    def __call__(self):
        # Permite uso como permission_classes = [HasModulePermission('exame')]
        # O DRF instancia a classe — aqui retornamos a própria instância.
        return self

    def has_permission(self, request, view) -> bool:
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False
        return tenant.has_module(self.module)

    def has_object_permission(self, request, view, obj) -> bool:
        return self.has_permission(request, view)
