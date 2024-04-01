from _decimal import Decimal
from django.db import models
from ..core.models import Usuario
from ..exame.models import Exame
from datetime import date


class OrcamentoExames(models.Model):
    FORMA_DE_PAGAMENTO = [
        ('DINHEIRO', 'DINHEIRO'),
        ('CARTAO_CREDITO', 'CARTAO_CREDITO'),
        ('CARTAO_DEBITO', 'CARTAO_DEBITO'),
        ('PIX', 'PIX'),
        ('OUTRO', 'OUTRO'),
    ]
    PAGAMENTO = [
        ('PENDENTE', 'PENDENTE'),
        ('PAGO', 'PAGO'),
        ('PARCIAL', 'PARCIAL'),
        ('OUTRO', 'OUTRO'),
    ]
    paciente = models.ForeignKey(Usuario, verbose_name='Paciente', on_delete=models.DO_NOTHING,
                                    related_name='r_paciente')
    exame = models.ManyToManyField(Exame, verbose_name='Exame', related_name='r_exame')
    valor_total = models.DecimalField(verbose_name='Total', max_digits=6, decimal_places=2)
    forma_pagamento = models.CharField(verbose_name='Forma de Pagamento',
                                       max_length=40, choices=FORMA_DE_PAGAMENTO, default='Selecionar')
    pagamento = models.CharField(verbose_name='Pagamento', max_length=20, choices=PAGAMENTO, default='PENDENTE')
    comentario = models.TextField(verbose_name='Observação', null=True, blank=True)
    cancelar = models.BooleanField(default=False)
    data_cadastro = models.DateField(verbose_name='Data Exames', default=date.today)
    data_alterado = models.DateTimeField(verbose_name='Data Modoficação', auto_now=True)


    def calcular_total(self):
        total = Decimal('0.00')
        for exame in self.exame.all():
            plano = exame.planos.first()
            total += plano.preco
        return total
