from django import forms
from django.forms import Select, NumberInput, DateInput, TextInput

from ..agenda.models import Plano, OrdemChegada
from ..core.models import Usuario


class PlanoForm(forms.ModelForm):
    class Meta:
        model = Plano
        fields = ('plano', 'preco')

        widgets = {
            'plano': TextInput(
                attrs={'class': 'form-control'}),
            'preco': NumberInput(
                attrs={'class': 'form-control'}),
        }


class OrdemChegadaForm(forms.ModelForm):
    nome_paciente_display = forms.CharField(label='Nome do Paciente', required=False)
    class Meta:
        model = OrdemChegada
        fields = ['nome_paciente_display', 'data']
        widgets = {
            'data': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        paciente_pk = kwargs.pop('paciente_pk', None)  # Remove o paciente_pk do kwargs
        super().__init__(*args, **kwargs)
        if paciente_pk:
            paciente = Usuario.objects.get(pk=paciente_pk)
            self.fields['nome_paciente_display'].widget.attrs['readonly'] = True
            self.fields['nome_paciente_display'].initial = paciente.nome



class OrdemChegadaUpdateForm(forms.ModelForm):
    nome_paciente_display = forms.CharField(label='Nome do Paciente', required=False)

    def __init__(self, *args, **kwargs):
        super(OrdemChegadaUpdateForm, self).__init__(*args, **kwargs)
        # Define o campo nome_paciente_display como somente leitura
        self.fields['nome_paciente_display'].widget.attrs['readonly'] = True
        if self.instance.nome_paciente:
            self.fields['nome_paciente_display'].initial = self.instance.nome_paciente.nome

    class Meta:
        model = OrdemChegada
        fields = ('nome_paciente_display', 'status_atendido', 'data')
