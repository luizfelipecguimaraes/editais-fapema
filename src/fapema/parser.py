import re
import unicodedata
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from fapema.scraper import buscar_pagina


TIMEZONE = ZoneInfo("America/Fortaleza")

DATA_NUMERICA_RE = re.compile(
    r"(?<!\d)(\d{1,2}/\d{1,2}/\d{4})(?!\d)"
)

DATA_EXTENSO_RE = re.compile(
    r"\b(\d{1,2}) de "
    r"(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|"
    r"setembro|outubro|novembro|dezembro) de "
    r"(\d{4})\b",
    re.IGNORECASE,
)

HORA_RE = re.compile(
    r"\b([01]?\d|2[0-3])h(?::?([0-5]\d))?\b",
    re.IGNORECASE,
)

MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

TERMOS_PRAZO = (
    "periodo de submissao",
    "periodo para submissao",
    "prazo de submissao",
    "prazo final para submissao",
    "submissao online",
    "submissao on-line",
    "submissao de projetos",
    "submissao das ideias",
    "submissao dos projetos",
    "periodo de inscricao",
    "prazo de inscricao",
    "inscricoes ate",
    "prazo para envio eletronico das propostas",
    "data limite para submissao",
    "data limite para preenchimento e envio",
)


def normalizar_texto(texto: str) -> str:
    """Converte o texto para minúsculas e remove acentos."""
    texto = texto.lower()

    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caractere)
    )


def contem_termo_prazo(texto: str) -> bool:
    texto_normalizado = normalizar_texto(texto)

    return any(
        termo in texto_normalizado
        for termo in TERMOS_PRAZO
    )


def extrair_titulo(soup: BeautifulSoup) -> str | None:
    titulo = soup.find("h1")

    if titulo is None:
        return None

    return titulo.get_text(" ", strip=True)


def extrair_data_publicacao(soup: BeautifulSoup) -> date | None:
    texto = soup.get_text(" ", strip=True)

    resultado = DATA_EXTENSO_RE.search(texto)

    if resultado is None:
        return None

    dia = int(resultado.group(1))
    mes_nome = resultado.group(2).lower()
    ano = int(resultado.group(3))

    return date(
        year=ano,
        month=MESES[mes_nome],
        day=dia,
    )


def encontrar_bloco_prazo(soup: BeautifulSoup) -> str | None:
    """
    Procura o trecho que contém o prazo de submissão/inscrição.
    Primeiro tenta linhas de tabela e depois o texto da página.
    """

    # Caso mais estruturado: cronograma em tabela
    for linha in soup.find_all("tr"):
        texto = linha.get_text(" ", strip=True)

        if contem_termo_prazo(texto):
            return texto

    # Fallback: texto separado em linhas
    linhas = [
        linha.strip()
        for linha in soup.get_text("\n", strip=True).splitlines()
        if linha.strip()
    ]

    for indice, linha in enumerate(linhas):
        if not contem_termo_prazo(linha):
            continue

        # A data pode estar na mesma linha
        if DATA_NUMERICA_RE.search(linha):
            return linha

        # Ou na célula/linha imediatamente seguinte
        for proxima in linhas[indice + 1:indice + 4]:
            if DATA_NUMERICA_RE.search(proxima):
                return f"{linha} {proxima}"

    return None


def extrair_prazo_final(bloco: str | None) -> date | None:
    if bloco is None:
        return None

    datas_encontradas = DATA_NUMERICA_RE.findall(bloco)

    if not datas_encontradas:
        return None

    datas = [
        datetime.strptime(valor, "%d/%m/%Y").date()
        for valor in datas_encontradas
    ]

    # Se houver início e fim, queremos a data final.
    return max(datas)


def extrair_hora_final(bloco: str | None) -> time | None:
    if bloco is None:
        return None

    resultados = HORA_RE.findall(bloco)

    if not resultados:
        return None

    horas = []

    for hora_texto, minuto_texto in resultados:
        hora = int(hora_texto)
        minuto = int(minuto_texto or 0)

        horas.append(
            time(
                hour=hora,
                minute=minuto,
            )
        )

    return max(horas)


def calcular_status(
    prazo_final: date | None,
    prazo_hora: time | None,
) -> str:
    if prazo_final is None:
        return "indeterminado"

    agora = datetime.now(TIMEZONE)

    if prazo_hora is not None:
        encerramento = datetime.combine(
            prazo_final,
            prazo_hora,
            tzinfo=TIMEZONE,
        )
    else:
        encerramento = datetime.combine(
            prazo_final,
            time(23, 59, 59),
            tzinfo=TIMEZONE,
        )

    if agora <= encerramento:
        return "aberto"

    return "encerrado"


def parsear_edital(url: str) -> dict:
    html = buscar_pagina(url)
    soup = BeautifulSoup(html, "html.parser")

    titulo = extrair_titulo(soup)
    publicado_em = extrair_data_publicacao(soup)

    bloco_prazo = encontrar_bloco_prazo(soup)

    prazo_final = extrair_prazo_final(bloco_prazo)
    prazo_hora = extrair_hora_final(bloco_prazo)

    status = calcular_status(
        prazo_final,
        prazo_hora,
    )

    return {
        "titulo": titulo,
        "url": url,
        "publicado_em": (
            publicado_em.isoformat()
            if publicado_em
            else None
        ),
        "prazo_final": (
            prazo_final.isoformat()
            if prazo_final
            else None
        ),
        "prazo_hora": (
            prazo_hora.strftime("%H:%M")
            if prazo_hora
            else None
        ),
        "status": status,
    }
