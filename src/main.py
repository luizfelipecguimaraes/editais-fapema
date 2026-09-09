from time import sleep

from fapema.parser import parsear_edital
from fapema.scraper import listar_editais
from fapema.validator import validar_editais
from storage.repository import (
    atualizar_estado,
    carregar_estado,
    salvar_estado,
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

    editais_atuais = coletar_editais()

    novo_estado, novos = atualizar_estado(
        estado,
        editais_atuais,
    )

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

    if novos:
        print("\nNOVOS ITENS\n")

        for edital in novos:
            print(
                f"- {edital['titulo']} "
                f"[{edital['status']}]"
            )


if __name__ == "__main__":
    main()
