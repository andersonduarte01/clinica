from django.db import models
from django.utils import timezone

from ..core.models import Usuario


class Plano(models.Model):
    plano = models.CharField(verbose_name='Plano', max_length=150)
    preco = models.DecimalField(verbose_name='Preço', max_digits=5, decimal_places=2, error_messages={'invalid': 'Por favor, insira um preço válido.'})
    habilitado = models.BooleanField(default=False)

    def __str__(self):
        return self.plano

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'


class OrdemChegada(models.Model):
    STATUS_ATENDIMENTO = [
        ('AGUARDANDO', 'AGUARDANDO'),
        ('ATENDIDO', 'ATENDIDO'),
        ('CANCELADO', 'CANCELADO'),
    ]
    nome_paciente = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING)
    sequencia = models.CharField(max_length=12, unique=True)
    data = models.DateField()
    status_atendido = models.CharField(max_length=15, verbose_name='Atendimento', choices=STATUS_ATENDIMENTO, default='AGUARDANDO')

    class Meta:
        ordering = ['sequencia']

    def save(self, *args, **kwargs):
        if not self.sequencia:  # Se a sequência não estiver definida
            data_hora_atual = timezone.now()
            ano = str(data_hora_atual.year)
            mes = str(data_hora_atual.month).zfill(2)
            dia = str(data_hora_atual.day).zfill(2)
            numero_sequencial = f"{dia}{mes}{ano}"
            # Encontra o último número sequencial para o dia atual
            ultimo_numero_sequencial = OrdemChegada.objects.filter(
                sequencia__startswith=numero_sequencial).order_by('-sequencia').first()
            if ultimo_numero_sequencial:
                ultimo_numero = int(ultimo_numero_sequencial.sequencia[-4:])
                novo_numero = str(ultimo_numero + 1).zfill(4)
                self.sequencia = f"{numero_sequencial}{novo_numero}"
            else:
                self.sequencia = f"{numero_sequencial}0001"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome_paciente.nome

    @classmethod
    def fila_dia_aguardando(cls, data):
        return cls.objects.filter(data=data, status_atendido='AGUARDANDO').count()

    @classmethod
    def fila_dia_atendido(cls, data):
        return cls.objects.filter(data=data, status_atendido='ATENDIDO').count()

    @classmethod
    def fila_dia_total(cls, data):
        return cls.objects.filter(data=data).count()

