import json
from datetime import datetime
from datetime import date
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from .models import Plano, OrdemChegada
from .form import PlanoForm, OrdemChegadaForm, OrdemChegadaUpdateForm
from django.views.generic import CreateView, ListView, UpdateView, TemplateView, DeleteView

from ..core.models import Usuario
from ..exame.models import Exame


class PlanosAdd(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Plano
    form_class = PlanoForm
    success_message = 'Plano adicionado com sucesso!'
    template_name = 'agenda/novo_plano.html'

    def get_success_url(self):
        return reverse_lazy('exame:exame_detail', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):
        plano = form.save()
        exame = Exame.objects.get(pk=self.kwargs['pk'])
        exame.planos.add(plano)
        exame.save()
        return super().form_valid(form)


class PlanoUp(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Plano
    form_class = PlanoForm
    template_name = 'agenda/plano_up.html'
    success_message = 'Plano atualizado com sucesso!'

    def get_success_url(self):
        return reverse_lazy('exame:exame_detail', kwargs={'pk': self.object.exame.pk})


class PlanoDEL(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Plano
    success_message = 'Plano removido com sucesso!'

    def get_object(self, queryset=None):
       return Plano.objects.get(pk=self.kwargs['pk'])

    def get_success_url(self):
       plano = Plano.objects.get(pk=self.kwargs['pk'])
       exame = Exame.objects.get(planos=plano)
       return reverse_lazy('exame:exame_detail', kwargs={'pk': exame.pk})


class OrdemChegadaCalendario(LoginRequiredMixin, TemplateView):
    template_name = 'agenda/ordem_chegada_data.html'


class ChegadaADD(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = OrdemChegada
    form_class = OrdemChegadaForm
    template_name = 'agenda/ordem_chegada_add.html'
    success_message = 'Adicionada a fila'

    def get_success_url(self):
        return reverse_lazy('agenda:ordem_chegada_lista')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['paciente_pk'] = self.kwargs['pk']
        return kwargs

    def form_valid(self, form):
        ordem = form.save(commit=False)
        paciente = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        ordem.nome_paciente = paciente
        ordem.save()
        return super().form_valid(form)


class OrdemChegadaLista(LoginRequiredMixin, ListView):
    model = OrdemChegada
    template_name = 'agenda/ordem_chegada_lista.html'
    context_object_name = 'ordem_chegada'

    def get_queryset(self):
        return OrdemChegada.objects.filter(data=date.today())


class OrdemChegadaListaData(LoginRequiredMixin, TemplateView):
    template_name = 'agenda/ordem_chegada_lista.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        dia = self.request.GET.get("data")
        data = datetime.strptime(dia, '%Y-%m-%d')
        atendimentos = OrdemChegada.objects.filter(data=data)
        contexto['ordem_chegada'] = atendimentos
        return contexto


class OrdemChegadaUP(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = OrdemChegada
    form_class = OrdemChegadaUpdateForm
    template_name = 'agenda/ordem_chegada_up.html'
    success_message = 'Ordem de chegada alterada!'

    def get_success_url(self):
        return reverse_lazy('agenda:ordem_chegada_lista')


class BuscarOrdem(LoginRequiredMixin, TemplateView):
    template_name = 'agenda/buscar_agendamento.html'


def buscar_agendamento(request):
    if request.POST.get('ajax_request') == 'true':
        res = None
        nomes = request.POST.get('nomes')
        query_se = Usuario.objects.filter(nome__icontains=nomes)

        if len(query_se) > 0 and len(nomes) > 0:
            data = []
            for paciente in query_se:
                item = {
                    'pk': paciente.pk,
                    'nome': paciente.nome,
                    'cpf': paciente.cpf,
                }

                data.append(item)
            res = data
        else:
            res = 'Nenhum paciente encontrado'

        return JsonResponse({'data': res})
    return JsonResponse({})


def buscar_paciente(request):
    if request.POST.get('ajax_request') == 'true':
        res = None
        nomes = request.POST.get('nomes')
        query_se = Usuario.objects.filter(nome__icontains=nomes)

        if len(query_se) > 0 and len(nomes) > 0:
            data = []
            for paciente in query_se:
                item = {
                    'pk': paciente.pk,
                    'nome': paciente.nome,
                    'cpf': paciente.cpf,
                }

                data.append(item)
            res = data
        else:
            res = 'Nenhum paciente encontrado'

        return JsonResponse({'data': res})
    return JsonResponse({})


class AgendamentosEncontrados(LoginRequiredMixin, TemplateView):
    template_name = 'agenda/agendamentos_encontrados.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        paciente = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        agendamentos = OrdemChegada.objects.filter(nome_paciente=paciente)
        contexto['paciente'] = paciente
        contexto['agendamentos'] = agendamentos
        return contexto


class Buscarpaciente(LoginRequiredMixin, TemplateView):
    template_name = 'agenda/buscar_paciente.html'
