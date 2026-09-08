from collections import Counter
from time import sleep

from fapema.parser import parsear_edital
from fapema.scraper import listar_editais
from fapema.validator import validar_editais


def main():
    print("Validando parser em todos os editais e oportunidades...\n")

    itens = validar_editais(listar_editais())

    candidatos = [
        item
        for item in itens
        if item["tipo"] in ("edital", "oportunidade")
    ]

    resultados = []
    erros = []

    for numero, item in enumerate(candidatos, start=1):
        print(
            f"[{numero}/{len(candidatos)}] "
            f"{item['titulo']}"
        )

        try:
            edital = parsear_edital(item["url"])
            edital["tipo"] = item["tipo"]

            resultados.append(edital)

        except Exception as erro:
            erros.append(
                {
                    "titulo": item["titulo"],
                    "url": item["url"],
                    "erro": str(erro),
                }
            )

        # Pequena pausa para não fazer várias requisições
        # consecutivas ao site da FAPEMA.
        sleep(0.5)

    print("\n" + "=" * 70)
    print("RESUMO\n")

    status = Counter(
        edital["status"]
        for edital in resultados
    )

    print(f"Candidatos:    {len(candidatos)}")
    print(f"Processados:   {len(resultados)}")
    print(f"Abertos:       {status['aberto']}")
    print(f"Encerrados:    {status['encerrado']}")
    print(f"Indeterminados:{status['indeterminado']}")
    print(f"Erros:         {len(erros)}")

    print("\n" + "=" * 70)
    print("INDETERMINADOS\n")

    indeterminados = [
        edital
        for edital in resultados
        if edital["status"] == "indeterminado"
    ]

    if not indeterminados:
        print("Nenhum.")
    else:
        for edital in indeterminados:
            print(edital["titulo"])
            print(edital["url"])
            print()

    print("=" * 70)
    print("ERROS\n")

    if not erros:
        print("Nenhum.")
    else:
        for erro in erros:
            print(erro["titulo"])
            print(erro["url"])
            print(f"Erro: {erro['erro']}")
            print()

    print("=" * 70)
    print("EDITAIS CONSIDERADOS ABERTOS\n")

    abertos = [
        edital
        for edital in resultados
        if edital["status"] == "aberto"
    ]

    if not abertos:
        print("Nenhum.")
    else:
        for edital in abertos:
            print(edital["titulo"])
            print(f"Prazo: {edital['prazo_final']}")
            print(f"Hora:  {edital['prazo_hora']}")
            print(edital["url"])
            print()


if __name__ == "__main__":
    main()
