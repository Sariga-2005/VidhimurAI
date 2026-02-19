import { useState, useRef, useEffect, useContext } from 'react'
import { LanguageContext, LANGUAGES } from '../../i18n/LanguageContext'
import type { LanguageCode } from '../../i18n/LanguageContext'

const LanguageSelector = () => {
    const { language, setLanguage } = useContext(LanguageContext)
    const [open, setOpen] = useState(false)
    const ref = useRef<HTMLDivElement>(null)

    const current = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0]

    // Close dropdown on outside click
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (ref.current && !ref.current.contains(e.target as Node)) {
                setOpen(false)
            }
        }
        document.addEventListener('mousedown', handler)
        return () => document.removeEventListener('mousedown', handler)
    }, [])

    const handleSelect = (code: LanguageCode) => {
        setLanguage(code)
        setOpen(false)
    }

    return (
        <div ref={ref} className="relative">
            {/* Trigger Button */}
            <button
                onClick={() => setOpen(!open)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-official-200 bg-white text-sm font-medium text-official-700 hover:border-brand/40 hover:text-brand transition-colors"
                aria-label="Select language"
            >
                <span className="text-xs">{current.nativeName}</span>
                <svg
                    className={`w-3.5 h-3.5 transition-transform ${open ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
            </button>

            {/* Dropdown */}
            {open && (
                <div className="absolute right-0 mt-2 w-48 max-h-72 overflow-y-auto rounded-lg border border-official-200 bg-white shadow-lg z-50">
                    {LANGUAGES.map((lang) => (
                        <button
                            key={lang.code}
                            onClick={() => handleSelect(lang.code)}
                            className={`w-full text-left px-4 py-2.5 text-sm flex items-center justify-between hover:bg-official-50 transition-colors ${lang.code === language
                                    ? 'text-brand font-semibold bg-blue-50/50'
                                    : 'text-official-700'
                                }`}
                        >
                            <span>{lang.nativeName}</span>
                            <span className="text-xs text-official-400">{lang.name}</span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    )
}

export default LanguageSelector
