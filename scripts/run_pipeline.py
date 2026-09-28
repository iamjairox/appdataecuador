"""Entry point del pipeline.

En el Modulo 1 (Foundation) este script solo demuestra que el Container
de dependencias arranca correctamente: carga settings, configura logging,
crea el engine de base de datos y crea el esquema si no existe. Los
casos de uso reales de scraping se conectan aqui a partir del Modulo 2.
"""

from __future__ import annotations

from govdata.config.container import Container
from govdata.infrastructure.persistence.postgresql.models import Base


def main() -> None:
    container = Container()
    logger = container.logger

    logger.info("arrancando_pipeline", app=container.settings.nombre_app)

    # Crea el esquema si aun no existe (idempotente). En produccion el
    # esquema se gestiona con Alembic (`alembic upgrade head`); esto es
    # una conveniencia para levantar un entorno de desarrollo rapido.
    Base.metadata.create_all(container.engine)
    logger.info("esquema_verificado")

    with container.nueva_sesion() as sesion:
        from sqlalchemy import text

        sesion.execute(text("SELECT 1"))
    logger.info("conexion_base_datos_verificada")

    logger.info("pipeline_modulo1_listo")


if __name__ == "__main__":
    main()
