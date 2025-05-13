from django.db import models
from django.utils import timezone

from .validacao import validate_pdf_extension
from ..agenda.models import Plano
from ..core.models import Usuario


class Exame(models.Model):
    STATUS_EXAME = [
        ('AGUARDANDO', 'AGUARDANDO'),
        ('REALIZADO', 'REALIZADO'),
        ('CANCELADO', 'CANCELADO'),
    ]
    nome = models.CharField(verbose_name='Nome', max_length=180)
    material = models.CharField(verbose_name='Material', max_length=120)
    metodo = models.CharField(verbose_name='Metodo', max_length=120)
    codigo = models.CharField(max_length=12, unique=True)
    anexo = models.FileField(upload_to='exames/terceirizados', verbose_name='Anexar arquivo', null=True, blank=True,
                             help_text='Anexar exame terceirizado',
                             max_length=300, validators=[validate_pdf_extension])
    bio_medico = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, verbose_name='Biomédico(a)', null=True, blank=True)
    planos = models.ManyToManyField(Plano, related_name='planos_list')
    status_exame = models.CharField(verbose_name='Status do Exame', max_length=20, choices=STATUS_EXAME, default='AGUARDANDO')
    comentario = models.TextField(verbose_name='Observações', null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_alterado = models.DateTimeField(auto_now=True)
    terceirizado = models.BooleanField(default=False)
    padrao = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)


    def __str__(self):
        return self.nome


    def save(self, *args, **kwargs):
        if not self.codigo:  # Se o código não estiver definido
            data_hora_atual = timezone.now()
            ano_mes_corrente = data_hora_atual.strftime('%m%Y')
            # Encontra o último número sequencial para o ano e mês correntes
            ultimo_exame_mes_ano_corrente = Exame.objects.filter(
                codigo__startswith=ano_mes_corrente).order_by('-codigo').first()
            if ultimo_exame_mes_ano_corrente:
                ultimo_numero = int(ultimo_exame_mes_ano_corrente.codigo[-6:]) + 1
            else:
                ultimo_numero = 1
            self.codigo = f"{ano_mes_corrente}{str(ultimo_numero).zfill(6)}"

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'EXAME'
        verbose_name_plural = 'EXAMES'


class ReferenciaExame(models.Model):
    exame = models.ForeignKey(Exame, on_delete=models.CASCADE, verbose_name='Exame', related_name='referencias')
    nome_referencia = models.CharField(verbose_name='Nome Referência', max_length=220)
    limite_inferior = models.CharField(verbose_name='Limite Inferior', max_length=80, null=True, blank=True)
    limite_superior = models.CharField(verbose_name='Limite Superior', max_length=80, null=True, blank=True)
    valor_obtido = models.CharField(verbose_name='Valor obtido', max_length=80, null=True, blank=True)
    fator = models.BooleanField(default=False, verbose_name='Fator')
    esperado = models.BooleanField(default=False, verbose_name='Valor padrão')


class FatoresReferencia(models.Model):
    referencia_exame = models.ForeignKey(ReferenciaExame, on_delete=models.CASCADE, related_name='fatores')
    nome_fator = models.CharField(verbose_name='Fator', max_length=100, null=True, blank=True)
    idade = models.CharField(verbose_name='Idade', max_length=50, null=True, blank=True)
    limite_inferior = models.CharField(verbose_name='Limite Inferior', max_length=80, null=True, blank=True)
    limite_superior = models.CharField(verbose_name='Limite Superior', max_length=80, null=True, blank=True)
    fator_obtido = models.CharField(verbose_name='Fator obtido', max_length=80, null=True, blank=True, default=None)


class ValorEsperado(models.Model):
    referencia = models.ForeignKey(ReferenciaExame, on_delete=models.CASCADE, related_name='padrao')
    tipo_valor = models.CharField(verbose_name='Nome', max_length=120)
    valor_esperado = models.CharField(verbose_name='Padrão', max_length=120)
    esperado_obtido = models.CharField(verbose_name='Valor obtido', max_length=80, null=True, blank=True, default=None)


class GrupoExame(models.Model):
    nome = models.CharField(verbose_name='Nome do Grupo/Área', max_length=180, unique=True)
    descricao = models.TextField(verbose_name='Descrição', null=True, blank=True)
    ativo = models.BooleanField(default=True)
    exames = models.ManyToManyField('Exame', related_name='grupos', verbose_name='Exames')

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Grupo de Exames'
        verbose_name_plural = 'Grupos de Exames'
