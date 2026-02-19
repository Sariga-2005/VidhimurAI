import { useContext } from 'react'
import { LanguageContext } from './LanguageContext'
import type { LanguageCode } from './LanguageContext'

// Import all translation files
import en from './translations/en.json'
import hi from './translations/hi.json'
import ta from './translations/ta.json'
import te from './translations/te.json'
import kn from './translations/kn.json'
import ml from './translations/ml.json'
import bn from './translations/bn.json'
import mr from './translations/mr.json'
import gu from './translations/gu.json'
import pa from './translations/pa.json'
import or_ from './translations/or.json'
import as_ from './translations/as.json'
import ur from './translations/ur.json'

type TranslationData = Record<string, unknown>

const translations: Record<LanguageCode, TranslationData> = {
    en, hi, ta, te, kn, ml, bn, mr, gu, pa,
    or: or_,
    as: as_,
    ur,
}

/**
 * Access a nested value by dot-notation key.
 * e.g. getNestedValue(obj, 'hero.headline1') → obj.hero.headline1
 */
function getNestedValue(obj: TranslationData, key: string): string {
    const parts = key.split('.')
    let current: unknown = obj
    for (const part of parts) {
        if (current && typeof current === 'object' && part in (current as Record<string, unknown>)) {
            current = (current as Record<string, unknown>)[part]
        } else {
            return key // fallback: return the key itself
        }
    }
    return typeof current === 'string' ? current : key
}

export function useTranslation() {
    const { language } = useContext(LanguageContext)
    const data = translations[language] || translations.en

    /**
     * Translate a dot-notation key, with optional interpolation.
     * Usage: t('footer.copyright', { year: '2026' })
     */
    const t = (key: string, vars?: Record<string, string>): string => {
        let result = getNestedValue(data as TranslationData, key)
        if (vars) {
            for (const [k, v] of Object.entries(vars)) {
                result = result.replace(`{${k}}`, v)
            }
        }
        return result
    }

    return { t, language }
}
