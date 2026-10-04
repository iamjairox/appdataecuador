"""La identidad se resuelve con los registros del Foro, no por orden de filas."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from govdata.application.dto.identificacion_cedula_dto import CedulaCandidateDTO
from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.infrastructure.api.routes import abogados


def ejecutar(monkeypatch, respuestas):
    candidatos = [CedulaCandidateDTO(str(i), 'MARIA LORENA', 'ANDRADE', 'GUZMAN') for i in (1, 2)]
    monkeypatch.setattr(abogados, '_detalle_publico', lambda codigo: {'codigo': codigo, 'nombre_completo': 'ANDRADE GUZMAN MARIA LORENA'})
    monkeypatch.setattr(abogados, 'consultar_cedula_en_cascada', AsyncMock(return_value=candidatos))
    consulta = AsyncMock(side_effect=respuestas)
    monkeypatch.setattr(abogados.ForoAbogadosPlaywrightAdapter, 'buscar_por_cedula', consulta)
    guardadas = []
    monkeypatch.setattr(abogados, '_guardar_ficha', lambda *args: guardadas.append(args))
    sesion = SimpleNamespace(scalar=lambda sentencia: SimpleNamespace(matricula='01-2009-180'))
    return asyncio.run(abogados.consultar_detalles_abogado(10, sesion)), guardadas, consulta


def registro(matricula='01-2009-180'):
    return RegistroForoDTO(nombre_completo='MARIA LORENA ANDRADE GUZMAN', registro=matricula, correo='prueba@example.test')


def test_una_identidad_verificada(monkeypatch):
    resultado, guardadas, consulta = ejecutar(monkeypatch, [[], [registro()]])
    assert consulta.await_count == 2
    assert resultado['cedula'] == '2'
    assert resultado['estado_consulta'] == 'completa'
    assert len(guardadas) == 1


def test_dos_identidades_separadas(monkeypatch):
    resultado, guardadas, _ = ejecutar(monkeypatch, [[registro()], [registro()]])
    assert resultado['estado_consulta'] == 'multiples_coincidencias_foro'
    assert {r['cedula'] for r in resultado['resultados']} == {'1', '2'}
    assert not guardadas


def test_fallo_parcial_no_declara_identidad_unica(monkeypatch):
    resultado, guardadas, _ = ejecutar(monkeypatch, [[registro()], abogados.FuenteForoNoDisponibleError('fuente no disponible')])
    assert resultado['estado_consulta'] == 'verificacion_incompleta'
    assert not guardadas


def test_matricula_distinta_no_se_asocia(monkeypatch):
    resultado, guardadas, _ = ejecutar(monkeypatch, [[registro('99-2020-1')], []])
    assert resultado['estado_consulta'] == 'sin_registro_foro'
    assert not guardadas
