import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

from app.schemas.reporte import ReporteResumen

ZONA = ZoneInfo("America/Santiago")
_DLLS = (
    Path(r"C:\msys64\ucrt64\bin"),
    Path(r"C:\msys64\mingw64\bin"),
    Path(r"C:\Program Files\GTK3-Runtime Win64\bin"),
)


class PdfNoDisponible(RuntimeError):
    pass


@dataclass
class LineaHoja:
    codigo: str
    tipo: str
    fecha: date
    ruta: str
    transporte: str | None
    estado: str
    esperados: int
    pistoleados: int
    faltantes: int
    incidencias: int


@dataclass
class BultoPendiente:
    codigo: str
    hoja: str
    ruta: str
    fecha: date


@dataclass
class IncidenciaPdf:
    fecha: datetime
    hoja: str
    bulto: str
    tipo: str
    estado: str
    observaciones: str | None


def generar_pdf_operativo(
    *,
    resumen: ReporteResumen,
    autor: str,
    fecha_desde: date | None,
    fecha_hasta: date | None,
    hojas: list[LineaHoja],
    faltantes: list[BultoPendiente],
    incidencias: list[IncidenciaPdf],
) -> tuple[bytes, str]:
    html = _html(
        resumen=resumen,
        autor=autor,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        hojas=hojas,
        faltantes=faltantes,
        incidencias=incidencias,
    )
    return _renderizar(html), nombre_archivo(fecha_desde, fecha_hasta)


def nombre_archivo(fecha_desde: date | None, fecha_hasta: date | None) -> str:
    if fecha_desde and fecha_hasta and fecha_desde == fecha_hasta:
        return f"reporte-operativo-{fecha_desde.isoformat()}.pdf"
    if fecha_desde or fecha_hasta:
        inicio = fecha_desde.isoformat() if fecha_desde else "inicio"
        fin = fecha_hasta.isoformat() if fecha_hasta else "hoy"
        return f"reporte-operativo-{inicio}-a-{fin}.pdf"
    return "reporte-operativo.pdf"


def _renderizar(html: str) -> bytes:
    _preparar_dlls()
    try:
        from weasyprint import HTML
    except OSError as exc:
        raise PdfNoDisponible(
            "WeasyPrint no encuentra las librerías gráficas (Pango). "
            "Instale Pango y deje accesible la carpeta de DLL, por ejemplo C:\\msys64\\ucrt64\\bin."
        ) from exc
    return HTML(string=html).write_pdf()


def _preparar_dlls() -> None:
    if os.name != "nt":
        return
    existentes = [str(path) for path in _DLLS if path.is_dir()]
    if not existentes:
        return
    actual = os.environ.get("WEASYPRINT_DLL_DIRECTORIES", "")
    carpetas: list[str] = []
    for parte in existentes + actual.split(os.pathsep):
        if parte and parte not in carpetas:
            carpetas.append(parte)
    os.environ["WEASYPRINT_DLL_DIRECTORIES"] = os.pathsep.join(carpetas)


def _html(
    *,
    resumen: ReporteResumen,
    autor: str,
    fecha_desde: date | None,
    fecha_hasta: date | None,
    hojas: list[LineaHoja],
    faltantes: list[BultoPendiente],
    incidencias: list[IncidenciaPdf],
) -> str:
    pistoleados = max(resumen.total_bultos_esperados - resumen.faltantes, 0)
    eficiencia = _porcentaje(pistoleados, resumen.total_bultos_esperados)
    generado = datetime.now(ZONA).strftime("%d/%m/%Y %H:%M")
    pendientes, regularizadas = _conteo_incidencias(incidencias)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte operativo</title>
  <style>
    @page {{
      size: A4;
      margin: 14mm 12mm 16mm;
      @bottom-left {{
        content: "SCALD  ·  Reporte operativo";
        font-family: "Segoe UI", sans-serif;
        font-size: 8pt;
        color: #8b909a;
      }}
      @bottom-right {{
        content: counter(page) " / " counter(pages);
        font-family: "Segoe UI", sans-serif;
        font-size: 8pt;
        color: #8b909a;
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: #1c1f26;
      font-family: "Segoe UI", sans-serif;
      font-size: 9.5pt;
      line-height: 1.35;
    }}
    h1, h2, p {{ margin: 0; }}
    .banner {{
      background: #1c1f26;
      color: white;
      border-radius: 12px;
      padding: 16px 18px;
      margin-bottom: 14px;
    }}
    .banner-table {{ width: 100%; border-collapse: collapse; }}
    .banner-table td {{ vertical-align: top; border: 0; padding: 0; }}
    .eyebrow {{
      color: #ff7a1a;
      font-size: 8pt;
      font-weight: 700;
      letter-spacing: 0.16em;
    }}
    h1 {{ font-size: 22pt; letter-spacing: -0.03em; margin-top: 2px; }}
    .period {{ color: #d7dbe3; margin-top: 4px; }}
    .meta {{ text-align: right; color: #d7dbe3; font-size: 8.5pt; }}
    .meta strong {{ display: block; color: white; font-size: 10pt; margin-bottom: 2px; }}
    .kpis {{ width: 100%; border-collapse: separate; border-spacing: 8px 0; margin: 0 -8px 12px; }}
    .kpis td {{
      width: 25%;
      background: #f8f9fb;
      border: 1px solid #e7e8ec;
      border-radius: 10px;
      padding: 10px 12px;
    }}
    .kpis span {{ display: block; color: #8b909a; font-size: 8pt; }}
    .kpis strong {{ display: block; font-size: 16pt; letter-spacing: -0.03em; margin-top: 2px; }}
    .panel {{
      border: 1px solid #e7e8ec;
      border-radius: 12px;
      padding: 12px 14px;
      margin-bottom: 16px;
    }}
    .panel-head {{ width: 100%; border-collapse: collapse; margin-bottom: 8px; }}
    .panel-head td {{ border: 0; padding: 0; }}
    .efficiency {{ text-align: right; font-size: 14pt; font-weight: 700; color: #16a34a; }}
    .bar {{ height: 8px; background: #ffe8ee; border-radius: 99px; overflow: hidden; }}
    .bar-fill {{ height: 8px; background: #16a34a; }}
    .stats {{ width: 100%; border-collapse: separate; border-spacing: 6px 0; margin: 10px -6px 0; }}
    .stats td {{
      background: #f8f9fb;
      border-radius: 8px;
      padding: 7px 8px;
      width: 16.66%;
    }}
    .stats span {{ display: block; color: #8b909a; font-size: 7.5pt; }}
    .stats strong {{ font-size: 11pt; }}
    h2 {{
      font-size: 12pt;
      margin: 16px 0 8px;
      padding-bottom: 4px;
      border-bottom: 2px solid #ff7a1a;
    }}
    table.data {{ width: 100%; border-collapse: collapse; }}
    table.data th {{
      text-align: left;
      font-size: 7.5pt;
      color: #8b909a;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 6px 6px;
      border-bottom: 1px solid #e7e8ec;
    }}
    table.data td {{
      padding: 6px;
      border-bottom: 1px solid #f0f1f4;
      vertical-align: top;
    }}
    tr {{ break-inside: avoid; }}
    thead {{ display: table-header-group; }}
    .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .code {{ font-weight: 700; }}
    .muted {{ color: #8b909a; }}
    .pill {{
      display: inline-block;
      border-radius: 99px;
      padding: 1px 7px;
      font-size: 7.5pt;
      font-weight: 700;
    }}
    .pill.ok {{ background: #e8f8ee; color: #16a34a; }}
    .pill.warn {{ background: #fff6df; color: #d97706; }}
    .pill.bad {{ background: #ffe8ee; color: #e11d48; }}
    .empty {{ color: #8b909a; padding: 8px 0 2px; }}
    .note {{ color: #8b909a; font-size: 8pt; margin-top: 10px; }}
  </style>
</head>
<body>
  <header class="banner">
    <table class="banner-table">
      <tr>
        <td>
          <p class="eyebrow">SCALD</p>
          <h1>Reporte operativo</h1>
          <p class="period">{escape(_periodo(fecha_desde, fecha_hasta))}</p>
        </td>
        <td class="meta">
          <strong>{escape(autor or "Usuario")}</strong>
          Generado el {escape(generado)}
        </td>
      </tr>
    </table>
  </header>

  <table class="kpis">
    <tr>
      {_kpi("Hojas", resumen.total_hojas)}
      {_kpi("Bultos esperados", resumen.total_bultos_esperados)}
      {_kpi("Pistoleados", pistoleados)}
      {_kpi("Faltantes", resumen.faltantes)}
    </tr>
  </table>

  <section class="panel">
    <table class="panel-head">
      <tr>
        <td>Eficiencia de pistoleo</td>
        <td class="efficiency">{eficiencia}</td>
      </tr>
    </table>
    <div class="bar"><div class="bar-fill" style="width: {eficiencia.rstrip('%')}%"></div></div>
    <table class="stats">
      <tr>
        {_mini("Pistoleos", resumen.total_pistoleos)}
        {_mini("OK", resumen.ok)}
        {_mini("Duplicados", resumen.duplicados)}
        {_mini("Sin lista", resumen.sin_lista_esperada)}
        {_mini("No pertenece", resumen.no_pertenece)}
        {_mini("Reasignados", resumen.reasignados)}
      </tr>
    </table>
  </section>

  <h2>Hojas de ruta</h2>
  {_tabla_hojas(hojas)}

  <h2>Bultos faltantes</h2>
  {_tabla_faltantes(faltantes)}

  <h2>Incidencias</h2>
  {_tabla_incidencias(incidencias)}
  <p class="note">Pendientes: {_num(pendientes)} · Regularizadas: {_num(regularizadas)}</p>
</body>
</html>
"""


def _kpi(etiqueta: str, valor: int) -> str:
    return f"<td><span>{escape(etiqueta)}</span><strong>{_num(valor)}</strong></td>"


def _mini(etiqueta: str, valor: int) -> str:
    return f"<td><span>{escape(etiqueta)}</span><strong>{_num(valor)}</strong></td>"


def _tabla_hojas(hojas: list[LineaHoja]) -> str:
    if not hojas:
        return '<p class="empty">No hay hojas de ruta en este periodo.</p>'
    filas = []
    for hoja in hojas:
        transporte = f'<br><span class="muted">{escape(hoja.transporte)}</span>' if hoja.transporte else ""
        filas.append(
            "<tr>"
            f'<td class="code">{escape(hoja.codigo)}</td>'
            f"<td>{escape(hoja.tipo)}</td>"
            f"<td>{_fecha(hoja.fecha)}</td>"
            f"<td>{escape(hoja.ruta)}{transporte}</td>"
            f"<td>{_pill(hoja.estado)}</td>"
            f'<td class="num">{_num(hoja.esperados)}</td>'
            f'<td class="num">{_num(hoja.pistoleados)}</td>'
            f'<td class="num">{_num(hoja.faltantes)}</td>'
            f'<td class="num">{_num(hoja.incidencias)}</td>'
            "</tr>"
        )
    return (
        "<table class='data'><thead><tr>"
        "<th>Código</th><th>Tipo</th><th>Registro</th><th>Ruta</th><th>Estado</th>"
        "<th class='num'>Esperados</th><th class='num'>Pistoleados</th><th class='num'>Faltantes</th><th class='num'>Incid.</th>"
        "</tr></thead><tbody>"
        + "".join(filas)
        + "</tbody></table>"
    )


def _tabla_faltantes(faltantes: list[BultoPendiente]) -> str:
    if not faltantes:
        return '<p class="empty">No hay bultos pendientes de pistoleo.</p>'
    filas = [
        "<tr>"
        f'<td class="code">{escape(item.codigo)}</td>'
        f"<td>{escape(item.hoja)}</td>"
        f"<td>{_fecha(item.fecha)}</td>"
        f"<td>{escape(item.ruta)}</td>"
        "</tr>"
        for item in faltantes
    ]
    return (
        "<table class='data'><thead><tr><th>Bulto</th><th>Hoja</th><th>Registro</th><th>Ruta</th></tr></thead><tbody>"
        + "".join(filas)
        + "</tbody></table>"
    )


def _tabla_incidencias(incidencias: list[IncidenciaPdf]) -> str:
    if not incidencias:
        return '<p class="empty">No hay incidencias en este periodo.</p>'
    filas = []
    for item in incidencias:
        nota = escape(_observacion_incidencia(item))
        filas.append(
            "<tr>"
            f"<td>{escape(_momento(item.fecha))}</td>"
            f"<td>{escape(item.hoja)}</td>"
            f'<td class="code">{escape(item.bulto)}</td>'
            f"<td>{escape(item.tipo)}</td>"
            f"<td>{_pill(_estado_incidencia(item.estado))}</td>"
            f"<td>{nota}</td>"
            "</tr>"
        )
    return (
        "<table class='data'><thead><tr>"
        "<th>Registro</th><th>Hoja</th><th>Bulto</th><th>Tipo</th><th>Estado</th><th>Observaciones</th>"
        "</tr></thead><tbody>"
        + "".join(filas)
        + "</tbody></table>"
    )


def _observacion_incidencia(item: IncidenciaPdf) -> str:
    tipo = item.tipo.upper()
    estado = item.estado.upper()
    if tipo in {"NO PERTENECE", "SIN LISTA ESPERADA"} and estado != "PENDIENTE":
        if estado == "ANULADO":
            return "Pistoleo eliminado"
        if estado == "REASIGNADO":
            return "El bulto se cambió a esta ruta"
    if item.observaciones:
        return item.observaciones
    return "—"


def _estado_incidencia(estado: str) -> str:
    if estado.upper() == "PENDIENTE":
        return "PENDIENTE"
    return "REGULARIZADO"


def _conteo_incidencias(incidencias: list[IncidenciaPdf]) -> tuple[int, int]:
    pendientes = sum(1 for item in incidencias if item.estado.upper() == "PENDIENTE")
    return pendientes, len(incidencias) - pendientes


def _pill(estado: str) -> str:
    normal = estado.upper()
    if normal in {"OK", "ACTIVA", "REGULARIZADO", "COMPLETADA"}:
        clase = "ok"
    elif normal in {"PENDIENTE", "FALTANTE", "CERRADA", "NO PERTENECE", "INACTIVA"}:
        clase = "bad"
    else:
        clase = "warn"
    return f'<span class="pill {clase}">{escape(estado)}</span>'


def _periodo(fecha_desde: date | None, fecha_hasta: date | None) -> str:
    if fecha_desde and fecha_hasta and fecha_desde == fecha_hasta:
        return f"Fecha de registro · {_fecha(fecha_desde)}"
    if fecha_desde and fecha_hasta:
        return f"Fecha de registro · del {_fecha(fecha_desde)} al {_fecha(fecha_hasta)}"
    if fecha_desde:
        return f"Fecha de registro · desde el {_fecha(fecha_desde)}"
    if fecha_hasta:
        return f"Fecha de registro · hasta el {_fecha(fecha_hasta)}"
    return "Fecha de registro · todo el historial"


def _fecha(valor: date) -> str:
    return valor.strftime("%d/%m/%Y")


def _momento(valor: datetime) -> str:
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(ZONA).strftime("%d/%m/%Y %H:%M")


def _num(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def _porcentaje(parte: int, total: int) -> str:
    if not total:
        return "0%"
    return f"{(parte / total) * 100:.1f}%"
