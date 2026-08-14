import React from 'react'

type Props = {
  data: any | null
}

const IncidentDetail: React.FC<Props> = ({ data }) => {
  if (!data) return <div>Select an incident</div>

  const { incident, analysis, risk, fused, escalations } = data
  const [recs, setRecs] = React.useState<any[] | null>(null)
  const [fullRec, setFullRec] = React.useState<any | null>(null)

  React.useEffect(()=>{
    if (data.recommendations) setRecs(data.recommendations)
  }, [data])

  return (
    <div style={{borderLeft: '1px solid #ddd', paddingLeft: 12}}>
      <h3>{incident.title}</h3>
      <p>{incident.category} • {incident.severity}</p>
      <h4>AI Analysis</h4>
      {analysis ? <div>{analysis.assessed_severity} by {analysis.provider}</div> : <div>No analysis</div>}

      <h4>Risk</h4>
      {risk ? <div>Score: {risk.risk_score} Level: {risk.risk_level}</div> : <div>No risk assessment</div>}

      <h4>Fusion</h4>
      {fused && fused.length > 0 ? fused.map((f:any)=>(<div key={f.id}>{f.confidence} {f.reason}</div>)) : <div>No fusion</div>}

      <h4>Escalations</h4>
      {escalations && escalations.length>0 ? escalations.map((e:any)=>(<div key={e.id}>{e.triggered_rule} • {e.status}</div>)) : <div>No escalations</div>}

      <h4>Recommendations</h4>
      {recs && recs.length > 0 ? (
        <div>
          {recs.map((r:any)=>(
            <div key={r.id} style={{border: '1px dashed #aaa', padding: 6, marginBottom: 6}}>
              <div><strong>{r.recommendation_type || 'Advisory'}</strong> {r.is_fallback ? '(fallback)' : ''}</div>
              <div>Provider: {r.provider}</div>
              <div><button onClick={async ()=>{
                try{
                  const detail = await (await fetch(`/api/v1/recommendations/${r.id}`, {headers: {'Authorization': `Bearer ${localStorage.getItem('cs_token')}`}})).json()
                  setFullRec(detail)
                }catch(err){
                  setFullRec({error: 'Failed to load'})
                }
              }}>View</button></div>
            </div>
          ))}
        </div>
      ) : (<div>No recommendations</div>)}

      {fullRec && (
        <div style={{marginTop: 12, padding: 8, border: '1px solid #ccc'}}>
          <h5>Recommendation</h5>
          {fullRec.error ? <div>{fullRec.error}</div> : (
            <div>
              <div><strong>Text:</strong> {fullRec.recommendation_text}</div>
              <div><strong>Provider:</strong> {fullRec.provider}</div>
              <div><strong>Anchors:</strong> {JSON.stringify(fullRec.evidence_anchors)}</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default IncidentDetail
