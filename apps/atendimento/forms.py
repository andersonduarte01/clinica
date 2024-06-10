from django import forms
from django.forms import CheckboxSelectMultiple
from .models import OrcamentoExames, Exame


class OrcamentoForm(forms.ModelForm):
    exames = forms.ModelMultipleChoiceField(
        queryset=Exame.objects.filter(padrao=True).order_by('nome'),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )

    planos_selecionados = forms.MultipleChoiceField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = OrcamentoExames
        fields = ['exames', 'forma_pagamento', 'valor_total', 'pagamento', 'comentario']


class OrcamentoFinanceiroForm(forms.ModelForm):
    class Meta:
        model = OrcamentoExames
        fields = ('forma_pagamento', 'valor_total', 'pagamento', 'comentario')


class DateRangeForm(forms.Form):
    data_inicial = forms.DateField(label='Data Inicial', widget=forms.DateInput(attrs={'type': 'date'}))
    data_final = forms.DateField(label='Data Final', widget=forms.DateInput(attrs={'type': 'date'}))

class OrcamentoFormUpdate(forms.ModelForm):
    exames = Exame.objects.filter(padrao=True)
    exame = forms.ModelMultipleChoiceField(
        queryset=exames,
        widget=CheckboxSelectMultiple(),
        required=False,
    )

    nome_paciente_display = forms.CharField(label='Paciente', required=False)

    def __init__(self, *args, **kwargs):
        super(OrcamentoFormUpdate, self).__init__(*args, **kwargs)
        self.fields['nome_paciente_display'].widget.attrs['readonly'] = True
        if self.instance.paciente:
            self.fields['nome_paciente_display'].initial = self.instance.paciente.nome
        exames_associados = self.instance.exame.all()
        self.fields['exame'].queryset = exames_associados

    class Meta:
        model = OrcamentoExames
        fields = ['nome_paciente_display', 'exame', 'forma_pagamento', 'valor_total', 'pagamento', 'comentario']