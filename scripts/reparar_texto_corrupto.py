"""Repara grafias corruptas ya persistidas por descargas anteriores.

Se puede ejecutar mas de una vez: solo actualiza filas que cambian.
"""

from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from govdata.config.settings import get_settings
from govdata.domain.rules.texto_humano import reparar_texto_humano
from govdata.infrastructure.persistence.postgresql.models.funcionario_model import FuncionarioModel
from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel


def _reparar(modelo: object, campos: tuple[str, ...]) -> int:
    cambios = 0
    for campo in campos:
        valor = getattr(modelo, campo)
        reparado = reparar_texto_humano(valor)
        if valor != reparado:
            setattr(modelo, campo, reparado)
            cambios += 1
    return cambios


def main() -> None:
    # Este mantenimiento no necesita construir todo el contenedor (que
    # inicializa adaptadores de scraping); abre solo la sesion de datos.
    engine = create_engine(get_settings().database.dsn)
    session = sessionmaker(bind=engine)()
    try:
        cambios = 0
        for persona in session.execute(select(PersonaModel)).scalars():
            cambios += _reparar(persona, ("nombres", "apellidos"))
        for funcionario in session.execute(select(FuncionarioModel)).scalars():
            cambios += _reparar(funcionario, ("cargo", "dependencia"))
        session.commit()
        print(f"Texto reparado: {cambios} campos actualizados.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
