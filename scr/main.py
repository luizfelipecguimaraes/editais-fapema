from fapema.scraper import listar_editais


def main():
    print("Buscando editais na FAPEMA...\n")

    editais = listar_editais()

    print(
        f"{len(editais)} item(ns) encontrado(s) "
        "na categoria Editais Abertos.\n"
    )

    for numero, edital in enumerate(editais, start=1):
        print(f"{numero}. {edital['titulo']}")
        print(f"   {edital['url']}")
        print()


if __name__ == "__main__":
    main()
