# Fixtures -- Modulo 4 (Motor de Extraccion)

Generadas con `python tests/fixtures/extraccion/_generar.py` (usa
`reportlab` para PDFs y `openpyxl` para Excel -- ambas dependencias de
`dev`). Ningun archivo aqui viene de un documento real de una entidad;
todos son sinteticos pero con la MISMA forma que el Modulo 2 encuentra en
la practica (headers variables, filas vacias, formatos mixtos).

| Archivo | Proposito |
|---|---|
| `directorio_con_tabla.pdf` | PDF con tabla real (bordes dibujados) -- estrategia camelot |
| `directorio_con_texto.pdf` | PDF de solo texto posicionado (sin tabla real) -- fallback pdfplumber |
| `directorio_escaneado.pdf` | Sin capa de texto -- debe detectarse como `REQUIERE_OCR` |
| `pdf_vacio.pdf` | Una pagina en blanco -- caso "PDF vacio" |
| `directorio.xlsx` | Encabezados variados (`Servidor`, `Puesto`, `Unidad`...) + una fila vacia intercalada |
| `columnas_desconocidas.xlsx` | Ninguna columna coincide con el diccionario de sinonimos -- todas las filas deben descartarse sin error |
| `excel_vacio.xlsx` | Workbook sin filas |
| `directorio.csv` | Delimitador `;`, encabezado `Apellidos y Nombres` (combinado) |
| `csv_vacio.csv` | Archivo de 0 bytes |
| `corrupto.pdf` / `corrupto.xlsx` / `corrupto.csv` | Bytes invalidos para cada formato -- deben producir `EstadoParseo.ERROR`, nunca una excepcion sin capturar |
| `legado_incompleto.xls` | Solo la firma OLE, sin contenido real (ver nota en `_generar.py` sobre por que no se genera un `.xls` completo) |

Todas las filas "relevantes" usan cargos del catalogo de
`config/rules/clasificacion_areas.yaml` (Director Juridico, Asesora
Juridica, Director Financiero) mezclados con cargos que deben
descartarse (Contadora, Chofer) -- para probar que el clasificador
filtra correctamente extremo a extremo.
