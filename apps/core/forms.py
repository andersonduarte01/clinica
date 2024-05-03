from django import forms
from django.core.exceptions import ValidationError

from apps.core.models import Usuario, Endereco


class CriarUsuarioForm(forms.ModelForm):
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={'placeholder': 'Senha', 'class': 'custom-text form-control', 'autocomplete': 'off'}))
    password2 = forms.CharField(label='Confirmar Senha', widget=forms.PasswordInput(attrs={'placeholder': 'Repetir Senha', 'class': 'custom-text form-control', 'autocomplete': 'off'}))

    class Meta:
        model = Usuario
        fields = ('nome', 'cpf', 'rg', 'sexo', 'data_nascimento', 'telefone')

        widgets = {
             'nome': forms.TextInput(attrs={'placeholder': 'Nome Completo', 'class': 'custom-text form-control'}),
             'cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00', 'class': 'custom-text form-control'}),
             'telefone': forms.TextInput(attrs={'placeholder': '(88) 9 9999-9999', 'class': 'custom-text form-control'}),
             'rg': forms.TextInput(attrs={'class': 'custom-text form-control'}),
             'sexo': forms.Select(attrs={'class': 'custom-select form-control'}),
             'data_nascimento': forms.TextInput(attrs={'placeholder': 'dd/mm/aaaa', 'class': 'custom-text form-control', 'autocomplete': 'off'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Senhas não coincidem.")
        return password2


class CriarFuncionarioForm(forms.ModelForm):
    usuario = forms.CharField(label='Usuário', widget=forms.TextInput(attrs={'placeholder': 'Usuário', 'class': 'custom-text form-control', 'autocomplete': 'off'}))
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={'placeholder': 'Senha', 'class': 'custom-text form-control', 'autocomplete': 'off'}))
    password2 = forms.CharField(label='Confirmar Senha', widget=forms.PasswordInput(attrs={'placeholder': 'Repetir Senha', 'class': 'custom-text form-control', 'autocomplete': 'off'}))

    class Meta:
        model = Usuario
        fields = ('nome', 'cpf', 'rg', 'sexo', 'data_nascimento', 'telefone', 'funcionario', 'adm', 'doutor' )

        widgets = {
             'nome': forms.TextInput(attrs={'placeholder': 'Nome Completo', 'class': 'custom-text form-control'}),
             'cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00', 'class': 'custom-text form-control'}),
             'telefone': forms.TextInput(attrs={'placeholder': '(88) 9 9999-9999', 'class': 'custom-text form-control'}),
             'rg': forms.TextInput(attrs={'class': 'custom-text form-control'}),
             'sexo': forms.Select(attrs={'class': 'custom-select form-control'}),
             'data_nascimento': forms.TextInput(attrs={'placeholder': 'dd/mm/aaaa', 'class': 'custom-text form-control', 'autocomplete': 'off'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Senhas não coincidem.")
        return password2


class EnderecoForm(forms.ModelForm):
    class Meta:
        model = Endereco
        fields = ('rua', 'numero', 'complemento', 'bairro', 'cep', 'cidade', 'estado')

