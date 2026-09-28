"""Tests de integracion: DpeScraperAdapter contra un servidor HTTP local
que sirve las fixtures reales/capturadas del portal DPE (modo simulacion,
sin depender de Internet ni de la disponibilidad del portal real).
"""

from __future__ import annotations

import pytest

from govdata.domain.entities.documento import TipoArchivo
from govdata.domain.exceptions.domain_exceptions import (
    DescargaFallidaError,
    EntidadNoEncontradaError,
    ExtraccionFallidaError,
)
from govdata.infrastructure.scraping.playwright.dpe_scraper_adapter import DpeScraperAdapter
from govdata.infrastructure.scraping.rate_limiter import RateLimiter


@pytest.fixture()
def adapter(contexto_navegador, servidor_fixtures_dpe):
    return DpeScraperAdapter(
        contexto=contexto_navegador,
        rate_limiter=RateLimiter(intervalo_minimo_segundos=0.0),
        url_origen=servidor_fixtures_dpe.url_origen,
        max_reintentos=2,
        backoff_base_segundos=0.05,
    )


class TestListarEntidades:
    def test_parsea_todas_las_entidades_de_todas_las_letras(self, adapter) -> None:
        entidades = adapter.listar_entidades()

        nombres = {e.nombre for e in entidades}
        assert "UNIVERSIDAD NACIONAL DE EDUCACION" in nombres
        assert "ESMEVIAL EP - EMPRESA DE MOVILIDAD Y TRANSITO DEL CANTON ESMERALDAS" in nombres
        assert len(entidades) == 4  # fixture recortada: 2 letras x 2 entidades

    def test_construye_url_transparencia_desde_el_id(self, adapter, servidor_fixtures_dpe) -> None:
        entidades = adapter.listar_entidades()
        unae = next(e for e in entidades if e.identificador_portal == "1920")
        assert unae.url_transparencia == f"{servidor_fixtures_dpe.url_origen}/entidades/1920"

    def test_conserva_estado_activo_inactivo(self, adapter) -> None:
        entidades = adapter.listar_entidades()
        inactiva = next(e for e in entidades if e.identificador_portal == "1234")
        assert inactiva.activo is False


class TestListarMesesPublicados:
    def test_retorna_meses_publicados(self, adapter, servidor_fixtures_dpe) -> None:
        url_entidad = f"{servidor_fixtures_dpe.url_origen}/entidades/1920"
        meses = adapter.listar_meses_publicados(url_entidad, 2026)
        assert meses == [6]

    def test_anio_sin_publicaciones_retorna_lista_vacia(self, adapter, servidor_fixtures_dpe) -> None:
        url_entidad = f"{servidor_fixtures_dpe.url_origen}/entidades/1920"
        meses = adapter.listar_meses_publicados(url_entidad, 2025)
        assert meses == []

    def test_entidad_inexistente_lanza_error_de_dominio(self, adapter, servidor_fixtures_dpe) -> None:
        url_entidad = f"{servidor_fixtures_dpe.url_origen}/entidades/9999"
        with pytest.raises(EntidadNoEncontradaError):
            adapter.listar_meses_publicados(url_entidad, 2026)


class TestListarPublicacionesMes:
    def test_parsea_numerales_y_archivos(self, adapter, servidor_fixtures_dpe) -> None:
        url_entidad = f"{servidor_fixtures_dpe.url_origen}/entidades/1920"
        numerales = adapter.listar_publicaciones_mes(url_entidad, 2026, 6)

        assert len(numerales) == 3
        directorio = next(
            n for n in numerales if "directorio y distributivo" in n.descripcion.lower()
        )
        assert len(directorio.archivos) == 3
        conjunto = next(a for a in directorio.archivos if a.descripcion == "Conjunto de datos")
        assert conjunto.url_descarga.endswith(".csv")
        # Las rutas `/media/...` se sirven via el prefijo del backend (la ruta
        # directa devuelve el HTML de la SPA en el portal real).
        assert conjunto.url_descarga.startswith(
            f"{servidor_fixtures_dpe.url_origen}/backend/v1/transparency/media/"
        )

    def test_publicacion_sin_item_directorio(self, adapter, servidor_fixtures_dpe) -> None:
        url_entidad = f"{servidor_fixtures_dpe.url_origen}/entidades/1358"
        numerales = adapter.listar_publicaciones_mes(url_entidad, 2026, 6)
        descripciones = [n.descripcion.lower() for n in numerales]
        assert not any("directorio y distributivo" in d for d in descripciones)

    def test_variante_pdf_sintetica(self, adapter, servidor_fixtures_dpe) -> None:
        from govdata.domain.rules.detector_tipo_archivo import detectar_tipo_por_extension
        from govdata.domain.rules.seleccionador_archivo_datos import seleccionar_archivo_datos

        url_entidad = f"{servidor_fixtures_dpe.url_origen}/entidades/7777"
        numerales = adapter.listar_publicaciones_mes(url_entidad, 2026, 3)

        resultado = seleccionar_archivo_datos(numerales[0].archivos)
        assert resultado is not None
        assert detectar_tipo_por_extension(resultado.archivo.url_descarga) == TipoArchivo.PDF

    def test_respuesta_no_json_lanza_extraccion_fallida(self, adapter, servidor_fixtures_dpe) -> None:
        url_entidad = f"{servidor_fixtures_dpe.url_origen}/entidades/6666"
        with pytest.raises(ExtraccionFallidaError):
            adapter.listar_publicaciones_mes(url_entidad, 2026, 6)


class TestReintentos:
    def test_recupera_tras_fallos_transitorios(self, contexto_navegador, servidor_fixtures_dpe) -> None:
        """El servidor fixture falla 2 veces con 503 antes de responder
        200 -- el adapter debe reintentar (backoff) y terminar exitoso."""
        servidor_fixtures_dpe.intentos_fallidos_restantes = 2
        adapter = DpeScraperAdapter(
            contexto=contexto_navegador,
            rate_limiter=RateLimiter(intervalo_minimo_segundos=0.0),
            url_origen=servidor_fixtures_dpe.url_origen,
            max_reintentos=3,
            backoff_base_segundos=0.05,
        )

        cuerpo = adapter._obtener_json("/simular-fallos-luego-exito", contexto="test de reintentos")
        assert cuerpo == [{"month": 6}]

    def test_agota_reintentos_y_propaga_error(self, contexto_navegador, servidor_fixtures_dpe) -> None:
        servidor_fixtures_dpe.intentos_fallidos_restantes = 10  # mas que max_reintentos
        adapter = DpeScraperAdapter(
            contexto=contexto_navegador,
            rate_limiter=RateLimiter(intervalo_minimo_segundos=0.0),
            url_origen=servidor_fixtures_dpe.url_origen,
            max_reintentos=2,
            backoff_base_segundos=0.05,
        )
        with pytest.raises(DescargaFallidaError):
            adapter._obtener_json("/simular-fallos-luego-exito", contexto="test de reintentos")
