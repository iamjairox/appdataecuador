"""Tests: generador de fingerprint fonetico (Submodulo 6.1/6.2)."""

from __future__ import annotations

from govdata.domain.rules.generador_fingerprint_fonetico import generar_fingerprint_fonetico


class TestFingerprintFonetico:
    def test_determinista_misma_entrada_misma_salida(self) -> None:
        a = generar_fingerprint_fonetico("Juan Carlos", "Perez Gomez")
        b = generar_fingerprint_fonetico("Juan Carlos", "Perez Gomez")
        assert a == b

    def test_v_y_b_son_equivalentes(self) -> None:
        assert generar_fingerprint_fonetico("Juan", "Vasquez") == generar_fingerprint_fonetico("Juan", "Basquez")

    def test_s_y_z_finales_son_equivalentes(self) -> None:
        assert generar_fingerprint_fonetico("Juan", "Gonzales") == generar_fingerprint_fonetico("Juan", "Gonzalez")

    def test_h_es_muda(self) -> None:
        assert generar_fingerprint_fonetico("Juan", "Herrera") == generar_fingerprint_fonetico("Juan", "Errera")

    def test_ll_se_pronuncia_como_y_yeismo(self) -> None:
        assert generar_fingerprint_fonetico("Juan", "Silla") == generar_fingerprint_fonetico("Juan", "Siya")

    def test_nombres_genuinamente_distintos_producen_claves_distintas(self) -> None:
        assert generar_fingerprint_fonetico("Juan", "Perez") != generar_fingerprint_fonetico("Maria", "Lopez")

    def test_tildes_no_afectan(self) -> None:
        assert generar_fingerprint_fonetico("José", "Pérez") == generar_fingerprint_fonetico("Jose", "Perez")
