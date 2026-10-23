
import logging
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup


CATEGORY_URL = (
    "https://www.fapema.br/category/editais/editais-em-aberto/"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )
}

logger = logging.getLogger(__name__)


def criar_sessao() -> requests.Session:
    """Cria uma sessão HTTP com tentativas automáticas."""

    retries = Retry(
        total=5,
        connect=5,
        read=3,
        status=3,
        backoff_factor=2,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],
        allowed_methods=frozenset(["GET"]),
        respect_retry_after_header=True,
    )

    sessao = requests.Session()

    adapter = HTTPAdapter(
        max_retries=retries,
        pool_connections=5,
        pool_maxsize=5,
    )

    sessao.mount("https://", adapter)
    sessao.mount("http://", adapter)

    return sessao


SESSAO = criar_sessao()


def buscar_pagina(url: str) -> str:
    """Baixa o HTML de uma página da FAPEMA."""

    logger.info("Acessando página: %s", url)

    try:
        response = SESSAO.get(
            url,
            headers=HEADERS,
            timeout=(10, 30),
        )

        response.raise_for_status()

        logger.info(
            "Página carregada: %s | HTTP %s",
            url,
            response.status_code,
        )

        return response.text

    except requests.exceptions.RequestException:
        logger.exception(
            "Falha ao acessar a página após as tentativas: %s",
            url,
        )
        raise


def extrair_editais(html: str) -> list[dict]:
    """Extrai título e URL dos editais encontrados."""

    soup = BeautifulSoup(html, "html.parser")

    editais = []
    urls_encontradas = set()

    for titulo_element in soup.find_all("h3"):
        link_element = titulo_element.find(
            "a",
            href=True,
        )

        if link_element is None:
            continue

        titulo = link_element.get_text(
            " ",
            strip=True,
        )

        url = urljoin(
            CATEGORY_URL,
            link_element["href"],
        )

        if not titulo:
            continue

        # Evita links de categorias e paginação.
        if "/category/" in url:
            continue

        # Evita duplicatas.
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


def encontrar_proxima_pagina(
    html: str,
) -> str | None:
    """Identifica a próxima página de editais."""

    soup = BeautifulSoup(html, "html.parser")

    for link in soup.find_all(
        "a",
        href=True,
    ):
        texto = link.get_text(
            " ",
            strip=True,
        ).lower()

        href = link["href"]

        if (
            "next" in texto
            and "/category/editais/editais-em-aberto/page/" in href
        ):
            return urljoin(
                CATEGORY_URL,
                href,
            )

    return None


def listar_editais() -> list[dict]:
    """Percorre todas as páginas de editais abertos."""

    url_atual = CATEGORY_URL

    editais_encontrados = {}
    paginas_visitadas = set()
    numero_pagina = 0

    while (
        url_atual
        and url_atual not in paginas_visitadas
    ):
        numero_pagina += 1

        logger.info(
            "Processando página %s: %s",
            numero_pagina,
            url_atual,
        )

        paginas_visitadas.add(
            url_atual
        )

        # Se a conexão falhar, a exceção será
        # propagada para o main.py.
        html = buscar_pagina(
            url_atual
        )

        editais_da_pagina = extrair_editais(
            html
        )

        logger.info(
            "Página %s: %s editais encontrados",
            numero_pagina,
            len(editais_da_pagina),
        )

        for edital in editais_da_pagina:
            editais_encontrados[
                edital["url"]
            ] = edital

        url_atual = encontrar_proxima_pagina(
            html
        )

    logger.info(
        "Coleta concluída: %s páginas e %s editais únicos",
        numero_pagina,
        len(editais_encontrados),
    )

    return list(
        editais_encontrados.values()
    )
