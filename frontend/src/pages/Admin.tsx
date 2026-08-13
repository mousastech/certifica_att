import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Users, ListChecks, Award, Pencil, Power, PowerOff, Trash2, Loader2, UserPlus, Activity,
  Link2, Copy, Check, Users2, Map, Upload, FileSpreadsheet, Download,
} from 'lucide-react'
import {
  getAdminOverview, adminCreateUser, adminUpdateUser, adminSetUserStatus,
  adminSetUserPassword, adminDeleteUser, adminInvite,
  adminBulkUsers, getUsersTemplate, adminListGroups, adminSetUserGroup,
  getMyTracks, getCertifications,
} from '@/services/api'
import type { BulkResult } from '@/types'
import { useT, useI18n } from '@/i18n'
import { useAuth } from '@/context/AuthContext'
import type { AdminUserRow } from '@/types'
import './History.css'

const LOCALE = { es: 'es-CL', pt: 'pt-BR', en: 'en-US' } as const

// ── Dashboard de engajamento: ranking + distribuição (dados do overview) ──────
function EngagementDashboard({ users, passMark }: { users: AdminUserRow[]; passMark: number }) {
  const t = useT()
  const active = users.filter(u => u.attempts > 0)
  if (!active.length) return null

  // ranking por nº de tentativas (engajamento); desempate pelo melhor score
  const ranked = [...active]
    .sort((a, b) => b.attempts - a.attempts || (b.best_score ?? 0) - (a.best_score ?? 0))
    .slice(0, 10)
  const maxAtt = Math.max(...ranked.map(u => u.attempts), 1)

  const passed = active.filter(u => u.passed_any).length
  const passRate = Math.round(100 * passed / active.length)
  const engagement = Math.round(100 * active.length / Math.max(users.length, 1))
  const avgAtt = (active.reduce((s, u) => s + u.attempts, 0) / active.length).toFixed(1)

  return (
    <div className="adm-dash">
      <div className="card adm-rank">
        <h3>{t('admin.rankTitle')}</h3>
        <p className="muted adm-dash-sub">{t('admin.rankSub')}</p>
        <div className="adm-rank-list">
          {ranked.map((u, i) => (
            <div key={u.email} className="adm-rank-row">
              <span className="adm-rank-pos">{i + 1}</span>
              <div className="adm-rank-body">
                <div className="adm-rank-label">
                  <span className="adm-rank-name">{u.name}</span>
                  <span className="adm-rank-meta">
                    {u.best_score != null && <span className="adm-rank-score">{u.best_score}%</span>}
                    <b>{u.attempts}</b> {t('admin.attempts').toLowerCase()}
                  </span>
                </div>
                <div className="adm-bar-track">
                  <div className={`adm-bar-fill ${u.passed_any ? 'pass' : ''}`}
                       style={{ width: `${Math.max(6, 100 * u.attempts / maxAtt)}%` }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="adm-dash-side">
        <div className="card adm-gauge">
          <span className="adm-gauge-lbl">{t('admin.passRate')}</span>
          <div className="adm-gauge-val">{passRate}%</div>
          <div className="adm-gauge-track"><div className="adm-gauge-fill" style={{ width: `${passRate}%` }} /></div>
          <span className="muted adm-gauge-note">{passed}/{active.length} · {t('admin.cut', { m: passMark })}</span>
        </div>
        <div className="card adm-gauge">
          <span className="adm-gauge-lbl">{t('admin.engagement')}</span>
          <div className="adm-gauge-val">{engagement}%</div>
          <div className="adm-gauge-track"><div className="adm-gauge-fill alt" style={{ width: `${engagement}%` }} /></div>
          <span className="muted adm-gauge-note">{active.length}/{users.length} · {t('admin.avgAttempts', { n: avgAtt })}</span>
        </div>
      </div>
    </div>
  )
}

function EditModal({ user, onClose }: { user: AdminUserRow; onClose: () => void }) {
  const t = useT(); const qc = useQueryClient()
  const { user: me } = useAuth()
  const [name, setName] = useState(user.name)
  const [area, setArea] = useState(user.area ?? '')
  const [groupKey, setGroupKey] = useState(user.group_key ?? '')
  const [isAdmin, setIsAdmin] = useState(user.is_admin)
  const [pw, setPw] = useState('')
  const [err, setErr] = useState<string | null>(null)
  const isSelf = me?.email?.toLowerCase() === user.email.toLowerCase()
  const { data: groups } = useQuery({ queryKey: ['adm-groups'], queryFn: adminListGroups })
  const { data: mine } = useQuery({ queryKey: ['my-tracks'], queryFn: getMyTracks })
  const { data: certs } = useQuery({ queryKey: ['certs'], queryFn: getCertifications })
  const selGroup = groups?.find(g => g.key === groupKey)
  const trackName = (k: string) => mine?.tracks.find(tr => tr.key === k)?.name || k
  const certName = (id: string) => certs?.find(c => c.id === id)?.name || id

  const save = useMutation({
    mutationFn: async () => {
      await adminUpdateUser(user.email, {
        name: name.trim(), area: area.trim(),
        ...(isAdmin !== user.is_admin ? { is_admin: isAdmin } : {}),
      })
      if ((groupKey || '') !== (user.group_key || ''))
        await adminSetUserGroup(user.email, { group_key: groupKey || null })
      if (pw) await adminSetUserPassword(user.email, pw)
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-overview'] }); onClose() },
    onError: (e: any) => setErr(e?.response?.data?.detail ?? 'Error'),
  })

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card card" onClick={e => e.stopPropagation()}>
        <h3>{t('admin.editUser')}</h3>
        <p className="muted" style={{ marginBottom: 12 }}>{user.email}</p>
        <label>{t('admin.name')}<input value={name} onChange={e => setName(e.target.value)} /></label>
        <label>{t('admin.area')}<input value={area} onChange={e => setArea(e.target.value)} placeholder="—" /></label>
        <label>{t('admin.group')}
          <select value={groupKey} onChange={e => setGroupKey(e.target.value)}>
            <option value="">{t('admin.noGroup')}</option>
            {(groups ?? []).map(g => <option key={g.key} value={g.key}>{g.name}</option>)}
          </select>
        </label>
        {selGroup && (
          <div className="card" style={{ padding: 12, marginTop: 8, borderLeft: `3px solid ${selGroup.color || 'var(--brand-primary)'}` }}>
            {selGroup.description && <p className="muted" style={{ fontSize: 12, margin: '0 0 8px' }}>{selGroup.description}</p>}
            <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 5 }}>{t('admin.groupWillSee')}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
              {(selGroup.track_keys?.length ?? 0) === 0
                ? <span className="muted" style={{ fontSize: 12 }}>{t('admin.allTracks')}</span>
                : selGroup.track_keys.map(k => (
                    <span key={k} className="badge badge-fundamentos" style={{ fontSize: 11 }}>{trackName(k)}</span>
                  ))}
            </div>
            {(selGroup.certification_ids?.length ?? 0) > 0 && (
              <div style={{ marginTop: 8 }}>
                <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 5 }}>{t('admin.groupSims')}</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {selGroup.certification_ids.map(id => (
                    <span key={id} className="badge badge-associate" style={{ fontSize: 11 }}>{certName(id)}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        <label>{t('admin.newPassword')}<input type="password" value={pw} onChange={e => setPw(e.target.value)} placeholder="••••••" /></label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 14 }}>
          <input type="checkbox" checked={isAdmin} disabled={isSelf}
                 onChange={e => setIsAdmin(e.target.checked)} style={{ width: 'auto' }} />
          {t('admin.makeAdmin')}
          {isSelf && <span className="muted" style={{ fontSize: 12 }}>({t('admin.cantChangeSelf')})</span>}
        </label>
        {err && <div className="login-error">{err}</div>}
        <div className="modal-actions">
          <button className="btn" onClick={onClose}>{t('admin.cancel')}</button>
          <button className="btn btn-primary" disabled={save.isPending} onClick={() => { setErr(null); save.mutate() }}>
            {save.isPending ? <Loader2 size={15} className="spinning" /> : t('admin.save')}
          </button>
        </div>
      </div>
    </div>
  )
}

function InviteModal({ onClose }: { onClose: () => void }) {
  const t = useT()
  const [f, setF] = useState({ name: '', email: '', is_admin: false })
  const [link, setLink] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const create = useMutation({
    mutationFn: async () => {
      const inv = await adminInvite({ email: f.email.trim(), name: f.name.trim(), is_admin: f.is_admin })
      return `${window.location.origin}${inv.invite_path}`
    },
    onSuccess: (l) => { setLink(l); setCopied(false) },
    onError: (e: any) => setErr(e?.response?.data?.detail ?? t('admin.createError')),
  })
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card card" onClick={e => e.stopPropagation()}>
        <h3>{t('admin.inviteUser')}</h3>
        {link ? (
          <>
            <p className="muted" style={{ margin: '10px 0' }}>{t('admin.inviteReady', { email: f.email.trim() })}</p>
            <div style={{ display: 'flex', gap: 8 }}>
              <input readOnly value={link} onFocus={e => e.currentTarget.select()}
                style={{ flex: 1, fontFamily: 'ui-monospace, monospace', fontSize: 12 }} />
              <button className="btn btn-primary" onClick={() => {
                navigator.clipboard?.writeText(link); setCopied(true); setTimeout(() => setCopied(false), 2000)
              }}>{copied ? <><Check size={15} /> {t('admin.copied')}</> : <><Copy size={15} /> {t('admin.copyLink')}</>}</button>
            </div>
            <div className="modal-actions">
              <button className="btn btn-primary" onClick={onClose}>{t('admin.done')}</button>
            </div>
          </>
        ) : (
          <>
            <p className="muted" style={{ marginBottom: 12 }}>{t('admin.inviteHint')}</p>
            <label>{t('admin.name')}<input value={f.name} onChange={e => setF({ ...f, name: e.target.value })} /></label>
            <label>{t('admin.email')}<input type="email" value={f.email} onChange={e => setF({ ...f, email: e.target.value })} /></label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 14 }}>
              <input type="checkbox" checked={f.is_admin} onChange={e => setF({ ...f, is_admin: e.target.checked })} style={{ width: 'auto' }} />
              {t('admin.makeAdmin')}
            </label>
            {err && <div className="login-error">{err}</div>}
            <div className="modal-actions">
              <button className="btn" onClick={onClose}>{t('admin.cancel')}</button>
              <button className="btn btn-primary" disabled={create.isPending} onClick={() => { setErr(null); create.mutate() }}>
                {create.isPending ? <Loader2 size={15} className="spinning" /> : t('admin.generateLink')}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function NewUserModal({ onClose }: { onClose: () => void }) {
  const t = useT(); const qc = useQueryClient()
  const [f, setF] = useState({ name: '', email: '', password: '', area: '', is_admin: false })
  const [err, setErr] = useState<string | null>(null)
  const create = useMutation({
    mutationFn: () => adminCreateUser({ ...f, area: f.area.trim() || undefined }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-overview'] }); onClose() },
    onError: (e: any) => setErr(e?.response?.data?.detail ?? t('admin.createError')),
  })
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card card" onClick={e => e.stopPropagation()}>
        <h3>{t('admin.newUser')}</h3>
        <label>{t('admin.name')}<input value={f.name} onChange={e => setF({ ...f, name: e.target.value })} /></label>
        <label>{t('admin.email')}<input type="email" value={f.email} onChange={e => setF({ ...f, email: e.target.value })} /></label>
        <label>{t('admin.password')}<input type="password" value={f.password} onChange={e => setF({ ...f, password: e.target.value })} /></label>
        <label>{t('admin.area')}<input value={f.area} onChange={e => setF({ ...f, area: e.target.value })} placeholder="—" /></label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 14 }}>
          <input type="checkbox" checked={f.is_admin} onChange={e => setF({ ...f, is_admin: e.target.checked })} style={{ width: 'auto' }} />
          {t('admin.makeAdmin')}
        </label>
        {err && <div className="login-error">{err}</div>}
        <div className="modal-actions">
          <button className="btn" onClick={onClose}>{t('admin.cancel')}</button>
          <button className="btn btn-primary" disabled={create.isPending} onClick={() => { setErr(null); create.mutate() }}>
            {create.isPending ? <Loader2 size={15} className="spinning" /> : t('admin.createUser')}
          </button>
        </div>
      </div>
    </div>
  )
}

function BulkImportModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const [pw, setPw] = useState('Databricks#ATT2026')
  const [result, setResult] = useState<BulkResult | null>(null)
  const [err, setErr] = useState<string | null>(null)

  async function dl(kind: 'csv' | 'xlsx') {
    const blob = await getUsersTemplate(kind)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `modelo_usuarios_att.${kind}`; a.click()
    URL.revokeObjectURL(url)
  }

  const run = useMutation({
    mutationFn: () => adminBulkUsers(file!, pw),
    onSuccess: (r) => { setResult(r); qc.invalidateQueries({ queryKey: ['admin-overview'] }) },
    onError: (e: any) => setErr(e?.response?.data?.detail ?? 'Falha ao importar'),
  })

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card card" onClick={e => e.stopPropagation()} style={{ maxWidth: 520 }}>
        <h3><Upload size={18} style={{ verticalAlign: -3 }} /> Importar usuários em lote</h3>
        <p className="muted" style={{ marginBottom: 12 }}>
          Planilha com colunas <b>nome, email, area, grupo</b> (CSV ou XLSX). O campo
          <b> grupo</b> aceita a chave ou o nome de uma área. Novos usuários recebem a
          senha inicial abaixo (troca no 1º acesso).
        </p>

        {result ? (
          <>
            <div className="card" style={{ padding: 14, marginBottom: 12 }}>
              <div style={{ display: 'flex', gap: 20 }}>
                <div><b style={{ fontSize: 22 }}>{result.created}</b><div className="muted" style={{ fontSize: 12 }}>criados</div></div>
                <div><b style={{ fontSize: 22 }}>{result.updated}</b><div className="muted" style={{ fontSize: 12 }}>atualizados</div></div>
                <div><b style={{ fontSize: 22 }}>{result.total}</b><div className="muted" style={{ fontSize: 12 }}>linhas</div></div>
                <div><b style={{ fontSize: 22, color: result.errors.length ? 'var(--brand-error)' : undefined }}>{result.errors.length}</b><div className="muted" style={{ fontSize: 12 }}>erros</div></div>
              </div>
            </div>
            {result.errors.length > 0 && (
              <div style={{ maxHeight: 160, overflow: 'auto', fontSize: 12 }} className="login-error">
                {result.errors.map((e, i) => <div key={i}>Linha {e.row} ({e.email || '—'}): {e.error}</div>)}
              </div>
            )}
            <p className="muted" style={{ fontSize: 12, marginTop: 8 }}>Senha inicial: <code>{result.default_password}</code></p>
            <div className="modal-actions">
              <button className="btn btn-primary" onClick={onClose}>Concluir</button>
            </div>
          </>
        ) : (
          <>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <button className="btn" onClick={() => dl('csv')}><Download size={14} /> Modelo CSV</button>
              <button className="btn" onClick={() => dl('xlsx')}><FileSpreadsheet size={14} /> Modelo XLSX</button>
            </div>
            <label>Arquivo (.csv / .xlsx)
              <input type="file" accept=".csv,.xlsx" onChange={e => setFile(e.target.files?.[0] ?? null)} />
            </label>
            <label>Senha inicial dos novos usuários
              <input value={pw} onChange={e => setPw(e.target.value)} />
            </label>
            {err && <div className="login-error">{err}</div>}
            <div className="modal-actions">
              <button className="btn" onClick={onClose}>Cancelar</button>
              <button className="btn btn-primary" disabled={!file || run.isPending} onClick={() => { setErr(null); run.mutate() }}>
                {run.isPending ? <Loader2 size={15} className="spinning" /> : <>Importar</>}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default function Admin() {
  const navigate = useNavigate()
  const t = useT()
  const { lang } = useI18n()
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['admin-overview'], queryFn: getAdminOverview })
  const { data: groups } = useQuery({ queryKey: ['adm-groups'], queryFn: adminListGroups })
  const groupName = (k?: string) => groups?.find(g => g.key === k)?.name
  const [editing, setEditing] = useState<AdminUserRow | null>(null)
  const [creating, setCreating] = useState(false)
  const [inviting, setInviting] = useState(false)
  const [importing, setImporting] = useState(false)

  const status = useMutation({
    mutationFn: ({ email, s }: { email: string; s: 'active' | 'suspended' }) => adminSetUserStatus(email, s),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-overview'] }),
  })
  const del = useMutation({
    mutationFn: (email: string) => adminDeleteUser(email),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-overview'] }),
  })

  if (isLoading) return <div className="spinner" />
  if (!data) return <p className="muted">{t('admin.noData')}</p>

  const fmt = (s?: string) => s ? new Date(s).toLocaleString(LOCALE[lang]) : '—'
  const score = (v?: number) => v == null ? '—' : `${v}%`
  const stop = (e: React.MouseEvent) => e.stopPropagation()

  return (
    <div>
      <div className="au-title-row">
        <div>
          <h1 className="hist-title">{t('admin.title')}</h1>
          <p className="muted hist-sub">{t('admin.sub', { m: data.pass_mark })}</p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button className="btn" onClick={() => navigate('/admin/grupos')}>
            <Users2 size={16} /> {t('nav.groups')}
          </button>
          <button className="btn" onClick={() => navigate('/admin/trilhas')}>
            <Map size={16} /> {t('nav.tracks')}
          </button>
          <button className="btn" onClick={() => navigate('/admin/activity')}>
            <Activity size={16} /> {t('admin.activityLog')}
          </button>
          <button className="btn" onClick={() => setImporting(true)}>
            <Upload size={16} /> Importar planilha
          </button>
          <button className="btn" onClick={() => setInviting(true)}>
            <Link2 size={16} /> {t('admin.inviteUser')}
          </button>
          <button className="btn btn-primary" onClick={() => setCreating(true)}>
            <UserPlus size={16} /> {t('admin.newUser')}
          </button>
        </div>
      </div>

      <div className="adm-kpis">
        <div className="card adm-kpi"><Users size={20} color="var(--brand-primary)" /><div><b>{data.total_users}</b><span>{t('admin.users')}</span></div></div>
        <div className="card adm-kpi"><ListChecks size={20} color="var(--brand-primary)" /><div><b>{data.total_attempts}</b><span>{t('admin.attempts')}</span></div></div>
        <div className="card adm-kpi"><Award size={20} color="var(--brand-primary)" /><div><b>{data.users.filter(u => u.passed_any).length}</b><span>{t('admin.approvedCount')}</span></div></div>
      </div>

      <EngagementDashboard users={data.users} passMark={data.pass_mark} />

      <div className="card hist-table-wrap">
        <table className="hist-table">
          <thead>
            <tr><th>{t('admin.name')}</th><th>{t('admin.area')}</th><th>{t('admin.status')}</th><th>{t('admin.attempts')}</th><th>{t('admin.best')}</th><th>{t('admin.lastAccess')}</th><th>{t('admin.actions')}</th></tr>
          </thead>
          <tbody>
            {data.users.map(u => (
              <tr key={u.email}
                  className={u.attempts > 0 ? 'adm-row-click' : ''}
                  onClick={() => u.attempts > 0 && navigate(`/admin/user/${encodeURIComponent(u.email)}`)}
                  title={u.attempts > 0 ? t('admin.viewAttempts') : t('admin.noAttempts')}>
                <td>
                  <b>{u.name}</b>{u.is_admin && <span className="badge badge-associate" style={{ marginLeft: 6 }}>{t('admin.roleAdmin')}</span>}
                  <div className="muted" style={{ fontSize: 12 }}>{u.email}</div>
                </td>
                <td>
                  {groupName(u.group_key)
                    ? <span className="badge badge-fundamentos">{groupName(u.group_key)}</span>
                    : (u.area || '—')}
                </td>
                <td><span className={`hist-badge ${u.status === 'active' ? 'ok' : 'no'}`}>
                  {u.status === 'active' ? t('admin.active') : t('admin.suspended')}</span></td>
                <td>{u.attempts}</td>
                <td>{score(u.best_score)}</td>
                <td>{fmt(u.last_attempt_at)}</td>
                <td onClick={stop}>
                  <span className="adm-actions">
                    <button className="link-btn" title={t('admin.edit')} onClick={() => setEditing(u)}><Pencil size={15} /></button>
                    <button className="link-btn" title={u.status === 'active' ? t('admin.suspend') : t('admin.activate')}
                      disabled={status.isPending}
                      onClick={() => status.mutate({ email: u.email, s: u.status === 'active' ? 'suspended' : 'active' })}>
                      {u.status === 'active' ? <PowerOff size={15} /> : <Power size={15} />}
                    </button>
                    <button className="link-btn" title={t('admin.deleteUser')} disabled={del.isPending}
                      onClick={() => { if (confirm(t('admin.confirmDelete', { name: u.name }))) del.mutate(u.email) }}>
                      <Trash2 size={15} />
                    </button>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && <EditModal user={editing} onClose={() => setEditing(null)} />}
      {creating && <NewUserModal onClose={() => setCreating(false)} />}
      {inviting && <InviteModal onClose={() => setInviting(false)} />}
      {importing && <BulkImportModal onClose={() => setImporting(false)} />}
    </div>
  )
}
