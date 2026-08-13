import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  CheckCircle2, XCircle, RefreshCw, ChevronDown, ChevronRight,
  FileText, FileSpreadsheet, Loader2, Wrench,
} from 'lucide-react'
import {
  getMyAttempts, getMySession, getMySessionPdf,
  getMySessionRepair, getMySessionRepairPdf,
} from '@/services/api'
import { downloadCsv, downloadBlob, optionLabels } from '@/lib/export'
import { useT, useI18n } from '@/i18n'
import type { Attempt } from '@/types'
import './History.css'

const LOCALE = { es: 'es-CL', pt: 'pt-BR', en: 'en-US' } as const

function RepairSection({ sessionId }: { sessionId: string }) {
  const t = useT()
  const [busy, setBusy] = useState(false)
  const { data } = useQuery({
    queryKey: ['my-session-repair', sessionId],
    queryFn: () => getMySessionRepair(sessionId),
  })
  const items = data?.items ?? []
  if (!items.length) return null

  async function exportPdf() {
    setBusy(true)
    try {
      const blob = await getMySessionRepairPdf(sessionId)
      downloadBlob(blob, `explicacoes_${sessionId.slice(0, 8)}.pdf`)
    } finally { setBusy(false) }
  }

  return (
    <div className="card pt-repair hist-repair">
      <div className="pt-repair-head">
        <h3><Wrench size={17} /> {t('practice.repairTitle')}</h3>
        <button className="au-exp-btn" disabled={busy} onClick={exportPdf}>
          {busy ? <Loader2 size={14} className="spinning" /> : <FileText size={14} />} {t('practice.exportPdf')}
        </button>
      </div>
      {items.map((it, i) => (
        <div key={i} className="pt-repair-item">
          <p className="pt-repair-q"><b>{i + 1}.</b> {it.question_text}</p>
          <div className="pt-repair-block pt-repair-mis">
            <span className="pt-repair-lbl">{t('practice.misconception')}</span> {it.misconception}
          </div>
          <div className="pt-repair-block pt-repair-why">
            <span className="pt-repair-lbl">{t('practice.whyCorrect')}</span> {it.why_correct}
          </div>
          <div className="pt-repair-block pt-repair-rel">
            <span className="pt-repair-lbl">{t('practice.relatedQuestion')}</span> {it.related_question}
          </div>
        </div>
      ))}
    </div>
  )
}

function AnswersPanel({ sessionId }: { sessionId: string }) {
  const t = useT()
  const { data, isLoading } = useQuery({
    queryKey: ['my-session', sessionId],
    queryFn: () => getMySession(sessionId),
  })
  if (isLoading) return <div className="spinner" />
  if (!data) return null
  return (
    <div className="au-answers">
      {data.answers.map((a, i) => (
        <div key={a.question_id} className="au-q">
          <div className="au-q-head">
            <span className="pt-topic-tag">{a.topic}</span>
            {a.is_ai_generated && <span className="badge badge-ai">IA</span>}
            <span className={`pt-verdict ${a.is_correct ? 'ok' : 'no'}`}>
              {a.is_correct ? <><CheckCircle2 size={14} /> {t('practice.correctLabel')}</> : <><XCircle size={14} /> {t('practice.incorrectLabel')}</>}
            </span>
          </div>
          <p className="au-q-text"><b>{i + 1}.</b> {a.question_text}</p>
          <div className="pt-rev-opts">
            {a.options.map((opt, oi) => {
              const isCorrect = a.correct_answers.includes(oi)
              const isSel = a.selected.includes(oi)
              return (
                <div key={oi} className={`pt-rev-opt ${isCorrect ? 'correct' : ''} ${isSel && !isCorrect ? 'wrong' : ''}`}>
                  <span>{opt}</span>
                  {isCorrect && <span className="pt-tag ok">{t('practice.correctTag')}</span>}
                  {isSel && !isCorrect && <span className="pt-tag no">{t('practice.yourAnswerWrong')}</span>}
                </div>
              )
            })}
          </div>
          {a.explanation && <div className="pt-explain"><b>{t('practice.explanation')}</b> {a.explanation}</div>}
        </div>
      ))}
      <RepairSection sessionId={sessionId} />
    </div>
  )
}

export default function History() {
  const navigate = useNavigate()
  const t = useT()
  const { lang } = useI18n()
  const { data, isLoading } = useQuery({ queryKey: ['my-attempts'], queryFn: getMyAttempts })
  const [open, setOpen] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)   // `${sid}:csv|pdf`

  if (isLoading) return <div className="spinner" />

  const attempts = data?.attempts ?? []
  const passMark = data?.pass_mark ?? 70
  const fmt = (s?: string) => s ? new Date(s).toLocaleString(LOCALE[lang]) : '—'

  async function exportAttemptCsv(a: Attempt) {
    setBusy(`${a.session_id}:csv`)
    try {
      const detail = await getMySession(a.session_id)
      const header = [
        [t('history.certification'), a.certification_name ?? a.certification_id],
        [t('history.date'), fmt(a.created_at)], [t('history.score'), `${a.score_pct}%`],
        [t('history.result'), a.passed ? t('history.approved') : t('history.reproved')],
        ['', `${a.correct}/${a.total}`], [t('history.repeated'), a.repeated_questions], [],
      ]
      const table: (string | number | boolean)[][] = [
        ['#', t('history.certification'), a.certification_name ?? a.certification_id],
        [],
        ['#', 'Topic', 'Question', 'Options', 'Your answer', 'Correct', 'OK?', 'Explanation'],
        ...detail.answers.map((ans, i) => [
          i + 1, ans.topic, ans.question_text,
          ans.options.map((o, oi) => `${'ABCDEFGH'[oi]}) ${o}`).join(' | '),
          optionLabels(ans.selected), optionLabels(ans.correct_answers),
          ans.is_correct ? 'OK' : 'X', ans.explanation,
        ]),
      ]
      downloadCsv(`test_${a.session_id.slice(0, 8)}.csv`, [...header, ...table])
    } finally { setBusy(null) }
  }

  async function exportAttemptPdf(a: Attempt) {
    setBusy(`${a.session_id}:pdf`)
    try {
      const blob = await getMySessionPdf(a.session_id)
      downloadBlob(blob, `test_${a.session_id.slice(0, 8)}.pdf`)
    } finally { setBusy(null) }
  }

  return (
    <div>
      <h1 className="hist-title">{t('history.title')}</h1>
      <p className="muted hist-sub">{t('history.sub', { m: passMark })}</p>

      {attempts.length === 0 ? (
        <div className="card hist-empty">
          <p>{t('history.empty')}</p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>{t('history.startNow')}</button>
        </div>
      ) : (
        <div className="au-list">
          {attempts.map(a => {
            const isOpen = open === a.session_id
            return (
              <div key={a.session_id} className="card au-attempt">
                <div className="au-attempt-bar">
                  <button className="au-attempt-head" onClick={() => setOpen(isOpen ? null : a.session_id)}>
                    {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                    <span className="au-cert">{a.certification_name ?? a.certification_id}</span>
                    <span className="au-date">{fmt(a.created_at)}</span>
                    <span className="au-score"><b>{a.score_pct}%</b> ({a.correct}/{a.total})</span>
                    {a.repeated_questions > 0 &&
                      <span className="hist-rep"><RefreshCw size={12} /> {a.repeated_questions}</span>}
                    {a.passed
                      ? <span className="hist-badge ok"><CheckCircle2 size={14} /> {t('history.approved')}</span>
                      : <span className="hist-badge no"><XCircle size={14} /> {t('history.reproved')}</span>}
                    {a.ai_generated && <span className="badge badge-ai">{t('history.ai')}</span>}
                  </button>
                  <div className="au-exports">
                    <button className="au-exp-btn" title="CSV"
                      disabled={busy === `${a.session_id}:csv`} onClick={() => exportAttemptCsv(a)}>
                      {busy === `${a.session_id}:csv` ? <Loader2 size={14} className="spinning" /> : <FileSpreadsheet size={14} />} CSV
                    </button>
                    <button className="au-exp-btn" title="PDF"
                      disabled={busy === `${a.session_id}:pdf`} onClick={() => exportAttemptPdf(a)}>
                      {busy === `${a.session_id}:pdf` ? <Loader2 size={14} className="spinning" /> : <FileText size={14} />} PDF
                    </button>
                  </div>
                </div>
                {isOpen && <AnswersPanel sessionId={a.session_id} />}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
