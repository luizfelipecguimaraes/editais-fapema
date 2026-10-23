from time import sleep

import requests

from fapema.parser import parsear_edital
from fapema.scraper import listar_editais
from fapema.validator import validar_editais
from storage.repository import (
    atualizar_estado,
    carregar_estado,
    salvar_estado,
)

from notifications.service import (
    formatar_mensagem,
    marcar_como_notificado,
    preparar_notificacoes,
)
from notifications.telegram import enviar_mensagem

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


TIPOS_MONITORADOS = (
    "edital",
    "oportunidade",
)


def coletar_editais() -> list[dict]:
    """Coleta e processa os editais monitorados."""

    itens = validar_editais(
        listar_editais()
    )

    candidatos = [
        item
        for item in itens
        if item["tipo"] in TIPOS_MONITORADOS
    ]

    editais = []

    for numero, item in enumerate(
        candidatos,
        start=1,
    ):
        print(
            f"[{numero}/{len(candidatos)}] "
            f"{item['titulo']}"
        )

        try:
            edital = parsear_edital(
                item["url"]
            )

            edital["tipo"] = item["tipo"]

            editais.append(edital)

        except requests.exceptions.RequestException as erro:
            print(
                f"Erro de conexão ao processar "
                f"{item['url']}: {erro}"
            )

        except Exception as erro:
            print(
                f"Erro ao processar "
                f"{item['url']}: {erro}"
            )

        sleep(0.5)

    return editais


def main():
    print(
        "Iniciando monitoramento "
        "de editais da FAPEMA...\n"
    )

    estado = carregar_estado()

    # Proteção contra indisponibilidade da FAPEMA.
    # Não altera o estado se a coleta principal falhar.
    try:
        editais_atuais = coletar_editais()

    except requests.exceptions.RequestException as erro:
        print("\n" + "=" * 70)
        print("ERRO DE CONEXÃO COM A FAPEMA\n")

        print(f"Detalhes: {erro}")

        print(
            "\nNão foi possível concluir a coleta."
        )

        print(
            "O estado anterior será preservado."
        )

        print(
            "Uma nova tentativa ocorrerá "
            "na próxima execução agendada."
        )

        print("=" * 70)

        raise SystemExit(1) from erro

    # Protege contra falhas inesperadas na coleta.
    except Exception as erro:
        print("\n" + "=" * 70)
        print("ERRO DURANTE A COLETA\n")

        print(f"Detalhes: {erro}")

        print(
            "Monitoramento interrompido "
            "sem modificar o estado."
        )

        print("=" * 70)

        raise

    # Evita atualizar o banco com uma coleta vazia.
    # Atenção: pressupõe que uma coleta válida
    # deva retornar pelo menos um edital.
    if not editais_atuais:
        print("\n" + "=" * 70)
        print("AVISO: NENHUM EDITAL PROCESSADO\n")

        print(
            "A coleta retornou uma lista vazia."
        )

        print(
            "O estado anterior será preservado."
        )

        print("=" * 70)

        raise SystemExit(1)

    novo_estado, novos = atualizar_estado(
        estado,
        editais_atuais,
    )

    notificacoes = preparar_notificacoes(
        novo_estado,
        novos,
    )

    # Salva antes de enviar para registrar
    # as notificações pendentes.
    salvar_estado(novo_estado)

    print("\n" + "=" * 70)
    print("RESUMO\n")

    print(
        f"Processados: "
        f"{len(editais_atuais)}"
    )

    print(
        f"Registrados no banco: "
        f"{len(novo_estado['editais'])}"
    )

    print(
        f"Novos detectados: "
        f"{len(novos)}"
    )

    print(
        f"Notificações pendentes: "
        f"{len(notificacoes)}"
    )

    print("\n" + "=" * 70)
    print("TELEGRAM\n")

    falhas = 0

    for edital in notificacoes:
        print(
            f"Enviando: "
            f"{edital['titulo']}"
        )

        try:
            mensagem = formatar_mensagem(
                edital
            )

            enviar_mensagem(mensagem)

            marcar_como_notificado(
                edital
            )

            # Salvamos após cada envio.
            # Se o programa cair depois,
            # mensagens já enviadas não serão duplicadas.
            salvar_estado(novo_estado)

            print("Enviado com sucesso.\n")

        except Exception as erro:
            falhas += 1

            print(
                f"Falha ao enviar: {erro}\n"
            )

    if (
        not novo_estado.get(
            "telegram_inicializado",
            False,
        )
        and falhas == 0
    ):
        novo_estado[
            "telegram_inicializado"
        ] = True

    salvar_estado(novo_estado)

    print("=" * 70)

    print(
        f"Notificações enviadas: "
        f"{len(notificacoes) - falhas}"
    )

    print(
        f"Falhas: {falhas}"
    )


if __name__ == "__main__":
    main()
