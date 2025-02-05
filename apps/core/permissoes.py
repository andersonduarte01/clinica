from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseRedirect
from django.urls import reverse


class PermissaoFuncionariosMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        elif not (request.user.usuario.funcionario or request.user.usuario.adm or request.user.usuario.doutor):
            return HttpResponseRedirect(reverse('home:indice')) # Redirecione para a página apropriada
        return super().dispatch(request, *args, **kwargs)
