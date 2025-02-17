from django.urls import path
from . import views

app_name = 'exame'

urlpatterns = [
    path('adicionar/novo/exame/', views.ExameAdd.as_view(), name='exame_add'),
    path('novo/atendimento/<int:pk>/adicionar/', views.ExameAtendimentoADD.as_view(), name='exame_atendimento_add'),
    path('<int:pk>/atualizar/', views.ExameUp.as_view(), name='exame_up'),
    path('atendimento/<int:pk>/atualizar/', views.ExameAtendimentoUp.as_view(), name='exame_atendimento_update'),
    path('deletar/<int:pk>/', views.ExameDel.as_view(), name='exame_del'),
    path('atendimento/<int:pk>/deletar/', views.ExameAtendimentoDel.as_view(), name='exame_atendimento_del'),
    path('lista/', views.ExamesLista.as_view(), name='exame_list'),
    path('<str:data>/lista/', views.ExamesListaData.as_view(), name='exame_list_data'),
    path('<str:data>/etiquetas/', views.ExamesEtiquetas.as_view(), name='exame_etiquetas'),
    path('aguardando/terceirizados/lista/', views.ExamesListaTerceirizado.as_view(), name='exame_list_terceirizado'),
    path('realizados/<str:data>/', views.ExamesListaDataRealizados.as_view(), name='exame_realizados_data'),
    path('<int:pk>/informacoes/', views.ExameDetalhes.as_view(), name='exame_detail'),
    path('nova/referencias/<int:pk>/', views.ReferenciaADD.as_view(), name='referencias_add'),
    path('referencia/<int:pk>/atualizar/', views.ReferenciaUp.as_view(), name='referencia_update'),
    path('<int:pk>/referencia/deletar/', views.ReferenciaDEL.as_view(), name='referencia_del'),
    path('novo/fator/<int:pk>/adicionar/', views.FatorReferenciaADD.as_view(), name='fator_add'),
    path('fator/atualizar/<int:pk>/', views.FatorUp.as_view(), name='fator_up'),
    path('remover/<int:pk>/fator/', views.FatorDEL.as_view(), name='fator_del'),
    path('novo/valor/<int:pk>/adicionar/', views.ValorEsperadoADD.as_view(), name='padrao_add'),
    path('valor/atualizar/<int:pk>/', views.ValorUp.as_view(), name='valor_up'),
    path('valor/remover/<int:pk>/', views.ValorDEL.as_view(), name='valor_del'),

    # temporario
    path('mostrar/todos/lista/', views.ExamesTodosLista.as_view(), name='exame_todos_lista'),
    path('<int:pk>/pdf/', views.criar_laudo_medico, name='pdf'),
    path('preencher/<int:pk>/folha/', views.preencher_laudo_medico, name='preencher_pdf'),
    path('preencher/grupo/folha/', views.preencher_laudo, name='laudo_pdf'),

    # area medica #
    path('area/restrita/<int:pk>/realizar/', views.realizar_exame, name='exame_medico_ver'),
    path('terceirizado/area/restrita/<int:pk>/anexar/', views.ExameTerceirizado.as_view(), name='exame_medico_anexar'),
    path('pesquisar/', views.BuscarExame.as_view(), name='pesquisar_exame'),
    path('terceirizado/pesquisar/', views.BuscarExameterceirizado.as_view(), name='pesquisar_exame_terceirizado'),
    path('buscar/exame/', views.buscar_exame, name='buscar_exame'),
    path('terceirizado/buscar/exame/', views.buscar_exame_terceirizado, name='buscar_exame_terceirizado'),
    path('imprimir/etiqueta/<int:pk>/', views.etiqueta_exame, name='etiqueta_exame'),
    path('etiquetas/impressas', views.etiquetas_de_exame, name='etiquetas'),
    #grupo
    path('add/grupo/', views.GrupoCreate.as_view(), name='add_grupo'),
    path('data/grupo/<str:data>/', views.ExamesGrupoData.as_view(), name='grupo_data'),
]
