import Button from '../ui/Button'
import { useTranslation } from '../../i18n/useTranslation'

const HeroSection = () => {
    const { t } = useTranslation()

    return (
        <section
            id="hero"
            className="relative min-h-screen flex items-center justify-center bg-official-50 pt-20"
        >
            {/* Content */}
            <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">

                {/* Headline */}
                <h1
                    className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-official-900 leading-tight tracking-tight mb-6"
                >
                    {t('hero.headline1')}
                    <br className="hidden sm:block" />
                    <span className="text-brand">{t('hero.headline2')}</span>
                </h1>

                {/* Subheadline */}
                <p
                    className="text-lg sm:text-xl md:text-2xl text-official-600 max-w-3xl mx-auto leading-relaxed mb-10"
                >
                    {t('hero.subheadline')}
                </p>

                {/* CTA Buttons */}
                <div
                    className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-5"
                >
                    <Button variant="secondary" size="lg" className="min-w-64">
                        {t('hero.cta2')}
                    </Button>
                    <Button variant="primary" size="lg" className="min-w-64">
                        {t('hero.cta1')}
                    </Button>
                </div>

            </div>
        </section>
    )
}

export default HeroSection
