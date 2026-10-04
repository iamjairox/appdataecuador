import pytest

from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_funcionario_consulta_paginada_repository import nombre_apellidos_primero


@pytest.mark.parametrize("nombres,apellidos,esperado", [
    ("JOSE ROBER", "ENCALADA AREVALO", "ENCALADA AREVALO JOSE ROBER"),
    ("ALEXANDRA JEANINE", "UCHUARI TOLEDO", "UCHUARI TOLEDO ALEXANDRA JEANINE"),
    ("CAMPOVERDE BUSTAMANTE", "HULVIA ELIZABETH", "CAMPOVERDE BUSTAMANTE HULVIA ELIZABETH"),
    ("MARIA ANDREA", "YANAYACO RAMIREZ", "YANAYACO RAMIREZ MARIA ANDREA"),
])
def test_presentacion_apellidos_primero(nombres, apellidos, esperado):
    pila = frozenset({"JOSE", "ALEXANDRA", "ELIZABETH", "MARIA", "ANDREA"})
    assert nombre_apellidos_primero(nombres, apellidos, pila) == esperado
