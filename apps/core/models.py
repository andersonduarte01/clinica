from django.contrib.auth.models import User
from django.db import models
from cpf_field.models import CPFField


class Usuario(models.Model):
    SEXO = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(verbose_name='Nome', max_length=155)
    cpf = CPFField('CPF')
    rg = models.CharField(verbose_name='RG', max_length=25, blank=True, null=True)
    sexo = models.CharField(verbose_name='Sexo', max_length=20, choices=SEXO)
    telefone = models.CharField(verbose_name='Telefone', max_length=20)
    data_nascimento = models.CharField(verbose_name='Data de Nascimento', max_length=50)
    cadastrado = models.DateTimeField(auto_now_add=True)
    atualizado = models.DateTimeField(auto_now=True)
    funcionario = models.BooleanField(verbose_name='Funcionário?', default=False)
    adm = models.BooleanField(verbose_name='Administrador?', default=False)
    doutor = models.BooleanField(verbose_name='Doutor(a)?', default=False)
    paciente = models.BooleanField(verbose_name='Paciente?', default=False)
    status = models.BooleanField(verbose_name='Status', default=True)


    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'


class Endereco(models.Model):
    pessoa = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    rua = models.CharField(verbose_name='Rua', max_length=100)
    numero = models.CharField(verbose_name='Número', max_length=20, null=True, blank=True)
    complemento = models.CharField(verbose_name='Complemento', max_length=200, blank=True, null=True)
    bairro = models.CharField(verbose_name='Bairro', max_length=100)
    cep = models.CharField(verbose_name='Cep', max_length=10, blank=True)
    cidade = models.CharField(verbose_name='Cidade', max_length=100, blank=True)
    estado = models.CharField(verbose_name='Estado', max_length=30, blank=True)

    def __str__(self):
        return self.rua

    class Meta:
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'
