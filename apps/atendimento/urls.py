from django.urls import path
from . import views

app_name = 'atendimento'

urlpatterns = [
    path('<int:pk>/atualizar/', views.OrcamentoUpdate.as_view(), name='orcamento_update'),
    path('financeiro/<int:pk>/atualizar/', views.OrcamentoFinanceiroUpdate.as_view(), name='financeiro_update'),
    path('paciente/<int:pk>/atendimento/', views.Orcamento.as_view(), name='orcamento'),
    path('<int:id>/paciente/<int:pk>/orcamento/', views.OrcamentoOrdem.as_view(), name='ordem_orcamento'),
    path('<int:ordem>/exames-selecionados/<int:pk>/', views.OrcamentoOrdem1.as_view(), name='exames_selecionados'),
    path('lista/', views.OrcamentoLista.as_view(), name='orcamento_lista'),
    path('add_orcamento-exames/', views.add_orcamento_exames, name='add_orcamento_exames'),
    path('pesquisar/', views.Buscaratendimento.as_view(), name='buscar_orcamento'),
    path('buscar/atendimento', views.buscar_atendimento, name='buscar_atendimento'),
    path('visualizar/<int:pk>/atendimento/', views.AtendimentoView.as_view(), name='ver_atendimento'),
    path('<int:pk>/<str:data>/visualizar/', views.AtendimentoView1.as_view(), name='ver_atendimento1'),
    path('relatorio/diario/', views.RelatorioDiario.as_view(), name='relatorio_diario'),
    path('relatorio/semanal/', views.RelatorioDSemanal.as_view(), name='relatorio_semanal'),
    path('relatorio/periodo/', views.RelatorioPeriodo.as_view(), name='relatorio_periodo'),
    path('ajax/buscar_exames/', views.buscar_exames, name='buscar_exames'),

]
