type Props = {
  codigo: string
  duplicado: boolean
  busy: boolean
  error: string
  onClose: () => void
  onDelete: () => void
  onAdd: () => void
}

export default function ResolverIncidencia({ codigo, duplicado, busy, error, onClose, onDelete, onAdd }: Props) {
  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      <section
        aria-labelledby="resolver-title"
        aria-modal="true"
        className="modal"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
      >
        <h2 id="resolver-title">Resolver incidencia</h2>
        <p>
          {duplicado
            ? `¿Deseas eliminar el pistoleo duplicado de ${codigo}?`
            : `¿Deseas eliminar el pistoleo de ${codigo} o añadir ese bulto a esta hoja de ruta?`}
        </p>
        {error && <p className="form-error">{error}</p>}
        <div className="modal-actions">
          <button className={duplicado ? 'button primary' : 'button'} disabled={busy} onClick={onDelete} type="button">
            {duplicado ? 'Eliminar duplicado' : 'Eliminar pistoleo'}
          </button>
          {!duplicado && (
            <button className="button primary" disabled={busy} onClick={onAdd} type="button">Añadir bulto a esta hoja</button>
          )}
          <button className="button ghost" disabled={busy} onClick={onClose} type="button">Cancelar</button>
        </div>
      </section>
    </div>
  )
}
