"""Tests: reglas de dominio del Modulo 2 (puras, sin IO)."""

from __future__ import annotations

from govdata.application.dto.descubrimiento_dto import ArchivoDTO, NumeralPublicadoDTO
from govdata.domain.entities.documento import TipoArchivo
from govdata.domain.rules.detector_tipo_archivo import detectar_tipo_por_extension
from govdata.domain.rules.detector_ultimo_mes import seleccionar_mes_mas_reciente
from govdata.domain.rules.matcher_item_documento import seleccionar_numeral_directorio_personal
from govdata.domain.rules.seleccionador_archivo_datos import seleccionar_archivo_datos


class TestSeleccionarMesMasReciente:
    def test_retorna_el_mayor(self) -> None:
        assert seleccionar_mes_mas_reciente([1, 3, 6, 2]) == 6

    def test_no_depende_del_orden(self) -> None:
        assert seleccionar_mes_mas_reciente([6]) == seleccionar_mes_mas_reciente([6, 1, 2, 3, 4, 5])

    def test_lista_vacia_retorna_none(self) -> None:
        assert seleccionar_mes_mas_reciente([]) is None

    def test_ignora_valores_fuera_de_rango(self) -> None:
        assert seleccionar_mes_mas_reciente([13, 0, -1, 5]) == 5

    def test_todos_invalidos_retorna_none(self) -> None:
        assert seleccionar_mes_mas_reciente([0, 13, -5]) is None


class TestSeleccionarNumeralDirectorioPersonal:
    def test_encuentra_texto_exacto_de_referencia(self) -> None:
        numerales = [
            NumeralPublicadoDTO(descripcion="Estructura orgánica"),
            NumeralPublicadoDTO(descripcion="Directorio y distributivo del personal"),
        ]
        resultado = seleccionar_numeral_directorio_personal(numerales)
        assert resultado is not None
        assert resultado.numeral.descripcion == "Directorio y distributivo del personal"
        assert resultado.score >= 90

    def test_encuentra_variante_real_del_portal(self) -> None:
        """Verificado contra transparencia.dpe.gob.ec: el texto real es
        'Directorio y distributivo personal de la entidad', distinto al
        texto de referencia -- por eso hace falta matching difuso."""
        numerales = [
            NumeralPublicadoDTO(descripcion="Remuneraciones ingresos adicionales"),
            NumeralPublicadoDTO(descripcion="Directorio y distributivo personal de la entidad"),
            NumeralPublicadoDTO(descripcion="Planes y programas"),
        ]
        resultado = seleccionar_numeral_directorio_personal(numerales)
        assert resultado is not None
        assert resultado.numeral.descripcion == "Directorio y distributivo personal de la entidad"

    def test_encuentra_variantes_cortas(self) -> None:
        for variante in (
            "Directorio del personal",
            "Distributivo del personal",
            "Directorio y distributivo",
        ):
            numerales = [NumeralPublicadoDTO(descripcion=variante)]
            resultado = seleccionar_numeral_directorio_personal(numerales)
            assert resultado is not None, f"deberia encontrar variante: {variante}"

    def test_sin_coincidencia_retorna_none(self) -> None:
        numerales = [
            NumeralPublicadoDTO(descripcion="Presupuesto de la institucion"),
            NumeralPublicadoDTO(descripcion="Procesos de contratacion publica"),
        ]
        assert seleccionar_numeral_directorio_personal(numerales) is None

    def test_lista_vacia_retorna_none(self) -> None:
        assert seleccionar_numeral_directorio_personal([]) is None

    def test_elige_el_de_mayor_score_entre_varios_candidatos(self) -> None:
        numerales = [
            NumeralPublicadoDTO(descripcion="Directorio Telefonico Institucional"),  # decoy, score bajo
            NumeralPublicadoDTO(descripcion="Directorio y distributivo del personal"),  # score alto
        ]
        resultado = seleccionar_numeral_directorio_personal(numerales)
        assert resultado is not None
        assert resultado.numeral.descripcion == "Directorio y distributivo del personal"

    def test_no_confunde_directorio_solo_con_directorio_de_personal(self) -> None:
        """Regresion: `partial_ratio` le daria 100 a 'Directorio' solo por
        ser prefijo de la variante; por eso la regla usa solo
        `token_sort_ratio`, que lo deja muy por debajo del umbral."""
        numerales = [NumeralPublicadoDTO(descripcion="Directorio")]
        assert seleccionar_numeral_directorio_personal(numerales) is None

    def test_umbral_mas_estricto_rechaza_coincidencias_debiles(self) -> None:
        numerales = [NumeralPublicadoDTO(descripcion="Directorio Telefonico Institucional")]
        resultado = seleccionar_numeral_directorio_personal(numerales, umbral=99.0)
        assert resultado is None


class TestSeleccionarArchivoDatos:
    def test_encuentra_conjunto_de_datos_exacto(self) -> None:
        archivos = [
            ArchivoDTO(descripcion="Metadatos", nombre="m.csv", url_descarga="/m.csv"),
            ArchivoDTO(descripcion="Conjunto de datos", nombre="d.csv", url_descarga="/d.csv"),
            ArchivoDTO(descripcion="Diccionario", nombre="dic.csv", url_descarga="/dic.csv"),
        ]
        resultado = seleccionar_archivo_datos(archivos)
        assert resultado is not None
        assert resultado.archivo.nombre == "d.csv"

    def test_encuentra_variante_con_prefijo_numerico(self) -> None:
        """Verificado contra el portal real: '1.Conjunto de datos'."""
        archivos = [ArchivoDTO(descripcion="1.Conjunto de datos", nombre="x.csv", url_descarga="/x.csv")]
        resultado = seleccionar_archivo_datos(archivos)
        assert resultado is not None

    def test_solo_metadatos_y_diccionario_retorna_none(self) -> None:
        archivos = [
            ArchivoDTO(descripcion="Metadatos", nombre="m.csv", url_descarga="/m.csv"),
            ArchivoDTO(descripcion="Diccionario", nombre="dic.csv", url_descarga="/dic.csv"),
        ]
        assert seleccionar_archivo_datos(archivos) is None

    def test_metadatos_no_se_confunde_con_datos(self) -> None:
        """Regresion: 'Metadatos' comparte el sufijo 'datos' con la variante
        'Datos' (~71 de similitud), calibrado para quedar bajo el umbral
        por defecto (80)."""
        archivos = [ArchivoDTO(descripcion="Metadatos", nombre="m.csv", url_descarga="/m.csv")]
        assert seleccionar_archivo_datos(archivos) is None

    def test_lista_vacia_retorna_none(self) -> None:
        assert seleccionar_archivo_datos([]) is None


class TestDetectarTipoPorExtension:
    def test_detecta_csv(self) -> None:
        assert detectar_tipo_por_extension("/media/publications/x_ab12.csv") == TipoArchivo.CSV

    def test_detecta_pdf(self) -> None:
        assert detectar_tipo_por_extension("/media/publications/directorio.pdf") == TipoArchivo.PDF

    def test_detecta_xlsx(self) -> None:
        assert detectar_tipo_por_extension("https://x.gob.ec/archivo.XLSX") == TipoArchivo.XLSX

    def test_detecta_xls(self) -> None:
        assert detectar_tipo_por_extension("archivo.xls") == TipoArchivo.XLS

    def test_ignora_query_string(self) -> None:
        assert detectar_tipo_por_extension("/archivo.pdf?token=abc123") == TipoArchivo.PDF

    def test_extension_no_reconocida_retorna_none(self) -> None:
        assert detectar_tipo_por_extension("/archivo.docx") is None

    def test_sin_extension_retorna_none(self) -> None:
        assert detectar_tipo_por_extension("/media/publications/sin-extension") is None
