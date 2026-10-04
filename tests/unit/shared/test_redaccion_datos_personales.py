"""Tests para el módulo de redacción de datos personales.

Verifica que la cédula no se exponga en:
- Logs
- Respuestas de API
- Exportaciones (CSV/Excel)
- Mensajes de excepción
- URLs registradas
- Auditoría textual
"""

from __future__ import annotations

import pytest

from govdata.shared.security.redaccion_datos_personales import (
    contiene_cedula,
    redactar_cedulas,
    sanitizar_error_externo,
    validar_sin_cedula,
)


class TestRedactarCedulas:
    """Tests para la redacción de cédulas."""

    def test_redactar_cedula_simple(self) -> None:
        texto = "La cédula es 1234567890"
        resultado = redactar_cedulas(texto)
        assert "1234567890" not in resultado
        assert "[IDENTIFICADOR_REDACTADO]" in resultado

    def test_redactar_multiples_cedulas(self) -> None:
        texto = "Cédulas: 1234567890 y 0987654321"
        resultado = redactar_cedulas(texto)
        assert "1234567890" not in resultado
        assert "0987654321" not in resultado
        assert resultado.count("[IDENTIFICADOR_REDACTADO]") == 2

    def test_redactar_cedula_en_texto_largo(self) -> None:
        texto = "El funcionario con cédula 1234567890 fue encontrado en la base de datos."
        resultado = redactar_cedulas(texto)
        assert "1234567890" not in resultado
        assert "[IDENTIFICADOR_REDACTADO]" in resultado

    def test_redactar_cedula_con_otros_numeros(self) -> None:
        """Los números que no son cédulas no se redactan."""
        texto = "Teléfono: 02-1234567, Cédula: 1234567890"
        resultado = redactar_cedulas(texto)
        assert "02-1234567" in resultado  # No se redacta
        assert "1234567890" not in resultado  # Se redacta

    def test_redactar_cedula_con_digitos_adyacentes(self) -> None:
        """Los números con más de 10 dígitos no se redactan."""
        texto = "Número largo: 12345678901234"
        resultado = redactar_cedulas(texto)
        assert "12345678901234" in resultado  # No se redacta (14 dígitos)

    def test_redactar_texto_sin_cedula(self) -> None:
        texto = "Este texto no contiene cédulas."
        resultado = redactar_cedulas(texto)
        assert resultado == texto


class TestSanitizarErrorExterno:
    """Tests para la sanitización de errores externos."""

    def test_sanitizar_excepcion(self) -> None:
        error = Exception("Error con cédula 1234567890")
        resultado = sanitizar_error_externo(error)
        assert "1234567890" not in resultado
        assert "[IDENTIFICADOR_REDACTADO]" in resultado

    def test_sanitizar_string(self) -> None:
        error = "Error con cédula 1234567890"
        resultado = sanitizar_error_externo(error)
        assert "1234567890" not in resultado
        assert "[IDENTIFICADOR_REDACTADO]" in resultado


class TestContieneCedula:
    """Tests para la detección de cédulas."""

    def test_contiene_cedula(self) -> None:
        assert contiene_cedula("La cédula es 1234567890") is True

    def test_no_contiene_cedula(self) -> None:
        assert contiene_cedula("Este texto no contiene cédulas") is False

    def test_contiene_cedula_con_otros_numeros(self) -> None:
        assert contiene_cedula("Teléfono: 02-1234567, Cédula: 1234567890") is True


class TestValidarSinCedula:
    """Tests para la validación de textos sin cédulas."""

    def test_validar_texto_sin_cedula(self) -> None:
        """No lanza excepción si el texto no contiene cédulas."""
        validar_sin_cedula("Este texto no contiene cédulas")

    def test_validar_texto_con_cedula(self) -> None:
        """Lanza excepción si el texto contiene una cédula."""
        with pytest.raises(ValueError, match="contiene una cédula"):
            validar_sin_cedula("La cédula es 1234567890", contexto="test")

    def test_validar_respuesta_api(self) -> None:
        """Verifica que una respuesta de API no contenga cédulas."""
        respuesta_api = '{"nombre": "Juan Pérez", "cédula": "1234567890"}'
        with pytest.raises(ValueError):
            validar_sin_cedula(respuesta_api, contexto="respuesta_api")

    def test_validar_exportacion_csv(self) -> None:
        """Verifica que una exportación CSV no contenga cédulas."""
        csv = "Nombre,Cédula\nJuan Pérez,1234567890"
        with pytest.raises(ValueError):
            validar_sin_cedula(csv, contexto="exportacion_csv")
