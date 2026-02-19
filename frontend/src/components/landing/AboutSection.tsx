import { useTranslation } from '../../i18n/useTranslation'

const AboutSection = () => {
    const { t } = useTranslation()

    const pillarKeys = ['access', 'intelligence', 'empowerment'] as const

    return (
        <section id="about" className="py-20 sm:py-28 bg-white border-t border-official-100">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Section Header */}
                <div className="text-center max-w-3xl mx-auto mb-16">
                    <span className="text-brand text-sm font-semibold tracking-widest uppercase">{t('about.label')}</span>
                    <h2 className="mt-3 text-3xl sm:text-4xl md:text-5xl font-bold text-official-900 leading-tight">
                        {t('about.heading1')}{' '}
                        <span className="text-brand">{t('about.heading2')}</span>
                    </h2>
                    <p className="mt-5 text-lg text-official-600 leading-relaxed">
                        {t('about.description')}
                    </p>
                </div>

                {/* Three Pillars */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
                    {pillarKeys.map((key) => (
                        <div
                            key={key}
                            className="group relative rounded-lg p-8 bg-official-50 border border-official-200 hover:border-brand/30 transition-all duration-300 flex items-center justify-center text-center"
                        >
                            <h3 className="text-2xl font-bold text-official-900">{t(`about.pillars.${key}`)}</h3>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}

export default AboutSection
