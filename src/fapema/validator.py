def classificar_item(titulo: str) -> str:
    """
    Classifica um item encontrado na listagem da FAPEMA.

    A classificação não determina ainda se a oportunidade está aberta.
    """
    titulo_normalizado = titulo.lower()

    if "edital" in titulo_normalizado:
        return "edital"

    termos_oportunidade = (
        "concurso",
        "chamada pública",
        "chamada publica",
        "seleção de propostas",
        "selecao de propostas",
    )

    if any(termo in titulo_normalizado for termo in termos_oportunidade):
        return "oportunidade"

    termos_administrativos = (
        "resolução",
        "resolucao",
        "portaria",
    )

    if any(termo in titulo_normalizado for termo in termos_administrativos):
        return "administrativo"

    return "desconhecido"


def validar_editais(editais: list[dict]) -> list[dict]:
    """
    Adiciona uma classificação aos itens coletados
    sem remover nenhum deles.
    """
    resultado = []

    for edital in editais:
        item = edital.copy()
        item["tipo"] = classificar_item(item["titulo"])

        resultado.append(item)

    return resultado