"""Tests de concurrencia: el Modulo 4 no introduce un orquestador propio
(a diferencia de `PipelineOrchestratorService`/`DescargaOrchestratorService`
de los Modulos 2/3) porque `ConsultaService.consultar_masiva` reutiliza
`consultar_entidad` secuencialmente. Lo que SI hay que verificar es que
sus piezas sean seguras bajo uso concurrente real quien las use asi en
el futuro (ej. un Worker Pool del Modulo 5/API):

    1. Los parsers (`PdfParserEngine`/`XlsxParser`/`CsvParser`) son
       instancias SIN estado mutable -- deben poder compartirse entre
       hilos sin resultados cruzados.
    2. `ExtraerDocumentoUseCase` completo (parser + normalizador +
       clasificador + fingerprint + persistencia SQLAlchemy) debe poder
       correr en paralelo, cada hilo con su propia `Session` (una
       `Session` de SQLAlchemy NUNCA se comparte entre hilos), sin
       corromper datos ni lanzar excepciones inesperadas.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

from sqlalchemy.orm import sessionmaker

from govdata.application.services.parser_factory import ParserFactory
from govdata.application.use_cases.extraer_documento_use_case import ExtraerDocumentoUseCase
from govdata.config.rule_engine import cargar_rule_engine
from govdata.domain.entities.documento import TipoArchivo
from govdata.infrastructure.parsers.csv.csv_parser import CsvParser
from govdata.infrastructure.parsers.excel.xlsx_parser import XlsxParser
from govdata.infrastructure.parsers.pdf.pdf_parser_engine import PdfParserEngine
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_funcionario_repository import (
    SqlAlchemyFuncionarioRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "extraccion"
_RULE_ENGINE = cargar_rule_engine()
_CARGOS_ESPERADOS = {"Director Juridico", "Asesora Juridica", "Director Financiero"}


class TestParsersCompartidosEntreHilos:
    def test_mismo_parser_pdf_en_paralelo_no_cruza_resultados(self) -> None:
        parser = PdfParserEngine()
        rutas = [str(FIXTURES / "directorio_con_tabla.pdf")] * 8

        with ThreadPoolExecutor(max_workers=8) as executor:
            futuros = [executor.submit(parser.extraer, ruta) for ruta in rutas]
            resultados = [f.result() for f in as_completed(futuros)]

        assert len(resultados) == 8
        assert all(r.tabla is not None and r.tabla.cantidad_filas == 5 for r in resultados)

    def test_parser_factory_compartida_entre_hilos_formatos_mixtos(self) -> None:
        factory = ParserFactory([PdfParserEngine(), XlsxParser(), CsvParser()])
        tareas = [
            (TipoArchivo.PDF, FIXTURES / "directorio_con_tabla.pdf"),
            (TipoArchivo.XLSX, FIXTURES / "directorio.xlsx"),
            (TipoArchivo.CSV, FIXTURES / "directorio.csv"),
        ] * 5

        def _procesar(tipo_ruta):
            tipo, ruta = tipo_ruta
            return factory.obtener_parser(tipo).extraer(str(ruta))

        with ThreadPoolExecutor(max_workers=6) as executor:
            resultados = list(executor.map(_procesar, tareas))

        assert len(resultados) == 15
        assert all(r.tabla is not None and r.tabla.cantidad_filas == 5 for r in resultados)


class TestExtraccionCompletaConcurrente:
    def test_multiples_documentos_en_paralelo_cada_uno_con_su_propia_sesion(
        self, sqlite_engine_multihilo
    ) -> None:
        """N hilos, cada uno con su propia `Session` SQLAlchemy (nunca
        compartida) y su propia `Entidad`/`Documento`, procesando el mismo
        directorio real en paralelo -- sin excepciones, sin resultados
        cruzados, sin corrupcion de datos entre hilos."""
        Factory = sessionmaker(bind=sqlite_engine_multihilo, future=True)
        cantidad_hilos = 6

        def _tarea(indice: int) -> int:
            sesion = Factory()
            try:
                entidad_modelo = EntidadModel(
                    nombre=f"Entidad Concurrente {indice}",
                    url_transparencia=f"https://x/concurrente/{indice}",
                    portal_origen="dpe",
                )
                sesion.add(entidad_modelo)
                sesion.flush()
                documento_modelo = DocumentoModel(
                    publicacion_id=indice + 1,
                    tipo_archivo=TipoArchivo.XLSX,
                    nombre_original="directorio.xlsx",
                    url_documento=f"https://x/concurrente/{indice}",
                    hash_sha256=f"{indice:064d}",
                    version=1,
                )
                sesion.add(documento_modelo)
                sesion.flush()

                from govdata.infrastructure.persistence.postgresql.mappers import (
                    documento_mapper,
                    entidad_mapper,
                )

                entidad = entidad_mapper.a_dominio(entidad_modelo)
                documento = documento_mapper.a_dominio(documento_modelo)

                caso_uso = ExtraerDocumentoUseCase(
                    parser_factory=ParserFactory([XlsxParser()]),
                    rule_engine=_RULE_ENGINE,
                    persona_repository=SqlAlchemyPersonaRepository(sesion),
                    funcionario_repository=SqlAlchemyFuncionarioRepository(sesion),
                )
                resultado = caso_uso.ejecutar(
                    entidad, documento, str(FIXTURES / "directorio.xlsx"), date(2026, 6, 1)
                )
                sesion.commit()
                cargos = {f.cargo for f in resultado.funcionarios}
                assert cargos == _CARGOS_ESPERADOS
                return len(resultado.funcionarios)
            finally:
                sesion.close()

        with ThreadPoolExecutor(max_workers=cantidad_hilos) as executor:
            futuros = [executor.submit(_tarea, i) for i in range(cantidad_hilos)]
            resultados = [f.result() for f in as_completed(futuros)]

        assert resultados == [3] * cantidad_hilos

        # Verificacion final: cada hilo persistio sus propios 3
        # funcionarios (18 en total) -- ninguno se perdio ni se duplico
        # por una condicion de carrera entre sesiones.
        sesion_verificacion = Factory()
        try:
            from govdata.infrastructure.persistence.postgresql.models.funcionario_model import (
                FuncionarioModel,
            )

            total = sesion_verificacion.query(FuncionarioModel).count()
            assert total == cantidad_hilos * 3
        finally:
            sesion_verificacion.close()
