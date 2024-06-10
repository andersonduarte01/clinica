from django.shortcuts import get_object_or_404, get_list_or_404
from .models import *
from ..agenda.models import Plano


def objeto_exame(pk, sequencia):
    exame_padrao = get_object_or_404(Exame, pk=pk)
    planos_padrao = exame_padrao.planos.all()

    exame_copia = Exame.objects.create(
        nome=exame_padrao.nome,
        material=exame_padrao.material,
        metodo=exame_padrao.metodo,
        comentario=exame_padrao.comentario,
        padrao=False,
        terceirizado=exame_padrao.terceirizado
    )

    for plano1 in planos_padrao:
        for num in sequencia:
            if num == plano1.pk:
                plano2 = Plano.objects.create(
                    plano=plano1.plano,
                    preco=plano1.preco,
                    habilitado=True
                )
                exame_copia.planos.add(plano2)

    exame_copia.save()

    referencias_do_exame_padrao = exame_padrao.referencias.all()

    for ref_padrao in referencias_do_exame_padrao:
        if ref_padrao.fator is False and ref_padrao.esperado is False:
            referencia_exame_copia = ReferenciaExame.objects.create(
                exame=exame_copia,
                nome_referencia=ref_padrao.nome_referencia,
                limite_inferior=ref_padrao.limite_inferior,
                limite_superior=ref_padrao.limite_superior,
                valor_obtido=ref_padrao.valor_obtido,
            )
        elif ref_padrao.fator is True and ref_padrao.esperado is True:
            referencia_exame_copia = ReferenciaExame.objects.create(
                exame=exame_copia,
                nome_referencia=ref_padrao.nome_referencia,
                limite_inferior=ref_padrao.limite_inferior,
                limite_superior=ref_padrao.limite_superior,
                valor_obtido=ref_padrao.valor_obtido,
                fator=True,
                esperado=True
            )
            fatores_referencia_padrao = ref_padrao.fatores.all()

            for fatores_padrao in fatores_referencia_padrao:
                fatores_copia = FatoresReferencia.objects.create(
                    referencia_exame=referencia_exame_copia,
                    nome_fator=fatores_padrao.nome_fator,
                    idade=fatores_padrao.idade,
                    limite_inferior=fatores_padrao.limite_inferior,
                    limite_superior=fatores_padrao.limite_superior
                )

            valores_esperados_padrao = ref_padrao.padrao.all()

            for valor_esperado1 in valores_esperados_padrao:
                valor_esperado_copia = ValorEsperado.objects.create(
                    referencia=referencia_exame_copia,
                    tipo_valor=valor_esperado1.tipo_valor,
                    valor_esperado=valor_esperado1.valor_esperado
                )
        elif ref_padrao.fator is True and ref_padrao.esperado is False:
            referencia_exame_copia = ReferenciaExame.objects.create(
                exame=exame_copia,
                nome_referencia=ref_padrao.nome_referencia,
                limite_inferior=ref_padrao.limite_inferior,
                limite_superior=ref_padrao.limite_superior,
                valor_obtido=ref_padrao.valor_obtido,
                fator=True,
            )
            fatores_referencia_padrao = ref_padrao.fatores.all()

            for fatores_padrao in fatores_referencia_padrao:
                fatores_copia = FatoresReferencia.objects.create(
                    referencia_exame=referencia_exame_copia,
                    nome_fator=fatores_padrao.nome_fator,
                    idade=fatores_padrao.idade,
                    limite_inferior=fatores_padrao.limite_inferior,
                    limite_superior=fatores_padrao.limite_superior
                )
        elif ref_padrao.fator is False and ref_padrao.esperado is True:
            referencia_exame_copia = ReferenciaExame.objects.create(
                exame=exame_copia,
                nome_referencia=ref_padrao.nome_referencia,
                limite_inferior=ref_padrao.limite_inferior,
                limite_superior=ref_padrao.limite_superior,
                valor_obtido=ref_padrao.valor_obtido,
                esperado=True
            )

            valores_esperados_padrao = ref_padrao.padrao.all()

            for valor_esperado1 in valores_esperados_padrao:
                valor_esperado_copia = ValorEsperado.objects.create(
                    referencia=referencia_exame_copia,
                    tipo_valor=valor_esperado1.tipo_valor,
                    valor_esperado=valor_esperado1.valor_esperado
                )

    return exame_copia
