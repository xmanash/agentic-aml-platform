'use client'
import { useEffect, useState } from 'react'
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

type Case = any

const API = process.env.NEXT_PUBLIC_API || '/api'

function EntityGraph({ graph }: { graph: any }) {
  const nodes = (graph?.nodes || []).slice(0, 18)
  const ids = new Set(nodes.map((node: any) => node.id))
  const links = (graph?.links || graph?.edges || []).filter((link: any) => ids.has(link.source) && ids.has(link.target))
  if (!nodes.length) {
    return <p className="text-sm text-zinc-500">No entity graph for this case.</p>
  }
  const pos: Record<string, { x: number; y: number }> = {}
  nodes.forEach((node: any, index: number) => {
    const angle = (2 * Math.PI * index) / nodes.length
    const radius = nodes.length === 1 ? 0 : 78
    pos[node.id] = { x: 160 + radius * Math.cos(angle), y: 100 + radius * Math.sin(angle) }
  })
  return (
    <svg viewBox="0 0 320 200" className="w-full h-52">
      {links.map((link: any, index: number) => {
        const source = pos[link.source]
        const target = pos[link.target]
        if (!source || !target) return null
        return <line key={index} x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke="#52525b" />
      })}
      {nodes.map((node: any) => (
        <g key={node.id}>
          <circle cx={pos[node.id].x} cy={pos[node.id].y} r="8" fill="#18181b" stroke="#e4e4e7" />
          <text x={pos[node.id].x} y={pos[node.id].y + 18} textAnchor="middle" fontSize="8" fill="#a1a1aa">
            {String(node.id).slice(0, 16)}
          </text>
        </g>
      ))}
    </svg>
  )
}

export default function Dashboard() {
  const [cases, setCases] = useState<Case[]>([])
  const [selected, setSelected] = useState<Case | null>(null)
  const [loading, setLoading] = useState(false)
  const [role, setRole] = useState('analyst')
  const [notice, setNotice] = useState('')
  const [audit, setAudit] = useState<any[]>([])
  const [error, setError] = useState('')

  function headers(json = false) {
    const value: Record<string, string> = { 'X-Role': role }
    if (json) value['Content-Type'] = 'application/json'
    return value
  }

  useEffect(() => {
    let stop = false
    async function tick() {
      try {
        const response = await fetch(`${API}/cases`, { headers: { 'X-Role': role } })
        const body = await response.json()
        if (stop) return
        const rows = Array.isArray(body) ? body : []
        setCases(rows)
        setSelected((prev: Case | null) => {
          if (!prev) return prev
          return rows.find((item: Case) => item.case_id === prev.case_id) || prev
        })
      } catch (err) {
        console.log(err)
      }
    }
    tick()
    const id = setInterval(tick, 5000)
    return () => {
      stop = true
      clearInterval(id)
    }
  }, [role])

  useEffect(() => {
    if (!selected?.case_id) {
      setAudit([])
      return
    }
    let stop = false
    fetch(`${API}/audit/logs?case_id=${selected.case_id}`, { headers: { 'X-Role': role } })
      .then((response) => response.json())
      .then((body) => {
        if (!stop) setAudit(Array.isArray(body) ? body : [])
      })
      .catch(() => {
        if (!stop) setAudit([])
      })
    return () => {
      stop = true
    }
  }, [selected?.case_id, role])

  async function runSynthetic() {
    setLoading(true)
    setError('')
    setNotice('')
    try {
      const txsRes = await fetch(`${API}/synthetic/transactions?n=30`)
      const txs = await txsRes.json()
      const payload = {
        transactions: txs.map((tx: any) => ({ ...tx, timestamp: new Date().toISOString() })),
        kyc_docs: [{ doc_type: 'passport', content_text: 'Name: John Smith Passport No: X123' }],
      }
      const response = await fetch(`${API}/ingest/transactions`, {
        method: 'POST',
        headers: headers(true),
        body: JSON.stringify(payload),
      })
      const body = await response.json()
      if (!response.ok) {
        setError(body.detail ? JSON.stringify(body.detail) : 'Investigation failed')
      } else {
        setSelected(body)
      }
    } catch (err) {
      setError('Could not reach the API')
    }
    setLoading(false)
  }

  async function sendFeedback(decision: string) {
    if (!selected) return
    setNotice('')
    const response = await fetch(`${API}/cases/${selected.case_id}/feedback`, {
      method: 'POST',
      headers: headers(true),
      body: JSON.stringify({ decision, notes: decision === 'confirmed' ? 'BSA confirmed' : 'Analyst marked false positive' }),
    })
    if (!response.ok) {
      setNotice('Feedback was not saved')
      return
    }
    const body = await response.json()
    setNotice(body.tuning?.status === 'pending_approval'
      ? 'Feedback saved. Further threshold changes need approval.'
      : 'Feedback saved. Optimization Agent recorded a bounded weight change.')
  }

  const chart = (selected?.transactions || []).slice(0, 20).map((tx: any, index: number) => ({
    name: String(index + 1),
    amount: tx.amount,
  }))
  const reviewable = selected && (selected.status === 'escalated' || selected.status === 'sar_draft')

  return (
    <div className="min-h-screen p-6 grid grid-cols-12 gap-6">
      <div className="col-span-12 flex justify-between items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agentic AML — Investigation Console</h1>
          <p className="text-zinc-400">Multi-agent orchestration • Pinecone • Supabase • MCP • Audit Chain</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setRole(role === 'officer' ? 'analyst' : 'officer')} className="border border-zinc-600 px-4 py-2 rounded-full text-sm">
            {role === 'officer' ? 'View as analyst' : 'View as officer'}
          </button>
          <button onClick={runSynthetic} disabled={loading} className="bg-white text-black px-5 py-2 rounded-full font-medium hover:bg-zinc-200 disabled:opacity-50">
            {loading ? 'Investigating...' : 'Run Synthetic Investigation'}
          </button>
        </div>
      </div>

      <div className="col-span-4 bg-zinc-900 rounded-2xl p-4 border border-zinc-800">
        <h2 className="font-semibold mb-3">Case Queue ({cases.length})</h2>
        <div className="space-y-2 max-h-[70vh] overflow-auto">
          {cases.map((item: any) => (
            <div key={item.case_id} onClick={() => setSelected(item)} className={`p-3 rounded-xl cursor-pointer border ${selected?.case_id === item.case_id ? 'bg-zinc-800 border-white' : 'bg-zinc-900 border-zinc-800 hover:border-zinc-700'}`}>
              <div className="flex justify-between">
                <span className="text-xs text-zinc-400">{item.case_id.slice(0, 8)}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${item.status === 'sar_draft' ? 'bg-red-500/20 text-red-300' : item.status === 'escalated' ? 'bg-amber-500/20 text-amber-300' : 'bg-green-500/20 text-green-300'}`}>{item.status}</span>
              </div>
              <div className="font-medium">Risk {item.risk_score}</div>
              <div className="text-xs text-zinc-500 truncate">{item.explanation?.[1]?.slice(0, 80)}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="col-span-8 space-y-6">
        {error && <div className="bg-red-500/10 text-red-300 rounded-xl p-3 text-sm">{error}</div>}
        {!selected && <div className="bg-zinc-900 rounded-2xl p-12 text-center border border-zinc-800 text-zinc-500">Select a case or run synthetic investigation to see the agent workflow</div>}
        {selected && (
          <>
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-zinc-900 rounded-2xl p-4 border border-zinc-800">
                <div className="text-zinc-400 text-sm">Risk Score</div>
                <div className="text-4xl font-bold">{selected.risk_score}</div>
                <div className="mt-2 h-2 bg-zinc-800 rounded-full"><div className="h-2 bg-white rounded-full" style={{ width: `${Math.min(selected.risk_score, 100)}%` }} /></div>
              </div>
              <div className="bg-zinc-900 rounded-2xl p-4 border border-zinc-800">
                <div className="text-zinc-400 text-sm">Entities Linked</div>
                <div className="text-2xl font-bold">{selected.entities?.length || 0}</div>
                <div className="text-xs text-zinc-500 truncate">{selected.entities?.map((entity: any) => entity.name).join(', ')}</div>
              </div>
              <div className="bg-zinc-900 rounded-2xl p-4 border border-zinc-800">
                <div className="text-zinc-400 text-sm">Evidence Items</div>
                <div className="text-2xl font-bold">{selected.evidence?.length || 0}</div>
                <div className="text-xs text-zinc-500">Sanctions {selected.evidence?.filter((item: any) => item.source === 'sanctions').length || 0} hits</div>
              </div>
              <div className="bg-zinc-900 rounded-2xl p-4 border border-zinc-800">
                <div className="text-zinc-400 text-sm">Confidence</div>
                <div className="text-xl font-bold">{selected.confidence === 'low_confidence' ? 'Low' : 'High'}</div>
                <div className="text-xs text-zinc-500">{role === 'officer' ? 'Officer view' : 'PII masked'}</div>
              </div>
            </div>

            <div className="bg-zinc-900 rounded-2xl p-4 border border-zinc-800">
              <h3 className="font-semibold mb-2">Reason codes</h3>
              <div className="flex flex-wrap gap-2">
                {(selected.reason_codes || []).map((code: string) => (
                  <span key={code} className="text-xs px-2 py-1 rounded-full bg-zinc-800">{code}</span>
                ))}
                {!selected.reason_codes?.length && <span className="text-sm text-zinc-500">No reason codes</span>}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-zinc-900 rounded-2xl p-4 border border-zinc-800">
                <h3 className="font-semibold mb-2">Amount profile</h3>
                <div className="h-40">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chart}>
                      <XAxis dataKey="name" hide />
                      <YAxis hide />
                      <Tooltip />
                      <Bar dataKey="amount" fill="#e4e4e7" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="bg-zinc-900 rounded-2xl p-4 border border-zinc-800">
                <h3 className="font-semibold mb-2">Entity graph</h3>
                <EntityGraph graph={selected.graph} />
              </div>
            </div>

            <div className="bg-zinc-900 rounded-2xl p-4 border border-zinc-800">
              <h3 className="font-semibold mb-2">Similar cases</h3>
              <div className="space-y-2">
                {(selected.memory_hits || []).map((hit: any) => (
                  <div key={hit.case_id} className="text-sm text-zinc-300">
                    {hit.case_id} · {Math.round((hit.similarity || 0) * 100)}% · {hit.summary}
                  </div>
                ))}
                {!selected.memory_hits?.length && <p className="text-sm text-zinc-500">No similar cases in memory yet.</p>}
              </div>
            </div>

            <div className="bg-zinc-900 rounded-2xl p-4 border border-zinc-800">
              <h3 className="font-semibold mb-2">Agent reasoning and evidence</h3>
              <div className="space-y-2">
                {selected.explanation?.map((line: string, index: number) => (
                  <div key={index} className="text-sm text-zinc-300 bg-zinc-950 p-2 rounded-lg">{line}</div>
                ))}
              </div>
              <div className="mt-4">
                {selected.evidence?.map((item: any, index: number) => (
                  <div key={index} className="flex gap-2 text-xs border-b border-zinc-800 py-2">
                    <span className="px-2 py-0.5 bg-zinc-800 rounded">{item.source}</span>
                    <span>{item.description}</span>
                    <span className="ml-auto text-zinc-500">w:{item.risk_weight}</span>
                  </div>
                ))}
              </div>
            </div>

            {selected.confidence === 'low_confidence' && (
              <div className="bg-amber-500/10 text-amber-200 rounded-2xl p-4 text-sm">Low confidence. A filing-ready SAR needs at least two evidence items.</div>
            )}

            {selected.sar_draft && (
              <div className="bg-white text-black rounded-2xl p-6">
                <h3 className="font-bold text-lg mb-2">SAR draft</h3>
                <pre className="whitespace-pre-wrap text-sm font-mono">{selected.sar_draft}</pre>
              </div>
            )}

            {reviewable && (
              <div className="flex gap-2 items-center">
                <button onClick={() => sendFeedback('confirmed')} className="bg-white text-black px-4 py-2 rounded-full">Confirm SAR</button>
                <button onClick={() => sendFeedback('false_positive')} className="border border-zinc-500 px-4 py-2 rounded-full">Mark false positive</button>
                {notice && <span className="text-sm text-zinc-300">{notice}</span>}
              </div>
            )}

            <div className="bg-zinc-900 rounded-2xl p-4 border border-zinc-800">
              <h3 className="font-semibold mb-2">Audit chain</h3>
              <div className="text-xs font-mono text-zinc-500 break-all mb-3">{selected.audit_hash}</div>
              <div className="space-y-1">
                {audit.map((row, index) => (
                  <div key={index} className="text-xs text-zinc-400 flex justify-between gap-3">
                    <span>{row.agent}</span>
                    <span>{row.action}</span>
                    <span className="font-mono truncate">{row.hash}</span>
                  </div>
                ))}
                {!audit.length && <p className="text-sm text-zinc-500">No audit events loaded.</p>}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
