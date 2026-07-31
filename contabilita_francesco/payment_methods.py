METODI_PAGAMENTO = ["Contanti", "POS", "Bonifico", "Carta", "Assegno", "Altro"]


def normalizza_metodo_pagamento(metodo):
    if not metodo:
        return "Contanti"

    mapping = {
        "Contante": "Contanti",
        "contante": "Contanti",
        "Pos": "POS",
        "pos": "POS",
        "Carta": "Carta",
        "Bonifico": "Bonifico",
        "Assegno": "Assegno",
        "Altro": "Altro",
    }
    return mapping.get(metodo, metodo)
