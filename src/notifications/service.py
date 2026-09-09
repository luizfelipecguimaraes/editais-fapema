from datetime import datetime
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo("America/Fortaleza")


def agora_iso() -> str:
    return datetime.now(TIMEZONE).isoformat(timespec="seconds")


def preparar_notificacoes(
    estado: dict,
    novos: list[dict],
) -> list[dict]:
    """
    Define quais editais devem ser enviados ao Telegram.

    Primeira execução:
    - envia somente editais atualmente abertos.

    Execuções seguintes:
    - envia itens novos que não estejam encerrados.

    Notificações pendentes de uma execução anterior
    também são retornadas para nova tentativa.
    """
    primeira_execucao = not estado.get(
        "telegram_inicializado",
        False,
    )

    urls_novas = {
        edital["url"]
        for edital in novos
    }

    for edital in estado["editais"]:
        edital.setdefault("notificado", False)
        edital.setdefault("notificado_em", None)
        edital.setdefault(
            "pendente_notificacao",
            False,
        )

        if edital["notificado"]:
            edital["pendente_notificacao"] = False
            continue

        if primeira_execucao:
            if edital["status"] == "aberto":
                edital["pendente_notificacao"] = True

        elif (
            edital["url"] in urls_novas
            and edital["status"] != "encerrado"
        ):
            edital["pendente_notificacao"] = True

    return [
        edital
        for edital in estado["editais"]
        if (
            edital["pendente_notificacao"]
            and not edital["notificado"]
        )
    ]


def marcar_como_notificado(
    edital: dict,
) -> None:
    edital["notificado"] = True
    edital["notificado_em"] = agora_iso()
    edital["pendente_notificacao"] = False


def formatar_mensagem(
    edital: dict,
) -> str:
    titulo = edital["titulo"]
    url = edital["url"]

    publicado_em = formatar_data(
        edital.get("publicado_em")
    )

    prazo_final = formatar_data(
        edital.get("prazo_final")
    )

    prazo_hora = edital.get("prazo_hora")

    if prazo_final:
        prazo = prazo_final

        if prazo_hora:
            prazo += f" às {prazo_hora}"

    else:
        prazo = (
            "Não identificado automaticamente"
        )

    if edital.get("tipo") == "oportunidade":
        cabecalho = "🔔 NOVA OPORTUNIDADE FAPEMA"
    else:
        cabecalho = "🔔 NOVO EDITAL FAPEMA"

    return (
        f"{cabecalho}\n\n"
        f"📄 {titulo}\n\n"
        f"📅 Publicado em: {publicado_em}\n"
        f"⏳ Prazo: {prazo}\n\n"
        f"🔗 Acessar:\n"
        f"{url}"
    )


def formatar_data(
    valor: str | None,
) -> str:
    if not valor:
        return "Não identificado"

    data = datetime.strptime(
        valor,
        "%Y-%m-%d",
    )

    return data.strftime("%d/%m/%Y")