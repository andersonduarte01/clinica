from django import forms
from django.forms import CheckboxSelectMultiple
from .models import OrcamentoExames, Exame


class OrcamentoForm1(forms.ModelForm):
    planos_selecionados = forms.MultipleChoiceField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = OrcamentoExames
        fields = ['exame', 'forma_pagamento', 'valor_total', 'pagamento', 'comentario']

    def __init__(self, *args, **kwargs):
        exames_selecionados = kwargs.pop('exames_selecionados', None)
        super().__init__(*args, **kwargs)
        if exames_selecionados:
            self.fields['exame'].queryset = Exame.objects.filter(id__in=exames_selecionados)




class OrcamentoForm(forms.ModelForm):
    planos_selecionados = forms.MultipleChoiceField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = OrcamentoExames
        fields = ['forma_pagamento', 'valor_total', 'pagamento', 'comentario']


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