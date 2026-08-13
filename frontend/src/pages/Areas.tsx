import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  ArrowRight, Sparkles, Building2, Lock, Database, BrainCircuit, BarChart3,
  Rocket, Compass, ShieldCheck, Layers, ChevronRight,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { listAreas, getMyTracks } from '@/services/api'
import { useT } from '@/i18n'
import type { Area } from '@/types'
import './Program.css'

const ICONS: Record<string, LucideIcon> = {
  Building2, Lock, Sparkles, Database, BrainCircuit, BarChart3, Rocket, Compass, ShieldCheck, Layers,
}
const iconFor = (name?: string) => ICONS[name || ''] || Layers

export default function Areas() {
  const navigate = useNavigate()
  const t = useT()
  const { data, isLoading } = useQuery({ queryKey: ['areas'], queryFn: listAreas })
  const { data: mine } = useQuery({ queryKey: ['my-tracks'], queryFn: getMyTracks })

  if (isLoading || !data) return <div className="spinner" />
  const areas = data.areas || []
  const myKey = mine?.group?.key
  const myArea = areas.find(a => a.key === myKey)
  const genie = areas.find(a => (a.track_keys || []).includes('genie_finanzas'))
    || areas.find(a => a.key === 'finanzas')

  const goArea = (a: Area) => navigate(`/rutas?area=${encodeURIComponent(a.key)}`)

  const AreaCard = ({ a, featured }: { a: Area; featured?: boolean }) => {
    const Icon = iconFor(a.icon)
    const color = a.color || 'var(--brand-primary)'
    return (
      <button className="card area-card" onClick={() => goArea(a)}
        style={{ borderTop: `4px solid ${color}` }}>
        <div className="area-card-icon" style={{ background: color }}><Icon size={26} /></div>
        <h3>{a.name}</h3>
        <p className="muted area-card-desc">{a.description}</p>
        <div className="area-card-foot">
          <span className="muted">{t('areas.tracks', { n: a.n_tracks })} · {t('areas.lessons', { n: a.n_classes })}</span>
          <span className="area-card-go" style={{ color }}>
            {featured ? t('areas.enter') : ''} <ChevronRight size={16} />
          </span>
        </div>
      </button>
    )
  }

  return (
    <div className="prog areas-hub">
      {/* Hero */}
      <section className="prog-hero card areas-hero">
        <img src="/att-logo.svg" alt="AT&T" className="prog-hero-logo" />
        <h1>{t('areas.title')}</h1>
        <p className="prog-tagline">{t('areas.sub')}</p>
        <div className="prog-hero-actions">
          <button className="btn btn-primary btn-lg" onClick={() => navigate('/rutas')}>
            {t('areas.myTracksCta')} <ArrowRight size={16} />
          </button>
          <button className="btn" onClick={() => navigate('/programa')}>
            {t('nav.programLink')}
          </button>
        </div>
      </section>

      {/* Featured Genie */}
      {genie && (
        <button className="card genie-banner" onClick={() => goArea(genie)}>
          <div className="genie-banner-glow" />
          <div className="genie-banner-body">
            <span className="genie-badge"><Sparkles size={13} /> {t('areas.genieBadge')}</span>
            <h2>{t('areas.genieTitle')}</h2>
            <p>{t('areas.genieDesc')}</p>
            <span className="genie-cta">{t('areas.genieCta')} <ArrowRight size={16} /></span>
          </div>
          <Sparkles className="genie-banner-icon" size={120} />
        </button>
      )}

      {/* Sua área (recomendada) */}
      {myArea && (
        <section className="prog-section">
          <h2>{t('areas.myArea')}</h2>
          <div className="area-featured card" style={{ borderLeft: `5px solid ${myArea.color || 'var(--brand-primary)'}` }}>
            <div className="area-card-icon" style={{ background: myArea.color || 'var(--brand-primary)' }}>
              {(() => { const I = iconFor(myArea.icon); return <I size={28} /> })()}
            </div>
            <div style={{ flex: 1 }}>
              <span className="area-reco">{t('areas.recommended')}</span>
              <h3 style={{ margin: '2px 0' }}>{myArea.name}</h3>
              <p className="muted" style={{ margin: 0 }}>{myArea.description}</p>
              <p className="muted" style={{ fontSize: 12, marginTop: 6 }}>
                {t('areas.tracks', { n: myArea.n_tracks })} · {t('areas.lessons', { n: myArea.n_classes })}
              </p>
            </div>
            <button className="btn btn-primary" onClick={() => navigate('/rutas')}>
              {t('areas.enter')} <ArrowRight size={15} />
            </button>
          </div>
        </section>
      )}

      {/* Todas as áreas */}
      <section className="prog-section">
        <h2>{t('areas.explore')}</h2>
        <div className="areas-grid">
          {areas.map(a => <AreaCard key={a.key} a={a} />)}
        </div>
      </section>
    </div>
  )
}
