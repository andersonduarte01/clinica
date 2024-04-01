import textwrap

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.platypus.para import Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from apps.agenda.models import Plano
from apps.atendimento.models import OrcamentoExames
from apps.exame.exame_create import objeto_exame
from apps.exame.forms import ExameForm, ReferenciaForm, FatorReferenciaForm, ValorEsperadoForm, ExameFormUpdate, \
    ExameAtendimentoForm, ReferenciaExameForm, ExameMedicForm
from apps.exame.models import Exame, ReferenciaExame, FatoresReferencia, ValorEsperado


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
def realizar_exame(request, pk):
    exame = get_object_or_404(Exame, pk=pk)
    referencias = exame.referencias.all()
    ReferenciaExameInlineFormSet = inlineformset_factory(Exame, ReferenciaExame, form=ReferenciaExameForm, extra=0, can_delete=False)

    if request.method == 'POST':
        form = ExameMedicForm(request.POST, instance=exame)
        formset = ReferenciaExameInlineFormSet(request.POST, request.FILES, instance=exame)
        print(f'Formset: {formset.is_valid()}')
        print(formset)
        if form.is_valid() and formset.is_valid():
            exame1 = form.save(commit=False)
            formset1 = formset.save()
            exame1.save()
            #url = reverse('home:painel', kwargs={'pk': aluno.sala.pk})
            url = reverse('home:painel')
            return HttpResponseRedirect(url)

    else:
        form = ExameMedicForm(instance=exame)
        formset = ReferenciaExameInlineFormSet(instance=exame)

    orcamento = OrcamentoExames.objects.filter(exame=exame).first()
    context = {'form': form, 'orcamento': orcamento, 'exame': exame, 'formset': formset}
    return render(request, "exame/editar_exame_teste.html", context)


def criar_laudo_medico(request, pk):
    exame = get_object_or_404(Exame, pk=pk)
    atendimento = OrcamentoExames.objects.filter(exame=exame).first()
    contador = 1
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{atendimento.paciente}.pdf"'

    # Definir as dimensões da página A4 em pontos
    largura_pagina, altura_pagina = A4

    # Definir as dimensões do paralelogramo em pontos
    largura_paralelogramo = 19 * 28.35  # Convertendo de cm para pontos
    altura_paralelogramo = 27 * 28.35   # Convertendo de cm para pontos

    # Calcular as coordenadas dos pontos para centralizar o paralelogramo na página A4
    margem_esquerda = (largura_pagina - largura_paralelogramo) / 2
    margem_superior = (altura_pagina - altura_paralelogramo) / 2

    ponto1 = (margem_esquerda, margem_superior)
    ponto2 = (ponto1[0] + largura_paralelogramo, margem_superior)
    ponto3 = (largura_pagina - margem_esquerda, margem_superior + altura_paralelogramo)
    ponto4 = (ponto1[0], ponto1[1] + altura_paralelogramo)

    # Criar o objeto Canvas para o PDF
    c = canvas.Canvas(response, pagesize=A4)

    # Definir uma cor mais clara para as bordas (cinza claro)
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
    c.setLineWidth(2)  # Largura da linha

    # Desenhar as bordas do paralelogramo
    c.line(ponto1[0], ponto1[1], ponto2[0], ponto2[1])  # Linha superior
    c.line(ponto2[0], ponto2[1], ponto3[0], ponto3[1])  # Linha direita
    c.line(ponto3[0], ponto3[1], ponto4[0], ponto4[1])  # Linha inferior
    c.line(ponto4[0], ponto4[1], ponto1[0], ponto1[1])  # Linha esquerda

    # Desenhar a primeira linha paralela à linha superior do paralelogramo (a 3cm)
    altura_linha_3cm = ponto3[1] - 3 * 28.35  # Altura da linha a 3cm da linha superior em pontos
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
    c.line(ponto1[0], altura_linha_3cm, ponto2[0], altura_linha_3cm)  # Linha horizontal a 3cm

    # Desenhar a linha vertical paralela à linha esquerda do paralelogramo (a 5cm)
    largura_linha_vertical = ponto1[0] + 5 * 28.35  # Largura da linha a 5cm da linha vertical à esquerda em pontos
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
    c.line(largura_linha_vertical, ponto3[1], largura_linha_vertical, altura_linha_3cm)  # Linha vertical a 5cm

    # Desenhar a linha paralela à linha superior do paralelogramo (a 4cm)
    altura_linha_4cm = ponto3[1] - 4 * 28.35  # Altura da linha a 4cm da linha superior em pontos
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
    c.line(ponto1[0], altura_linha_4cm, ponto2[0], altura_linha_4cm)  # Linha horizontal a 4cm

    # Desenhar a linha paralela à linha superior do paralelogramo (a 6,5cm)
    altura_linha_65cm = ponto3[1] - 6.5 * 28.35  # Altura da linha a 6,5cm da linha superior em pontos
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
    c.line(ponto1[0], altura_linha_65cm, ponto2[0], altura_linha_65cm)  # Linha horizontal a 6,5cm

    # Desenhar a linha paralela à linha superior do paralelogramo (a 25cm)
    altura_linha_25cm = ponto3[1] - 25 * 28.35  # Altura da linha a 25cm da linha superior em pontos
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
    c.line(ponto1[0], altura_linha_25cm, ponto2[0], altura_linha_25cm)  # Linha horizontal a 25cm

    # Desenhar a linha paralela à linha superior do paralelogramo (a 26cm)
    altura_linha_26cm = ponto3[1] - 26 * 28.35  # Altura da linha a 26cm da linha superior em pontos
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
    c.line(ponto1[0], altura_linha_26cm, ponto2[0], altura_linha_26cm)  # Linha horizontal a 26cm

    # Desenhar a linha vertical paralela à linha esquerda do paralelogramo (a 14cm)
    largura_linha_vertical_14cm = ponto1[0] + 14 * 28.35  # Largura da linha a 14cm da linha vertical à esquerda em pontos
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
    c.line(largura_linha_vertical_14cm, ponto3[1], largura_linha_vertical_14cm,
           altura_linha_3cm)  # Linha vertical a 14cm

    # Desenhar a linha horizontal paralela à linha de 3cm e entre as linhas verticais de 14cm e 5cm
    largura_linha_horizontal_15cm = ponto1[0] + 19 * 28.35  # Largura da linha a 15cm da linha vertical à esquerda em pontos
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
    c.line(largura_linha_vertical_14cm, altura_linha_3cm + 1.5 * 28.35, largura_linha_horizontal_15cm,
           altura_linha_3cm + 1.5 * 28.35)  # Linha horizontal a 1,5cm paralela à linha de 3cm

    # Escrever o texto "Nome Gen's Diagnóstica" em negrito e cor verde
    c.setFont("Helvetica-Bold", 18)  # Definir a fonte em negrito e o tamanho do texto
    c.setFillColorRGB(0, 0.5, 0)  # Definir a cor verde (RGB)
    texto = "Gen's Diagnóstica"
    largura_texto = c.stringWidth(texto, "Helvetica-Bold", 14)  # Obter a largura do texto em pontos

    # Calcular as coordenadas para centralizar o texto entre largura_linha_vertical e largura_linha_vertical_14cm
    posicao_horizontal = (largura_linha_vertical - 40 + largura_linha_vertical_14cm - largura_texto) / 2

    # Calcular a coordenada y para posicionar o texto entre a linha superior e altura_linha_3cm
    posicao_vertical = altura_linha_3cm + 2.25 * 28.35  # Ajuste fino da posição vertical

    # Desenhar o texto na posição calculada
    c.drawString(posicao_horizontal, posicao_vertical, texto)

    # Escrever o texto "Laboratório de análises clínicas" em tamanho 10 e cor verde mais clara
    c.setFont("Helvetica", 9)  # Definir a fonte e o tamanho do texto
    c.setFillColorRGB(0, 0.7, 0.3)  # Definir uma cor verde mais clara (RGB)
    texto_laboratorio = "Laboratório de análises clínicas"
    largura_texto_laboratorio = c.stringWidth(texto_laboratorio)  # Obter a largura do texto em pontos

    # Calcular as coordenadas para centralizar o texto abaixo do texto anterior
    posicao_horizontal_laboratorio = (largura_linha_vertical + largura_linha_vertical_14cm - largura_texto_laboratorio) / 2
    posicao_vertical = altura_linha_3cm + 1.5 * 28.35 + 10  # Distância vertical entre os textos

    # Desenhar o texto na posição calculada
    c.drawString(posicao_horizontal_laboratorio, posicao_vertical, texto_laboratorio)

    # Escrever o endereço
    endereco = "Rua Projetada, N15, Santa Maria, Pedra Branca/CE"
    largura_endereco = c.stringWidth(endereco)  # Obter a largura do texto em pontos

    # Calcular as coordenadas para centralizar o texto abaixo do texto anterior
    posicao_horizontal_endereco = (largura_linha_vertical - 25 + largura_linha_vertical_14cm - largura_endereco) / 2
    posicao_vertical_endereco = posicao_vertical - 15  # Distância vertical entre os textos

    # Desenhar o texto na posição calculada
    c.setFont("Helvetica", 10)  # Definir a fonte e o tamanho do texto
    c.setFillColorRGB(0, 0, 0)  # Definir cor preta (RGB)
    c.drawString(posicao_horizontal_endereco, posicao_vertical_endereco, endereco)

    # Escrever o número de telefone
    telefone = "Tel: (88) 9 9694 8264"
    largura_telefone = c.stringWidth(telefone)  # Obter a largura do texto em pontos

    # Calcular as coordenadas para centralizar o texto abaixo do texto anterior
    posicao_horizontal_telefone = (largura_linha_vertical + largura_linha_vertical_14cm - largura_telefone) / 2
    posicao_vertical_telefone = posicao_vertical_endereco - 15  # Distância vertical entre os textos

    # Desenhar o texto na posição calculada
    c.drawString(posicao_horizontal_telefone, posicao_vertical_telefone, telefone)

    # Escrever o endereço do site
    site = "www.gensdiagnostica.com.br"
    largura_site = c.stringWidth(site)  # Obter a largura do texto em pontos

    # Calcular as coordenadas para centralizar o texto abaixo do texto anterior
    posicao_horizontal_site = (largura_linha_vertical + largura_linha_vertical_14cm - largura_site) / 2
    posicao_vertical_site = posicao_vertical_telefone - 15  # Distância vertical entre os textos

    # Desenhar o texto na posição calculada
    c.drawString(posicao_horizontal_site, posicao_vertical_site, site)

    # Adicionar a imagem entre as linhas horizontais superior e de 3cm
    imagem = "https://www.thefirstwrite.com/wp-content/uploads/2021/09/django-framework.jpg"  # Caminho para a imagem
    largura_imagem = 140  # Largura da imagem em pontos
    altura_imagem = 85  # Altura da imagem em pontos
    c.drawImage(imagem, ponto1[0], altura_linha_3cm + 1, width=largura_imagem, height=altura_imagem)

    # Escrever Nº 123456789 entre largura_linha_vertical_14cm e a linha vertical a direita e acima da largura_linha_horizontal_15cm
    numero = f'Nº {exame.codigo}'
    largura_numero = c.stringWidth(numero)  # Obter a largura do texto em pontos

    # Calcular as coordenadas para posicionar o texto entre largura_linha_vertical_14cm e a linha vertical a direita
    posicao_horizontal_numero = largura_linha_vertical_14cm + 5

    # Calcular a coordenada y para posicionar o texto acima da largura_linha_horizontal_15cm
    posicao_vertical_numero = altura_linha_3cm + 1.5 * 28.35 + 17  # Ajuste fino da posição vertical

    # Desenhar o texto na posição calculada
    c.drawString(posicao_horizontal_numero, posicao_vertical_numero, numero)

    # Escrever 'EXAME' entre altura_linha_4cm e altura_linha_3cm, tamanho 18, em negrito
    c.setFont("Helvetica-Bold", 18)  # Definir a fonte em negrito e o tamanho do texto
    c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
    texto_exame = f'{exame}'
    largura_texto_exame = c.stringWidth(texto_exame, "Helvetica-Bold", 18)  # Obter a largura do texto em pontos

    # Calcular as coordenadas para centralizar o texto entre a linha de 4cm e a linha de 3cm
    posicao_horizontal_exame = (ponto1[0] + ponto2[0] - largura_texto_exame) / 2
    posicao_vertical_exame = altura_linha_4cm + 8

    # Desenhar o texto na posição calculada
    c.drawString(posicao_horizontal_exame, posicao_vertical_exame, texto_exame)

    # Escrever 'EXAME' entre altura_linha_4cm e altura_linha_3cm, tamanho 18, em negrito
    c.setFont("Helvetica", 11)  # Definir a fonte em negrito e o tamanho do texto
    c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
    texto_emissao = f'Emissão: {exame.data_alterado.strftime("%d/%m/%Y")}'
    # Calcular as coordenadas para centralizar o texto entre a linha de 4cm e a linha de 3cm
    posicao_horizontal_emissao = largura_linha_vertical_14cm + 5
    posicao_vertical_emissao = altura_linha_4cm + 1.5 * 28.35 + 4

    # Desenhar o texto na posição calculada
    c.drawString(posicao_horizontal_emissao, posicao_vertical_emissao, texto_emissao)


    # Escrever o nome 'Nome'
    c.setFont("Helvetica", 10)  # Definir a fonte e o tamanho do texto
    c.setFillColorRGB(0, 0, 0)  # Definir a cor preta
    c.drawString(ponto1[0] + 5, altura_linha_65cm + 55, f'Nome: {atendimento.paciente}')

    # Escrever o nome 'CPF'
    c.drawString(ponto1[0] + 5, altura_linha_65cm + 35, f'CPF: {atendimento.paciente.cpf}')

    # Escrever o nome 'Data de Nascimento'
    c.drawString(ponto1[0] + 5, altura_linha_65cm + 15, f'Data de Nascimento: {atendimento.paciente.data_nascimento}')

    # Escrever o nome 'Sexo'
    c.drawString(ponto1[0] + 370, altura_linha_65cm + 55, f'Sexo: {atendimento.paciente.sexo}')

    # Escrever o nome 'Data do exame'
    c.drawString(ponto1[0] + 370, altura_linha_65cm + 35, f'Data do exame: {exame.data_cadastro.strftime("%d/%m/%Y")}')

    # Escrever o nome 'Código'
    c.drawString(ponto1[0] + 370, altura_linha_65cm + 15, f'Número do exame: {exame.codigo}')

    referencias = exame.referencias.all()
    contador_interno = 1
    for referencia in referencias:
        c.setFont("Helvetica-Bold", 11)  # Definir a fonte em negrito e o tamanho do texto
        c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
        texto_referencia = f'{referencia.nome_referencia}: {referencia.valor_obtido}'
        # Calcular as coordenadas para centralizar o texto entre a linha de 4cm e a linha de 3cm
        posicao_horizontal_referencia = ponto1[0] + 10
        posicao_vertical_referencia = altura_linha_65cm - (10 * 2 * contador)

        # Desenhar o texto na posição calculada
        c.drawString(posicao_horizontal_referencia, posicao_vertical_referencia, texto_referencia)
        if referencia.fator is False and referencia.esperado is False:
            c.setFont("Helvetica", 11)  # Definir a fonte em negrito e o tamanho do texto
            c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
            c.drawString(ponto1[0] + 300, altura_linha_65cm - (10 * 2 * contador), f'{referencia.limite_inferior} a {referencia.limite_superior}')
        elif referencia.fator is True and referencia.esperado is False:
            fator_ref = referencia.fatores.all()
            contador_interno = 1
            for fator in fator_ref:
                c.setFont("Helvetica", 7)  # Definir a fonte em negrito e o tamanho do texto
                fator_nome = ''
                if fator.nome_fator is None:
                    fator_nome = f'{fator.idade}'
                else:
                    fator_nome = f'{fator.nome_fator}'

                c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
                c.drawString(ponto1[0] + 25, altura_linha_65cm - (10 * 2 * (contador + contador_interno) - (5 * contador_interno)),
                             f'{fator_nome}: {fator.limite_inferior} a {fator.limite_superior}')
                contador_interno += 1
        elif referencia.fator is False and referencia.esperado is True:
            ref_esperado = referencia.padrao.all()
            contador_interno = 1
            for esperado in ref_esperado:
                c.setFont("Helvetica", 7)  # Definir a fonte em negrito e o tamanho do texto
                c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
                c.drawString(ponto1[0] + 25, altura_linha_65cm - (10 * 2 * (contador + contador_interno) - (5 * contador_interno)),
                             f'{esperado.tipo_valor}: {esperado.valor_esperado}')
                contador_interno += 1
        else:
            fator_ref = referencia.fatores.all()
            contador_interno = 1
            for fator in fator_ref:
                c.setFont("Helvetica", 7)  # Definir a fonte em negrito e o tamanho do texto
                fator_nome = ''
                if fator.nome_fator is None:
                    fator_nome = f'{fator.idade}'
                else:
                    fator_nome = f'{fator.nome_fator}'

                c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
                c.drawString(ponto1[0] + 25,
                             altura_linha_65cm - (10 * 2 * (contador + contador_interno) - (5 * contador_interno)),
                             f'{fator_nome}: {fator.limite_inferior} a {fator.limite_superior}')
                contador_interno += 1

            ref_esperado = referencia.padrao.all()
            for esperado in ref_esperado:
                c.setFont("Helvetica", 7)  # Definir a fonte em negrito e o tamanho do texto
                c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
                c.drawString(ponto1[0] + 25,
                             altura_linha_65cm - (10 * 2 * (contador + contador_interno) - (5 * contador_interno)),
                             f'{esperado.tipo_valor}: {esperado.valor_esperado}')
                contador_interno += 1


        contador = contador + contador_interno

    c.setFont("Helvetica-Bold", 11)  # Definir a fonte em negrito e o tamanho do texto
    c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
    observacoes = f'Observações'
    if len(exame.comentario) == 0:
        observacoes = ''
    # Calcular as coordenadas para centralizar o texto entre a linha de 4cm e a linha de 3cm
    posicao_horizontal_observer = ponto1[0] + 10
    posicao_vertical_observer = altura_linha_65cm - (10 * 2 * contador) - 20
    c.drawString(posicao_horizontal_observer, posicao_vertical_observer, observacoes)

    c.setFont("Helvetica", 9)  # Definir a fonte em negrito e o tamanho do texto
    c.setFillColorRGB(0, 0, 0)  # Definir a cor preta (RGB)
    observacoes1 = f'{exame.comentario}'

    # Largura máxima da linha (pode ajustar conforme necessário)
    largura_maxima = 100

    # Dividir o texto em linhas com base na largura máxima
    linhas = textwrap.wrap(observacoes1, width=largura_maxima)

    # Calcular as coordenadas para centralizar o texto entre a linha de 4cm e a linha de 3cm
    posicao_horizontal_observacao = ponto1[0] + 15
    posicao_vertical_observacao = altura_linha_65cm - (10 * 2 * contador) - 35

    # Escrever cada linha individualmente
    for linha in linhas:
        c.drawString(posicao_horizontal_observacao, posicao_vertical_observacao, linha)
        # Atualizar a posição vertical para a próxima linha
        posicao_vertical_observacao -= 15
    # Salvar e finalizar o PDF
    c.save()

    return response

