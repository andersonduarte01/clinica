from django import forms
from django.forms import TextInput
from ..exame.models import Exame, ReferenciaExame, FatoresReferencia, ValorEsperado


class ExameForm(forms.ModelForm):
    class Meta:
        model = Exame
        fields = ('nome', 'material', 'metodo', 'comentario')


class ExameFormUpdate(forms.ModelForm):
    planos_relacionados = forms.ModelChoiceField(queryset=Exame.objects.none())

    class Meta:
        model = Exame
        fields = ()

    def __init__(self, *args, **kwargs):
        exame_instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        if exame_instance:
            exames_padrao = Exame.objects.filter(padrao=True, nome=exame_instance.nome)
            if exames_padrao.exists():
                self.fields['planos_relacionados'].queryset = exames_padrao.first().planos.all()


class ReferenciaForm(forms.ModelForm):
    class Meta:
        model = ReferenciaExame
        fields = ('nome_referencia', 'limite_inferior', 'limite_superior')
        widgets = {
            'nome_referencia': TextInput(
                attrs={'class': 'form-control'}),
            'limite_inferior': TextInput(
                attrs={'class': 'form-control'}),
            'limite_superior': TextInput(
                attrs={'class': 'form-control'}),
        }


class FatorReferenciaForm(forms.ModelForm):
    class Meta:
        model = FatoresReferencia
        fields = ('nome_fator', 'idade', 'limite_inferior', 'limite_superior')


class ValorEsperadoForm(forms.ModelForm):
    class Meta:
        model = ValorEsperado
        fields = ('tipo_valor', 'valor_esperado')


class ExameAtendimentoForm(forms.ModelForm):
    exames = forms.ModelMultipleChoiceField(
        queryset=Exame.objects.filter(padrao=True),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )

    planos_selecionados = forms.MultipleChoiceField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Exame
        fields = ['exames',]


# Area Medica
class ExameMedicForm(forms.ModelForm):
    class Meta:
        model = Exame
        fields = ('medico', 'comentario', 'status_exame')


class ReferenciaExameForm(forms.ModelForm):
    class Meta:
        model = ReferenciaExame
        fields = ['valor_obtido', ]
        widgets = {
            'valor_obtido': forms.TextInput(attrs={'class': 'form-control'}),
        }
