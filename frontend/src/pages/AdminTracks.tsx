import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Map, ChevronDown, ChevronRight, Users, CheckCircle2, ClipboardCheck } from 'lucide-react'
import { adminTracksOverview } from '@/services/api'

export default function AdminTracks() {
  const { data, isLoading } = useQuery({ queryKey: ['adm-tracks'], queryFn: adminTracksOverview })
  const [open, setOpen] = useState<string | null>(null)
  const groupName = (key?: string) => data?.groups.find(g => g.key === key)?.name || key || '—'

  return (
    <div>
      <div className="au-title-row">
        <div>
          <h1 className="hist-title"><Map size={20} style={{ verticalAlign: -3 }} /> Visão por Trilha</h1>
          <p className="muted hist-sub">Quem está matriculado em cada trilha e o progresso: aulas concluídas, simulados e aprovações.</p>
        </div>
        <Link className="btn" to="/admin">← Admin</Link>
      </div>

      {isLoading ? <div className="spinner" /> : (
        <div style={{ display: 'grid', gap: 12 }}>
          {(data?.tracks ?? []).map(tr => {
            const isOpen = open === tr.key
            return (
              <div key={tr.key} className="card" style={{ padding: 0, overflow: 'hidden', borderLeft: `4px solid ${tr.color || 'var(--brand-primary)'}` }}>
                <button onClick={() => setOpen(isOpen ? null : tr.key)}
                  style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', cursor: 'pointer', padding: 18, display: 'flex', alignItems: 'center', gap: 14 }}>
                  {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                  <div style={{ flex: 1 }}>
                    <h3 style={{ margin: 0, fontSize: 16 }}>{tr.name}</h3>
                    <p className="muted" style={{ fontSize: 13, margin: '2px 0 0' }}>{tr.description}</p>
                  </div>
                  <div style={{ display: 'flex', gap: 22, textAlign: 'center' }}>
                    <div><div style={{ fontWeight: 800, fontSize: 18 }}><Users size={14} style={{ verticalAlign: -2 }} /> {tr.enrolled_count}</div><div className="muted" style={{ fontSize: 11 }}>matriculados</div></div>
                    <div><div style={{ fontWeight: 800, fontSize: 18 }}>{tr.avg_pct}%</div><div className="muted" style={{ fontSize: 11 }}>progresso médio</div></div>
                    <div><div style={{ fontWeight: 800, fontSize: 18, color: 'var(--brand-success)' }}>{tr.completed_count}</div><div className="muted" style={{ fontSize: 11 }}>concluíram</div></div>
                  </div>
                </button>

                {isOpen && (
                  <div style={{ borderTop: '1px solid var(--brand-border)', overflowX: 'auto' }}>
                    {tr.enrolled.length === 0 ? (
                      <p className="muted" style={{ padding: 18 }}>Nenhum usuário matriculado nesta trilha ainda. Atribua-a a um grupo em <b>Grupos</b>.</p>
                    ) : (
                      <table className="tbl" style={{ width: '100%', borderCollapse: 'collapse', minWidth: 640 }}>
                        <thead>
                          <tr style={{ textAlign: 'left', fontSize: 12, color: 'var(--brand-text-secondary)' }}>
                            <th style={{ padding: '9px 14px' }}>Nome</th>
                            <th style={{ padding: '9px 14px' }}>Área</th>
                            <th style={{ padding: '9px 14px', minWidth: 160 }}>Aulas</th>
                            <th style={{ padding: '9px 14px', textAlign: 'center' }}><ClipboardCheck size={13} /> Simulados</th>
                            <th style={{ padding: '9px 14px', textAlign: 'center' }}><CheckCircle2 size={13} /> Aprovações</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tr.enrolled.map(u => (
                            <tr key={u.email} style={{ borderTop: '1px solid var(--brand-border)' }}>
                              <td style={{ padding: '9px 14px' }}>{u.name}<div className="muted" style={{ fontSize: 11 }}>{u.email}</div></td>
                              <td style={{ padding: '9px 14px' }} className="muted">{groupName(u.group_key)}</td>
                              <td style={{ padding: '9px 14px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                  <div className="prog-bar" style={{ height: 7, flex: 1, minWidth: 80 }}><div style={{ width: `${u.pct}%` }} /></div>
                                  <span style={{ fontSize: 12, whiteSpace: 'nowrap' }}>{u.classes_done}/{u.classes_total}</span>
                                </div>
                              </td>
                              <td style={{ padding: '9px 14px', textAlign: 'center' }}>{u.attempts}</td>
                              <td style={{ padding: '9px 14px', textAlign: 'center', fontWeight: u.passed ? 700 : 400, color: u.passed ? 'var(--brand-success)' : undefined }}>{u.passed}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
