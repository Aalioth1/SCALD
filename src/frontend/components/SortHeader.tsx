export type SortDir = 'asc' | 'desc'

export type SortState<K extends string> = { key: K; dir: SortDir }

export function nextSort<K extends string>(current: SortState<K> | null, key: K): SortState<K> {
  if (current?.key !== key) return { key, dir: 'asc' }
  return { key, dir: current.dir === 'asc' ? 'desc' : 'asc' }
}

export function compareText(a: string, b: string, dir: SortDir) {
  const factor = dir === 'asc' ? 1 : -1
  return a.localeCompare(b, 'es', { numeric: true, sensitivity: 'base' }) * factor
}

type Props<K extends string> = {
  label: string
  column: K
  sort: SortState<K> | null
  onSort: (key: K) => void
}

export default function SortHeader<K extends string>({ label, column, sort, onSort }: Props<K>) {
  const active = sort?.key === column
  return (
    <th aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}>
      <button className="sort-header" onClick={() => onSort(column)} type="button">
        {label}
        <span aria-hidden="true">{active ? (sort.dir === 'asc' ? '↑' : '↓') : '↕'}</span>
      </button>
    </th>
  )
}
