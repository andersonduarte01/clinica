from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

handler400 = 'apps.core.views.Erro400'
handler500 = 'apps.core.views.Erro500'
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls', namespace='inicio')),
    path('exame/', include('apps.exame.urls', namespace='exame')),
    path('agenda/', include('apps.agenda.urls', namespace='agenda')),
    path('atendimento/', include('apps.atendimento.urls', namespace='atendimento')),
    path('accounts/', include('django.contrib.auth.urls'),),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

