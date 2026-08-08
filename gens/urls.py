from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # ------------------------------------------------------------------
    # API v1 — consumida pelo app mobile
    # ------------------------------------------------------------------
    path('api/v1/', include([
        # Autenticação JWT
        path('auth/', include('apps.accounts.api_urls')),
        # Módulo core: pacientes
        path('', include('apps.core.api_urls')),
    ])),

    # ------------------------------------------------------------------
    # Web legado (manter durante migração)
    # ------------------------------------------------------------------
    path('', include('apps.core.urls', namespace='inicio')),
    path('exame/', include('apps.exame.urls', namespace='exame')),
    path('agenda/', include('apps.agenda.urls', namespace='agenda')),
    path('atendimento/', include('apps.atendimento.urls', namespace='atendimento')),
    path('accounts/', include('django.contrib.auth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

