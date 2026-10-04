"""Directorio local de auditores externos que son personas."""
from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
import re

import pandas as pd
import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from govdata.infrastructure.api.dependencies import get_sesion
from govdata.infrastructure.persistence.postgresql.models.auditor_ecuador_model import AuditorEcuadorModel

router = APIRouter(prefix="/auditores-ecuador", tags=["Auditores Ecuador"])
URL_EXCEL = "https://mercadodevalores.supercias.gob.ec/reportes/excel/auditores_externos.xlsx"

def _texto(valor: object) -> str | None:
    return None if pd.isna(valor) else (str(valor).strip() or None)

def _es_compania(nombre: str) -> bool:
    return bool(re.search(r"\b(S\.?A\.?S?|C\.?L\.?|CIA\.?|LTDA|COMPANIA|ASOCIADOS)\b", nombre.upper()))

@router.post("/actualizar")
def actualizar_directorio(sesion: Session = Depends(get_sesion)) -> dict:
    try:
        # El archivo oficial tiene cuatro filas informativas antes de la
        # cabecera (reporte, total y fecha de actualización).
        tabla = pd.read_excel(BytesIO(requests.get(URL_EXCEL, timeout=60).content), dtype=str, header=4)
    except Exception as exc:
        raise HTTPException(502, "No se pudo descargar el listado oficial de auditores.") from exc
    def valor(fila: object, indice: int) -> str | None:
        return _texto(fila.iloc[indice]) if len(fila) > indice else None
    filas = []
    for _, fila in tabla.iterrows():
        nombre = valor(fila, 2) or ""
        identificacion = re.sub(r"\D", "", valor(fila, 1) or "")
        rnae = valor(fila, 0)
        if not nombre or not identificacion or not rnae or _es_compania(nombre):
            continue
        filas.append({"rnae": rnae, "identificacion": identificacion, "nombre": nombre, "resolucion": valor(fila, 3), "fecha_resolucion": valor(fila, 4), "nacionalidad": valor(fila, 5), "provincia": valor(fila, 6), "canton": valor(fila, 7), "direccion": valor(fila, 8), "telefono": valor(fila, 9), "correo": valor(fila, 10), "cargado_en": datetime.now(UTC)})
    if filas:
        sentencia = insert(AuditorEcuadorModel).values(filas)
        sesion.execute(sentencia.on_conflict_do_update(index_elements=["rnae"], set_={campo: getattr(sentencia.excluded, campo) for campo in filas[0] if campo != "rnae"}))
        sesion.commit()
    return {"total": len(filas), "mensaje": "Listado de auditores personas actualizado."}

@router.get("")
def listar_auditores(q: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), sesion: Session = Depends(get_sesion)) -> dict:
    consulta = select(AuditorEcuadorModel)
    if q:
        consulta = consulta.where(AuditorEcuadorModel.nombre.ilike(f"%{q.strip()}%"))
    total = sesion.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = sesion.scalars(consulta.order_by(AuditorEcuadorModel.nombre).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [{"rnae": x.rnae, "identificacion": x.identificacion, "nombre": x.nombre, "resolucion": x.resolucion, "fecha_resolucion": x.fecha_resolucion, "nacionalidad": x.nacionalidad, "provincia": x.provincia, "canton": x.canton, "direccion": x.direccion, "telefono": x.telefono, "correo": x.correo} for x in filas], "total": total, "page": page}
