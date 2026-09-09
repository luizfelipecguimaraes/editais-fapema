import json
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo("America/Fortaleza")

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT_DIR / "data" / "editais.json"


def agora_iso() -> str:
    """Retorna data/hora atual no fuso de Fortaleza."""
    return datetime.now(TIMEZONE).isoformat(timespec="seconds")


def carregar_estado() -> dict:
    """
    Carrega o estado persistido.

    Caso o arquivo não exista, esteja vazio ou contenha
    um JSON inválido, retorna um estado vazio.
    """
    estado_vazio = {
        "ultima_execucao_em": None,
        "telegram_inicializado": False,
        "editais": [],
    }

    if not DATA_FILE.exists():
        return estado_vazio

    try:
        with DATA_FILE.open(
            "r",
            encoding="utf-8",
        ) as arquivo:
            return json.load(arquivo)

    except (JSONDecodeError, OSError):
        return estado_vazio


def salvar_estado(estado: dict) -> None:
    """Salva o estado no arquivo JSON."""
    DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with DATA_FILE.open(
        "w",
        encoding="utf-8",
    ) as arquivo:
        json.dump(
            estado,
            arquivo,
            ensure_ascii=False,
            indent=2,
        )

        arquivo.write("\n")


def atualizar_estado(
    estado: dict,
    editais_atuais: list[dict],
) -> tuple[dict, list[dict]]:
    """
    Atualiza o estado com os itens coletados.

    Retorna:
    - estado atualizado;
    - lista de itens novos detectados.
    """
    momento = agora_iso()

    editais_salvos = {
        edital["url"]: edital
        for edital in estado.get("editais", [])
    }

    novos = []

    for edital_atual in editais_atuais:
        url = edital_atual["url"]

        if url in editais_salvos:
            registro = editais_salvos[url]

            # Atualiza dados que podem mudar com o tempo.
            registro.update(edital_atual)
            registro["ultima_verificacao_em"] = momento

        else:
            registro = {
                **edital_atual,
                "detectado_em": momento,
                "ultima_verificacao_em": momento,
            }

            editais_salvos[url] = registro
            novos.append(registro)

    editais = list(editais_salvos.values())

    # Mantém o JSON previsível e coloca publicações mais novas primeiro.
    editais.sort(
        key=lambda edital: (
            edital.get("publicado_em") or "",
            edital.get("detectado_em") or "",
        ),
        reverse=True,
    )

    novo_estado = {
    "ultima_execucao_em": momento,
    "telegram_inicializado": estado.get(
        "telegram_inicializado",
        False,
    ),
    "editais": editais,
    }

    return novo_estado, novos