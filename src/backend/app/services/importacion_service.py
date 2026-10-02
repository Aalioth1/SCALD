from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.bulto import Bulto
from app.models.auditoria import Auditoria
from app.models.hoja_ruta import HojaRuta
from app.schemas.importacion import ImportacionArchivoResultado, ImportacionResponse
from app.services.pdf_parser_service import PdfParseError, parse_pdf_bytes

MAX_PDF_BYTES = 10 * 1024 * 1024


class ImportacionService:
    def __init__(self, db: Session):
        self.db = db

    def importar(self, archivos: list[tuple[str, str | None, bytes]], usuario_id: int) -> ImportacionResponse:
        resultados: list[ImportacionArchivoResultado] = []
        hojas_creadas = 0
        hojas_actualizadas = 0
        bultos_creados = 0

        for filename, content_type, content in archivos:
            try:
                self._validate_file(filename, content_type, content)
                parsed = parse_pdf_bytes(content, filename)
                with self.db.begin_nested():
                    hoja = self.db.query(HojaRuta).filter(
                        HojaRuta.codigo == parsed["codigo"],
                        HojaRuta.usuario_id == usuario_id,
                    ).first()
                    if hoja is None:
                        hoja = HojaRuta(
                            codigo=parsed["codigo"],
                            tipo=parsed["tipo"],
                            fecha=parsed["fecha"],
                            ruta=parsed["ruta"],
                            transporte=parsed["transporte"],
                            cantidad_declarada=parsed["cantidad_declarada"],
                            estado="ACTIVA",
                            activo=True,
                            usuario_id=usuario_id,
                            created_at=date.today(),
                        )
                        self.db.add(hoja)
                        self.db.flush()
                        hojas_creadas += 1
                    else:
                        hoja.fecha = parsed["fecha"]
                        hoja.ruta = parsed["ruta"]
                        hoja.transporte = parsed["transporte"]
                        hoja.cantidad_declarada = parsed["cantidad_declarada"]
                        hoja.activo = True
                        hoja.estado = "ACTIVA"
                        hoja.situacion = "VIGENTE"
                        hojas_actualizadas += 1

                    created = 0
                    existing = 0
                    for codigo_bulto in parsed["bultos"]:
                        found = self.db.query(Bulto).filter(
                            Bulto.hoja_ruta_id == hoja.id,
                            Bulto.codigo == codigo_bulto,
                        ).first()
                        if found is not None:
                            existing += 1
                            continue
                        self.db.add(
                            Bulto(
                                codigo=codigo_bulto,
                                hoja_ruta_id=hoja.id,
                                usuario_id=usuario_id,
                                estado="PENDIENTE",
                                pistoleado=False,
                                fecha=parsed["fecha"] or date.today(),
                                info_adicional=f"Importado desde {filename}",
                            )
                        )
                        created += 1

                    self.db.add(
                        Auditoria(
                            usuario_id=usuario_id,
                            entidad="HOJA_RUTA",
                            entidad_id=hoja.id,
                            accion="IMPORTAR_PDF",
                            datos_nuevos={
                                "codigo": parsed["codigo"],
                                "archivo": filename,
                                "bultos": len(parsed["bultos"]),
                            },
                        )
                    )

                bultos_creados += created
                resultados.append(
                    ImportacionArchivoResultado(
                        archivo=filename,
                        exitoso=True,
                        hoja_ruta=parsed["codigo"],
                        bultos_creados=created,
                        bultos_existentes=existing,
                    )
                )
            except (PdfParseError, ValueError, HTTPException) as exc:
                resultados.append(
                    ImportacionArchivoResultado(
                        archivo=filename,
                        exitoso=False,
                        error=str(exc),
                    )
                )
            except SQLAlchemyError:
                resultados.append(
                    ImportacionArchivoResultado(
                        archivo=filename,
                        exitoso=False,
                        error="No se pudo guardar la información del archivo",
                    )
                )

        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se pudo confirmar la importación",
            ) from exc

        exitosos = sum(1 for resultado in resultados if resultado.exitoso)
        return ImportacionResponse(
            archivos_procesados=len(resultados),
            archivos_exitosos=exitosos,
            archivos_fallidos=len(resultados) - exitosos,
            hojas_creadas=hojas_creadas,
            hojas_actualizadas=hojas_actualizadas,
            bultos_creados=bultos_creados,
            resultados=resultados,
        )

    @staticmethod
    def _validate_file(filename: str, content_type: str | None, content: bytes) -> None:
        if not filename.lower().endswith(".pdf"):
            raise ValueError("El archivo debe tener extensión .pdf")
        if len(content) > MAX_PDF_BYTES:
            raise ValueError("El archivo supera el tamaño máximo permitido de 10 MB")
        if content_type not in (None, "application/pdf"):
            raise ValueError("El tipo de archivo debe ser application/pdf")
