"""Tests: generador de fingerprint (Submodulo 4.4)."""

from __future__ import annotations

from govdata.domain.rules.generador_fingerprint import generar_fingerprint


class TestGenerarFingerprint:
    def test_ejemplo_del_cliente(self) -> None:
        fingerprint, _ = generar_fingerprint("Juan Carlos", "Pérez Gómez")
        assert fingerprint == "JUANCARLOSPEREZGOMEZ"

    def test_es_determinista(self) -> None:
        assert generar_fingerprint("Ana", "Lopez") == generar_fingerprint("Ana", "Lopez")

    def test_quita_tildes(self) -> None:
        fingerprint, _ = generar_fingerprint("José", "Muñoz")
        assert fingerprint == "JOSEMUNOZ"

    def test_quita_puntuacion_y_dobles_espacios(self) -> None:
        fingerprint, _ = generar_fingerprint("Juan,  Carlos.", "Pérez -Gómez")
        assert fingerprint == "JUANCARLOSPEREZGOMEZ"

    def test_mayusculas_no_afectan_resultado(self) -> None:
        assert generar_fingerprint("juan", "perez") == generar_fingerprint("JUAN", "PEREZ")

    def test_hash_es_sha256_hexadecimal(self) -> None:
        _, hash_ = generar_fingerprint("Juan", "Perez")
        assert len(hash_) == 64
        int(hash_, 16)  # no lanza si es hexadecimal valido

    def test_nombres_distintos_dan_fingerprints_distintos(self) -> None:
        fp1, hash1 = generar_fingerprint("Juan", "Perez")
        fp2, hash2 = generar_fingerprint("Juana", "Perez")
        assert fp1 != fp2
        assert hash1 != hash2

    def test_conectores_se_conservan(self) -> None:
        """Decision documentada: NO se eliminan conectores como 'DE LA' --
        podrian fusionar apellidos distintos."""
        fingerprint, _ = generar_fingerprint("Juan", "De La Cruz")
        assert "DELACRUZ" in fingerprint
