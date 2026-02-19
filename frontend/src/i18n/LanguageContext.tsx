import { createContext, useState, useEffect, type ReactNode } from 'react'

export type LanguageCode =
    | 'en' | 'hi' | 'ta' | 'te' | 'kn' | 'ml'
    | 'bn' | 'mr' | 'gu' | 'pa' | 'or' | 'as' | 'ur'

export interface LanguageInfo {
    code: LanguageCode
    name: string       // English name
    nativeName: string // Name in its own script
}

export const LANGUAGES: LanguageInfo[] = [
    { code: 'en', name: 'English', nativeName: 'English' },
    { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी' },
    { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்' },
    { code: 'te', name: 'Telugu', nativeName: 'తెలుగు' },
    { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ' },
    { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം' },
    { code: 'bn', name: 'Bengali', nativeName: 'বাংলা' },
    { code: 'mr', name: 'Marathi', nativeName: 'मराठी' },
    { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી' },
    { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ' },
    { code: 'or', name: 'Odia', nativeName: 'ଓଡ଼ିଆ' },
    { code: 'as', name: 'Assamese', nativeName: 'অসমীয়া' },
    { code: 'ur', name: 'Urdu', nativeName: 'اردو' },
]

interface LanguageContextType {
    language: LanguageCode
    setLanguage: (lang: LanguageCode) => void
}

export const LanguageContext = createContext<LanguageContextType>({
    language: 'en',
    setLanguage: () => { },
})

const STORAGE_KEY = 'vidhimurai-lang'

export const LanguageProvider = ({ children }: { children: ReactNode }) => {
    const [language, setLanguageState] = useState<LanguageCode>(() => {
        const saved = localStorage.getItem(STORAGE_KEY)
        return (saved as LanguageCode) || 'en'
    })

    const setLanguage = (lang: LanguageCode) => {
        setLanguageState(lang)
        localStorage.setItem(STORAGE_KEY, lang)
    }

    useEffect(() => {
        document.documentElement.lang = language
        // Set RTL for Urdu
        document.documentElement.dir = language === 'ur' ? 'rtl' : 'ltr'
    }, [language])

    return (
        <LanguageContext.Provider value={{ language, setLanguage }}>
            {children}
        </LanguageContext.Provider>
    )
}
