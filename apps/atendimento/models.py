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

    @classmethod
    def calcular_total_por_data_e_pagamento(cls, data_cadastro, pagamento):
        total = Decimal('0.00')
        orcamentos = cls.objects.filter(data_cadastro=data_cadastro, pagamento=pagamento)
        for orcamento in orcamentos:
            total += orcamento.calcular_total()
        return total, orcamentos

    @classmethod
    def calcular_total_por_periodo(cls, data_inicio, data_fim):
        total = Decimal('0.00')
        if data_inicio == data_fim:
            orcamentos = cls.objects.filter(data_cadastro=data_inicio)
        else:
            orcamentos = cls.objects.filter(data_cadastro__range=(data_inicio, data_fim))

        for orcamento in orcamentos:
            total += orcamento.calcular_total()
        return total, orcamentos

    @classmethod
    def total_atendimentos_diarios(cls):
        return cls.objects.filter(data_cadastro=date.today()).count()

    @classmethod
    def total_atendimentos_semanal(cls):
        return cls.objects.filter(data_cadastro=date.today()).count()

    @classmethod
    def algum_exame_realizado(cls, orcamento):
        return orcamento.exame.filter(status_exame='REALIZADO').exists()
