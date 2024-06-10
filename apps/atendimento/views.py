from django.utils.datetime_safe import datetime
import json
from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core import serializers
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, TemplateView, FormView

from ..agenda.models import OrdemChegada
from ..atendimento.models import OrcamentoExames
from ..exame.models import *
from .forms import OrcamentoForm, OrcamentoFinanceiroForm
from ..exame.exame_create import objeto_exame
# Create your views here.


class Orcamento(LoginRequiredMixin, SuccessMessageMixin,  CreateView):
    model = OrcamentoExames
    form_class = OrcamentoForm
    template_name = 'atendimento/orcamento.html'
    success_message = 'Atendimento concluído'
    success_url = reverse_lazy('home:painel')

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        paciente = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        contexto['paciente'] = paciente
        return contexto

    def form_valid(self, form):
        orcamento = form.save(commit=False)
        paciente = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        orcamento.paciente = paciente
        with transaction.atomic():
            orcamento.save()
            exames_selecionados_ids = self.request.POST.getlist('exames')
            sequencia_selecionada = []
            planos_selecionados = self.request.POST.getlist('planos_selecionados')
            print(planos_selecionados)
            planos = [plano for plano in planos_selecionados if plano]
            numeros = []
            for plano in planos:
                numeros.extend(map(int, plano.split(',')))

            print(f'Numeros: {numeros}')

            for numero in numeros:
                sequencia_selecionada.append(numero)

            for numero in exames_selecionados_ids:
                id = int(numero)
                obj_exame = objeto_exame(pk=id, sequencia=numeros)
                orcamento.exame.add(obj_exame)

        orcamento.save()
        return super().form_valid(form)


class OrcamentoOrdem(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = OrcamentoExames
    form_class = OrcamentoForm
    template_name = 'atendimento/orcamento.html'
    success_message = 'Atendimento realizado'
    success_url = reverse_lazy('agenda:ordem_chegada_lista')

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        paciente = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        contexto['paciente'] = paciente
        return contexto

    def form_valid(self, form):
        orcamento = form.save(commit=False)
        paciente = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        ordem = get_object_or_404(OrdemChegada, id=self.kwargs['id'])
        orcamento.paciente = paciente

        with transaction.atomic():
            orcamento.save()
            exames_selecionados_ids = self.request.POST.getlist('exames')
            sequencia_selecionada = []
            planos_selecionados = self.request.POST.getlist('planos_selecionados')
            planos = [plano for plano in planos_selecionados if plano]
            numeros = []
            for plano in planos:
                numeros.extend(map(int, plano.split(',')))

            for numero in numeros:
                sequencia_selecionada.append(numero)

            for numero in exames_selecionados_ids:
                id = int(numero)
                obj_exame = objeto_exame(pk=id, sequencia=numeros)
                orcamento.exame.add(obj_exame)

            ordem.status_atendido = 'ATENDIDO'
            ordem.save()

        orcamento.save()
        return super().form_valid(form)


class OrcamentoLista(LoginRequiredMixin, ListView):
    model = OrcamentoExames
    template_name = 'atendimento/orcamento_lista.html'
    context_object_name = 'orcamentos'

    def get_queryset(self):
        return OrcamentoExames.objects.filter(data_cadastro=date.today())


class OrcamentoUpdate(LoginRequiredMixin, TemplateView):
    template_name = 'atendimento/atendimento_update.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        orcamento = get_object_or_404(OrcamentoExames, pk=self.kwargs['pk'])
        contexto['orcamento'] = orcamento
        return contexto


class OrcamentoFinanceiroUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = OrcamentoExames
    form_class = OrcamentoFinanceiroForm
    template_name = 'atendimento/orcamento_financeiro_up.html'
    success_message = 'Atendimento atualizado'

    def get_success_url(self):
        return reverse_lazy('atendimento:orcamento_update', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        orcamento = get_object_or_404(OrcamentoExames, pk=self.kwargs['pk'])
        contexto['orcamento'] = orcamento
        return contexto


class Buscaratendimento(LoginRequiredMixin, TemplateView):
    template_name = 'atendimento/buscar_atendimento.html'


def buscar_atendimento(request):
    if request.POST.get('ajax_request') == 'true':
        res = None
        nomes = request.POST.get('nomes')

        query_se = OrcamentoExames.objects.filter(paciente__nome__icontains=nomes)

        if query_se.exists() and nomes:
            data = []
            for orcamento in query_se:
                paciente_serialized = serializers.serialize('json', [orcamento.paciente, ])
                paciente_dict = json.loads(paciente_serialized)[0]['fields']
                item = {
                    'pk': orcamento.pk,
                    'paciente': paciente_dict['nome'],  # Supondo que 'nome' é um campo no modelo Usuario
                    'data': orcamento.data_cadastro.strftime("%d/%m/%Y"),
                }
                data.append(item)
            res = data
        else:
            res = 'Nenhum atendimento encontrado'

        return JsonResponse({'data': res})
    return JsonResponse({})


class AtendimentoView(LoginRequiredMixin, TemplateView):
    template_name = 'atendimento/ver_atendimento.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        orcamento = get_object_or_404(OrcamentoExames, pk=self.kwargs['pk'])
        contexto['orcamento'] = orcamento
        return contexto


class AtendimentoView1(LoginRequiredMixin, TemplateView):
    template_name = 'atendimento/ver_atendimento.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        paciente = Usuario.objects.get(pk=self.kwargs['pk'])
        orcamento = get_object_or_404(OrcamentoExames, paciente=paciente, data_cadastro=self.kwargs['data'])
        exame_realizado = OrcamentoExames.algum_exame_realizado(orcamento)
        contexto['orcamento'] = orcamento
        contexto['exame_realizado'] = exame_realizado
        return contexto


class RelatorioDiario(LoginRequiredMixin, ListView):
    model = OrcamentoExames
    template_name = 'atendimento/diario.html'
    context_object_name = 'atendimentos'
    paginate_by = 10

    def get_queryset(self):
        total, atendimentos = OrcamentoExames.calcular_total_por_data_e_pagamento(data_cadastro=date.today(), pagamento='PAGO')
        return atendimentos

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        total, atendimentos1 = OrcamentoExames.calcular_total_por_data_e_pagamento(data_cadastro=date.today(), pagamento='PAGO')
        contexto['total_atendimentos'] = self.get_queryset().count()
        contexto['total'] = total
        return contexto


class RelatorioDSemanal(LoginRequiredMixin, ListView):
    model = OrcamentoExames
    template_name = 'atendimento/semanal.html'
    context_object_name = 'atendimentos'
    paginate_by = 5

    def get_queryset(self):
        today = date.today()
        inicio_semana = today - timedelta(days=today.weekday())
        final_semana = inicio_semana + timedelta(days=6)
        total, atendimentos = OrcamentoExames.calcular_total_por_periodo(data_inicio=inicio_semana,
                                                                         data_fim=final_semana)
        return atendimentos.order_by('-data_cadastro')

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        today = date.today()
        inicio_semana = today - timedelta(days=today.weekday())
        final_semana = inicio_semana + timedelta(days=6)
        total, atendimentos = OrcamentoExames.calcular_total_por_periodo(data_inicio=inicio_semana,
                                                                         data_fim=final_semana)
        contexto['total'] = total
        contexto['total_atendimentos'] = self.get_queryset().count()
        contexto['inicio'] = inicio_semana
        contexto['final'] = final_semana
        return contexto


class RelatorioPeriodo(LoginRequiredMixin, ListView):
    model = OrcamentoExames
    template_name = 'atendimento/periodo.html'
    context_object_name = 'atendimentos'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("inicio")
        query1 = self.request.GET.get("final")

        if query and query1:
            data_inicio = datetime.strptime(query, "%Y-%m-%d").date()
            data_fim = datetime.strptime(query1, "%Y-%m-%d").date()

            if data_inicio > data_fim:
                return OrcamentoExames.objects.none()

            return OrcamentoExames.objects.filter(data_cadastro__range=(data_inicio, data_fim)).order_by('-data_cadastro')
        else:
            return OrcamentoExames.objects.none()

    def get_context_data(self, *, object_list=None, **kwargs):
        contexto = super().get_context_data(*kwargs)
        query = self.request.GET.get("inicio")
        query1 = self.request.GET.get("final")
        total = None
        data_inicio = None
        data_fim = None
        if query and query1:
            data_inicio = datetime.strptime(query, "%Y-%m-%d").date()
            data_fim = datetime.strptime(query1, "%Y-%m-%d").date()
            total, atendimentos = OrcamentoExames.calcular_total_por_periodo(data_inicio=data_inicio,
                                                                         data_fim=data_fim)
        contexto['inicio'] = data_inicio
        contexto['final'] = data_fim
        contexto['atendimentos_total'] = self.get_queryset().count()
        contexto['total'] = total
        return contexto
