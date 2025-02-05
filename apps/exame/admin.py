from django.contrib import admin
from .models import Exame, ReferenciaExame, FatoresReferencia, ValorEsperado, GrupoExame
# Register your models here.

admin.site.register(Exame)
admin.site.register(ReferenciaExame)
admin.site.register(FatoresReferencia)
admin.site.register(ValorEsperado)
admin.site.register(GrupoExame)
