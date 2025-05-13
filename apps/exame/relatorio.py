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


def configurar_margens(c):
    """
    Função para configurar as margens do documento PDF e retornar as margens e os limites de largura e altura.
    """
    # Definindo as margens
    margem_esquerda = 40  # Margem esquerda
    margem_direita = 40  # Margem direita
    margem_superior = 40  # Margem superior
    margem_inferior = 40  # Margem inferior

    # Configurando o tamanho da página
    c.setPageSize(A4)

    largura, altura = A4  # Obtém o tamanho da página (largura e altura)

    # Calculando o espaço disponível dentro da página para o conteúdo
    largura_disponivel = largura - margem_esquerda - margem_direita
    altura_disponivel = altura - margem_superior - margem_inferior

    return margem_esquerda, margem_direita, margem_superior, margem_inferior, largura_disponivel, altura_disponivel

def escrever_texto(c, texto, x, y, font="Helvetica", font_size=10, color=(0, 0, 0)):
    """
    Função para escrever o texto no PDF.
    """
    c.setFont(font, font_size)
    c.setFillColorRGB(*color)
    c.drawString(x, y, texto)


def escrever_dados_clinica(c, altura):
    """
    Função para escrever as informações da clínica no cabeçalho, centralizado no topo.
    """
    # Texto da clínica
    texto = "Gen's Diagnóstica"
    largura_texto = c.stringWidth(texto, "Helvetica-Bold", 18)
    x = (A4[0] - largura_texto) / 2  # Centraliza o texto horizontalmente
    escrever_texto(c, texto=texto, x=x, y=(altura - 10), font="Helvetica-Bold", font_size=18, color=(0, 0.5, 0))

    # Texto do laboratório
    texto_laboratorio = "Laboratório de análises clínicas"
    largura_texto_laboratorio = c.stringWidth(texto_laboratorio, "Helvetica", 9)
    x_laboratorio = (A4[0] - largura_texto_laboratorio) / 2
    escrever_texto(c, texto=texto_laboratorio, x=x_laboratorio, y=(altura - 30), font_size=9, color=(0, 0.7, 0.3))

    # Endereço
    endereco = "Rua Fortunato Silva, Nº164, Pedra Branca/CE"
    largura_endereco = c.stringWidth(endereco, "Helvetica", 10)
    x_endereco = (A4[0] - largura_endereco) / 2
    escrever_texto(c, texto=endereco, x=x_endereco, y=(altura - 45), font_size=10, color=(0, 0, 0))

    # Telefone
    telefone = "Tel: (88) 9 9995 0037 / 3515 1822"
    largura_telefone = c.stringWidth(telefone, "Helvetica", 10)
    x_telefone = (A4[0] - largura_telefone) / 2
    escrever_texto(c, texto=telefone, x=x_telefone, y=(altura - 60), font_size=10, color=(0, 0, 0))

    # Site
    site = "gensdiagnostica.com.br"
    largura_site = c.stringWidth(site, "Helvetica", 10)
    x_site = (A4[0] - largura_site) / 2
    escrever_texto(c, texto=site, x=x_site, y=(altura - 75), font_size=10, color=(0, 0, 0))


def escrever_exame_info(c, altura, exame):

    texto_codigo = f'Nº {exame.codigo}'
    largura_codigo = c.stringWidth(texto_codigo, "Helvetica", 11)
    x_codigo = (A4[0] - largura_codigo) / 2
    escrever_texto(c, texto=texto_codigo, x=x_codigo, y=(altura + 57), font_size=11, color=(0, 0, 0))

    # Data de emissão
    texto_emissao = f'Emissão: {exame.data_alterado.strftime("%d/%m/%Y")}'
    largura_emissao = c.stringWidth(texto_emissao, "Helvetica", 11)
    x_emissao = (A4[0] - largura_emissao) / 2
    escrever_texto(c, texto=texto_emissao, x=x_emissao, y=(altura + 18), font_size=11, color=(0, 0, 0))