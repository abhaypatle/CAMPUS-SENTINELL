import React from 'react'

type Props = {
  incidents: any[]
  onSelect: (id: string) => void
}

const IncidentList: React.FC<Props> = ({ incidents, onSelect }) => {
  return (
    <div>
      {incidents.map((i) => (
        <div key={i.id} style={{border: '1px solid #ccc', padding: 8, marginBottom: 8}}>
          <div><strong>{i.title}</strong></div>
          <div>{i.category} • {i.severity} • {i.status}</div>
          <div><button onClick={() => onSelect(i.id)}>View</button></div>
        </div>
      ))}
    </div>
  )
}

export default IncidentList
