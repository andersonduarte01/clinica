from django.utils.datetime_safe import datetime
import json
from datetime import date, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core import serializers
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, TemplateView, FormView

from ..agenda.models import OrdemChegada
from ..atendimento.models import OrcamentoExames
from ..exame.models import *
from .forms import OrcamentoForm, OrcamentoFinanceiroForm, OrcamentoForm1, AtualizarPagamentoForm
from ..exame.exame_create import objeto_exame
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


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


class OrcamentoOrdem1(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = OrcamentoExames
    form_class = OrcamentoForm1
    template_name = 'atendimento/orcamento_backup.html'
    success_message = 'Orçamento finalizado com sucesso!'
    success_url = reverse_lazy('agenda:ordem_chegada_lista')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        exames_selecionados = self.request.GET.get('exames', '').split(',')
        kwargs['exames_selecionados'] = [int(id) for id in exames_selecionados if id.isdigit()]
        return kwargs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        paciente = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        contexto['paciente'] = paciente

        # Captura os IDs dos exames selecionados
        exames_selecionados_ids = []
        if self.request.method == 'POST':
            exames_selecionados_ids = self.request.POST.getlist('exame')
            print(f'POST: {exames_selecionados_ids}')
        else:
            exames_ids_url = self.request.GET.get('exames', '')
            if exames_ids_url:
                exames_selecionados_ids = exames_ids_url.split(',')
                print(f'GET: {exames_ids_url}')

        contexto['exames_selecionados'] = exames_selecionados_ids
        return contexto

    def form_valid(self, form):
        print('FORMULARIO!!!!!!')
        paciente = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        ordem = get_object_or_404(OrdemChegada, id=self.kwargs['ordem'])

        # Cria uma instância do orçamento sem salvar
        orcamento = form.save(commit=False)
        orcamento.paciente = paciente

        with transaction.atomic():
            try:
                # Obter IDs dos exames selecionados
                exames_selecionados_ids = self.request.POST.getlist('exame')
                if not exames_selecionados_ids:
                    form.add_error(None, 'Nenhum exame selecionado.')
                    return self.form_invalid(form)

                # Salvar o orçamento antes de adicionar os exames
                orcamento.save()

                # Adicionar exames ao orçamento
                for id in exames_selecionados_ids:
                    if id:  # Verifica se id não está vazio
                        exame = get_object_or_404(Exame, id=int(id))
                        orcamento.exame.add(exame)

                # Atualizar o status da ordem
                ordem.status_atendido = 'ATENDIDO'
                ordem.save()

                # Calcular o total e salvar
                orcamento.valor_total = orcamento.calcular_total()
                orcamento.save()  # Salvar orçamento novamente para garantir que o valor total seja atualizado

                return super().form_valid(form)

            except Exception as e:
                print("Erro ao salvar o orçamento:", e)
                form.add_error(None, 'Erro ao salvar o orçamento. Tente novamente.')
                return self.form_invalid(form)

    def form_invalid(self, form):
        print("Formulário inválido:", form.errors)
        return super().form_invalid(form)

    def __init__(self, *args, **kwargs):
        exames_selecionados = kwargs.pop('exames_selecionados', None)
        super().__init__(*args, **kwargs)
        if exames_selecionados:
            self.fields['exame'].queryset = Exame.objects.filter(id__in=exames_selecionados)


def buscar_exames_planos(request):
    termo = request.GET.get('q', '')
    exames = Exame.objects.none()  # Exibe nada por padrão
    if termo:
        exames = Exame.objects.filter(nome__icontains=termo).prefetch_related('planos')

    resultados = []
    for exame in exames:
        planos = [{'id': plano.id, 'nome': plano.plano, 'preco': plano.preco} for plano in exame.planos.all()]
        resultados.append({'id': exame.id, 'nome': exame.nome, 'planos': planos})

    return JsonResponse(resultados, safe=False)


def add_orcamento_exames(request):
    term = request.GET.get('q', '')
    exames = Exame.objects.filter(nome__icontains=term, padrao=True)[:10]
    resultados = [{'id': exame.id, 'nome': exame.nome} for exame in exames]
    print(f'RESULTADOS: {resultados}')
    return JsonResponse(resultados, safe=False)


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


def buscar_exames(request):
    query = request.GET.get('q', '')
    exames = Exame.objects.filter(nome__icontains=query, padrao=True) if query else []
    exames_list = [{'id': exame.id, 'nome': exame.nome} for exame in exames]
    return JsonResponse({'exames': exames_list})


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


class AtualizarPagamento(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = OrcamentoExames
    form_class = AtualizarPagamentoForm
    template_name = 'atendimento/atualizar_pagamento.html'
    success_message = 'Status de pagamento atualizado!'

    def get_success_url(self):
        orcamento = get_object_or_404(OrcamentoExames, pk=self.kwargs['pk'])
        return reverse_lazy('atendimento:ver_atendimento1', kwargs={'pk': orcamento.paciente.pk, 'data': orcamento.data_cadastro})

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


class EtiquetasView1(LoginRequiredMixin, TemplateView):
    template_name = 'atendimento/ver_etiquetas.html'

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


def criar_comprovante1(request, pk, data, atendimento):
    att = get_object_or_404(OrdemChegada, id=atendimento)
    paciente = get_object_or_404(Usuario, pk=pk)
    data_obj = datetime.strptime(data, "%Y-%m-%d")
    data_formatada = data_obj.strftime("%d/%m/%Y")
    atendimento = get_object_or_404(OrcamentoExames, paciente=paciente, data_cadastro=data)
    exames = atendimento.exame.all()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{atendimento.paciente}.pdf"'


    largura_pagina, altura_pagina = A4
    largura_paralelogramo = 19 * 28.35
    altura_paralelogramo = 10 * 28.35
    margem_esquerda = (largura_pagina - largura_paralelogramo) / 2
    margem_superior = 18.5 * 28.35

    ponto1 = (margem_esquerda, margem_superior)
    ponto2 = (ponto1[0] + largura_paralelogramo, margem_superior)
    ponto3 = (largura_pagina - margem_esquerda, margem_superior + altura_paralelogramo)
    ponto4 = (ponto1[0], ponto1[1] + altura_paralelogramo)

    c = canvas.Canvas(response, pagesize=A4)
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(2)

    c.line(ponto1[0], ponto1[1], ponto2[0], ponto2[1])
    c.line(ponto2[0], ponto2[1], ponto3[0], ponto3[1])
    c.line(ponto3[0], ponto3[1], ponto4[0], ponto4[1])
    c.line(ponto4[0], ponto4[1], ponto1[0], ponto1[1])

    altura_linha_4cm = ponto3[1] - 1 * 28.35
    c.line(ponto1[0], altura_linha_4cm, ponto2[0], altura_linha_4cm)

    altura_linha_65cm = ponto3[1] - 3.3 * 28.35
    c.line(ponto1[0], altura_linha_65cm, ponto2[0], altura_linha_65cm)

    altura_linha_exames = ponto3[1] - 4 * 28.35
    c.line(ponto1[0], altura_linha_exames, ponto2[0], altura_linha_exames)

    altura_linha_7cm = ponto3[1] - 7.3 * 28.35
    c.line(ponto1[0], altura_linha_7cm, ponto2[0], altura_linha_7cm)

    altura_linha_100cm = ponto3[1] - 8 * 28.35
    c.line(ponto1[0], altura_linha_100cm, ponto2[0], altura_linha_100cm)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0, 0.5, 0)
    texto = "Gen's Diagnóstica"
    largura_texto = c.stringWidth(texto, "Helvetica-Bold", 10)
    posicao_horizontal = (ponto1[0] + ponto2[0] - largura_texto) / 2
    posicao_vertical = altura_linha_100cm - 0.55 * 28.35
    c.drawString(posicao_horizontal, posicao_vertical, texto)

    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0, 0.7, 0.3)
    texto_laboratorio = "Laboratório de análises clínicas"
    largura_texto_laboratorio = c.stringWidth(texto_laboratorio, "Helvetica", 7)
    posicao_horizontal_laboratorio = (ponto1[0] + ponto2[0] - largura_texto_laboratorio) / 2
    posicao_vertical -= 8
    c.drawString(posicao_horizontal_laboratorio, posicao_vertical, texto_laboratorio)

    endereco = "Rua Fortunato Silva, Nº164, Pedra Branca/CE"
    largura_endereco = c.stringWidth(endereco, "Helvetica", 7)
    posicao_horizontal_endereco = (ponto1[0] + ponto2[0] - largura_endereco) / 2
    posicao_vertical -= 8
    c.drawString(posicao_horizontal_endereco, posicao_vertical, endereco)

    telefone = "Tel: (88) 9 9995 0037 / 3515 1822"
    largura_telefone = c.stringWidth(telefone, "Helvetica", 7)
    posicao_horizontal_telefone = (ponto1[0] + ponto2[0] - largura_telefone) / 2
    posicao_vertical -= 8
    c.drawString(posicao_horizontal_telefone, posicao_vertical, telefone)

    site = "gensdiagnostica.com.br"
    largura_site = c.stringWidth(site, "Helvetica", 7)
    posicao_horizontal_site = (ponto1[0] + ponto2[0] - largura_site) / 2
    posicao_vertical -= 8
    c.drawString(posicao_horizontal_site, posicao_vertical, site)

    c.setFont("Helvetica-Bold", 18)
    texto_exame = 'Comprovante de Atendimento'
    largura_texto_exame = c.stringWidth(texto_exame, "Helvetica-Bold", 18)
    posicao_horizontal_exame = (ponto1[0] + ponto2[0] - largura_texto_exame) / 2
    posicao_vertical_exame = altura_linha_4cm + 8
    c.drawString(posicao_horizontal_exame, posicao_vertical_exame, texto_exame)

    c.setFont("Helvetica-Bold", 12)
    texto_exame = 'EXAMES'
    largura_texto_exame = c.stringWidth(texto_exame, "Helvetica-Bold", 12)
    posicao_horizontal_exame = (ponto1[0] + ponto2[0] - largura_texto_exame) / 2
    posicao_vertical_exame = altura_linha_65cm - 14
    c.drawString(posicao_horizontal_exame, posicao_vertical_exame, texto_exame)

    # Exames a serem realizados
    posicao_vertical_exames = altura_linha_exames - 5
    contador = 1
    for exame in exames:
        c.setFont("Helvetica-Bold", 9)
        texto_exame = f' {contador}. {exame}'
        posicao_horizontal_exame = ponto1[0] + 8
        posicao_vertical_exames -= 14
        c.drawString(posicao_horizontal_exame, posicao_vertical_exames, texto_exame)
        planos = exame.planos.all()
        for plano in planos:
            c.drawString(ponto1[0] + 485, posicao_vertical_exames, f'R$ {plano.preco}')
            contador += 1


    c.setFont("Helvetica-Bold", 9)
    texto_exame = f'Status: {atendimento.pagamento}'
    posicao_horizontal_exame = ponto1[0] + 8
    posicao_vertical_exame = altura_linha_7cm - 14
    c.drawString(posicao_horizontal_exame, posicao_vertical_exame, texto_exame)
    c.drawString(ponto1[0] + 486, posicao_vertical_exame, f'R$ {atendimento.calcular_total()}')

    c.setFont("Helvetica-Bold", 9)
    c.setFillColorRGB(0, 0.7, 0.3)
    c.drawString(ponto1[0] + 8, altura_linha_4cm - 15, f'Nome: {atendimento.paciente}')
    cpf_1 = atendimento.paciente.cpf if atendimento.paciente.cpf else 'Não cadastrado'
    c.drawString(ponto1[0] + 8, altura_linha_4cm - 35, f'CPF: {cpf_1}')
    c.drawString(ponto1[0] + 8, altura_linha_4cm - 55, f'Data de Nascimento: {atendimento.paciente.data_nascimento}')
    c.drawString(ponto1[0] + 370, altura_linha_4cm - 15, f'Sexo: {atendimento.paciente.sexo}')
    c.drawString(ponto1[0] + 370, altura_linha_4cm - 35, f'Data do atend: {data_formatada}')
    c.drawString(ponto1[0] + 370, altura_linha_4cm - 55, f'Nº atendimento: {att.sequencia}')

    c.save()
    return response

def criar_comprovante(request, pk, data, atendimento):
    att = get_object_or_404(OrdemChegada, id=atendimento)
    paciente = get_object_or_404(Usuario, pk=pk)
    data_obj = datetime.strptime(data, "%Y-%m-%d")
    data_formatada = data_obj.strftime("%d/%m/%Y")
    atendimento = get_object_or_404(OrcamentoExames, paciente=paciente, data_cadastro=data)
    exames = atendimento.exame.all()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{atendimento.paciente}.pdf"'


    largura_pagina, altura_pagina = A4
    largura_paralelogramo = 19 * 28.35
    altura_paralelogramo = 10 * 28.35
    margem_esquerda = (largura_pagina - largura_paralelogramo) / 2
    margem_superior = 18.5 * 28.35

    ponto1 = (margem_esquerda, margem_superior)
    ponto2 = (ponto1[0] + largura_paralelogramo, margem_superior)
    ponto3 = (largura_pagina - margem_esquerda, margem_superior + altura_paralelogramo)
    ponto4 = (ponto1[0], ponto1[1] + altura_paralelogramo)

    c = canvas.Canvas(response, pagesize=A4)
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(2)

    #c.line(ponto1[0], ponto1[1], ponto2[0], ponto2[1])
    #c.line(ponto2[0], ponto2[1], ponto3[0], ponto3[1])
    c.line(ponto3[0], ponto3[1], ponto4[0], ponto4[1])


    altura_linha_4cm = ponto3[1] - 1 * 28.35
    c.line(ponto1[0], altura_linha_4cm, ponto2[0], altura_linha_4cm)

    altura_linha_65cm = ponto3[1] - 3.3 * 28.35
    c.line(ponto1[0], altura_linha_65cm, ponto2[0], altura_linha_65cm)

    altura_linha_exames = ponto3[1] - 4 * 28.35
    c.line(ponto1[0], altura_linha_exames, ponto2[0], altura_linha_exames)
    #
    # altura_linha_7cm = ponto3[1] - 7.3 * 28.35
    # c.line(ponto1[0], altura_linha_7cm, ponto2[0], altura_linha_7cm)
    #
    # altura_linha_100cm = ponto3[1] - 8 * 28.35
    # c.line(ponto1[0], altura_linha_100cm, ponto2[0], altura_linha_100cm)


    c.setFillColorRGB(0, 0.7, 0.3)

    c.setFont("Helvetica-Bold", 18)
    texto_exame = 'Comprovante de Atendimento'
    largura_texto_exame = c.stringWidth(texto_exame, "Helvetica-Bold", 18)
    posicao_horizontal_exame = (ponto1[0] + ponto2[0] - largura_texto_exame) / 2
    posicao_vertical_exame = altura_linha_4cm + 8
    c.drawString(posicao_horizontal_exame, posicao_vertical_exame, texto_exame)

    c.setFont("Helvetica-Bold", 12)
    texto_exame = 'EXAMES'
    largura_texto_exame = c.stringWidth(texto_exame, "Helvetica-Bold", 12)
    posicao_horizontal_exame = (ponto1[0] + ponto2[0] - largura_texto_exame) / 2
    posicao_vertical_exame = altura_linha_65cm - 14
    c.drawString(posicao_horizontal_exame, posicao_vertical_exame, texto_exame)

    # Exames a serem realizados
    posicao_vertical_exames = altura_linha_exames - 5
    contador = 1
    for exame in exames:
        c.setFont("Helvetica-Bold", 9)
        texto_exame = f' {contador}. {exame}'
        posicao_horizontal_exame = ponto1[0] + 8
        posicao_vertical_exames -= 14
        c.drawString(posicao_horizontal_exame, posicao_vertical_exames, texto_exame)
        planos = exame.planos.all()
        for plano in planos:
            c.drawString(ponto1[0] + 485, posicao_vertical_exames, f'R$ {plano.preco}')
            contador += 1

    altura_linha_7cm = posicao_vertical_exames - 14
    c.line(ponto1[0], altura_linha_7cm, ponto2[0], altura_linha_7cm)

    altura_linha_100cm = altura_linha_7cm - (0.7 * 28.35)
    c.line(ponto1[0], altura_linha_100cm, ponto2[0], altura_linha_100cm)

    c.setFont("Helvetica-Bold", 9)
    texto_exame = f'Status: {atendimento.pagamento}'
    posicao_horizontal_exame = ponto1[0] + 8
    posicao_vertical_exame = altura_linha_7cm - 14
    c.drawString(posicao_horizontal_exame, posicao_vertical_exame, texto_exame)
    c.drawString(ponto1[0] + 486, posicao_vertical_exame, f'R$ {atendimento.calcular_total()}')

    c.setFont("Helvetica-Bold", 9)
    c.setFillColorRGB(0, 0.7, 0.3)
    c.drawString(ponto1[0] + 8, altura_linha_4cm - 15, f'Nome: {atendimento.paciente}')
    cpf_1 = atendimento.paciente.cpf if atendimento.paciente.cpf else 'Não cadastrado'
    c.drawString(ponto1[0] + 8, altura_linha_4cm - 35, f'CPF: {cpf_1}')
    c.drawString(ponto1[0] + 8, altura_linha_4cm - 55, f'Data de Nascimento: {atendimento.paciente.data_nascimento}')
    c.drawString(ponto1[0] + 370, altura_linha_4cm - 15, f'Sexo: {atendimento.paciente.sexo}')
    c.drawString(ponto1[0] + 370, altura_linha_4cm - 35, f'Data do atend: {data_formatada}')
    c.drawString(ponto1[0] + 370, altura_linha_4cm - 55, f'Nº atendimento: {att.sequencia}')

    # RODAPE

    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0, 0.5, 0)
    texto = "Gen's Diagnóstica"
    largura_texto = c.stringWidth(texto, "Helvetica-Bold", 10)
    posicao_horizontal = (ponto1[0] + ponto2[0] - largura_texto) / 2
    posicao_vertical = altura_linha_100cm - 0.55 * 28.35
    c.drawString(posicao_horizontal, posicao_vertical, texto)

    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0, 0.7, 0.3)

    texto_laboratorio = "Laboratório de análises clínicas"
    largura_texto_laboratorio = c.stringWidth(texto_laboratorio, "Helvetica", 7)
    posicao_horizontal_laboratorio = (ponto1[0] + ponto2[0] - largura_texto_laboratorio) / 2
    posicao_vertical -= 8
    c.drawString(posicao_horizontal_laboratorio, posicao_vertical, texto_laboratorio)

    endereco = "Rua Fortunato Silva, Nº164, Pedra Branca/CE"
    largura_endereco = c.stringWidth(endereco, "Helvetica", 7)
    posicao_horizontal_endereco = (ponto1[0] + ponto2[0] - largura_endereco) / 2
    posicao_vertical -= 8
    c.drawString(posicao_horizontal_endereco, posicao_vertical, endereco)

    telefone = "Tel: (88) 9 9995 0037 / 3515 1822"
    largura_telefone = c.stringWidth(telefone, "Helvetica", 7)
    posicao_horizontal_telefone = (ponto1[0] + ponto2[0] - largura_telefone) / 2
    posicao_vertical -= 8
    c.drawString(posicao_horizontal_telefone, posicao_vertical, telefone)

    site = "gensdiagnostica.com.br"
    largura_site = c.stringWidth(site, "Helvetica", 7)
    posicao_horizontal_site = (ponto1[0] + ponto2[0] - largura_site) / 2
    posicao_vertical -= 8
    c.drawString(posicao_horizontal_site, posicao_vertical, site)

    c.line(ponto1[0], posicao_vertical - 10, ponto2[0], posicao_vertical - 10)
    #c.line(ponto4[0], ponto4[1], ponto1[0], ponto1[1])
    c.save()

    return response

