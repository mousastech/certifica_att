import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Trophy, Flame, Award, Medal, Crown, Target, BookOpen, GraduationCap,
  PlayCircle, ClipboardCheck, Star,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { getMyGamification, getGamiLeaderboard } from '@/services/api'
import { useAuth } from '@/context/AuthContext'
import { useT } from '@/i18n'

const BADGE_ICON: Record<string, LucideIcon> = {
  PlayCircle, BookOpen, GraduationCap, ClipboardCheck, Target,
  Award, Medal, Flame, Crown,
}

export default function Leaderboard() {
  const { user } = useAuth()
  const t = useT()
  const [scope, setScope] = useState<'all' | 'group'>('all')
  const { data: gami } = useQuery({ queryKey: ['gami'], queryFn: getMyGamification })
  const { data: lb, isLoading } = useQuery({
    queryKey: ['gami-lb', scope], queryFn: () => getGamiLeaderboard(scope),
  })
  const groupName = (key?: string) => lb?.groups.find(g => g.key === key)?.name || key || '—'

  const pct = gami && gami.next_level_at
    ? Math.min(100, Math.round(100 * (gami.points - gami.level_floor) / (gami.next_level_at - gami.level_floor)))
    : 100

  return (
    <div>
      <div className="hist-title-row" style={{ marginBottom: 16 }}>
        <div>
          <h1 className="hist-title"><Trophy size={20} style={{ verticalAlign: -3 }} /> {t('gami.title')}</h1>
          <p className="muted hist-sub">{t('gami.sub')}</p>
        </div>
      </div>

      {/* Meu progresso */}
      {gami && (
        <div className="card" style={{ padding: 22, marginBottom: 20 }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20, alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: 13, color: 'var(--brand-text-secondary)' }}>{t('gami.yourLevel')}</div>
              <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--brand-primary)' }}>
                <Star size={22} style={{ verticalAlign: -3 }} /> {gami.level}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 26 }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 800 }}>{gami.points}</div>
                <div className="muted" style={{ fontSize: 12 }}>{t('gami.points')}</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 800 }}>{gami.classes_done}</div>
                <div className="muted" style={{ fontSize: 12 }}>{t('gami.classes')}</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 800 }}>{gami.attempts}</div>
                <div className="muted" style={{ fontSize: 12 }}>{t('gami.sims')}</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--brand-success)' }}>{gami.passed}</div>
                <div className="muted" style={{ fontSize: 12 }}>{t('gami.approvals')}</div>
              </div>
            </div>
          </div>

          {gami.next_level_at != null && (
            <div style={{ marginTop: 16 }}>
              <div className="prog-bar" style={{ height: 9 }}><div style={{ width: `${pct}%` }} /></div>
              <div className="muted" style={{ fontSize: 12, marginTop: 5 }}>
                {t('gami.toNext', { n: Math.max(0, gami.next_level_at - gami.points) })}
              </div>
            </div>
          )}

          {gami.badges.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 18 }}>
              {gami.badges.map(b => {
                const Ico = BADGE_ICON[b.icon] || Award
                return (
                  <span key={b.key} className="card" style={{
                    display: 'inline-flex', alignItems: 'center', gap: 7, padding: '7px 12px',
                    borderColor: 'var(--brand-primary)', fontSize: 13, fontWeight: 600,
                  }}>
                    <Ico size={16} style={{ color: 'var(--brand-primary)' }} /> {t(`gami.b_${b.key}`)}
                  </span>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Ranking */}
      <div className="login-tabs" style={{ maxWidth: 360, marginBottom: 14 }}>
        <button className={scope === 'all' ? 'active' : ''} onClick={() => setScope('all')}>{t('gami.tabAll')}</button>
        <button className={scope === 'group' ? 'active' : ''} onClick={() => setScope('group')}>{t('gami.tabGroup')}</button>
      </div>

      {isLoading ? <div className="spinner" /> : (
        <div className="card" style={{ overflow: 'hidden' }}>
          <table className="tbl" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', fontSize: 12, color: 'var(--brand-text-secondary)' }}>
                <th style={{ padding: '10px 14px' }}>#</th>
                <th style={{ padding: '10px 14px' }}>{t('gami.colName')}</th>
                <th style={{ padding: '10px 14px' }}>{t('gami.colArea')}</th>
                <th style={{ padding: '10px 14px', textAlign: 'right' }}>{t('gami.colPoints')}</th>
                <th style={{ padding: '10px 14px', textAlign: 'right' }}>{t('gami.colLevel')}</th>
              </tr>
            </thead>
            <tbody>
              {(lb?.rows ?? []).map(r => {
                const me = r.email === user?.email
                return (
                  <tr key={r.email} style={{
                    borderTop: '1px solid var(--brand-border)',
                    background: me ? 'var(--brand-primary-pale)' : undefined, fontWeight: me ? 700 : 400,
                  }}>
                    <td style={{ padding: '10px 14px' }}>
                      {r.rank <= 3 ? ['🥇', '🥈', '🥉'][r.rank - 1] : r.rank}
                    </td>
                    <td style={{ padding: '10px 14px' }}>{r.name}{me && ` ${t('gami.you')}`}</td>
                    <td style={{ padding: '10px 14px' }} className="muted">{groupName(r.group_key)}</td>
                    <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 700 }}>{r.points}</td>
                    <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                      <span className="badge badge-associate">{r.level}</span>
                    </td>
                  </tr>
                )
              })}
              {(lb?.rows?.length ?? 0) === 0 && (
                <tr><td colSpan={5} className="muted" style={{ padding: 20, textAlign: 'center' }}>
                  {t('gami.empty')}
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
