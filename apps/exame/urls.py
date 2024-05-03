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

    # area medica #
    #path('area/restrita/<int:pk>/atualizar/', views.ExameUpdateMedicView.as_view(), name='exame_medico_update'),
    #path('area/restrita/<int:pk>/visualizar/', views.ExameMedicView.as_view(), name='exame_medico_ver'),
    path('area/restrita/<int:pk>/realizar/', views.realizar_exame, name='exame_medico_ver'),

]
