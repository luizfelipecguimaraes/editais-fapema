import requests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    validar_config_telegram,
)


API_BASE_URL = "https://api.telegram.org"


def _fazer_requisicao(
    metodo: str,
    dados: dict | None = None,
) -> dict:
    """
    Executa uma chamada à Telegram Bot API.

    O token não é incluído em mensagens de erro para evitar
    vazamento acidental em logs.
    """
    validar_config_telegram()

    url = (
        f"{API_BASE_URL}/"
        f"bot{TELEGRAM_BOT_TOKEN}/"
        f"{metodo}"
    )

    try:
        response = requests.post(
            url,
            json=dados or {},
            timeout=20,
        )

    except requests.RequestException:
        raise RuntimeError(
            "Falha de conexão com a API do Telegram."
        ) from None

    try:
        resposta = response.json()

    except ValueError:
        raise RuntimeError(
            "Resposta inválida recebida da API do Telegram."
        ) from None

    if not response.ok or not resposta.get("ok"):
        descricao = resposta.get(
            "description",
            "Erro desconhecido.",
        )

        raise RuntimeError(
            f"Telegram API retornou erro: {descricao}"
        )

    return resposta["result"]


def obter_bot() -> dict:
    """Consulta as informações do bot autenticado."""
    return _fazer_requisicao("getMe")


def enviar_mensagem(texto: str) -> dict:
    """Envia uma mensagem para o canal configurado."""

    dados = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto,
    }

    return _fazer_requisicao(
        "sendMessage",
        dados,
    )