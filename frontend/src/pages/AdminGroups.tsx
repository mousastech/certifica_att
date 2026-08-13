import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Users2, Plus, Pencil, Trash2, X, Check, Layers, ClipboardList } from 'lucide-react'
import {
  adminListGroups, adminCreateGroup, adminUpdateGroup, adminDeleteGroup,
  getMyTracks, getCertifications,
} from '@/services/api'
import { useT } from '@/i18n'
import type { Group } from '@/types'

const EMPTY: Partial<Group> = {
  key: '', name: '', description: '', color: '#00A8E0', icon: '',
  track_keys: [], certification_ids: [], sort_order: 0,
}

export default function AdminGroups() {
  const qc = useQueryClient()
  const t = useT()
  const { data: groups, isLoading } = useQuery({ queryKey: ['adm-groups'], queryFn: adminListGroups })
  const { data: mine } = useQuery({ queryKey: ['my-tracks'], queryFn: getMyTracks })
  const { data: certs } = useQuery({ queryKey: ['certs'], queryFn: getCertifications })
  const tracks = mine?.tracks ?? []

  const [editing, setEditing] = useState<Partial<Group> | null>(null)
  const [isNew, setIsNew] = useState(false)

  const save = useMutation({
    mutationFn: (g: Partial<Group>) =>
      isNew ? adminCreateGroup(g) : adminUpdateGroup(g.key!, g),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['adm-groups'] }); setEditing(null) },
  })
  const del = useMutation({
    mutationFn: (key: string) => adminDeleteGroup(key),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['adm-groups'] }),
  })

  const trackName = (k: string) => tracks.find(t => t.key === k)?.name || k
  const certName = (id: string) => certs?.find(c => c.id === id)?.name || id

  function toggle(list: string[], v: string): string[] {
    return list.includes(v) ? list.filter(x => x !== v) : [...list, v]
  }

  return (
    <div>
      <div className="au-title-row">
        <div>
          <h1 className="hist-title"><Users2 size={20} style={{ verticalAlign: -3 }} /> {t('gadmin.title')}</h1>
          <p className="muted hist-sub">{t('gadmin.sub')}</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Link className="btn" to="/admin">{t('gadmin.back')}</Link>
          <button className="btn btn-primary" onClick={() => { setEditing({ ...EMPTY }); setIsNew(true) }}>
            <Plus size={15} /> {t('gadmin.newGroup')}
          </button>
        </div>
      </div>

      {isLoading ? <div className="spinner" /> : (
        <div className="prog-grid">
          {(groups ?? []).map(g => (
            <div key={g.key} className="card prog-pillar" style={{ textAlign: 'left', borderTop: `3px solid ${g.color || 'var(--brand-primary)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <h4 style={{ margin: 0 }}>{g.name}</h4>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button className="link-btn" title={t('gadmin.editGroup')} onClick={() => { setEditing({ ...g }); setIsNew(false) }}><Pencil size={15} /></button>
                  <button className="link-btn" title={t('gadmin.deleteTip')} onClick={() => { if (confirm(t('gadmin.confirmDelete', { name: g.name }))) del.mutate(g.key) }}><Trash2 size={15} /></button>
                </div>
              </div>
              <p className="muted" style={{ fontSize: 13 }}>{g.description}</p>
              <div style={{ marginTop: 8 }}>
                <div style={{ fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 5 }}><Layers size={13} /> {t('gadmin.visibleTracks')} ({g.track_keys.length || '∞'})</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 5 }}>
                  {g.track_keys.length === 0 ? <span className="muted" style={{ fontSize: 12 }}>{t('gadmin.allTracks')}</span>
                    : g.track_keys.map(k => <span key={k} className="badge badge-fundamentos" style={{ fontSize: 11 }}>{trackName(k)}</span>)}
                </div>
              </div>
              {g.certification_ids.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 5 }}><ClipboardList size={13} /> {t('gadmin.sims')}</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 5 }}>
                    {g.certification_ids.map(id => <span key={id} className="badge badge-associate" style={{ fontSize: 11 }}>{certName(id)}</span>)}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Editor modal */}
      {editing && (
        <div className="modal-backdrop" onClick={() => setEditing(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: 16 }}>
          <div className="card" onClick={e => e.stopPropagation()} style={{ maxWidth: 560, width: '100%', maxHeight: '90vh', overflow: 'auto', padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 style={{ margin: 0 }}>{isNew ? t('gadmin.newGroup') : `${t('gadmin.editGroup')}: ${editing.name}`}</h3>
              <button className="link-btn" onClick={() => setEditing(null)}><X size={18} /></button>
            </div>

            <div style={{ display: 'grid', gap: 12 }}>
              <label>{t('gadmin.name')}
                <input value={editing.name || ''} onChange={e => setEditing({ ...editing, name: e.target.value })} placeholder="Oficina del CDO" />
              </label>
              {isNew && (
                <label>{t('gadmin.keyField')}
                  <input value={editing.key || ''} onChange={e => setEditing({ ...editing, key: e.target.value })} placeholder={t('gadmin.keyHint')} />
                </label>
              )}
              <label>{t('gadmin.description')}
                <input value={editing.description || ''} onChange={e => setEditing({ ...editing, description: e.target.value })} />
              </label>
              <div style={{ display: 'flex', gap: 12 }}>
                <label style={{ flex: '0 0 110px' }}>{t('gadmin.color')}
                  <input type="color" value={editing.color || '#00A8E0'} onChange={e => setEditing({ ...editing, color: e.target.value })} style={{ height: 38, padding: 2 }} />
                </label>
                <label style={{ flex: 1 }}>{t('gadmin.icon')}
                  <input value={editing.icon || ''} onChange={e => setEditing({ ...editing, icon: e.target.value })} placeholder="Building2" />
                </label>
              </div>

              <div>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>{t('gadmin.visibleTracks')} <span className="muted" style={{ fontWeight: 400 }}>{t('gadmin.visibleTracksHint')}</span></div>
                <div style={{ display: 'grid', gap: 6 }}>
                  {tracks.map(tr => (
                    <label key={tr.key} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer', fontWeight: 400 }}>
                      <input type="checkbox" checked={(editing.track_keys || []).includes(tr.key!)}
                        onChange={() => setEditing({ ...editing, track_keys: toggle(editing.track_keys || [], tr.key!) })} />
                      {tr.name}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>{t('gadmin.extraSims')} <span className="muted" style={{ fontWeight: 400 }}>{t('gadmin.extraSimsHint')}</span></div>
                <div style={{ display: 'grid', gap: 6 }}>
                  {(certs ?? []).map(c => (
                    <label key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer', fontWeight: 400 }}>
                      <input type="checkbox" checked={(editing.certification_ids || []).includes(c.id)}
                        onChange={() => setEditing({ ...editing, certification_ids: toggle(editing.certification_ids || [], c.id) })} />
                      {c.name}
                    </label>
                  ))}
                </div>
              </div>

              {save.isError && <div className="login-error">{t('gadmin.errSave')}</div>}
              <button className="btn btn-primary btn-lg" disabled={save.isPending || !editing.name}
                onClick={() => save.mutate(editing)}>
                <Check size={16} /> {save.isPending ? t('gadmin.saving') : t('gadmin.save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
