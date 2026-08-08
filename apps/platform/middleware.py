import threading

from django.conf import settings
from django.http import Http404

_thread_local = threading.local()


def get_current_tenant():
    """Retorna o tenant resolvido para o request atual. None fora de um request de tenant."""
    return getattr(_thread_local, "current_tenant", None)


def set_current_tenant(tenant) -> None:
    _thread_local.current_tenant = tenant


class TenantMiddleware:
    """
    Resolve o tenant pelo subdomínio do Host header e injeta em:
      - request.tenant
      - thread-local (acessível por TenantAwareManager e get_current_tenant())

    Hosts isentos (domínio raiz, painel da plataforma) recebem tenant=None.
    Após o response, o thread-local é limpo para evitar vazamento entre requests
    em workers que reutilizam threads (ex: Gunicorn gevent).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._base_domain: str = getattr(settings, "SAAS_BASE_DOMAIN", "labsaas.com.br")
        self._exempt: set[str] = getattr(settings, "TENANT_EXEMPT_HOSTS", set()) | {
            self._base_domain,
            f"www.{self._base_domain}",
            "localhost",
            "127.0.0.1",
        }

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()

        if host in self._exempt:
            set_current_tenant(None)
            request.tenant = None
            return self.get_response(request)

        tenant = self._resolve_tenant(host)
        set_current_tenant(tenant)
        request.tenant = tenant

        try:
            response = self.get_response(request)
        finally:
            # Garante limpeza mesmo em caso de exceção não tratada
            set_current_tenant(None)

        return response

    def _resolve_tenant(self, host: str):
        from apps.platform.models import Tenant

        slug = host.replace(f".{self._base_domain}", "")

        try:
            return Tenant.objects.get(
                slug=slug,
                status__in=[Tenant.Status.TRIAL, Tenant.Status.ACTIVE],
                deleted_at__isnull=True,
            )
        except Tenant.DoesNotExist:
            raise Http404(
                f"Laboratório '{slug}' não encontrado ou suspenso. "
                "Verifique o endereço ou entre em contato com o suporte."
            )
