import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { admin } from '../services/admin'
import IncidentList from '../components/Admin/IncidentList'
import IncidentDetail from '../components/Admin/IncidentDetail'

const AdminDashboard: React.FC = () => {
  const { user } = useAuth()
  const [incidents, setIncidents] = useState<any[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] = useState<any | null>(null)

  useEffect(()=>{
    if (!user) return
    if (user.role !== 'ADMIN' && user.role !== 'RESPONDER') return
    admin.listIncidents().then((d:any)=>setIncidents(d)).catch(()=>setIncidents([]))
  }, [user])

  useEffect(()=>{
    if (!selected) return
    admin.intelligence(selected).then((d:any)=>setDetail(d)).catch(()=>setDetail(null))
  }, [selected])

  if (!user) return null
  if (user.role !== 'ADMIN' && user.role !== 'RESPONDER') return <div>Insufficient privileges</div>

  return (
    <div className="container">
      <header>
        <h1>Admin Command Center</h1>
      </header>

      <main style={{display: 'flex', gap: 12}}>
        <div style={{flex: 1}}>
          <h2>Incidents</h2>
          <IncidentList incidents={incidents} onSelect={(id)=>setSelected(id)} />
        </div>
        <div style={{width: 420}}>
          <IncidentDetail data={detail} />
        </div>
      </main>
    </div>
  )
}

export default AdminDashboard
