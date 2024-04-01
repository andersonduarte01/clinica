from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.Home.as_view(), name='indice'),
    path('redirecionar/', views.custom_login_redirect, name='redirecione'),
    path('painel/cadastrar/novo/paciente/', views.Cadastrar.as_view(), name='add'),
    path('painel/<int:id>/endereco/', views.EnderecoCad.as_view(), name='endereco'),
    path('painel/administrativo/', views.Painel.as_view(), name='painel'),
    path('painel/lista/pacientes/', views.Pacientes.as_view(), name='pacientes'),
    path('buscar/atendimento/paciente/', views.BuscarAtendimentoPaciente.as_view(), name='buscar_paciente'),
    path('painel/paciente/<int:pk>/perfil/', views.MostrarPerfil.as_view(), name='perfil'),
    path('paciente/atualizar/<int:pk>/senha/', views.AtualizarSenha.as_view(), name='senha_up'),
    path('painel/atualizar/<int:pk>/paciente/', views.AtualizarPerfil.as_view(), name='atualizar_perfil'),
    path('painel/atualizar/<int:pk>/endereco/', views.AtualizarEndereco.as_view(), name='atualizar_endereco'),
    path('buscar/', views.buscar_atendimento_paciente, name='busca'),
    path('paciente/buscar/', views.buscar_paciente, name='busca_paciente'),
    path('opcoes/<int:pk>/paciente/', views.OpcoesPaciente.as_view(), name='opcoes_paciente'),
    path('opcoes/atendimento/paciente/', views.BuscarOpcoesPaciente.as_view(), name='buscar_opcoes_paciente'),

]
