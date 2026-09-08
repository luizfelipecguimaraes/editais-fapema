from collections import Counter

from fapema.scraper import listar_editais
from fapema.validator import validar_editais


def main():
    print("Buscando editais na FAPEMA...\n")

    editais = listar_editais()
    editais = validar_editais(editais)

    print(f"{len(editais)} item(ns) encontrado(s).\n")

    contagem = Counter(edital["tipo"] for edital in editais)

    print("Resumo:")
    print(f"Editais: {contagem['edital']}")
    print(f"Oportunidades: {contagem['oportunidade']}")
    print(f"Administrativos: {contagem['administrativo']}")
    print(f"Desconhecidos: {contagem['desconhecido']}")
    print()

    for numero, edital in enumerate(editais, start=1):
        print(f"{numero}. [{edital['tipo'].upper()}]")
        print(f"   {edital['titulo']}")
        print(f"   {edital['url']}")
        print()


if __name__ == "__main__":
    main()