"""El rechazo por CAPTCHA se puede activar sin impedir resultados válidos."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from govdata.config.settings import ScrapingSettings
from govdata.domain.exceptions.domain_exceptions import ConsultaForoPermanenteError
from govdata.domain.rules.reglas_foro import CatalogoCamposForo
from govdata.infrastructure.http.foro_abogados_adapter import ForoAbogadosAdapter


@pytest.mark.parametrize("rechazar", [False, True])
def test_respuesta_con_datos_y_captcha(monkeypatch, rechazar):
    monkeypatch.setattr(
        "govdata.infrastructure.http.foro_abogados_adapter.get_settings",
        lambda: SimpleNamespace(scraping=SimpleNamespace(rechazar_captcha_antibot=rechazar)),
    )
    adapter = ForoAbogadosAdapter(
        base_url="https://example.test",
        catalogo_campos=CatalogoCamposForo(campo_por_etiqueta={"NO REGISTRO": "registro"}),
    )
    adapter._solicitar = Mock(return_value=SimpleNamespace(
        status_code=200,
        text='<html><div class="g-recaptcha">captcha</div>'
             '<table><tr><td>No. Registro</td><td>R-12345</td></tr></table>'
             + '<!-- contenido -->' * 30 + '</html>',
    ))
    try:
        if rechazar:
            with pytest.raises(ConsultaForoPermanenteError, match="CAPTCHA"):
                adapter._consultar_raw({"cedula": "0000000000"})
        else:
            resultados = adapter._consultar_raw({"cedula": "0000000000"})
            assert len(resultados) == 1
            assert resultados[0].registro == "R-12345"
    finally:
        adapter.cerrar()


def test_rechazo_desactivado_por_defecto(monkeypatch):
    monkeypatch.delenv("SCRAPING_RECHAZAR_CAPTCHA_ANTIBOT", raising=False)
    assert ScrapingSettings().rechazar_captcha_antibot is False
