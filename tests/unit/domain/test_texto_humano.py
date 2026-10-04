from govdata.domain.rules.texto_humano import reparar_texto_humano


def test_repara_caracteres_perdidos_frecuentes_de_dpe() -> None:
    assert reparar_texto_humano("CUNISPUMA BU�AY") == "CUNISPUMA BUÑAY"
    assert reparar_texto_humano("T�Cnico Planificaci�N") == "TÉCNICO PLANIFICACIÓN"


def test_conserva_grafia_correcta_y_repara_mojibake() -> None:
    assert reparar_texto_humano("Muñoz Pérez") == "Muñoz Pérez"
    assert reparar_texto_humano("MuÃ±oz PÃ©rez") == "Muñoz Pérez"
