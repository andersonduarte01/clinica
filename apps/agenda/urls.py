from django.urls import path
from . import views

app_name = 'agenda'

urlpatterns = [
    path('<int:pk>/novo/plano/', views.PlanosAdd.as_view(), name='plano_add'),
    path('<int:pk>/atualizar/plano/', views.PlanoUp.as_view(), name='plano_up'),
    path('<int:pk>/deletar/plano/', views.PlanoDEL.as_view(), name='plano_del'),
    path('calendario/', views.OrdemChegadaCalendario.as_view(), name='ordem_chegada_calendario'),
    path('ordem/<int:pk>/fila/', views.ChegadaADD.as_view(), name='chegada_add'),
    path('atualizar/<int:pk>/fila/', views.OrdemChegadaUP.as_view(), name='ordem_chegada_up'),
    path('lista/ordem_fila/', views.OrdemChegadaLista.as_view(), name='ordem_chegada_lista'),
    path('ordem/fila/lista/', views.OrdemChegadaListaData.as_view(), name='ordem_chegada_lista_data'),
    path('pesquisar/atendimento/', views.BuscarOrdem.as_view(), name='pesquisar_agendamento'),
    path('pesquisar/paciente/', views.Buscarpaciente.as_view(), name='pesquisar_paciente'),
    path('buscar/agendamento/', views.buscar_agendamento, name='busca_agendamento'),
    path('buscar/paciente/', views.buscar_paciente, name='busca_paciente'),
    path('agendamentos/<int:pk>/encontrados/', views.AgendamentosEncontrados.as_view(), name='agendamentos_encontrados'),

]
