import { useState, useEffect } from 'react'
import { useTranslation } from '../../i18n/useTranslation'
import LanguageSelector from '../ui/LanguageSelector'

const Header = () => {
    const [scrolled, setScrolled] = useState(false)
    const { t } = useTranslation()

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 50)
        }
        window.addEventListener('scroll', handleScroll)
        return () => window.removeEventListener('scroll', handleScroll)
    }, [])

    return (
        <header
            className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled
                ? 'bg-white/95 backdrop-blur-md shadow-sm border-b border-official-200'
                : 'bg-white border-b border-transparent'
                }`}
        >
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16 sm:h-20">
                    {/* Brand (Text Only) */}
                    <div className="flex items-center gap-3">
                        <div>
                            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-official-900">
                                {t('header.brand')}
                            </h1>
                            <p className="text-[10px] sm:text-xs text-official-500 tracking-widest uppercase mt-0.5">
                                {t('header.tagline')}
                            </p>
                        </div>
                    </div>

                    {/* Nav Links */}
                    <nav className="hidden md:flex items-center gap-8">
                        {[
                            { key: 'about', href: '#about' },
                            { key: 'features', href: '#features' },
                            { key: 'useCases', href: '#use-cases' },
                        ].map((item) => (
                            <a
                                key={item.key}
                                href={item.href}
                                className="text-sm text-official-600 hover:text-brand transition-colors font-medium"
                            >
                                {t(`header.nav.${item.key}`)}
                            </a>
                        ))}
                        <LanguageSelector />
                    </nav>

                    {/* Mobile: Language Selector + Menu */}
                    <div className="md:hidden flex items-center gap-3">
                        <LanguageSelector />
                        <button className="text-official-900 font-medium text-sm">
                            {t('header.menu')}
                        </button>
                    </div>
                </div>
            </div>
        </header>
    )
}

export default Header
