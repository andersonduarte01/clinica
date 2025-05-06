from reportlab.lib.pagesizes import A4


def desenhar_retangulo(c, largura_cm=19, altura_cm=27):

    # Dimensões da página A4 em pontos
    largura_pagina, altura_pagina = A4

    # Converter dimensões de cm para pontos
    largura_paralelogramo = largura_cm * 28.35  # 1 cm = 28.35 pontos
    altura_paralelogramo = altura_cm * 28.35  # 1 cm = 28.35 pontos

    # Calcular as coordenadas dos pontos para centralizar o retângulo
    margem_esquerda = (largura_pagina - largura_paralelogramo) / 2
    margem_superior = (altura_pagina - altura_paralelogramo) / 2

    ponto1 = (margem_esquerda, margem_superior)
    ponto2 = (ponto1[0] + largura_paralelogramo, margem_superior)
    ponto3 = (ponto1[0] + largura_paralelogramo, ponto1[1] + altura_paralelogramo)
    ponto4 = (ponto1[0], ponto1[1] + altura_paralelogramo)

    # Configurar as bordas do retângulo
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cinza claro
    c.setLineWidth(2)  # Largura da linha

    # Desenhar as linhas do retângulo
    c.line(ponto1[0], ponto1[1], ponto2[0], ponto2[1])  # Linha superior
    c.line(ponto2[0], ponto2[1], ponto3[0], ponto3[1])  # Linha direita
    c.line(ponto3[0], ponto3[1], ponto4[0], ponto4[1])  # Linha inferior
    c.line(ponto4[0], ponto4[1], ponto1[0], ponto1[1])  # Linha esquerda

    # Retornar os pontos
    return ponto1, ponto2, ponto3, ponto4


def adicionar_linha_paralela(c, ponto3, ponto4, intervalo=28.35):
    """
    Desenha uma única linha paralela a partir de um ponto de referência, com um intervalo especificado.

    :param c: Canvas do ReportLab
    :param ponto1: O ponto inicial da linha de referência (ex: ponto1 do retângulo)
    :param ponto2: O ponto final da linha de referência (ex: ponto2 do retângulo)
    :param intervalo: A distância entre a linha de referência e a linha paralela em pontos (padrão: 1 cm, ou 28.35 pontos)
    """
    # Calcular a posição da linha paralela com base no intervalo
    altura_linha = ponto3[1] - intervalo

    # Configurar o estilo da linha
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cor cinza claro
    c.setLineWidth(2)  # Largura da linha

    # Desenhar a linha paralela
    c.line(ponto3[0], altura_linha, ponto4[0], altura_linha)

    return altura_linha


def adicionar_linha_vertical(c, ponto1, ponto3, altura, largura_intervalo=28.35):
    """
    Desenha uma única linha vertical delimitada pelas linhas paralelas no retângulo.

    :param c: Canvas do ReportLab
    :param ponto1: O ponto inicial (superior esquerdo) do retângulo ou região de referência
    :param ponto3: O ponto inferior direito do retângulo ou região de referência
    :param largura_intervalo: A distância entre a linha de referência e a linha vertical, em pontos (padrão: 1 cm, ou 28.35 pontos)
    """
    # Calcular a posição da linha vertical com base no intervalo
    largura_linha_vertical = ponto1[0] + largura_intervalo

    # Configurar o estilo da linha
    c.setStrokeColorRGB(0.8, 0.8, 0.8)  # Cor cinza claro
    c.setLineWidth(2)  # Largura da linha

    # Desenhar a linha vertical dentro do intervalo delimitado
    c.line(largura_linha_vertical, ponto3[1], largura_linha_vertical, (ponto3[1] - altura))
    return largura_linha_vertical


def escrever_texto(c, texto, x, y, font="Helvetica", font_size=10, color=(0, 0, 0)):
    """
    Desenha um texto em uma posição específica no canvas.

    Args:
        c (Canvas): O objeto canvas do ReportLab.
        texto (str): O texto a ser adicionado.
        x (float): A coordenada horizontal (em pontos).
        y (float): A coordenada vertical (em pontos).
        font (str): A fonte do texto (padrão: Helvetica).
        font_size (int): O tamanho da fonte (padrão: 10).
        color (tuple): Uma tupla RGB com os valores de cor (padrão: preto).
    """
    c.setFont(font, font_size)
    c.setFillColorRGB(*color)
    c.drawString(x, y, texto)
