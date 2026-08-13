import { useRef, useState, type MouseEvent } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, FlaskConical, Layers, ExternalLink, GraduationCap, Target } from 'lucide-react'
import { getCertification } from '@/services/api'
import { useT } from '@/i18n'
import PracticeTest from '@/pages/PracticeTest'
import Flashcards from '@/pages/Flashcards'
import StudyAI from '@/pages/StudyAI'
import StudyPlan from '@/pages/StudyPlan'
import './CertDetail.css'

type Tab = 'overview' | 'practice' | 'flashcards' | 'study' | 'plan'

export default function CertDetail() {
  const { id = '' } = useParams()
  const t = useT()
  const [tab, setTab] = useState<Tab>('overview')
  const tabsRef = useRef<HTMLDivElement>(null)

  // No mobile a barra de abas rola horizontalmente (ver CertDetail.css): ao
  // escolher uma aba parcialmente fora da faixa, traz ela para a vista.
  const pick = (next: Tab) => (e: MouseEvent<HTMLButtonElement>) => {
    setTab(next)
    if (tabsRef.current && tabsRef.current.scrollWidth > tabsRef.current.clientWidth) {
      e.currentTarget.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
    }
  }

  const { data: cert, isLoading } = useQuery({
    queryKey: ['cert', id],
    queryFn: () => getCertification(id),
  })

  if (isLoading) return <div className="spinner" />
  if (!cert) return <p className="muted">{t('cert.notFound')}</p>

  return (
    <div>
      <div className="cd-header card">
        <div className="cd-header-main">
          <span className={`badge badge-${cert.level}`}>{cert.level}</span>
          <h1>{cert.name}</h1>
          <p className="muted">{cert.description}</p>
          <div className="cd-links">
            {cert.exam_guide_url && (
              <a href={cert.exam_guide_url} target="_blank" rel="noreferrer" className="btn">
                <BookOpen size={16} /> {t('cert.examGuide')}
              </a>
            )}
          </div>
        </div>
      </div>

      <div className="cd-tabs" ref={tabsRef} role="tablist">
        <button role="tab" aria-selected={tab === 'overview'}
                className={tab === 'overview' ? 'active' : ''} onClick={pick('overview')}>
          <Layers size={16} /> {t('cert.overview')}
        </button>
        <button role="tab" aria-selected={tab === 'practice'}
                className={tab === 'practice' ? 'active' : ''} onClick={pick('practice')}>
          <FlaskConical size={16} /> {t('cert.practice')}
        </button>
        <button role="tab" aria-selected={tab === 'flashcards'}
                className={tab === 'flashcards' ? 'active' : ''} onClick={pick('flashcards')}>
          <BookOpen size={16} /> {t('cert.flashcards')}
        </button>
        <button role="tab" aria-selected={tab === 'study'}
                className={tab === 'study' ? 'active' : ''} onClick={pick('study')}>
          <GraduationCap size={16} /> {t('cert.studyAI')}
        </button>
        <button role="tab" aria-selected={tab === 'plan'}
                className={tab === 'plan' ? 'active' : ''} onClick={pick('plan')}>
          <Target size={16} /> {t('cert.studyPlan')}
        </button>
      </div>

      <div className="cd-panel">
        {tab === 'overview' && (
          <div className="cd-overview">
            <div className="card cd-topics">
              <h3>{t('cert.topicsCovered')}</h3>
              <ul>{cert.topics.map(tp => <li key={tp}>{tp}</li>)}</ul>
            </div>
            <div className="cd-overview-cards">
              <div className="card cd-action" onClick={() => setTab('practice')}>
                <FlaskConical size={26} color="var(--brand-primary)" />
                <h4>{t('cert.practice')}</h4>
                <p className="muted">{t('cert.practiceDesc')}</p>
              </div>
              <div className="card cd-action" onClick={() => setTab('flashcards')}>
                <BookOpen size={26} color="var(--brand-primary)" />
                <h4>{t('cert.flashcards')}</h4>
                <p className="muted">{t('cert.flashcardsDesc')}</p>
              </div>
            </div>
            {cert.resources?.length > 0 && (
              <div className="card cd-resources">
                <h3>{t('cert.studyResources')}</h3>
                <ul>
                  {cert.resources.map(r => (
                    <li key={r.url}>
                      <a href={r.url} target="_blank" rel="noreferrer">
                        <ExternalLink size={14} /> {r.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        {tab === 'practice' && <PracticeTest cert={cert} />}
        {tab === 'flashcards' && <Flashcards cert={cert} />}
        {tab === 'study' && <StudyAI cert={cert} />}
        {tab === 'plan' && <StudyPlan cert={cert} />}
      </div>
    </div>
  )
}
