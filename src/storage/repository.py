
import json
import os
import tempfile

from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo("America/Fortaleza")

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT_DIR / "data" / "editais.json"


def agora_iso() -> str:
    """Retorna data/hora atual no fuso de Fortaleza."""
    return datetime.now(TIMEZONE).isoformat(
        timespec="seconds"
    )


def carregar_estado() -> dict:
    """Carrega o estado persistido dos editais."""

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
            estado = json.load(arquivo)

    except (JSONDecodeError, OSError) as erro:
        raise RuntimeError(
            f"Erro ao carregar o estado em {DATA_FILE}. "
            "Execução interrompida para preservar os dados."
        ) from erro

    if (
        not isinstance(estado, dict)
        or not isinstance(estado.get("editais"), list)
    ):
        raise ValueError(
            "Estrutura inválida no arquivo editais.json."
        )

    return estado


def salvar_estado(estado: dict) -> None:
    """Salva o estado usando escrita atômica."""

    DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    caminho_temporario = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DATA_FILE.parent,
            prefix="editais_",
            suffix=".tmp",
            delete=False,
        ) as arquivo:

            caminho_temporario = Path(
                arquivo.name
            )

            json.dump(
                estado,
                arquivo,
                ensure_ascii=False,
                indent=2,
            )

            arquivo.write("\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())

        # Substitui o arquivo original somente
        # após a gravação completa.
        os.replace(
            caminho_temporario,
            DATA_FILE,
        )

    finally:
        if (
            caminho_temporario is not None
            and caminho_temporario.exists()
        ):
            caminho_temporario.unlink()


def atualizar_estado(
    estado: dict,
    editais_atuais: list[dict],
) -> tuple[dict, list[dict]]:
    """Atualiza os editais sem remover registros antigos."""

    momento = agora_iso()

    editais_salvos = {
        edital["url"]: edital.copy()
        for edital in estado.get("editais", [])
    }

    novos = []

    for edital_atual in editais_atuais:
        url = edital_atual["url"]

        if url in editais_salvos:
            registro = editais_salvos[url]

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

    editais = list(
        editais_salvos.values()
    )

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
