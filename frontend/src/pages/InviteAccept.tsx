import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Loader2, ShieldCheck, UserPlus } from 'lucide-react'
import { getInvite, acceptInvite, setToken, setTenantSlug } from '@/services/api'
import { useAuth } from '@/context/AuthContext'
import { useT } from '@/i18n'
import LanguageSwitcher from '@/components/LanguageSwitcher'
import './Login.css'

export default function InviteAccept() {
  const { token = '' } = useParams()
  const t = useT()
  const { setUser } = useAuth()
  const { data, isLoading } = useQuery({ queryKey: ['invite', token], queryFn: () => getInvite(token), enabled: !!token })
  const [pw, setPw] = useState('')
  const [pw2, setPw2] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const color = data?.primary_color || '#EC0000'

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (pw !== pw2) { setError(t('invite.mismatch')); return }
    setError(null); setLoading(true)
    try {
      const res = await acceptInvite(token, pw)
      setToken(res.access_token)
      if (res.user.tenant_slug) setTenantSlug(res.user.tenant_slug)
      setUser(res.user)
      window.location.assign('/')
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? t('invite.error'))
    } finally { setLoading(false) }
  }

  if (isLoading) return <div className="login-page"><div className="spinner" /></div>

  const state = data?.state
  if (state !== 'valid') {
    const msg = state === 'accepted' ? t('invite.alreadyUsed')
      : state === 'expired' ? t('invite.expired') : t('invite.notFound')
    return (
      <div className="login-page">
        <div className="login-langs"><LanguageSwitcher /></div>
        <div className="login-card card" style={{ maxWidth: 440, textAlign: 'center' }}>
          <div className="login-brand"><span className="login-brand-name">Certifica</span></div>
          <p className="login-error" style={{ marginTop: 16 }}>{msg}</p>
          <p className="login-foot" style={{ marginTop: 18 }}><a href="/">{t('common.back')}</a></p>
        </div>
      </div>
    )
  }

  return (
    <div className="login-page">
      <div className="login-langs"><LanguageSwitcher /></div>
      <div className="login-card card" style={{ maxWidth: 440 }}>
        <div className="login-brand" style={{ flexDirection: 'column', gap: 10 }}>
          {data?.logo_url
            ? <img src={data.logo_url} alt={data.tenant_name} style={{ maxHeight: 40 }} />
            : <span className="login-brand-name" style={{ color }}>{data?.tenant_name}</span>}
        </div>
        <p className="login-sub">
          {data?.is_admin ? <ShieldCheck size={15} /> : <UserPlus size={15} />}
          {' '}{data?.is_admin ? t('invite.adminSub', { tenant: data?.tenant_name || '' })
                              : t('invite.userSub', { tenant: data?.tenant_name || '' })}
        </p>
        <p className="muted" style={{ fontSize: 13, marginBottom: 4 }}>
          {t('invite.welcome', { name: data?.name || '' })}
        </p>
        <form onSubmit={submit} className="login-form">
          <label>{t('invite.email')}
            <input value={data?.email || ''} disabled style={{ opacity: .7 }} />
          </label>
          <label>{t('invite.password')}
            <input type="password" value={pw} onChange={e => setPw(e.target.value)}
              placeholder="••••••••" required minLength={6} autoFocus />
          </label>
          <label>{t('invite.confirm')}
            <input type="password" value={pw2} onChange={e => setPw2(e.target.value)}
              placeholder="••••••••" required minLength={6} />
          </label>
          {error && <div className="login-error">{error}</div>}
          <button type="submit" className="btn btn-primary btn-lg login-submit"
            style={{ background: color, borderColor: color }} disabled={loading}>
            {loading ? <><Loader2 size={18} className="spinning" /> {t('invite.activating')}</> : t('invite.activate')}
          </button>
        </form>
      </div>
    </div>
  )
}
