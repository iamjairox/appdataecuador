# Fixtures offline -- portal DPE (modo simulacion)

Capturas usadas por los tests de integracion del `DpeScraperAdapter` sin
depender de la disponibilidad de `transparencia.dpe.gob.ec`. Si el portal
cambia de forma, estos tests dejan de reflejar la realidad -- son una
fotografia, no una garantia perpetua -- pero permiten detectar cuando nuestro
parsing deja de coincidir con la ultima forma conocida, y correr la suite
completa sin red.

| Archivo | Origen | Endpoint real que representa |
|---|---|---|
| `establishment_list_sample.json` | Real (recortado a 4 entidades de ~1919) | `GET /backend/v1/admin/public/establishment/list` |
| `months_2026_publicado.json` | Real | `GET /backend/v1/transparency/transparency/months?establishment_id=1920&year=2026&type=A` |
| `months_vacio.json` | Real | idem, `year=2025` (esa entidad no publico ese anio) |
| `active_public_junio_2026.json` | Real (recortado a 3 numerales de ~30) | `GET /backend/v1/transparency/transparency/active/public?month=6&year=2026&establishment_id=1920` |
| `active_public_sin_item_directorio.json` | Real, recombinado | Igual, sin el numeral del directorio de personal (para probar el camino "no encontrado") |
| `active_public_variante_pdf_sintetica.json` | **Sintetico** | Mismo esquema confirmado contra el portal, con `url_download` en `.pdf` -- el portal solo nos mostro un caso real en `.csv`; esta variante prueba que la deteccion de tipo no esta hardcodeada a un solo formato |

Capturados el 2026-08-04 navegando manualmente la entidad
`UNIVERSIDAD NACIONAL DE EDUCACION` (`establishment_id=1920`).

Si el portal cambia su contrato JSON, actualizar estas fixtures Y
verificar manualmente el sitio real antes de tocar el adaptador.
