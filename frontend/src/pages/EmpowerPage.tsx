import { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { analyzeEmpowerment } from '../services/api'
import type { EmpowerResponse, CaseResult } from '../services/api'
import { useTranslation } from '../i18n/useTranslation'
import { useSpeechRecognition } from '../hooks/useSpeechRecognition'
import LanguageSelector from '../components/ui/LanguageSelector'

const EmpowerPage = () => {
    const { t } = useTranslation()
    const [query, setQuery] = useState('')
    const [context, setContext] = useState('')
    const [results, setResults] = useState<EmpowerResponse | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const onVoiceResult = useCallback((text: string) => {
        setQuery(prev => prev ? prev + ' ' + text : text)
    }, [])
    const { isListening, toggleListening, isSupported } = useSpeechRecognition(onVoiceResult)

    const handleAnalyze = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!query.trim()) return

        setLoading(true)
        setError('')
        setResults(null)

        try {
            const data = await analyzeEmpowerment(query, context || undefined)
            setResults(data)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Something went wrong')
        } finally {
            setLoading(false)
        }
    }

    const strengthConfig = {
        Strong: { color: 'text-emerald-700 bg-emerald-50 border-emerald-300', icon: '🟢', bar: 'bg-emerald-500', width: 'w-full' },
        Moderate: { color: 'text-amber-700 bg-amber-50 border-amber-300', icon: '🟡', bar: 'bg-amber-500', width: 'w-2/3' },
        Weak: { color: 'text-red-600 bg-red-50 border-red-300', icon: '🔴', bar: 'bg-red-500', width: 'w-1/3' },
    }

    const renderCaseCard = (c: CaseResult, index: number) => (
        <div key={`${c.case_name}-${index}`} className="group rounded-xl border border-official-200 bg-white p-5 hover:shadow-md hover:border-brand/20 hover:-translate-y-0.5 transition-all duration-300">
            <h4 className="font-bold text-official-900 group-hover:text-brand transition-colors leading-snug mb-2 line-clamp-2">{c.case_name}</h4>
            <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className="px-2 py-0.5 rounded-md bg-official-100 text-official-600 text-xs font-medium">🏛️ {c.court}</span>
                <span className="px-2 py-0.5 rounded-md bg-official-100 text-official-600 text-xs font-medium">📅 {c.year}</span>
                <span className={`px-2 py-0.5 rounded-md border text-xs font-bold ${c.strength_score >= 70 ? 'text-emerald-600 bg-emerald-50 border-emerald-200' : c.strength_score >= 40 ? 'text-amber-600 bg-amber-50 border-amber-200' : 'text-red-500 bg-red-50 border-red-200'}`}>
                    Score: {c.strength_score.toFixed(1)}
                </span>
            </div>
            <p className="text-sm text-official-500 leading-relaxed line-clamp-2">{c.summary}</p>
            {c.kanoon_tid && (
                <a href={`https://indiankanoon.org/doc/${c.kanoon_tid}/`} target="_blank" rel="noopener noreferrer" className="inline-block mt-3 text-xs text-brand hover:text-brand-dark font-medium transition-colors">
                    View on Indian Kanoon →
                </a>
            )}
        </div>
    )

    return (
        <div className="min-h-screen bg-official-50">
            {/* Header Bar */}
            <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-official-200 shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <Link to="/" className="flex items-center gap-2 group">
                            <span className="text-xl font-bold text-official-900 group-hover:text-brand transition-colors">VidhimurAI</span>
                            <span className="hidden sm:inline text-xs text-official-400 font-medium tracking-wider uppercase">/ {t('empower.title')}</span>
                        </Link>
                        <div className="flex items-center gap-3">
                            <Link to="/research" className="text-sm text-official-600 hover:text-brand font-medium transition-colors">
                                {t('header.nav.research')}
                            </Link>
                            <LanguageSelector />
                        </div>
                    </div>
                </div>
            </header>

            {/* Hero Input */}
            <section className="relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-50/50 via-transparent to-brand/5"></div>
                <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-10">
                    <div className="text-center mb-8">
                        <h1 className="text-3xl sm:text-4xl font-bold text-official-900 mb-3">
                            {t('empower.heading1')} <span className="text-brand">{t('empower.heading2')}</span>
                        </h1>
                        <p className="text-official-500 text-lg">{t('empower.subtitle')}</p>
                    </div>

                    <form onSubmit={handleAnalyze} className="space-y-4">
                        <div className="bg-white rounded-xl border border-official-200 shadow-lg focus-within:border-brand focus-within:ring-2 focus-within:ring-brand/20 transition-all overflow-hidden">
                            <div className="relative">
                                <textarea
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder={t('empower.placeholder')}
                                    rows={4}
                                    className="w-full px-5 pt-5 pb-2 pr-12 text-base text-official-900 placeholder:text-official-400 focus:outline-none resize-none bg-transparent"
                                />
                                {isSupported && (
                                    <button
                                        type="button"
                                        onClick={toggleListening}
                                        className={`absolute top-4 right-4 p-1.5 rounded-full transition-all duration-300 ${isListening
                                            ? 'text-red-500 bg-red-50 animate-pulse'
                                            : 'text-official-400 hover:text-brand hover:bg-official-50'
                                            }`}
                                        title={isListening ? 'Stop listening' : 'Voice input'}
                                    >
                                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                                            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                                        </svg>
                                    </button>
                                )}
                            </div>
                            <div className="border-t border-official-100 px-5 py-3">
                                <input
                                    type="text"
                                    value={context}
                                    onChange={(e) => setContext(e.target.value)}
                                    placeholder={t('empower.contextPlaceholder')}
                                    className="w-full text-sm text-official-700 placeholder:text-official-400 focus:outline-none bg-transparent"
                                />
                            </div>
                        </div>

                        <div className="text-center">
                            <button
                                type="submit"
                                disabled={loading || !query.trim()}
                                className="px-10 py-3.5 bg-brand text-white font-semibold rounded-xl shadow-md hover:bg-brand-dark hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 active:scale-[0.98]"
                            >
                                {loading ? (
                                    <span className="inline-flex items-center gap-2">
                                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                                        {t('empower.analyzing')}
                                    </span>
                                ) : t('empower.analyzeBtn')}
                            </button>
                        </div>
                    </form>
                </div>
            </section>

            {/* Results */}
            <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
                {error && (
                    <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm font-medium flex items-center gap-2">
                        <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        {error}
                    </div>
                )}

                {loading && (
                    <div className="flex flex-col items-center justify-center py-20">
                        <div className="w-12 h-12 border-4 border-official-200 border-t-brand rounded-full animate-spin mb-4"></div>
                        <p className="text-official-500 font-medium">{t('empower.analyzing')}</p>
                    </div>
                )}

                {results && !loading && (
                    <div className="space-y-8">
                        {/* Top Summary Row */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {/* Issue Type */}
                            <div className="rounded-xl border border-official-200 bg-white p-6 shadow-sm">
                                <p className="text-xs font-semibold text-official-400 uppercase tracking-wider mb-2">{t('empower.issueType')}</p>
                                <p className="text-xl font-bold text-official-900">{results.issue_type}</p>
                            </div>

                            {/* Legal Strength */}
                            <div className={`rounded-xl border p-6 shadow-sm ${strengthConfig[results.legal_strength].color}`}>
                                <p className="text-xs font-semibold uppercase tracking-wider mb-2 opacity-70">{t('empower.legalStrength')}</p>
                                <div className="flex items-center gap-3">
                                    <span className="text-2xl">{strengthConfig[results.legal_strength].icon}</span>
                                    <span className="text-xl font-bold">{results.legal_strength}</span>
                                </div>
                                <div className="mt-3 h-2 rounded-full bg-black/10 overflow-hidden">
                                    <div className={`h-full rounded-full transition-all duration-700 ${strengthConfig[results.legal_strength].bar} ${strengthConfig[results.legal_strength].width}`}></div>
                                </div>
                            </div>
                        </div>

                        {/* Relevant Legal Sections */}
                        {results.relevant_sections.length > 0 && (
                            <div className="rounded-xl border border-official-200 bg-white p-6 shadow-sm">
                                <h3 className="text-sm font-bold text-official-900 uppercase tracking-wider mb-4">{t('empower.relevantSections')}</h3>
                                <div className="flex flex-wrap gap-2">
                                    {results.relevant_sections.map((s, i) => (
                                        <span key={i} className="px-3 py-1.5 rounded-lg bg-brand/5 text-brand text-sm font-medium border border-brand/10">
                                            {s}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Precedent Cases */}
                        {results.precedents.length > 0 && (
                            <div>
                                <h3 className="text-sm font-bold text-official-900 uppercase tracking-wider mb-4">{t('empower.precedents')}</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {results.precedents.map((c, i) => renderCaseCard(c, i))}
                                </div>
                            </div>
                        )}

                        {/* Action Roadmap */}
                        {results.action_steps.length > 0 && (
                            <div className="rounded-xl border border-official-200 bg-white p-6 shadow-sm">
                                <h3 className="text-sm font-bold text-official-900 uppercase tracking-wider mb-5">{t('empower.actionRoadmap')}</h3>
                                <div className="space-y-4">
                                    {results.action_steps.map((step, i) => (
                                        <div key={i} className="flex gap-4 group">
                                            <div className="flex flex-col items-center">
                                                <div className="w-8 h-8 rounded-full bg-brand text-white flex items-center justify-center text-sm font-bold shrink-0 shadow-sm group-hover:scale-110 transition-transform">
                                                    {i + 1}
                                                </div>
                                                {i < results.action_steps.length - 1 && (
                                                    <div className="w-0.5 flex-1 bg-official-200 mt-1"></div>
                                                )}
                                            </div>
                                            <div className="pb-4 flex-1">
                                                <p className="text-sm text-official-700 leading-relaxed font-medium">{step}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {!results && !loading && !error && (
                    <div className="text-center py-20">
                        <div className="text-5xl mb-4 opacity-40">🛡️</div>
                        <p className="text-official-400 text-lg font-medium">{t('empower.emptyState')}</p>
                    </div>
                )}
            </section>
        </div>
    )
}

export default EmpowerPage
