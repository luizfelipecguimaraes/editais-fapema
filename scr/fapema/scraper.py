from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


CATEGORY_URL = "https://www.fapema.br/category/editais/editais-em-aberto/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )
}


def buscar_pagina(url: str) -> str:
    """Baixa o HTML de uma página da FAPEMA."""
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    return response.text


def extrair_editais(html: str) -> list[dict]:
    """Extrai título e URL dos editais encontrados em uma página."""
    soup = BeautifulSoup(html, "html.parser")

    editais = []
    urls_encontradas = set()

    for titulo_element in soup.find_all("h3"):
        link_element = titulo_element.find("a", href=True)

        if link_element is None:
            continue

        titulo = link_element.get_text(" ", strip=True)
        url = urljoin(CATEGORY_URL, link_element["href"])

        # Evita links da própria categoria/paginação
        if "/category/" in url:
            continue

        # Evita duplicidade
        if url in urls_encontradas:
            continue

        urls_encontradas.add(url)

        editais.append(
            {
                "titulo": titulo,
                "url": url,
            }
        )

    return editais


def encontrar_proxima_pagina(html: str) -> str | None:
    """Retorna a URL da próxima página da categoria, quando existir."""
    soup = BeautifulSoup(html, "html.parser")

    for link in soup.find_all("a", href=True):
        texto = link.get_text(" ", strip=True).lower()
        href = link["href"]

        if (
            "next" in texto
            and "/category/editais/editais-em-aberto/page/" in href
        ):
            return urljoin(CATEGORY_URL, href)

    return None


def listar_editais() -> list[dict]:
    """Percorre todas as páginas da categoria Editais Abertos."""
    url_atual = CATEGORY_URL

    editais_encontrados = {}
    paginas_visitadas = set()

    while url_atual and url_atual not in paginas_visitadas:
        paginas_visitadas.add(url_atual)

        html = buscar_pagina(url_atual)

        editais_da_pagina = extrair_editais(html)

        for edital in editais_da_pagina:
            editais_encontrados[edital["url"]] = edital

        url_atual = encontrar_proxima_pagina(html)

    return list(editais_encontrados.values())
