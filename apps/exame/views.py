import json
import textwrap
from io import BytesIO
from urllib.parse import unquote

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from ..agenda.models import Plano
from ..atendimento.models import OrcamentoExames
from ..core.models import Usuario
from ..exame.exame_create import objeto_exame
from ..exame.forms import *
from ..exame.models import Exame, ReferenciaExame, FatoresReferencia, ValorEsperado, GrupoExame
from ..exame.relatorio import desenhar_retangulo, adicionar_linha_paralela, adicionar_linha_vertical, escrever_texto, \
    escrever_dados_clinica, escrever_exame_info, configurar_margens


class ExameAdd(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = ExameForm
    template_name = 'exame/exame_add.html'
    success_message = 'Exame cadastrado com sucesso!'

    def get_success_url(self):
        return reverse_lazy('exame:exame_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        exame = form.save(commit=False)
        exame.padrao = True
        exame.save()
        return super().form_valid(form)


class ExameAtendimentoADD(LoginRequiredMixin, SuccessMessageMixin,  CreateView):
    model = Exame
    form_class = ExameAtendimentoForm
    template_name = 'exame/exame_atendimento_add.html'
    success_message = 'Exame adicionado ao atendimento'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        orcamento = OrcamentoExames.objects.get(pk=self.kwargs['pk'])
        contexto['orcamento'] = orcamento
        return contexto

    def form_valid(self, form):
        # Execute sua lógica de salvar exame aqui
        orcamento = get_object_or_404(OrcamentoExames, pk=self.kwargs['pk'])
        with transaction.atomic():
            exames_selecionados_ids = self.request.POST.getlist('exames')
            planos_selecionados = self.request.POST.getlist('planos_selecionados')
            planos = [plano for plano in planos_selecionados if plano]
            numeros = []
            for plano in planos:
                numeros.extend(map(int, plano.split(',')))

            print(f'Numeros: {numeros}')

            for numero in exames_selecionados_ids:
                id = int(numero)
                obj_exame = objeto_exame(pk=id, sequencia=numeros)
                orcamento.exame.add(obj_exame)
            orcamento.valor_total = orcamento.calcular_total()
            orcamento.save()

        messages.success(self.request, self.success_message)
        url = reverse_lazy('atendimento:orcamento_update', kwargs={'pk': orcamento.pk})
        return HttpResponseRedirect(url)


class ExamesLista(LoginRequiredMixin, ListView):
    model = Exame
    template_name = 'exame/exames_lista.html'
    context_object_name = 'exames'

    def get_queryset(self):
        return Exame.objects.filter(ativo=True, padrao=True).order_by('nome')


class ExamesListaData(LoginRequiredMixin, ListView):
    model = Exame
    template_name = 'exame/exames_lista_data.html'
    context_object_name = 'exames'

    def get_queryset(self):
        data = self.kwargs['data']
        return Exame.objects.filter(data_cadastro__date=data, status_exame='AGUARDANDO', padrao=False, terceirizado=False)

    def get_context_data(self, *, object_list=None, **kwargs):
        contexto = super().get_context_data(**kwargs)
        data = self.kwargs['data']
        contexto['terceirizados'] = Exame.objects.filter(data_cadastro__date=data, status_exame='AGUARDANDO', padrao=False, terceirizado=True)
        return contexto


class ExamesEtiquetas(LoginRequiredMixin, ListView):
    model = Exame
    template_name = 'exame/exames_etiquetas.html'
    context_object_name = 'exames'

    def get_queryset(self):
        data = self.kwargs['data']
        return Exame.objects.filter(data_cadastro__date=data, status_exame='AGUARDANDO', padrao=False)

    def get_context_data(self, *, object_list=None, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['data'] = self.kwargs['data']
        return contexto


class ExamesGrupoData(LoginRequiredMixin, ListView):
    model = Exame
    template_name = 'exame/exames_grupo_data.html'
    context_object_name = 'exames'

    def get_queryset(self):
        data = self.kwargs['data']
        return Exame.objects.filter(data_cadastro__date=data, status_exame='AGUARDANDO', padrao=False, terceirizado=False)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        exames = self.get_queryset()
        grupos = GrupoExame.objects.all()

        grupos_exames = {}  # Dicionário para armazenar {grupo: ids_dos_exames}

        for grupo in grupos:
            exames_do_grupo = grupo.exames.all()
            exames_ids = [exame.id for exame in exames if exame.nome in exames_do_grupo.values_list('nome', flat=True)]

            if exames_ids:
                grupos_exames[grupo.nome] = exames_ids  # Apenas os IDs dos exames

        exames_sem_grupo = []
        for exame in exames:
            # Verifica se o nome do exame não pertence a nenhum grupo
            pertence_a_grupo = False
            for grupo in grupos:
                exames_do_grupo = grupo.exames.all()
                if exame.nome in exames_do_grupo.values_list('nome', flat=True):
                    pertence_a_grupo = True
                    break
            if not pertence_a_grupo:
                exames_sem_grupo.append(exame.id)

        # Adiciona os exames sem grupo ao dicionário
        if exames_sem_grupo:
            grupos_exames['Sem Grupo'] = exames_sem_grupo

        contexto['grupos'] = grupos_exames  # Passa apenas os IDs para o template
        return contexto


class ExamesListaTerceirizado(LoginRequiredMixin, ListView):
    model = Exame
    template_name = 'exame/exames_lista_terceirizado.html'
    context_object_name = 'exames'

    def get_queryset(self):
        return Exame.objects.filter(status_exame='AGUARDANDO', padrao=False, terceirizado=True)


class ExamesListaDataRealizados(LoginRequiredMixin, ListView):
    model = Exame
    template_name = 'exame/exames_realizados_data.html'
    context_object_name = 'exames'

    def get_queryset(self):
        data = self.kwargs['data']
        return Exame.objects.filter(data_cadastro__date=data, status_exame='REALIZADO')


class ExameUp(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Exame
    form_class = ExameForm
    template_name = 'exame/exame_up.html'
    success_message = 'Exame atualizado com sucesso!'

    def get_success_url(self):
        return reverse_lazy('exame:exame_detail', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        exame = Exame.objects.get(pk=self.kwargs['pk'])
        contexto['exame'] = exame
        return contexto


class ExameAtendimentoUp(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Exame
    fields = ()
    template_name = 'exame/exame_atendimento_up.html'
    success_message = 'Exame atualizado com sucesso!'

    def get_success_url(self):
        exame = self.get_object()
        orcamento = OrcamentoExames.objects.filter(exame=exame).first()
        return reverse_lazy('atendimento:orcamento_update', kwargs={'pk': orcamento.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exame = self.get_object()
        orcamento = OrcamentoExames.objects.filter(exame=exame).first()
        exame1 = ''
        exames = Exame.objects.filter(ativo=True, padrao=True)
        for exam in exames:
            if exam.nome == exame.nome:
                exame1 = exam

        context['exame'] = exame1
        context['orcamento'] = orcamento
        return context

    def form_valid(self, form):
        exame = form.save(commit=False)
        plano_selecionado_id = self.request.POST.get('plano_selecionado')
        plano = Plano.objects.get(pk=plano_selecionado_id)
        plano_create = Plano.objects.create(
            plano=plano.plano,
            preco=plano.preco,
            habilitado=True
        )
        plano1 = exame.planos.first()
        plano1.delete()

        exame.planos.add(plano_create)
        orcamento = OrcamentoExames.objects.filter(exame=exame).first()
        orcamento.valor_total = orcamento.calcular_total()
        orcamento.save()
        return super().form_valid(form)


class ExameDetalhes(LoginRequiredMixin, DetailView):
    model = Exame
    template_name = 'exame/exame_detalhes.html'
    context_object_name = 'exame'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        exame = Exame.objects.get(pk=self.kwargs['pk'], ativo=True)
        contexto['exame'] = exame
        return contexto


class ExameDel(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Exame
    success_message = 'Exame padrão removido com sucesso.'

    def get_object(self, queryset=None):
        return Exame.objects.get(pk=self.kwargs['pk'])

    def get_success_url(self):
        return reverse_lazy('exame:exame_list')


class ExameAtendimentoDel(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Exame
    success_message = 'Exame removido com sucesso.'

    def get_success_url(self):
        exame = self.get_object()
        orcamento = OrcamentoExames.objects.filter(exame=exame).first()
        return reverse_lazy('atendimento:orcamento_update', kwargs={'pk': orcamento.pk})

    def form_valid(self, form):
        exame = self.get_object()
        orcamento = OrcamentoExames.objects.filter(exame=exame).first()
        try:
            plano = exame.planos.first()
            plano.delete()
        except:
            print('Erro ao excluir plano associado ao exame.')

        response = super().form_valid(form)

        orcamento.valor_total = orcamento.calcular_total()
        orcamento.save()

        return response


class ReferenciaADD(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = ReferenciaForm
    success_message = 'Referência adicionada com sucesso!'
    template_name = 'exame/novas_referencias.html'

    def get_success_url(self):
        return reverse_lazy('exame:exame_detail', kwargs={'pk': self.kwargs['pk']})
    
    def form_valid(self, form):
        referecia = form.save(commit=False)
        exame = Exame.objects.get(pk=self.kwargs['pk'])
        referecia.exame = exame
        referecia.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        exame = Exame.objects.get(pk=self.kwargs['pk'])
        contexto['exame'] = exame
        return contexto


class ReferenciaUp(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ReferenciaExame
    form_class = ReferenciaForm
    template_name = 'exame/referencia_up.html'
    success_message = 'Referência atualizada com sucesso!'

    def get_success_url(self):
        referencia = ReferenciaExame.objects.get(pk=self.kwargs['pk'])
        return reverse_lazy('exame:exame_detail', kwargs={'pk': referencia.exame.pk})

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        referencia = ReferenciaExame.objects.get(pk=self.kwargs['pk'])
        exame = Exame.objects.get(pk=referencia.exame.pk)
        contexto['exame'] = exame
        contexto['referencia'] = referencia
        return contexto


class ReferenciaDEL(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = ReferenciaExame
    success_message = 'Referência removida com sucesso!'

    def get_object(self, queryset=None):
       return ReferenciaExame.objects.get(pk=self.kwargs['pk'])

    def get_success_url(self):
       referencia = ReferenciaExame.objects.get(pk=self.kwargs['pk'])
       return reverse_lazy('exame:exame_detail', kwargs={'pk': referencia.exame.pk})


class FatorReferenciaADD(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = FatoresReferencia
    form_class = FatorReferenciaForm
    template_name = 'exame/fator_add.html'
    success_message = 'Fator adicionado com sucesso!'

    def get_success_url(self):
        return reverse_lazy('exame:referencia_update', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):
        fator1 = form.save(commit=False)
        referencia = ReferenciaExame.objects.get(pk=self.kwargs['pk'])
        referencia.limite_inferior = None
        referencia.limite_superior = None
        referencia.fator = True
        referencia.save()
        fator1.referencia_exame = referencia
        fator1.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        referencia = ReferenciaExame.objects.get(pk=self.kwargs['pk'])
        exame = referencia.exame
        contexto['exame'] = exame
        return contexto


class FatorUp(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = FatoresReferencia
    form_class = FatorReferenciaForm
    template_name = 'exame/fator_up.html'
    success_message = 'Fator atualizado com sucesso!'

    def get_success_url(self):
        fator = FatoresReferencia.objects.get(pk=self.kwargs['pk'])
        return reverse_lazy('exame:referencia_update', kwargs={'pk': fator.referencia_exame.pk})

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        fator = FatoresReferencia.objects.get(pk=self.kwargs['pk'])
        exame = Exame.objects.get(pk=fator.referencia_exame.exame.pk)
        contexto['exame'] = exame
        contexto['fator'] = fator
        return contexto


class FatorDEL(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = FatoresReferencia
    success_message = 'Fator removido com sucesso!'

    def get_object(self, queryset=None):
       return FatoresReferencia.objects.get(pk=self.kwargs['pk'])

    def get_success_url(self):
       referencia = FatoresReferencia.objects.get(pk=self.kwargs['pk'])
       return reverse_lazy('exame:referencia_update', kwargs={'pk': referencia.referencia_exame.pk})

    def form_valid(self, form):
        success_url = super().form_valid(form)
        referencia_exame_pk = self.object.referencia_exame.pk
        fatores = FatoresReferencia.objects.filter(referencia_exame=referencia_exame_pk).count()
        if fatores == 0:
            ref = ReferenciaExame.objects.get(pk=self.object.referencia_exame.pk)
            ref.fator = False
            ref.save(force_update=True)

        return success_url


class ValorEsperadoADD(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ValorEsperado
    form_class = ValorEsperadoForm
    template_name = 'exame/padrao_add.html'
    success_message = 'Valor único adicionado com sucesso!'

    def get_success_url(self):
        return reverse_lazy('exame:referencia_update', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):
        valor = form.save(commit=False)
        referencia = ReferenciaExame.objects.get(pk=self.kwargs['pk'])
        referencia.limite_inferior = None
        referencia.limite_superior = None
        referencia.esperado = True
        referencia.save()
        valor.referencia = referencia
        valor.save()
        return super().form_valid(form)


class ValorUp(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ValorEsperado
    form_class = ValorEsperadoForm
    template_name = 'exame/valor_up.html'
    success_message = 'Valor atualizado com sucesso!'

    def get_success_url(self):
        fator = self.object.referencia.pk
        return reverse_lazy('exame:referencia_update', kwargs={'pk': fator})

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        valor = ValorEsperado.objects.get(pk=self.kwargs['pk'])
        exame = Exame.objects.get(pk=valor.referencia.exame.pk)
        contexto['exame'] = exame
        contexto['valor'] = valor
        return contexto


class ValorDEL(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = ValorEsperado
    success_message = 'Valor removido com sucesso!'

    def get_object(self, queryset=None):
       return ValorEsperado.objects.get(pk=self.kwargs['pk'])

    def get_success_url(self):
       valor = self.object.referencia.pk
       return reverse_lazy('exame:referencia_update', kwargs={'pk': valor})

    def form_valid(self, form):
        success_url = super().form_valid(form)
        valor_exame_pk = self.object.referencia.pk
        valores = ValorEsperado.objects.filter(referencia=valor_exame_pk).count()
        if valores == 0:
            ref = ReferenciaExame.objects.get(pk=self.object.referencia.pk)
            ref.esperado = False
            ref.save(force_update=True)

        return success_url


# temporario
class ExamesTodosLista(LoginRequiredMixin, ListView):
    model = Exame
    template_name = 'exame/exames_todos_lista.html'
    context_object_name = 'exames'
    paginate_by = 8

    def get_queryset(self):
        return Exame.objects.filter(ativo=True, padrao=False).order_by('-data_cadastro')


# Area Medica

class ExameUpdateMedicView(LoginRequiredMixin, UpdateView):
    model = Exame
    fields = ['medico', 'comentario']
    template_name = 'exame/exame_area_medica_update.html'
    success_url = reverse_lazy('exame:exame_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exame = self.get_object()

        # Inline formsets
        ReferenciaFormSet = inlineformset_factory(Exame, ReferenciaExame, fields=(
        'nome_referencia', 'limite_inferior', 'limite_superior', 'valor_obtido', 'fator', 'esperado'), extra=1)
        FatoresFormSet = inlineformset_factory(ReferenciaExame, FatoresReferencia,
                                               fields=('nome_fator', 'idade', 'limite_inferior', 'limite_superior'),
                                               extra=1)
        ValorFormSet = inlineformset_factory(ReferenciaExame, ValorEsperado, fields=('tipo_valor', 'valor_esperado'),
                                             extra=1)

        # Passar os formsets para o contexto
        context['referencia_formset'] = ReferenciaFormSet(instance=exame)
        context['fatores_formsets'] = [FatoresFormSet(instance=referencia) for referencia in exame.referencias.all()]
        context['valor_formsets'] = [ValorFormSet(instance=referencia) for referencia in exame.referencias.all()]

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        referencia_formset = context['referencia_formset']
        fatores_formsets = context['fatores_formsets']
        valor_formsets = context['valor_formsets']

        if referencia_formset.is_valid():
            referencia_formset.save()

            for fatores_formset in fatores_formsets:
                if fatores_formset.is_valid():
                    fatores_formset.save()

            for valor_formset in valor_formsets:
                if valor_formset.is_valid():
                    valor_formset.save()

        return super().form_valid(form)


class ExameMedicView(LoginRequiredMixin, TemplateView):
    model = Exame
    template_name = 'exame/exame_area_medica_ver.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exame = get_object_or_404(Exame, pk=self.kwargs['pk'])
        context['exame'] = exame
        return context

@login_required
def finalizar_exame(request, pk):
    exame = get_object_or_404(Exame, pk=pk)

    if request.method == "POST":
        comentario = request.POST.get("comentario")
        if comentario is not None:
            exame.comentario = comentario

        bio_medico = Usuario.objects.get(usuario=request.user)
        exame.bio_medico = bio_medico
        exame.status_exame = 'REALIZADO'  # ajuste o valor conforme o seu `choices`
        exame.save()
        return redirect('home:painel')


class ExameDetailView(DetailView):
    model = Exame
    template_name = 'exame/referencias_list.html'
    context_object_name = 'exame'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Passando as referências diretamente para o template
        context['referencias'] = self.object.referencias.all()
        context['orcamento'] = OrcamentoExames.objects.filter(exame=self.object).first()
        return context


def salvar_referencia(request, pk):
    referencia = get_object_or_404(ReferenciaExame, pk=pk)

    if request.method == "POST":
        # Salvar valor direto na ReferenciaExame
        valor = request.POST.get('valor_obtido')
        print(f'Valor:{valor}')
        if valor is not None:
            referencia.valor_obtido = valor
            referencia.save()

        # Salvar valores esperados (padrao)
        for esperado in referencia.padrao.all():
            novo_valor = request.POST.get(f"esperado_{esperado.id}")
            if novo_valor is not None:
                esperado.esperado_obtido = novo_valor
                esperado.save()

    url = reverse('exame:exame_medico_ver', args=[referencia.exame.id])
    return HttpResponseRedirect(f"{url}#referencia{referencia.id}")


class ExameTerceirizado(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Exame
    form_class = ExameMedicTerceirizado
    success_message = 'Exame anexado com sucesso!'
    template_name = 'exame/editar_exame_terceirizado.html'
    success_url = reverse_lazy('home:painel')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exame = get_object_or_404(Exame, pk=self.kwargs['pk'])
        orcamento = OrcamentoExames.objects.filter(exame=exame).first()
        context['orcamento'] = orcamento
        return context


def criar_laudo_medico(request, pk):
    exame = get_object_or_404(Exame, pk=pk)

    if exame.nome == "HEMOGRAMA COMPLETO":
        atendimento = OrcamentoExames.objects.filter(exame=exame).first()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{atendimento.paciente}.pdf"'

        c = canvas.Canvas(response, pagesize=A4)

        ponto1, ponto2, ponto3, ponto4 = desenhar_retangulo(c=c)


        #linhas paralelas
        altura = adicionar_linha_paralela(c, ponto3, ponto4, intervalo=85.05)
        altura1 = adicionar_linha_paralela(c, ponto3, ponto4, intervalo=156)

        #linhas verticais
        linha = adicionar_linha_vertical(c, ponto1, ponto3, altura=85.05, largura_intervalo=141.75)
        linha_vertical = adicionar_linha_vertical(c, ponto1, ponto3, altura=85.05, largura_intervalo=14 * 28.35)

        # Desenhar a linha horizontal paralela à linha de 3cm e entre as linhas verticais de 14cm e 5cm
        largura_linha_horizontal_15cm = ponto1[0] + 1 * 28.35  # Largura da linha a 15cm da linha vertical à esquerda em pontos
        c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
        c.line(ponto2[0], altura + 1.5 * 28.35, linha_vertical,
               altura + 1.5 * 28.35)


        # Escrever o texto "Nome Gen's Diagnóstica" em negrito e cor verde
        texto = "Gen's Diagnóstica"
        largura_texto = c.stringWidth(texto, "Helvetica-Bold", 14)  # Obter a largura do texto em pontos

        escrever_texto(c, texto=texto,
                       x=((linha - 40 + linha_vertical - largura_texto) / 2),
                       y=(altura + 2.25 * 28.35), font="Helvetica-Bold", font_size=18,
                       color=(0, 0.5, 0))

        c.setFont("Helvetica", 9)
        texto_laboratorio = "Laboratório de análises clínicas"
        largura_texto_laboratorio = c.stringWidth(texto_laboratorio)  # Obter a largura do texto em pontos

        escrever_texto(c, texto=texto_laboratorio,
                       x=((linha + linha_vertical - largura_texto_laboratorio) / 2),
                       y=(altura + 1.5 * 28.35 + 10), font_size=9,
                       color=(0, 0.7, 0.3))

        endereco = "Rua Fortunato Silva, Nº164, Pedra Branca/CE"
        largura_endereco = c.stringWidth(endereco)

        escrever_texto(c, texto=endereco,
                       x=((linha - 16 + linha_vertical - largura_endereco) / 2),
                       y=(altura + 1.5 * 28.35 - 3), font_size=10,
                       color=(0, 0, 0))

        telefone = "Tel: (88) 9 9995 0037 / 3515 1822"
        largura_telefone = c.stringWidth(telefone)

        escrever_texto(c, texto=telefone,
                       x=((linha - 5 + linha_vertical - largura_telefone) / 2),
                       y=(altura + 1.5 * 28.35 - 18), font_size=10,
                       color=(0, 0, 0))

        site = "gensdiagnostica.com.br"
        largura_site = c.stringWidth(site)

        escrever_texto(c, texto=site,
                       x=((linha - 5 + linha_vertical - largura_site) / 2),
                       y=(altura + 1.5 * 28.35 - 33), font_size=10,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Nº {exame.codigo}',
                       x=(linha_vertical + 5),
                       y=(altura + 57), font_size=11,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Emissão: {exame.data_alterado.strftime("%d/%m/%Y")}',
                       x=linha_vertical + 5,
                       y=(altura + 18), font_size=11,
                       color=(0, 0, 0))



        # Escrever o nome 'CPF'
        cpf_1 = 'Não cadastrado'
        if atendimento.paciente.cpf:
            cpf_1 = atendimento.paciente.cpf

        escrever_texto(c,texto=f'CPF: {cpf_1}',
                       x=ponto1[0] + 5,
                       y=(altura1 + 35), font_size=10,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Material: {exame.material}',
                       x=ponto1[0] + 5,
                       y=(altura1 + 15), font_size=10,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Data de Nascimento: {atendimento.paciente.data_nascimento}',
                       x=ponto1[0] + 370,
                       y=(altura1 + 55), font_size=10,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Nome: {atendimento.paciente}',
                       x=ponto1[0] + 5,
                       y=(altura1 + 55), font_size=10,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Número do exame: {exame.codigo}',
                       x=ponto1[0] + 370,
                       y=(altura1 + 35), font_size=10,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Método: {exame.metodo}',
                       x=ponto1[0] + 370,
                       y=(altura1 + 15), font_size=10,
                       color=(0, 0, 0))

        # Adicionar a imagem entre as linhas horizontais superior e de 3cm
        imagem = "https://gensdiagnostica.com.br/static/img/gens.png"  # Caminho para a imagem
        largura_imagem = 140  # Largura da imagem em pontos
        altura_imagem = 80  # Altura da imagem em pontos
        c.drawImage(imagem, ponto1[0] + 1, altura + 1, width=largura_imagem, height=altura_imagem)

        distancia = altura1

        escrever_texto(c, texto=f'{exame.nome}',
                       x=ponto1[0] + 5,
                       y=(altura1 - 15), font_size=10,
                       color=(0, 0, 0))

        distancia -= 15

        referencias = exame.referencias.all()
        serie_vermelha = referencias[:8]
        leucocitos = referencias[8:9]
        serie_branca = referencias[9:20]
        outros = referencias[20:]

        escrever_texto(c, texto=f'ERITROGRAMA',
                       x=ponto1[0] + 5,
                       y=(distancia - 20), font_size=9,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'VALORES DE REFERÊNCIA',
                       x=ponto1[0] + 270,
                       y=(distancia - 20), font_size=9,
                       color=(0, 0, 0))

        distancia -= 20

        # Calcula o maior tamanho entre os nomes de referência
        maior_tamanho = max(len(ref.nome_referencia) for ref in serie_vermelha)

        for referencia_vermelha in serie_vermelha:
            if not referencia_vermelha.fator and not referencia_vermelha.esperado:
                nome = referencia_vermelha.nome_referencia
                fator = referencia_vermelha.valor_obtido
                max_min = f'{referencia_vermelha.limite_inferior} a {referencia_vermelha.limite_superior}'
                # Preenche com pontos até o maior tamanho e adiciona os dois-pontos
                nome_formatado = nome.ljust(maior_tamanho, '.') + ': ' + fator

                escrever_texto(c, texto=nome_formatado,
                               x=ponto1[0] + 5,
                               y=(distancia - 13), font_size=8,
                               color=(0, 0, 0), font= "Courier")

                escrever_texto(c, texto=max_min,
                               x=ponto1[0] + 270,
                               y=(distancia - 13), font_size=8,
                               color=(0, 0, 0), font= "Courier")

                distancia -= 13

            elif referencia_vermelha.fator and not referencia_vermelha.esperado:
                nome = referencia_vermelha.nome_referencia
                fator = referencia_vermelha.valor_obtido

                fatores = referencia_vermelha.fatores.all()
                max_min = ''
                for fat in fatores:
                    max_min += f'{fat.nome_fator}: {fat.limite_inferior} a {fat.limite_superior} | '
                # Preenche com pontos até o maior tamanho e adiciona os dois-pontos

                nome_formatado = nome.ljust(maior_tamanho, '.') + ': ' + fator

                escrever_texto(c, texto=nome_formatado,
                               x=ponto1[0] + 5,
                               y=(distancia - 13), font_size=8,
                               color=(0, 0, 0), font="Courier")

                escrever_texto(c, texto=max_min[:-2],
                               x=ponto1[0] + 270,
                               y=(distancia - 13), font_size=7,
                               color=(0, 0, 0), font="Courier")

                distancia -= 13


        escrever_texto(c, texto=f'Observações: ',
                       x=ponto1[0] + 5,
                       y=(distancia - 13), font_size=7,
                       color=(0, 0, 0), font="Courier")

        distancia -= 25

        escrever_texto(c, texto=f'{leucocitos[0].nome_referencia} totais.: {leucocitos[0].valor_obtido}',
                       x=ponto1[0] + 5,
                       y=(distancia - 13), font_size=8,
                       color=(0, 0, 0), font="Courier")

        escrever_texto(c, texto=f'{leucocitos[0].limite_inferior} a {leucocitos[0].limite_superior}',
                       x=ponto1[0] + 270,
                       y=(distancia - 13), font_size=7,
                       color=(0, 0, 0), font="Courier")

        distancia -= 25

        escrever_texto(c, texto=f'',
                       x=ponto1[0] + 5,
                       y=(distancia - 15), font_size=9,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'VALORES DE REFERÊNCIA',
                       x=ponto1[0] + 270,
                       y=(distancia - 15), font_size=9,
                       color=(0, 0, 0))

        distancia -= 18

        # Calcula o maior tamanho entre os nomes de referência
        maior_tamanho = max(len(ref.nome_referencia) for ref in serie_branca)
        maior_tamanho_fator = 0
        for referencia in serie_branca:
            for fator in referencia.fatores.all():
                if len(fator.nome_fator) > maior_tamanho_fator:
                    maior_tamanho_fator = len(fator.nome_fator)

        for referencia_branca in serie_branca:
            nome = referencia_branca.nome_referencia
            esperados_ref1 = 270
            esperados_valor = ''
            if not referencia_branca.fator and referencia_branca.esperado:
                esperados = referencia_branca.padrao.all()
                for espere in esperados:
                    escrever_texto(c, texto=f'{espere.tipo_valor}: {espere.valor_esperado}',
                                   x=ponto1[0] + esperados_ref1,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")
                    esperados_valor += f'{espere.esperado_obtido}             '
                    esperados_ref1 += 110
            # Preenche com pontos até o maior tamanho e adiciona os dois-pontos
                nome_formatado = nome.ljust(maior_tamanho, '.') + ': ' + esperados_valor[:-5]

                escrever_texto(c, texto=nome_formatado,
                               x=ponto1[0] + 5,
                               y=(distancia - 13), font_size=8,
                               color=(0, 0, 0), font="Courier")

            elif referencia_branca.fator and referencia_branca.esperado:
                fatores = referencia_branca.fatores.all()
                esperados = referencia_branca.padrao.all()
                esperados_ref = ''
                for espere in esperados:
                    esperados_ref += f'{espere.tipo_valor}: {espere.valor_esperado}'
                    esperados_valor += f'{espere.esperado_obtido}'

                max_min = ''
                for fat in fatores:
                    max_min += f'{fat.nome_fator}: {fat.limite_inferior} a {fat.limite_superior}'
            # Preenche com pontos até o maior tamanho e adiciona os dois-pontos
                nome_formatado = nome.ljust(maior_tamanho, '.') + ': ' + referencia_branca.valor_obtido

                escrever_texto(c, texto=nome_formatado,
                               x=ponto1[0] + 5,
                               y=(distancia - 13), font_size=8,
                               color=(0, 0, 0), font="Courier")

                escrever_texto(c, texto=esperados_valor,
                               x=ponto1[0] + 150,
                               y=(distancia - 13), font_size=8,
                               color=(0, 0, 0), font="Courier")


                escrever_texto(c, texto=f'{max_min}',
                               x=ponto1[0] + 270,
                               y=(distancia - 13), font_size=7,
                               color=(0, 0, 0), font="Courier")

                escrever_texto(c, texto=f'{esperados_ref}',
                               x=ponto1[0] +380,
                               y=(distancia - 13), font_size=7,
                               color=(0, 0, 0), font="Courier")

            distancia -= 13

        escrever_texto(c, texto=f'Observações: ',
                       x=ponto1[0] + 5,
                       y=(distancia - 13), font_size=7,
                       color=(0, 0, 0), font="Courier")

        distancia -= 30

        maior_tamanho = max(len(ref.nome_referencia) for ref in outros)
        for outro in outros:
            nome = outro.nome_referencia
            # Preenche com pontos até o maior tamanho e adiciona os dois-pontos
            nome_formatado = nome.ljust(maior_tamanho, '.') + ': ' + outro.valor_obtido

            escrever_texto(c, texto=nome_formatado,
                           x=ponto1[0] + 5,
                           y=(distancia - 13), font_size=8,
                           color=(0, 0, 0), font="Courier")

            escrever_texto(c, texto=f'{outro.limite_inferior} a {outro.limite_superior}',
                           x=ponto1[0] + 270,
                           y=(distancia - 13), font_size=7,
                           color=(0, 0, 0), font="Courier")

            distancia -= 13

        distancia -= 10

        escrever_texto(c, texto=f'Observações:',
                       x=ponto1[0] + 5,
                       y=(distancia - 15), font_size=7,
                       color=(0, 0, 0), font="Courier")

        distancia -= 15

        comentario = exame.comentario or ''
        max_largura = 500
        largura_caractere = 4.2  # aproximação para Courier 7pt
        max_caracteres = int(max_largura / largura_caractere)

        linhas = textwrap.wrap(f'{comentario}', width=max_caracteres)

        for linha in linhas:
            escrever_texto(c, texto=linha,
                           x=ponto1[0] + 10,
                           y=(distancia - 15), font_size=7,
                           color=(0, 0, 0), font="Courier")
            distancia -= 10



        imagem_url = request.build_absolute_uri(exame.bio_medico.assinatura.url)

        # Baixar a imagem
        response_imagem = requests.get(imagem_url)
        if response_imagem.status_code == 200:
            imagem_bytes = response_imagem.content
            imagem_reader = ImageReader(BytesIO(imagem_bytes))

            largura_imagem = 120
            altura_imagem = 100

            # Calcular posição da assinatura
            y_assinatura = ponto4[0] + 10
            x_assinatura = ponto4[0] + ((ponto3[0] - ponto4[0]) - largura_imagem) / 2

            # Inserir imagem no PDF
            c.drawImage(imagem_reader, x_assinatura, y_assinatura, width=largura_imagem, height=altura_imagem, mask='auto')
        else:
            return HttpResponse('Erro ao baixar a imagem', status=500)

    else:
        atendimento = OrcamentoExames.objects.filter(exame=exame).first()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{atendimento.paciente}.pdf"'

        c = canvas.Canvas(response, pagesize=A4)

        ponto1, ponto2, ponto3, ponto4 = desenhar_retangulo(c=c)

        # linhas paralelas
        altura = adicionar_linha_paralela(c, ponto3, ponto4, intervalo=85.05)
        altura1 = adicionar_linha_paralela(c, ponto3, ponto4, intervalo=156)

        # linhas verticais
        linha = adicionar_linha_vertical(c, ponto1, ponto3, altura=85.05, largura_intervalo=141.75)
        linha_vertical = adicionar_linha_vertical(c, ponto1, ponto3, altura=85.05, largura_intervalo=14 * 28.35)

        # Desenhar a linha horizontal paralela à linha de 3cm e entre as linhas verticais de 14cm e 5cm
        largura_linha_horizontal_15cm = ponto1[
                                            0] + 1 * 28.35  # Largura da linha a 15cm da linha vertical à esquerda em pontos
        c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
        c.line(ponto2[0], altura + 1.5 * 28.35, linha_vertical,
               altura + 1.5 * 28.35)

        # Escrever o texto "Nome Gen's Diagnóstica" em negrito e cor verde
        texto = "Gen's Diagnóstica"
        largura_texto = c.stringWidth(texto, "Helvetica-Bold", 14)  # Obter a largura do texto em pontos

        escrever_texto(c, texto=texto,
                       x=((linha - 40 + linha_vertical - largura_texto) / 2),
                       y=(altura + 2.25 * 28.35), font="Helvetica-Bold", font_size=18,
                       color=(0, 0.5, 0))

        c.setFont("Helvetica", 9)
        texto_laboratorio = "Laboratório de análises clínicas"
        largura_texto_laboratorio = c.stringWidth(texto_laboratorio)  # Obter a largura do texto em pontos

        escrever_texto(c, texto=texto_laboratorio,
                       x=((linha + linha_vertical - largura_texto_laboratorio) / 2),
                       y=(altura + 1.5 * 28.35 + 10), font_size=9,
                       color=(0, 0.7, 0.3))

        endereco = "Rua Fortunato Silva, Nº164, Pedra Branca/CE"
        largura_endereco = c.stringWidth(endereco)

        escrever_texto(c, texto=endereco,
                       x=((linha - 16 + linha_vertical - largura_endereco) / 2),
                       y=(altura + 1.5 * 28.35 - 3), font_size=10,
                       color=(0, 0, 0))

        telefone = "Tel: (88) 9 9995 0037 / 3515 1822"
        largura_telefone = c.stringWidth(telefone)

        escrever_texto(c, texto=telefone,
                       x=((linha - 5 + linha_vertical - largura_telefone) / 2),
                       y=(altura + 1.5 * 28.35 - 18), font_size=10,
                       color=(0, 0, 0))

        site = "gensdiagnostica.com.br"
        largura_site = c.stringWidth(site)

        escrever_texto(c, texto=site,
                       x=((linha - 5 + linha_vertical - largura_site) / 2),
                       y=(altura + 1.5 * 28.35 - 33), font_size=10,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Nº {exame.codigo}',
                       x=(linha_vertical + 5),
                       y=(altura + 57), font_size=11,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Emissão: {exame.data_alterado.strftime("%d/%m/%Y")}',
                       x=linha_vertical + 5,
                       y=(altura + 18), font_size=11,
                       color=(0, 0, 0))

        # Escrever o nome 'CPF'
        cpf_1 = 'Não cadastrado'
        if atendimento.paciente.cpf:
            cpf_1 = atendimento.paciente.cpf

        escrever_texto(c, texto=f'CPF: {cpf_1}',
                       x=ponto1[0] + 5,
                       y=(altura1 + 35), font_size=10,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Material: {exame.material}',
                       x=ponto1[0] + 5,
                       y=(altura1 + 15), font_size=8,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Data de Nascimento: {atendimento.paciente.data_nascimento}',
                       x=ponto1[0] + 370,
                       y=(altura1 + 55), font_size=10,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Nome: {atendimento.paciente}',
                       x=ponto1[0] + 5,
                       y=(altura1 + 55), font_size=10,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Número do exame: {exame.codigo}',
                       x=ponto1[0] + 370,
                       y=(altura1 + 35), font_size=10,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'Método: {exame.metodo[:23]}',
                       x=ponto1[0] + 370,
                       y=(altura1 + 15), font_size=8,
                       color=(0, 0, 0))

        # Adicionar a imagem entre as linhas horizontais superior e de 3cm
        imagem = "https://gensdiagnostica.com.br/static/img/gens.png"  # Caminho para a imagem
        largura_imagem = 140  # Largura da imagem em pontos
        altura_imagem = 80  # Altura da imagem em pontos
        c.drawImage(imagem, ponto1[0] + 1, altura + 1, width=largura_imagem, height=altura_imagem)

        distancia = altura1

        escrever_texto(c, texto=f'{exame.nome}',
                       x=ponto1[0] + 5,
                       y=(altura1 - 15), font_size=10,
                       color=(0, 0, 0))

        distancia -= 15

        referencias = exame.referencias.all()
        # Calcula o maior tamanho entre os nomes de referência
        try:
            maior_tamanho = max(len(ref.nome_referencia) for ref in referencias)
            maior_tamanho = 29
        except:
            referencias1 = ReferenciaExame.objects.filter(exame=exame).first()


        escrever_texto(c, texto=f'REFERENCIAS',
                       x=ponto1[0] + 5,
                       y=(distancia - 20), font_size=9,
                       color=(0, 0, 0))

        escrever_texto(c, texto=f'VALORES DE REFERÊNCIA',
                       x=ponto1[0] + 270,
                       y=(distancia - 20), font_size=9,
                       color=(0, 0, 0))

        distancia -= 20

        for referencia in referencias:
            if not referencia.fator and not referencia.esperado:
                nome = referencia.nome_referencia[:29]
                fator = referencia.valor_obtido
                max_min = f'{referencia.limite_inferior} a {referencia.limite_superior}'
                nome_formatado = nome.ljust(maior_tamanho, '.') + ': ' + fator

                escrever_texto(c, texto=nome_formatado,
                               x=ponto1[0] + 5,
                               y=(distancia - 13), font_size=8,
                               color=(0, 0, 0), font="Courier")

                escrever_texto(c, texto=max_min,
                               x=ponto1[0] + 270,
                               y=(distancia - 13), font_size=8,
                               color=(0, 0, 0), font="Courier")

                distancia -= 13

            elif referencia.fator and not referencia.esperado:
                nome = referencia.nome_referencia[:29]
                fator = referencia.valor_obtido

                fatores = referencia.fatores.all()
                max_min = ''
                for fat in fatores:
                    max_min += f'{fat.nome_fator}: {fat.limite_inferior} a {fat.limite_superior} | '
                # Preenche com pontos até o maior tamanho e adiciona os dois-pontos
                nome_formatado = nome.ljust(maior_tamanho, '.') + ': ' + fator
                if len(max_min) < 60:
                    escrever_texto(c, texto=nome_formatado,
                                   x=ponto1[0] + 5,
                                   y=(distancia - 13), font_size=8,
                                   color=(0, 0, 0), font="Courier")

                    escrever_texto(c, texto=max_min[:-2],
                                   x=ponto1[0] + 270,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")

                elif len(max_min) > 60 and len(max_min) <= 120:
                    escrever_texto(c, texto=max_min[:61],
                                   x=ponto1[0] + 270,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")

                    escrever_texto(c, texto=nome_formatado,
                                   x=ponto1[0] + 5,
                                   y=(distancia - 13), font_size=8,
                                   color=(0, 0, 0), font="Courier")

                    distancia -= 13

                    escrever_texto(c, texto=max_min[61:-2],
                                   x=ponto1[0] + 270,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")


                elif len(max_min) > 120:
                    escrever_texto(c, texto=max_min[:61],
                                   x=ponto1[0] + 270,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")

                    escrever_texto(c, texto=nome_formatado,
                                   x=ponto1[0] + 5,
                                   y=(distancia - 13), font_size=8,
                                   color=(0, 0, 0), font="Courier")

                    distancia -= 13

                    escrever_texto(c, texto=max_min[61:121],
                                   x=ponto1[0] + 270,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")

                    distancia -= 13

                    escrever_texto(c, texto=max_min[121:-2],
                                   x=ponto1[0] + 270,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")

                distancia -= 13

            elif not referencia.fator and referencia.esperado:
                nome = referencia.nome_referencia[:29]

                val_esp = referencia.padrao.all()
                ref_esp = ''
                esp_val = ''
                val = 160

                nome_formatado = nome.ljust(maior_tamanho, '.') + ': '

                escrever_texto(c, texto=nome_formatado,
                               x=ponto1[0] + 5,
                               y=(distancia - 13), font_size=8,
                               color=(0, 0, 0), font="Courier")


                for esperado in val_esp:
                    ref_esp += f'{esperado.tipo_valor}: {esperado.valor_esperado}'

                    escrever_texto(c, texto=esperado.esperado_obtido,
                                   x=ponto1[0] + val,
                                   y=(distancia - 13), font_size=8,
                                   color=(0, 0, 0), font="Courier")

                    val += 50

                # Preenche com pontos até o maior tamanho e adiciona os dois-pontos

                if len(ref_esp) <= 60:
                    escrever_texto(c, texto=ref_esp,
                                   x=ponto1[0] + 270,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")


                elif len(ref_esp) > 60 and len(ref_esp) <= 120:
                    escrever_texto(c, texto=ref_esp[:61],
                                   x=ponto1[0] + 270,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")

                    distancia -= 13

                    escrever_texto(c, texto=ref_esp[61:120],
                                   x=ponto1[0] + 270,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")

                elif len(ref_esp) > 120:
                    escrever_texto(c, texto=ref_esp[:61],
                                   x=ponto1[0] + 270,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")

                    distancia -= 13

                    escrever_texto(c, texto=ref_esp[61:120],
                                   x=ponto1[0] + 270,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")

                    distancia -= 13

                    escrever_texto(c, texto=ref_esp[121:],
                                   x=ponto1[0] + 270,
                                   y=(distancia - 13), font_size=7,
                                   color=(0, 0, 0), font="Courier")

            elif referencia.fator and referencia.esperado:
                fatores = referencia.fatores.all()
                esperados = referencia.padrao.all()
                nome = referencia.nome_referencia[:29]
                esperados_ref = ''
                esperados_valor = ''
                for espere in esperados:
                    esperados_ref += f'{espere.tipo_valor}: {espere.valor_esperado}'
                    esperados_valor += f'{espere.esperado_obtido}'

                max_min = ''
                for fat in fatores:
                    max_min += f'{fat.nome_fator}: {fat.limite_inferior} a {fat.limite_superior}'
            # Preenche com pontos até o maior tamanho e adiciona os dois-pontos
                nome_formatado = nome.ljust(maior_tamanho, '.') + ': ' + referencia.valor_obtido

                escrever_texto(c, texto=nome_formatado,
                               x=ponto1[0] + 5,
                               y=(distancia - 13), font_size=8,
                               color=(0, 0, 0), font="Courier")

                escrever_texto(c, texto=esperados_valor,
                               x=ponto1[0] + 150,
                               y=(distancia - 13), font_size=8,
                               color=(0, 0, 0), font="Courier")


                escrever_texto(c, texto=f'{max_min}',
                               x=ponto1[0] + 270,
                               y=(distancia - 13), font_size=7,
                               color=(0, 0, 0), font="Courier")

                escrever_texto(c, texto=f'{esperados_ref}',
                               x=ponto1[0] +380,
                               y=(distancia - 13), font_size=7,
                               color=(0, 0, 0), font="Courier")

            distancia -= 13

    distancia -= 10

    escrever_texto(c, texto=f'Observações:',
                   x=ponto1[0] + 5,
                   y=(distancia - 15), font_size=7,
                   color=(0, 0, 0), font="Courier")

    distancia -= 15

    comentario = exame.comentario or ''
    max_largura = 500
    largura_caractere = 4.2  # aproximação para Courier 7pt
    max_caracteres = int(max_largura / largura_caractere)

    linhas = textwrap.wrap(f'{comentario}', width=max_caracteres)

    for linha in linhas:
        escrever_texto(c, texto=linha,
                       x=ponto1[0] + 10,
                       y=(distancia - 15), font_size=7,
                       color=(0, 0, 0), font="Courier")
        distancia -= 10

    imagem_url = request.build_absolute_uri(exame.bio_medico.assinatura.url)

    # Baixar a imagem
    response_imagem = requests.get(imagem_url)
    if response_imagem.status_code == 200:
        imagem_bytes = response_imagem.content
        imagem_reader = ImageReader(BytesIO(imagem_bytes))

        largura_imagem = 120
        altura_imagem = 100

        # Calcular posição da assinatura
        y_assinatura = ponto4[0] + 10
        x_assinatura = ponto4[0] + ((ponto3[0] - ponto4[0]) - largura_imagem) / 2

        # Inserir imagem no PDF
        c.drawImage(imagem_reader, x_assinatura, y_assinatura, width=largura_imagem, height=altura_imagem,
                    mask='auto')
    else:
        return HttpResponse('Erro ao baixar a imagem', status=500)

    c.save()
    return response


def preencher_laudo_medico(request, pk):
    exame = get_object_or_404(Exame, pk=pk)
    atendimento = OrcamentoExames.objects.filter(exame=exame).first()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{atendimento.paciente}.pdf"'

    c = canvas.Canvas(response, pagesize=A4)

    ponto1, ponto2, ponto3, ponto4 = desenhar_retangulo(c=c)


    #linhas paralelas
    altura = adicionar_linha_paralela(c, ponto3, ponto4, intervalo=85.05)
    altura1 = adicionar_linha_paralela(c, ponto3, ponto4, intervalo=156)

    #linhas verticais
    linha = adicionar_linha_vertical(c, ponto1, ponto3, altura=85.05, largura_intervalo=141.75)
    linha_vertical = adicionar_linha_vertical(c, ponto1, ponto3, altura=85.05, largura_intervalo=14 * 28.35)

    # Desenhar a linha horizontal paralela à linha de 3cm e entre as linhas verticais de 14cm e 5cm
    largura_linha_horizontal_15cm = ponto1[0] + 1 * 28.35  # Largura da linha a 15cm da linha vertical à esquerda em pontos
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
    c.line(ponto2[0], altura + 1.5 * 28.35, linha_vertical,
           altura + 1.5 * 28.35)


    # Escrever o texto "Nome Gen's Diagnóstica" em negrito e cor verde
    texto = "Gen's Diagnóstica"
    largura_texto = c.stringWidth(texto, "Helvetica-Bold", 14)  # Obter a largura do texto em pontos

    escrever_texto(c, texto=texto,
                   x=((linha - 40 + linha_vertical - largura_texto) / 2),
                   y=(altura + 2.25 * 28.35), font="Helvetica-Bold", font_size=18,
                   color=(0, 0.5, 0))

    c.setFont("Helvetica", 9)
    texto_laboratorio = "Laboratório de análises clínicas"
    largura_texto_laboratorio = c.stringWidth(texto_laboratorio)  # Obter a largura do texto em pontos

    escrever_texto(c, texto=texto_laboratorio,
                   x=((linha + linha_vertical - largura_texto_laboratorio) / 2),
                   y=(altura + 1.5 * 28.35 + 10), font_size=9,
                   color=(0, 0.7, 0.3))

    endereco = "Rua Fortunato Silva, Nº164, Pedra Branca/CE"
    largura_endereco = c.stringWidth(endereco)

    escrever_texto(c, texto=endereco,
                   x=((linha - 16 + linha_vertical - largura_endereco) / 2),
                   y=(altura + 1.5 * 28.35 - 3), font_size=10,
                   color=(0, 0, 0))

    telefone = "Tel: (88) 9 9995 0037 / 3515 1822"
    largura_telefone = c.stringWidth(telefone)

    escrever_texto(c, texto=telefone,
                   x=((linha - 5 + linha_vertical - largura_telefone) / 2),
                   y=(altura + 1.5 * 28.35 - 18), font_size=10,
                   color=(0, 0, 0))

    site = "gensdiagnostica.com.br"
    largura_site = c.stringWidth(site)

    escrever_texto(c, texto=site,
                   x=((linha - 5 + linha_vertical - largura_site) / 2),
                   y=(altura + 1.5 * 28.35 - 33), font_size=10,
                   color=(0, 0, 0))

    escrever_texto(c, texto=f'Nº {exame.codigo}',
                   x=(linha_vertical + 5),
                   y=(altura + 57), font_size=11,
                   color=(0, 0, 0))

    escrever_texto(c, texto=f'Emissão: {exame.data_alterado.strftime("%d/%m/%Y")}',
                   x=linha_vertical + 5,
                   y=(altura + 18), font_size=11,
                   color=(0, 0, 0))






    # Escrever o nome 'CPF'
    cpf_1 = 'Não cadastrado'
    if atendimento.paciente.cpf:
        cpf_1 = atendimento.paciente.cpf

    escrever_texto(c, texto=cpf_1,
                   x=ponto1[0] + 5,
                   y=(altura1 + 35), font_size=10,
                   color=(0, 0, 0))

    escrever_texto(c, texto=f'Data de Nascimento: {atendimento.paciente.data_nascimento}',
                   x=ponto1[0] + 5,
                   y=(altura1 + 15), font_size=10,
                   color=(0, 0, 0))

    escrever_texto(c, texto=f'Sexo: {atendimento.paciente.sexo}',
                   x=ponto1[0] + 370,
                   y=(altura1 + 55), font_size=10,
                   color=(0, 0, 0))

    escrever_texto(c, texto=f'Nome: {atendimento.paciente}',
                   x=ponto1[0] + 5,
                   y=(altura1 + 55), font_size=10,
                   color=(0, 0, 0))

    escrever_texto(c, texto=f'Data do exame: {exame.data_cadastro.strftime("%d/%m/%Y")}',
                   x=ponto1[0] + 370,
                   y=(altura1 + 35), font_size=10,
                   color=(0, 0, 0))

    escrever_texto(c, texto=f'Número do exame: {exame.codigo}',
                   x=ponto1[0] + 370,
                   y=(altura1 + 15), font_size=10,
                   color=(0, 0, 0))

    # Adicionar a imagem entre as linhas horizontais superior e de 3cm
    imagem = "https://gensdiagnostica.com.br/static/img/gens.png"  # Caminho para a imagem
    largura_imagem = 140  # Largura da imagem em pontos
    altura_imagem = 80  # Altura da imagem em pontos
    c.drawImage(imagem, ponto1[0] + 1, altura + 1, width=largura_imagem, height=altura_imagem)

    data_referencia = None
    data_referencia_fator = None
    data_referencia_esperado = None
    referencias = exame.referencias.all()
    for ref in referencias:
        if ref.fator is False and ref.esperado is False:
            data_referencia = [
                ['REFERÊNCIA', 'V. ENCONTRADO', 'VALORES DE REFERÊNCIA'],
            ]
        elif ref.fator is True and ref.esperado is False:
            data_referencia_fator = [
                ['REFERÊNCIA', 'V. ENCONTRADO', 'VALORES DE REFERÊNCIA'],
            ]
        elif ref.fator is False and ref.esperado is True:
            data_referencia_esperado = [
                ['REFERÊNCIA', 'V. ENCONTRADO', 'VALORES DE REFERÊNCIA'],
            ]

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), (0.8, 0.8, 0.8)),  # Cor de fundo para o cabeçalho
        ('TEXTCOLOR', (0, 0), (-1, 0), (0, 0, 0)),  # Cor do texto para o cabeçalho
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alinhamento central para todas as células
        ('GRID', (0, 0), (-1, -1), 1, (0.8, 0.8, 0.8)),  # Bordas da tabela
    ])

    largura_disponivel, _ = A4

    for referencia in referencias:
        if referencia.fator is False and referencia.esperado is False:
            ref = [referencia.nome_referencia, referencia.valor_obtido,
                   f'{referencia.limite_inferior} a {referencia.limite_superior}']
            data_referencia.append(ref)
        elif referencia.fator is True and referencia.esperado is False:
            fator_ref = referencia.fatores.all()
            fator_nome1 = ''
            fator10 = ''
            fator100 = ''
            for fator in fator_ref:
                if fator.nome_fator is None:
                    fator_nome1 = f'{fator.idade}'
                else:
                    fator_nome1 = f'{fator.nome_fator}'

                fator10 = fator10 + f' {fator_nome1} || '
                fator100 = fator100 + f'{fator.limite_inferior} a {fator.limite_superior}  || '

            fator100 = fator100[:-3]
            fator10 = fator10[:-3]

            linhas1 = textwrap.wrap(fator10, width=50)
            for linha in linhas1:
                fator0 = ['', '', f'{linha}']
                data_referencia_fator.append(fator0)

            linhas10 = textwrap.wrap(fator100, width=50)

            numero_linha = 1
            for linha in linhas10:
                if numero_linha == 1:
                    fator1 = [referencia.nome_referencia, referencia.valor_obtido, f'{linha}']
                else:
                    fator1 = ['', '', f'{linha}']

                data_referencia_fator.append(fator1)
                numero_linha += 1

            esperado1 = ['', '', '']
            data_referencia_fator.append(esperado1)

        elif referencia.fator is False and referencia.esperado is True:
            ref_esperado = referencia.padrao.all()
            numero_1 = 1
            esperado1 = ''
            for esperado in ref_esperado:
                if numero_1 == 1:
                    esperado1 = [referencia.nome_referencia, referencia.valor_obtido,
                                 f'{esperado.tipo_valor}: {esperado.valor_esperado}']
                else:
                    esperado1 = ['', '',
                                 f'{esperado.tipo_valor}: {esperado.valor_esperado}']
                data_referencia_esperado.append(esperado1)
                numero_1 += 1
            if numero_1 > 2:
                esperado1 = ['', '', '']
                data_referencia_esperado.append(esperado1)
        else:
            fator_ref = referencia.fatores.all()

    observacao = 0
    tabela_referencia_altura = 0

    if data_referencia != None:
        larguras_colunas = [212, 100, 225]
        t = Table(data_referencia, colWidths=larguras_colunas)
        largura_tabela, altura_tabela = t.wrapOn(None, largura_disponivel, 0)
        t.setStyle(style)
        largura_tabela = sum(t._argW)
        posicao_horizontal_tabela = ponto1[0] + (((19 * 28.35) - largura_tabela) / 2)
        tabela_referencia_altura = 20 + altura_tabela
        observacao += tabela_referencia_altura
        posicao_vertical_tabela = altura1 - tabela_referencia_altura
        t.wrapOn(c, largura_tabela, 100)
        t.drawOn(c, posicao_horizontal_tabela, posicao_vertical_tabela)
        print(f'Observação: {observacao}')

    tabela_referencia_altura_ref = 0

    if data_referencia_fator != None:
        if altura1 - (observacao + (len(data_referencia_fator) * 20)) <= 130:
            c.showPage()
            ponto1, ponto2, ponto3, ponto4 = desenhar_retangulo(c=c)
            altura1 = adicionar_linha_paralela(c, ponto3, ponto4, intervalo=0)
            larguras_colunas_ref = [212, 100, 225]  # total 537
            tr = Table(data_referencia_fator, colWidths=larguras_colunas_ref)
            largura_tabela_ref, altura_tabela_ref = tr.wrapOn(None, largura_disponivel, 0)
            tr.setStyle(style)
            largura_tabela_ref = sum(tr._argW)
            posicao_horizontal_tabela_ref = ponto1[0] + (((19 * 28.35) - largura_tabela_ref) / 2)
            tabela_referencia_altura_ref = altura_tabela_ref
            observacao = tabela_referencia_altura_ref
            posicao_vertical_tabela_ref = altura1 - tabela_referencia_altura_ref
            tr.wrapOn(c, largura_tabela_ref, 100)
            tr.drawOn(c, posicao_horizontal_tabela_ref, posicao_vertical_tabela_ref)
            print(f'Observação DRF IF: {observacao}')
            print(f'DRF IF: {tabela_referencia_altura_ref}')
        else:
            larguras_colunas_ref = [212, 100, 225]  # total 537
            tr = Table(data_referencia_fator, colWidths=larguras_colunas_ref)
            largura_tabela_ref, altura_tabela_ref = tr.wrapOn(None, largura_disponivel, 0)
            tr.setStyle(style)
            largura_tabela_ref = sum(tr._argW)
            posicao_horizontal_tabela_ref = ponto1[0] + (((19 * 28.35) - largura_tabela_ref) / 2)
            tabela_referencia_altura_ref = observacao + altura_tabela_ref + 20
            observacao = tabela_referencia_altura_ref
            posicao_vertical_tabela_ref = altura1 - tabela_referencia_altura_ref
            tr.wrapOn(c, largura_tabela_ref, 100)
            tr.drawOn(c, posicao_horizontal_tabela_ref, posicao_vertical_tabela_ref)
            print(f'Observação DRF: {observacao}')

    tabela_referencia_altura_esp = 0
    if data_referencia_esperado != None:

        if altura1 - (observacao + (len(data_referencia_esperado) * 20)) <= 130:
            c.showPage()
            ponto1, ponto2, ponto3, ponto4 = desenhar_retangulo(c=c)
            altura1 = adicionar_linha_paralela(c, ponto3, ponto4, intervalo=0)

            larguras_colunas_esperado = [212, 100, 225]  # total 537
            te = Table(data_referencia_esperado, colWidths=larguras_colunas_esperado)
            largura_tabela_esp, altura_tabela_esp = te.wrapOn(None, largura_disponivel, 0)
            te.setStyle(style)
            largura_tabela_esp = sum(te._argW)
            posicao_horizontal_tabela_esp = ponto1[0] + (((19 * 28.35) - largura_tabela_esp) / 2)
            tabela_referencia_altura_esp = altura_tabela_esp
            observacao = tabela_referencia_altura_esp
            posicao_vertical_tabela_esp = altura1 - tabela_referencia_altura_esp
            te.wrapOn(c, largura_tabela_esp, 100)
            te.drawOn(c, posicao_horizontal_tabela_esp, posicao_vertical_tabela_esp)
            print(f'Observação DRE IF: {observacao}')

        else:
            larguras_colunas_esperado = [212, 100, 225]  # total 537
            te = Table(data_referencia_esperado, colWidths=larguras_colunas_esperado)
            largura_tabela_esp, altura_tabela_esp = te.wrapOn(None, largura_disponivel, 0)
            te.setStyle(style)
            largura_tabela_esp = sum(te._argW)
            posicao_horizontal_tabela_esp = ponto1[0] + (((19 * 28.35) - largura_tabela_esp) / 2)
            tabela_referencia_altura_esp = observacao + altura_tabela_esp + 20
            observacao = tabela_referencia_altura_esp
            posicao_vertical_tabela_esp = altura1 - tabela_referencia_altura_esp
            te.wrapOn(c, largura_tabela_esp, 100)
            te.drawOn(c, posicao_horizontal_tabela_esp, posicao_vertical_tabela_esp)
            print(f'Observação DRE: {observacao}')
    c.save()

    return response


def preencher_laudo(request):
    exames_ids = request.GET.get('exames', '')
    grupo_id = request.GET.get('grupo', '')
    grupo_id = unquote(grupo_id)
    exames_ids_lista = [int(id) for id in exames_ids.split(',') if id.isdigit()]

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{grupo_id}.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    ponto1, ponto2, ponto3, ponto4 = desenhar_retangulo(c=c)

    base = 27 * 28.35
    observacao = base
    print(f'Observação Init: {observacao}')
    for id in exames_ids_lista:
        exame = get_object_or_404(Exame, pk=id)
        atendimento = exame.r_exame.first()
        #observacao = observacao - 20
        altura1 = adicionar_linha_paralela(c, ponto3, ponto4, intervalo=(base - (observacao - 20)))
        escrever_texto(c, texto=f'{atendimento.paciente} - {exame} - N° {exame.codigo}',
                       font="Helvetica-Bold",
                       x=ponto1[0] + 5,
                       y=(altura1 + 5), font_size=10,
                       color=(0, 0.5, 0))

        data_referencia = None
        data_referencia_fator = None
        data_referencia_esperado = None
        referencias = exame.referencias.all()
        for ref in referencias:
            if ref.fator is False and ref.esperado is False:
                data_referencia = [
                    ['REFERÊNCIA', 'V. ENCONTRADO', 'VALORES DE REFERÊNCIA'],
                ]
            elif ref.fator is True and ref.esperado is False:
                data_referencia_fator = [
                    ['REFERÊNCIA', 'V. ENCONTRADO', 'VALORES DE REFERÊNCIA'],
                ]
            elif ref.fator is False and ref.esperado is True:
                data_referencia_esperado = [
                    ['REFERÊNCIA', 'V. ENCONTRADO', 'VALORES DE REFERÊNCIA'],
                ]

        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), (0.8, 0.8, 0.8)),  # Cor de fundo para o cabeçalho
            ('TEXTCOLOR', (0, 0), (-1, 0), (0, 0, 0)),  # Cor do texto para o cabeçalho
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alinhamento central para todas as células
            ('GRID', (0, 0), (-1, -1), 1, (0.8, 0.8, 0.8)),  # Bordas da tabela
        ])

        largura_disponivel, _ = A4

        for referencia in referencias:
            if referencia.fator is False and referencia.esperado is False:
                ref = [referencia.nome_referencia, referencia.valor_obtido,
                       f'{referencia.limite_inferior} a {referencia.limite_superior}']
                data_referencia.append(ref)
            elif referencia.fator is True and referencia.esperado is False:
                fator_ref = referencia.fatores.all()
                fator_nome1 = ''
                fator10 = ''
                fator100 = ''
                for fator in fator_ref:
                    if fator.nome_fator is None:
                        fator_nome1 = f'{fator.idade}'
                    else:
                        fator_nome1 = f'{fator.nome_fator}'

                    fator10 = fator10 + f' {fator_nome1} || '
                    fator100 = fator100 + f'{fator.limite_inferior} a {fator.limite_superior}  || '

                fator100 = fator100[:-3]
                fator10 = fator10[:-3]

                linhas1 = textwrap.wrap(fator10, width=50)
                for linha in linhas1:
                    fator0 = ['', '', f'{linha}']
                    data_referencia_fator.append(fator0)

                linhas10 = textwrap.wrap(fator100, width=50)

                numero_linha = 1
                for linha in linhas10:
                    if numero_linha == 1:
                        fator1 = [referencia.nome_referencia, referencia.valor_obtido, f'{linha}']
                    else:
                        fator1 = ['', '', f'{linha}']

                    data_referencia_fator.append(fator1)
                    numero_linha += 1

                esperado1 = ['', '', '']
                data_referencia_fator.append(esperado1)

            elif referencia.fator is False and referencia.esperado is True:
                ref_esperado = referencia.padrao.all()
                numero_1 = 1
                esperado1 = ''
                for esperado in ref_esperado:
                    if numero_1 == 1:
                        esperado1 = [referencia.nome_referencia, referencia.valor_obtido,
                                     f'{esperado.tipo_valor}: {esperado.valor_esperado}']
                    else:
                        esperado1 = ['', '',
                                     f'{esperado.tipo_valor}: {esperado.valor_esperado}']
                    data_referencia_esperado.append(esperado1)
                    numero_1 += 1
                if numero_1 > 2:
                    esperado1 = ['', '', '']
                    data_referencia_esperado.append(esperado1)
            else:
                fator_ref = referencia.fatores.all()


        tabela_referencia_altura = 0

        if data_referencia != None:
            print(f'Observação1: {observacao}')
            if observacao - (len(data_referencia) * 20) <= 5:
                c.showPage()
                observacao = 27 * 28.35
                ponto1, ponto2, ponto3, ponto4 = desenhar_retangulo(c=c)
                larguras_colunas = [212, 100, 225]
                t = Table(data_referencia, colWidths=larguras_colunas)
                largura_tabela, altura_tabela = t.wrapOn(None, largura_disponivel, 0)
                t.setStyle(style)
                largura_tabela = sum(t._argW)
                posicao_horizontal_tabela = ponto1[0] + (((19 * 28.35) - largura_tabela) / 2)
                tabela_referencia_altura = altura_tabela
                posicao_vertical_tabela = observacao - tabela_referencia_altura
                t.wrapOn(c, largura_tabela, 100)
                t.drawOn(c, posicao_horizontal_tabela, posicao_vertical_tabela)
                observacao = observacao - tabela_referencia_altura
            else:
                larguras_colunas = [212, 100, 225]
                t = Table(data_referencia, colWidths=larguras_colunas)
                largura_tabela, altura_tabela = t.wrapOn(None, largura_disponivel, 0)
                t.setStyle(style)
                largura_tabela = sum(t._argW)
                posicao_horizontal_tabela = ponto1[0] + (((19 * 28.35) - largura_tabela) / 2)
                tabela_referencia_altura = altura_tabela
                posicao_vertical_tabela = observacao - tabela_referencia_altura
                t.wrapOn(c, largura_tabela, 100)
                t.drawOn(c, posicao_horizontal_tabela, posicao_vertical_tabela)
                observacao = observacao - tabela_referencia_altura

        tabela_referencia_altura_ref = 0

        if data_referencia_fator != None:
            if observacao - (len(data_referencia_fator) * 20) <= 5:
                c.showPage()
                observacao = 27 * 28.35
                ponto1, ponto2, ponto3, ponto4 = desenhar_retangulo(c=c)
                larguras_colunas_ref = [212, 100, 225]  # total 537
                tr = Table(data_referencia_fator, colWidths=larguras_colunas_ref)
                largura_tabela_ref, altura_tabela_ref = tr.wrapOn(None, largura_disponivel, 0)
                tr.setStyle(style)
                largura_tabela_ref = sum(tr._argW)
                posicao_horizontal_tabela_ref = ponto1[0] + (((19 * 28.35) - largura_tabela_ref) / 2)
                tabela_referencia_altura_ref = altura_tabela_ref
                posicao_vertical_tabela_ref = observacao - tabela_referencia_altura_ref
                tr.wrapOn(c, largura_tabela_ref, 100)
                tr.drawOn(c, posicao_horizontal_tabela_ref, posicao_vertical_tabela_ref)
                observacao = observacao - tabela_referencia_altura_ref

            else:
                larguras_colunas_ref = [212, 100, 225]  # total 537
                tr = Table(data_referencia_fator, colWidths=larguras_colunas_ref)
                largura_tabela_ref, altura_tabela_ref = tr.wrapOn(None, largura_disponivel, 0)
                tr.setStyle(style)
                largura_tabela_ref = sum(tr._argW)
                posicao_horizontal_tabela_ref = ponto1[0] + (((19 * 28.35) - largura_tabela_ref) / 2)
                tabela_referencia_altura_ref = altura_tabela_ref
                posicao_vertical_tabela_ref = observacao - tabela_referencia_altura_ref
                tr.wrapOn(c, largura_tabela_ref, 100)
                tr.drawOn(c, posicao_horizontal_tabela_ref, posicao_vertical_tabela_ref)
                observacao = observacao - tabela_referencia_altura_ref

        tabela_referencia_altura_esp = 0
        if data_referencia_esperado != None:
            if observacao - (len(data_referencia_esperado) * 20) <= 5:
                c.showPage()
                observacao = 27 * 28.35
                ponto1, ponto2, ponto3, ponto4 = desenhar_retangulo(c=c)
                larguras_colunas_esperado = [212, 100, 225]  # total 537
                te = Table(data_referencia_esperado, colWidths=larguras_colunas_esperado)
                largura_tabela_esp, altura_tabela_esp = te.wrapOn(None, largura_disponivel, 0)
                te.setStyle(style)
                largura_tabela_esp = sum(te._argW)
                posicao_horizontal_tabela_esp = ponto1[0] + (((19 * 28.35) - largura_tabela_esp) / 2)
                tabela_referencia_altura_esp = altura_tabela_esp
                posicao_vertical_tabela_esp = observacao - tabela_referencia_altura_esp
                te.wrapOn(c, largura_tabela_esp, 100)
                te.drawOn(c, posicao_horizontal_tabela_esp, posicao_vertical_tabela_esp)
                observacao = observacao - tabela_referencia_altura_esp
            else:
                larguras_colunas_esperado = [212, 100, 225]  # total 537
                te = Table(data_referencia_esperado, colWidths=larguras_colunas_esperado)
                largura_tabela_esp, altura_tabela_esp = te.wrapOn(None, largura_disponivel, 0)
                te.setStyle(style)
                largura_tabela_esp = sum(te._argW)
                posicao_horizontal_tabela_esp = ponto1[0] + (((19 * 28.35) - largura_tabela_esp) / 2)
                tabela_referencia_altura_esp = altura_tabela_esp
                posicao_vertical_tabela_esp = observacao - tabela_referencia_altura_esp
                te.wrapOn(c, largura_tabela_esp, 100)
                te.drawOn(c, posicao_horizontal_tabela_esp, posicao_vertical_tabela_esp)
                observacao = observacao - tabela_referencia_altura_esp

        observacao = observacao - 40

    c.save()

    return response


# def criar_laudo_medico1(request, pk):
#     exame = get_object_or_404(Exame, pk=pk)
#     atendimento = OrcamentoExames.objects.filter(exame=exame).first()
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="{atendimento.paciente}.pdf"'
#
#     # Definir as dimensões da página A4 em pontos
#     largura_pagina, altura_pagina = A4
#
#     # Definir as dimensões do paralelogramo em pontos
#     largura_paralelogramo = 19 * 28.35  # Convertendo de cm para pontos
#     altura_paralelogramo = 27 * 28.35   # Convertendo de cm para pontos
#
#
#     # Calcular as coordenadas dos pontos para centralizar o paralelogramo na página A4
#     margem_esquerda = (largura_pagina - largura_paralelogramo) / 2
#     margem_superior = (altura_pagina - altura_paralelogramo) / 2
#     print(f'X: {margem_esquerda}')
#     print(f'Y: {margem_superior}')
#     ponto1 = (margem_esquerda, margem_superior)
#     ponto2 = (ponto1[0] + largura_paralelogramo, margem_superior)
#     ponto3 = (largura_pagina - margem_esquerda, margem_superior + altura_paralelogramo)
#     ponto4 = (ponto1[0], ponto1[1] + altura_paralelogramo)
#
#     # Criar o objeto Canvas para o PDF
#     c = canvas.Canvas(response, pagesize=A4)
#
#     # Definir uma cor mais clara para as bordas (cinza claro)
#     c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
#     c.setLineWidth(2)  # Largura da linha
#
#     # Desenhar as bordas do paralelogramo
#     c.line(ponto1[0], ponto1[1], ponto2[0], ponto2[1])  # Linha superior
#     c.line(ponto2[0], ponto2[1], ponto3[0], ponto3[1])  # Linha direita
#     c.line(ponto3[0], ponto3[1], ponto4[0], ponto4[1])  # Linha inferior
#     c.line(ponto4[0], ponto4[1], ponto1[0], ponto1[1])  # Linha esquerda
#
#     # Desenhar a primeira linha paralela à linha superior do paralelogramo (a 3cm)
#     altura_linha_3cm = ponto3[1] - 3 * 28.35  # Altura da linha a 3cm da linha superior em pontos
#     c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
#     c.line(ponto1[0], altura_linha_3cm, ponto2[0], altura_linha_3cm)  # Linha horizontal a 3cm
#
#     # Desenhar a linha vertical paralela à linha esquerda do paralelogramo (a 5cm)
#     largura_linha_vertical = ponto1[0] + 5 * 28.35  # Largura da linha a 5cm da linha vertical à esquerda em pontos
#     c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
#     c.line(largura_linha_vertical, ponto3[1], largura_linha_vertical, altura_linha_3cm)  # Linha vertical a 5cm
#
#     # Desenhar a linha paralela à linha superior do paralelogramo (a 6,5cm)
#     altura_linha_65cm = ponto3[1] - 5.5 * 28.35  # Altura da linha a 6,5cm da linha superior em pontos
#     c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
#     c.line(ponto1[0], altura_linha_65cm, ponto2[0], altura_linha_65cm)  # Linha horizontal a 6,5cm
#     linha_limite = altura_linha_65cm
#
#
#     # Desenhar a linha paralela à linha superior do paralelogramo (a 26cm)
#     altura_linha_26cm = ponto3[1] - 26 * 28.35  # Altura da linha a 26cm da linha superior em pontos
#     imagem_url = request.build_absolute_uri(exame.bio_medico.assinatura.url)
#
#     # Baixa a imagem da URL
#     response_imagem = requests.get(imagem_url)
#     if response_imagem.status_code == 200:
#         imagem_bytes = response_imagem.content
#     else:
#         return HttpResponse('Erro ao baixar a imagem', status=500)
#
#     imagem_reader = ImageReader(BytesIO(imagem_bytes))
#     largura_imagem = 160
#     altura_imagem = 140
#     posicao_horizontal_central = (largura_pagina - largura_imagem) / 2
#     c.drawImage(imagem_reader, posicao_horizontal_central, altura_linha_26cm - 20, width=largura_imagem, height=altura_imagem)
#
#
#     # Desenhar a linha vertical paralela à linha esquerda do paralelogramo (a 14cm)
#     largura_linha_vertical_14cm = ponto1[0] + 14 * 28.35  # Largura da linha a 14cm da linha vertical à esquerda em pontos
#     c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
#     c.line(largura_linha_vertical_14cm, ponto3[1], largura_linha_vertical_14cm,
#            altura_linha_3cm)  # Linha vertical a 14cm
#
#     # Desenhar a linha horizontal paralela à linha de 3cm e entre as linhas verticais de 14cm e 5cm
#     largura_linha_horizontal_15cm = ponto1[0] + 19 * 28.35  # Largura da linha a 15cm da linha vertical à esquerda em pontos
#     c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
#     c.line(largura_linha_vertical_14cm, altura_linha_3cm + 1.5 * 28.35, largura_linha_horizontal_15cm,
#            altura_linha_3cm + 1.5 * 28.35)  # Linha horizontal a 1,5cm paralela à linha de 3cm
#
#     # Escrever o texto "Nome Gen's Diagnóstica" em negrito e cor verde
#     c.setFont("Helvetica-Bold", 18)  # Definir a fonte em negrito e o tamanho do texto
#     c.setFillColorRGB(0, 0.5, 0)  # Definir a cor verde (RGB)
#     texto = "Gen's Diagnóstica"
#     largura_texto = c.stringWidth(texto, "Helvetica-Bold", 14)  # Obter a largura do texto em pontos
#
#     # Calcular as coordenadas para centralizar o texto entre largura_linha_vertical e largura_linha_vertical_14cm
#     posicao_horizontal = (largura_linha_vertical - 40 + largura_linha_vertical_14cm - largura_texto) / 2
#
#     # Calcular a coordenada y para posicionar o texto entre a linha superior e altura_linha_3cm
#     posicao_vertical = altura_linha_3cm + 2.25 * 28.35  # Ajuste fino da posição vertical
#
#     # Desenhar o texto na posição calculada
#     c.drawString(posicao_horizontal, posicao_vertical, texto)
#
#     # Escrever o texto "Laboratório de análises clínicas" em tamanho 10 e cor verde mais clara
#     c.setFont("Helvetica", 9)  # Definir a fonte e o tamanho do texto
#     c.setFillColorRGB(0, 0.7, 0.3)  # Definir uma cor verde mais clara (RGB)
#     texto_laboratorio = "Laboratório de análises clínicas"
#     largura_texto_laboratorio = c.stringWidth(texto_laboratorio)  # Obter a largura do texto em pontos
#
#     # Calcular as coordenadas para centralizar o texto abaixo do texto anterior
#     posicao_horizontal_laboratorio = (largura_linha_vertical + largura_linha_vertical_14cm - largura_texto_laboratorio) / 2
#     posicao_vertical = altura_linha_3cm + 1.5 * 28.35 + 10  # Distância vertical entre os textos
#
#     # Desenhar o texto na posição calculada
#     c.drawString(posicao_horizontal_laboratorio, posicao_vertical, texto_laboratorio)
#
#     # Escrever o endereço
#     endereco = "Rua Fortunato Silva, Nº164, Pedra Branca/CE"
#     largura_endereco = c.stringWidth(endereco)  # Obter a largura do texto em pontos
#
#     # Calcular as coordenadas para centralizar o texto abaixo do texto anterior
#     posicao_horizontal_endereco = (largura_linha_vertical - 25 + largura_linha_vertical_14cm - largura_endereco) / 2
#     posicao_vertical_endereco = posicao_vertical - 15  # Distância vertical entre os textos
#
#     # Desenhar o texto na posição calculada
#     c.setFont("Helvetica", 10)  # Definir a fonte e o tamanho do texto
#     c.setFillColorRGB(0, 0, 0)  # Definir cor preta (RGB)
#     c.drawString(posicao_horizontal_endereco, posicao_vertical_endereco, endereco)
#
#     # Escrever o número de telefone
#     telefone = "Tel: (88) 9 9995 0037 / 3515 1822"
#     largura_telefone = c.stringWidth(telefone)  # Obter a largura do texto em pontos
#
#     # Calcular as coordenadas para centralizar o texto abaixo do texto anterior
#     posicao_horizontal_telefone = (largura_linha_vertical + largura_linha_vertical_14cm - largura_telefone) / 2
#     posicao_vertical_telefone = posicao_vertical_endereco - 15  # Distância vertical entre os textos
#
#     # Desenhar o texto na posição calculada
#     c.drawString(posicao_horizontal_telefone, posicao_vertical_telefone, telefone)
#
#     # Escrever o endereço do site
#     site = "gensdiagnostica.com.br"
#     largura_site = c.stringWidth(site)  # Obter a largura do texto em pontos
#
#     # Calcular as coordenadas para centralizar o texto abaixo do texto anterior
#     posicao_horizontal_site = (largura_linha_vertical + largura_linha_vertical_14cm - largura_site) / 2
#     posicao_vertical_site = posicao_vertical_telefone - 15  # Distância vertical entre os textos
#
#     # Desenhar o texto na posição calculada
#     c.drawString(posicao_horizontal_site, posicao_vertical_site, site)
#
#     # Adicionar a imagem entre as linhas horizontais superior e de 3cm
#     imagem = "https://gensdiagnostica.com.br/static/img/gens.png"  # Caminho para a imagem
#     largura_imagem = 140  # Largura da imagem em pontos
#     altura_imagem = 85  # Altura da imagem em pontos
#     c.drawImage(imagem, ponto1[0], altura_linha_3cm + 1, width=largura_imagem, height=altura_imagem)
#
#     # Escrever Nº 123456789 entre largura_linha_vertical_14cm e a linha vertical a direita e acima da largura_linha_horizontal_15cm
#     numero = f'Nº {exame.codigo}'
#     largura_numero = c.stringWidth(numero)  # Obter a largura do texto em pontos
#
#     # Calcular as coordenadas para posicionar o texto entre largura_linha_vertical_14cm e a linha vertical a direita
#     posicao_horizontal_numero = largura_linha_vertical_14cm + 5
#
#     # Calcular a coordenada y para posicionar o texto acima da largura_linha_horizontal_15cm
#     posicao_vertical_numero = altura_linha_3cm + 1.5 * 28.35 + 17  # Ajuste fino da posição vertical
#
#     # Desenhar o texto na posição calculada
#     c.drawString(posicao_horizontal_numero, posicao_vertical_numero, numero)
#
#
#     # Escrever 'EXAME' entre altura_linha_4cm e altura_linha_3cm, tamanho 18, em negrito
#     c.setFont("Helvetica", 11)  # Definir a fonte em negrito e o tamanho do texto
#     c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
#     texto_emissao = f'Emissão: {exame.data_alterado.strftime("%d/%m/%Y")}'
#     # Calcular as coordenadas para centralizar o texto entre a linha de 4cm e a linha de 3cm
#     posicao_horizontal_emissao = largura_linha_vertical_14cm + 5
#     posicao_vertical_emissao = altura_linha_3cm + 17
#
#     # Desenhar o texto na posição calculada
#     c.drawString(posicao_horizontal_emissao, posicao_vertical_emissao, texto_emissao)
#
#
#     # Escrever o nome 'Nome'
#     c.setFont("Helvetica", 10)  # Definir a fonte e o tamanho do texto
#     c.setFillColorRGB(0, 0, 0)  # Definir a cor preta
#     c.drawString(ponto1[0] + 5, altura_linha_65cm + 55, f'Nome: {atendimento.paciente}')
#
#     # Escrever o nome 'CPF'
#     cpf_1 = 'Não cadastrado'
#     if atendimento.paciente.cpf:
#         cpf_1 = atendimento.paciente.cpf
#
#     c.drawString(ponto1[0] + 5, altura_linha_65cm + 35, f'CPF: {cpf_1}')
#
#     # Escrever o nome 'Data de Nascimento'
#     c.drawString(ponto1[0] + 5, altura_linha_65cm + 15, f'Data de Nascimento: {atendimento.paciente.data_nascimento}')
#
#     # Escrever o nome 'Sexo'
#     c.drawString(ponto1[0] + 370, altura_linha_65cm + 55, f'Sexo: {atendimento.paciente.sexo}')
#
#     # Escrever o nome 'Data do exame'
#     c.drawString(ponto1[0] + 370, altura_linha_65cm + 35, f'Data do exame: {exame.data_cadastro.strftime("%d/%m/%Y")}')
#
#     # Escrever o nome 'Código'
#     c.drawString(ponto1[0] + 370, altura_linha_65cm + 15, f'Número do exame: {exame.codigo}')
#
#     data_referencia = None
#     data_referencia_fator = None
#     data_referencia_esperado = None
#     referencias = exame.referencias.all()
#     for ref in referencias:
#         if ref.fator is False and ref.esperado is False:
#             data_referencia = [
#                 ['REFERÊNCIA', 'V. ENCONTRADO', 'VALORES DE REFERÊNCIA'],
#             ]
#             linha_limite -= 20
#         elif ref.fator is True and ref.esperado is False:
#             data_referencia_fator = [
#                 ['REFERÊNCIA', 'V. ENCONTRADO', 'VALORES DE REFERÊNCIA'],
#             ]
#             linha_limite -= 20
#         elif ref.fator is False and ref.esperado is True:
#             data_referencia_esperado = [
#                 ['REFERÊNCIA', 'V. ENCONTRADO', 'VALORES DE REFERÊNCIA'],
#             ]
#             linha_limite -= 20
#
#     style = TableStyle([
#        ('BACKGROUND', (0, 0), (-1, 0), (0.8, 0.8, 0.8)),  # Cor de fundo para o cabeçalho
#        ('TEXTCOLOR', (0, 0), (-1, 0), (0, 0, 0)),  # Cor do texto para o cabeçalho
#        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alinhamento central para todas as células
#        ('GRID', (0, 0), (-1, -1), 1, (0.8, 0.8, 0.8)),  # Bordas da tabela
#     ])
#
#     largura_disponivel, _ = A4
#
#     for referencia in referencias:
#         if referencia.fator is False and referencia.esperado is False:
#             ref = [referencia.nome_referencia, referencia.valor_obtido, f'{referencia.limite_inferior} a {referencia.limite_superior}']
#             data_referencia.append(ref)
#         elif referencia.fator is True and referencia.esperado is False:
#             fator_ref = referencia.fatores.all()
#             fator_nome1 = ''
#             fator10 = ''
#             fator100 = ''
#             for fator in fator_ref:
#                 if fator.nome_fator is None:
#                     fator_nome1 = f'{fator.idade}'
#                 else:
#                     fator_nome1 = f'{fator.nome_fator}'
#
#                 fator10 = fator10 + f' {fator_nome1} || '
#                 fator100 = fator100 + f'{fator.limite_inferior} a {fator.limite_superior}  || '
#
#             fator100 = fator100[:-3]
#             fator10 = fator10[:-3]
#
#             linhas1 = textwrap.wrap(fator10, width=50)
#             for linha in linhas1:
#                 fator0 = ['', '', f'{linha}']
#                 data_referencia_fator.append(fator0)
#
#             linhas10 = textwrap.wrap(fator100, width=50)
#
#             numero_linha = 1
#             for linha in linhas10:
#                 if numero_linha == 1:
#                     fator1 = [referencia.nome_referencia, referencia.valor_obtido, f'{linha}']
#                 else:
#                     fator1 = ['', '', f'{linha}']
#
#                 data_referencia_fator.append(fator1)
#                 numero_linha += 1
#
#             esperado1 = ['', '', '']
#             data_referencia_fator.append(esperado1)
#
#         elif referencia.fator is False and referencia.esperado is True:
#             ref_esperado = referencia.padrao.all()
#             numero_1 = 1
#             esperado1 = ''
#             for esperado in ref_esperado:
#                 if numero_1 == 1:
#                     esperado1 = [referencia.nome_referencia, referencia.valor_obtido,
#                               f'{esperado.tipo_valor}: {esperado.valor_esperado}']
#                 else:
#                     esperado1 = ['', '',
#                                  f'{esperado.tipo_valor}: {esperado.valor_esperado}']
#                 data_referencia_esperado.append(esperado1)
#                 numero_1 += 1
#             if numero_1 > 2:
#                 esperado1 = ['', '', '']
#                 data_referencia_esperado.append(esperado1)
#         else:
#             fator_ref = referencia.fatores.all()
#     observacao = 0
#     tabela_referencia_altura = 0
#
#     if data_referencia != None:
#         larguras_colunas = [212, 100, 225]
#         t = Table(data_referencia, colWidths=larguras_colunas)
#         linha_limite = linha_limite - (len(data_referencia) * 20)
#         print(f'Linha Limite Refrência: {linha_limite}')
#         # if linha_limite < 400:
#         #     c.showPage()
#         #     pp = desenhar_paralelogramo(c)
#         #     print(f'PP1: {pp}')
#         #     altura_linha_65cm = pp
#
#         largura_tabela, altura_tabela = t.wrapOn(None, largura_disponivel, 0)
#         t.setStyle(style)
#         largura_tabela = sum(t._argW)
#         posicao_horizontal_tabela = ponto1[0] + ((largura_paralelogramo - largura_tabela) / 2)
#         tabela_referencia_altura = 20 + altura_tabela
#         observacao += tabela_referencia_altura
#         posicao_vertical_tabela = altura_linha_65cm - tabela_referencia_altura
#         t.wrapOn(c, largura_tabela, 100)
#         t.drawOn(c, posicao_horizontal_tabela, posicao_vertical_tabela)
#
#     tabela_referencia_altura_ref = 0
#     if data_referencia_fator != None:
#         larguras_colunas_ref = [212, 100, 225]  # total 537
#         tr = Table(data_referencia_fator, colWidths=larguras_colunas_ref)
#         linha_limite = linha_limite - (len(data_referencia_fator) * 20)
#         print(f'Linha Limite Refrência_FATOR: {linha_limite}')
#         # if linha_limite < 400:
#         #     c.showPage()
#         #     pp = desenhar_paralelogramo(c)
#         #     print(f'PP2: {pp}')
#         #     altura_linha_65cm = pp
#
#         largura_tabela_ref, altura_tabela_ref = tr.wrapOn(None, largura_disponivel, 0)
#         tr.setStyle(style)
#         largura_tabela_ref = sum(tr._argW)
#         posicao_horizontal_tabela_ref = ponto1[0] + ((largura_paralelogramo - largura_tabela_ref) / 2)
#         tabela_referencia_altura_ref = tabela_referencia_altura + altura_tabela_ref + 20
#         observacao = tabela_referencia_altura_ref
#         posicao_vertical_tabela_ref = altura_linha_65cm - tabela_referencia_altura_ref
#         tr.wrapOn(c, largura_tabela_ref, 100)
#         tr.drawOn(c, posicao_horizontal_tabela_ref, posicao_vertical_tabela_ref)
#
#     tabela_referencia_altura_esp = 0
#     if data_referencia_esperado != None:
#         larguras_colunas_esperado = [212, 100, 225]  # total 537
#         te = Table(data_referencia_esperado, colWidths=larguras_colunas_esperado)
#         linha_limite = linha_limite - (len(data_referencia_esperado) * 20)
#         print(f'Linha Limite Refrência_ESPERADO: {linha_limite}')
#         # if linha_limite < 400:
#         #     c.showPage()
#         #     pp = desenhar_paralelogramo(c)
#         #     print(f'PP3: {pp}')
#         #     altura_linha_65cm = pp
#
#         largura_tabela_esp, altura_tabela_esp = te.wrapOn(None, largura_disponivel, 0)
#         te.setStyle(style)
#         largura_tabela_esp = sum(te._argW)
#         posicao_horizontal_tabela_esp = ponto1[0] + ((largura_paralelogramo - largura_tabela_esp) / 2)
#         tabela_referencia_altura_esp = tabela_referencia_altura_ref + altura_tabela_esp + 20
#         observacao = tabela_referencia_altura_esp
#         posicao_vertical_tabela_esp = altura_linha_65cm - tabela_referencia_altura_esp
#         te.wrapOn(c, largura_tabela_esp, 100)
#         te.drawOn(c, posicao_horizontal_tabela_esp, posicao_vertical_tabela_esp)
#
#
#     c.setFont("Helvetica-Bold", 11)  # Definir a fonte em negrito e o tamanho do texto
#     c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
#     observacoes = f'Observações'
#     if len(exame.comentario) == 0:
#         observacoes = ''
#     # Calcular as coordenadas para centralizar o texto entre a linha de 4cm e a linha de 3cm
#     posicao_horizontal_observer = ponto1[0] + 10
#     posicao_vertical_observer = altura_linha_65cm - observacao - 30
#     c.drawString(posicao_horizontal_observer, posicao_vertical_observer, observacoes)
#
#     c.setFont("Helvetica", 9)  # Definir a fonte em negrito e o tamanho do texto
#     c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
#     observacoes1 = f'{exame.comentario}'
#
#     # Largura máxima da linha (pode ajustar conforme necessário)
#     largura_maxima = 100
#
#     # Dividir o texto em linhas com base na largura máxima
#     linhas = textwrap.wrap(observacoes1, width=largura_maxima)
#
#     # Calcular as coordenadas para centralizar o texto entre a linha de 4cm e a linha de 3cm
#     posicao_horizontal_observacao = ponto1[0] + 15
#     posicao_vertical_observacao = altura_linha_65cm - observacao - 40
#
#     # Escrever cada linha individualmente
#     obs_1 = 1
#     for linha in linhas:
#         if obs_1 == 1:
#             c.drawString(posicao_horizontal_observacao, posicao_vertical_observacao - 5, linha)
#             posicao_vertical_observacao -= 20
#         # Atualizar a posição vertical para a próxima linha
#         else:
#             c.drawString(posicao_horizontal_observacao, posicao_vertical_observacao, linha)
#             posicao_vertical_observacao -= 15
#
#         obs_1 += 1
#     # Salvar e finalizar o PDF
#     c.save()
#
#     return response


class BuscarExame(LoginRequiredMixin, TemplateView):
    template_name = 'exame/buscar_exame1.html'


class BuscarExameterceirizado(LoginRequiredMixin, TemplateView):
    template_name = 'exame/buscar_exame_terceirizado.html'


def buscar_exame(request):
    if request.POST.get('ajax_request') == 'true':
        res = None
        nomes = request.POST.get('nomes')
        query_se = Exame.objects.filter(codigo__icontains=nomes, terceirizado=False)

        if len(query_se) > 0 and len(nomes) > 0:
            data = []
            for exame in query_se:
                item = {
                    'pk': exame.pk,
                    'codigo': exame.codigo,
                    'nome': exame.nome,
                }

                data.append(item)
            res = data
        else:
            res = 'Nenhum exame encontrado'

        return JsonResponse({'data': res})
    return JsonResponse({})


def buscar_exame_terceirizado(request):
    if request.POST.get('ajax_request') == 'true':
        res = None
        nomes = request.POST.get('nomes')
        query_se = Exame.objects.filter(codigo__icontains=nomes, terceirizado=True)

        if len(query_se) > 0 and len(nomes) > 0:
            data = []
            for exame in query_se:
                item = {
                    'pk': exame.pk,
                    'codigo': exame.codigo,
                    'nome': exame.nome,
                }

                data.append(item)
            res = data
        else:
            res = 'Nenhum exame encontrado'

        return JsonResponse({'data': res})
    return JsonResponse({})


def etiqueta_exame(request, pk):
    # Dimensões personalizadas (largura x altura em pontos)

    exame = get_object_or_404(Exame, pk=pk)
    orcamento = OrcamentoExames.objects.filter(exame=exame).first()
    etiqueta_tamanho = (283, 70)  # 100 mm x 50 mm
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="etiqueta_{orcamento.paciente.nome}.pdf"'
# Criando o PDF
    c = canvas.Canvas(response, pagesize=etiqueta_tamanho)
    c.setFont("Helvetica-Bold", 11)
    largura_etiqueta, altura_etiqueta = etiqueta_tamanho

    altura_inicio = altura_etiqueta - 25
    palavra = f'{orcamento.paciente.nome}'
    exame_nome = f'{exame.nome}'

    largura_nome = c.stringWidth(palavra[:50], "Helvetica-Bold", 11)
    x = (largura_etiqueta - largura_nome) / 2
    c.drawString(x, altura_inicio, palavra[:50])
    altura_inicio -= 15
    c.setFont("Helvetica", 11)
    largura_exame = c.stringWidth(exame_nome[:46], "Helvetica", 11)
    x = (largura_etiqueta - largura_exame) / 2
    c.drawString(x, altura_inicio, exame_nome[:46])
    altura_inicio -= 13
    c.setFont("Helvetica", 9)
    largura_codigo = c.stringWidth(f'{exame.codigo}', "Helvetica", 9)
    x = (largura_etiqueta - largura_codigo) / 2
    c.drawString(x, altura_inicio, f'{exame.codigo}')
    altura_inicio -= 10
    c.save()
    return response


def etiquetas_de_exame(request):
    exames_ids = request.GET.get('exames', '')
    exames_ids_lista = [int(id) for id in exames_ids.split(',') if id.isdigit()]
    exame = get_object_or_404(Exame, pk=exames_ids_lista[0])
    orcamento = OrcamentoExames.objects.filter(exame=exame).first()

    print(f'lista:{exames_ids_lista}')

    etiqueta_tamanho = (283, 150)  # 100 mm x 50 mm
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="etiqueta_{orcamento.paciente.nome}.pdf"'

    c = canvas.Canvas(response, pagesize=etiqueta_tamanho)
    c.setFont("Helvetica-Bold", 11)
    largura_etiqueta, altura_etiqueta = etiqueta_tamanho

    altura_inicio = altura_etiqueta - 25
    palavra = f'{orcamento.paciente.nome}'
    largura_nome = c.stringWidth(palavra[:50], "Helvetica-Bold", 11)
    x = (largura_etiqueta - largura_nome) / 2
    c.drawString(x, altura_inicio, palavra[:50])
    altura_inicio -= 15


    for id in exames_ids_lista:
        exame = get_object_or_404(Exame, pk=id)
        exame_nome = f'{exame.nome}'
        c.setFont("Helvetica", 11)
        largura_exame = c.stringWidth(exame_nome[:46], "Helvetica", 11)
        x = (largura_etiqueta - largura_exame) / 2
        c.drawString(x, altura_inicio, exame_nome[:46])
        altura_inicio -= 13
        c.setFont("Helvetica", 9)
        largura_codigo = c.stringWidth(f'{exame.codigo}', "Helvetica", 9)
        x = (largura_etiqueta - largura_codigo) / 2
        c.drawString(x, altura_inicio, f'{exame.codigo}')
        altura_inicio -= 10

    c.save()
    return response

#### GRUPOS DE EXAMES ####


class GrupoCreate(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = GrupoExamesForm
    model = GrupoExame
    template_name = 'exame/grupo_add.html'
    success_message = 'Grupo criado com sucesso'
    success_url = '/'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['exames'].queryset = Exame.objects.filter(padrao=True)
        return form
