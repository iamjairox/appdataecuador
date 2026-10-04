from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from govdata.infrastructure.api.routes.entidades import _ultimo_intento_externo


@pytest.mark.parametrize("estado,exito", [("completado", True), ("error", False)])
def test_intento_sin_foro_no_desaparece(estado, exito):
    fecha = datetime.now(UTC)
    trabajo = SimpleNamespace(
        iniciado_en=fecha, creado_en=fecha, finalizado_en=fecha,
        estado=SimpleNamespace(value=estado), ultimo_error=None,
    )
    sesion = Mock()
    sesion.scalar.side_effect = [None, trabajo]
    resultado = _ultimo_intento_externo(sesion, 1)
    assert resultado.exito is exito
    assert resultado.finalizado_en == fecha
    assert resultado.pagina_vacia is True


def test_sin_intentos_permanece_pendiente():
    sesion = Mock()
    sesion.scalar.side_effect = [None, None]
    assert _ultimo_intento_externo(sesion, 1) is None
