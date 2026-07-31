from contabilità_francesco.payment_methods import METODI_PAGAMENTO, normalizza_metodo_pagamento


def test_payment_methods_include_pos_and_contanti():
    assert "Contanti" in METODI_PAGAMENTO
    assert "POS" in METODI_PAGAMENTO


def test_legacy_payment_method_is_normalized():
    assert normalizza_metodo_pagamento("Contante") == "Contanti"
    assert normalizza_metodo_pagamento("Pos") == "POS"
