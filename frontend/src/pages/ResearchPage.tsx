import { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { searchCases } from '../services/api'
import type { CaseResult, SearchResponse, SearchFilters } from '../services/api'
import { useTranslation } from '../i18n/useTranslation'
import { useSpeechRecognition } from '../hooks/useSpeechRecognition'
import LanguageSelector from '../components/ui/LanguageSelector'

const ResearchPage = () => {
    const { t } = useTranslation()
    const [query, setQuery] = useState('')
    const [court, setCourt] = useState('')
    const [yearStart, setYearStart] = useState('')
    const [yearEnd, setYearEnd] = useState('')
    const [results, setResults] = useState<SearchResponse | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [showFilters, setShowFilters] = useState(false)

    const onVoiceResult = useCallback((text: string) => {
        setQuery(prev => prev ? prev + ' ' + text : text)
    }, [])
    const { isListening, toggleListening, isSupported } = useSpeechRecognition(onVoiceResult)

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!query.trim()) return

        setLoading(true)
        setError('')
        setResults(null)

        try {
            const filters: SearchFilters = {}
            if (court) filters.court = court
            if (yearStart) filters.year_start = parseInt(yearStart)
            if (yearEnd) filters.year_end = parseInt(yearEnd)

            const data = await searchCases(query, Object.keys(filters).length > 0 ? filters : undefined)
            setResults(data)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Something went wrong')
        } finally {
            setLoading(false)
        }
    }

    const getScoreColor = (score: number) => {
        if (score >= 70) return 'text-emerald-600 bg-emerald-50 border-emerald-200'
        if (score >= 40) return 'text-amber-600 bg-amber-50 border-amber-200'
        return 'text-red-500 bg-red-50 border-red-200'
    }

    const renderCaseCard = (c: CaseResult, index: number, isInfluential = false) => (
        <div
            key={`${c.case_name}-${index}`}
            className={`group relative rounded-xl border p-6 transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5 ${isInfluential
                ? 'bg-gradient-to-br from-brand/5 via-white to-blue-50 border-brand/30 shadow-md ring-1 ring-brand/10'
                : 'bg-white border-official-200 hover:border-brand/20'
                }`}
        >
            {isInfluential && (
                <div className="absolute -top-3 left-6 px-3 py-1 bg-brand text-white text-xs font-bold rounded-full shadow-sm">
                    ⭐ {t('research.mostInfluential')}
                </div>
            )}

            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-4">
                <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-bold text-official-900 leading-snug group-hover:text-brand transition-colors line-clamp-2">
                        {c.case_name}
                    </h3>
                    <div className="flex flex-wrap items-center gap-2 mt-2">
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-official-100 text-official-600 text-xs font-medium">
                            🏛️ {c.court}
                        </span>
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-official-100 text-official-600 text-xs font-medium">
                            📅 {c.year}
                        </span>
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-official-100 text-official-600 text-xs font-medium">
                            📚 {c.citation_count} citations
                        </span>
                    </div>
                </div>
                <div className={`shrink-0 px-3 py-1.5 rounded-lg border text-sm font-bold ${getScoreColor(c.strength_score)}`}>
                    {c.strength_score.toFixed(1)}
                </div>
            </div>

            <p className="text-sm text-official-600 leading-relaxed mb-4 line-clamp-3">{c.summary}</p>

            <div className="flex flex-wrap gap-3 pt-3 border-t border-official-100">
                <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-brand"></div>
                    <span className="text-xs text-official-500">{t('research.authority')}: <strong className="text-official-700">{c.authority_score.toFixed(1)}</strong></span>
                </div>
                <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                    <span className="text-xs text-official-500">{t('research.relevance')}: <strong className="text-official-700">{c.relevance_score.toFixed(1)}</strong></span>
                </div>
                {c.kanoon_tid && (
                    <a
                        href={`https://indiankanoon.org/doc/${c.kanoon_tid}/`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-auto text-xs text-brand hover:text-brand-dark font-medium transition-colors"
                    >
                        View on Indian Kanoon →
                    </a>
                )}
            </div>
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
                            <span className="hidden sm:inline text-xs text-official-400 font-medium tracking-wider uppercase">/ {t('research.title')}</span>
                        </Link>
                        <div className="flex items-center gap-3">
                            <Link to="/empower" className="text-sm text-official-600 hover:text-brand font-medium transition-colors">
                                {t('header.nav.empower')}
                            </Link>
                            <LanguageSelector />
                        </div>
                    </div>
                </div>
            </header>

            {/* Hero Search */}
            <section className="relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-brand/5 via-transparent to-blue-50/50"></div>
                <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-10">
                    <div className="text-center mb-8">
                        <h1 className="text-3xl sm:text-4xl font-bold text-official-900 mb-3">
                            {t('research.heading1')} <span className="text-brand">{t('research.heading2')}</span>
                        </h1>
                        <p className="text-official-500 text-lg">{t('research.subtitle')}</p>
                    </div>

                    <form onSubmit={handleSearch} className="space-y-4">
                        <div className="relative">
                            <div className="flex rounded-xl overflow-hidden shadow-lg border border-official-200 focus-within:border-brand focus-within:ring-2 focus-within:ring-brand/20 transition-all bg-white">
                                <span className="flex items-center pl-5 text-official-400">
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                                </span>
                                <input
                                    type="text"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder={t('research.placeholder')}
                                    className="flex-1 px-4 py-4 text-base text-official-900 placeholder:text-official-400 focus:outline-none bg-transparent"
                                />
                                {isSupported && (
                                    <button
                                        type="button"
                                        onClick={toggleListening}
                                        className={`flex items-center justify-center px-3 transition-all duration-300 ${isListening
                                            ? 'text-red-500 animate-pulse'
                                            : 'text-official-400 hover:text-brand'
                                            }`}
                                        title={isListening ? 'Stop listening' : 'Voice input'}
                                    >
                                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                                            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                                        </svg>
                                    </button>
                                )}
                                <button
                                    type="submit"
                                    disabled={loading || !query.trim()}
                                    className="px-6 sm:px-8 bg-brand text-white font-semibold hover:bg-brand-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    {loading ? (
                                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                                    ) : t('research.searchBtn')}
                                </button>
                            </div>
                        </div>

                        {/* Filter Toggle */}
                        <div className="text-center">
                            <button
                                type="button"
                                onClick={() => setShowFilters(!showFilters)}
                                className="inline-flex items-center gap-2 text-sm text-official-500 hover:text-brand font-medium transition-colors"
                            >
                                <svg className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                {t('research.advancedFilters')}
                            </button>
                        </div>

                        {/* Filters Panel */}
                        {showFilters && (
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-5 bg-white rounded-xl border border-official-200 shadow-sm animate-in">
                                <div>
                                    <label className="block text-xs font-semibold text-official-600 mb-1.5 uppercase tracking-wider">{t('research.filterCourt')}</label>
                                    <select value={court} onChange={(e) => setCourt(e.target.value)} className="w-full px-3 py-2.5 rounded-lg border border-official-200 text-sm text-official-700 bg-white focus:border-brand focus:ring-2 focus:ring-brand/20 focus:outline-none transition-all">
                                        <option value="">{t('research.allCourts')}</option>
                                        <option value="Supreme Court of India">Supreme Court</option>
                                        <option value="High Court">High Court</option>
                                        <option value="District Court">District Court</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-official-600 mb-1.5 uppercase tracking-wider">{t('research.filterYearFrom')}</label>
                                    <input type="number" value={yearStart} onChange={(e) => setYearStart(e.target.value)} placeholder="e.g. 2000" className="w-full px-3 py-2.5 rounded-lg border border-official-200 text-sm text-official-700 focus:border-brand focus:ring-2 focus:ring-brand/20 focus:outline-none transition-all" />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-official-600 mb-1.5 uppercase tracking-wider">{t('research.filterYearTo')}</label>
                                    <input type="number" value={yearEnd} onChange={(e) => setYearEnd(e.target.value)} placeholder="e.g. 2024" className="w-full px-3 py-2.5 rounded-lg border border-official-200 text-sm text-official-700 focus:border-brand focus:ring-2 focus:ring-brand/20 focus:outline-none transition-all" />
                                </div>
                            </div>
                        )}
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
                        <p className="text-official-500 font-medium">{t('research.searching')}</p>
                    </div>
                )}

                {results && !loading && (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <p className="text-sm text-official-500 font-medium">
                                {t('research.resultsFound', { count: String(results.total_cases) })}
                            </p>
                        </div>

                        {/* Most Influential */}
                        {results.most_influential_case && (
                            <div className="mb-2">
                                {renderCaseCard(results.most_influential_case, -1, true)}
                            </div>
                        )}

                        {/* All Cases */}
                        <div className="space-y-4">
                            {results.top_cases
                                .filter(c => c.case_name !== results.most_influential_case?.case_name)
                                .map((c, i) => renderCaseCard(c, i))}
                        </div>

                        {results.total_cases === 0 && (
                            <div className="text-center py-16">
                                <p className="text-xl text-official-400 mb-2">🔍</p>
                                <p className="text-official-500 font-medium">{t('research.noResults')}</p>
                            </div>
                        )}
                    </div>
                )}

                {!results && !loading && !error && (
                    <div className="text-center py-20">
                        <div className="text-5xl mb-4 opacity-40">⚖️</div>
                        <p className="text-official-400 text-lg font-medium">{t('research.emptyState')}</p>
                    </div>
                )}
            </section>
        </div>
    )
}

export default ResearchPage
