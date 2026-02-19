import { useTranslation } from '../../i18n/useTranslation'

const featureKeys = ['research', 'empower', 'rankings', 'strength', 'roadmap', 'draft'] as const

const FeaturesSection = () => {
    const { t } = useTranslation()

    return (
        <section id="features" className="py-20 sm:py-28 bg-official-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Section Header */}
                <div className="text-center max-w-3xl mx-auto mb-16">
                    <span className="text-brand text-sm font-semibold tracking-widest uppercase">{t('features.label')}</span>
                    <h2 className="mt-3 text-3xl sm:text-4xl md:text-5xl font-bold text-official-900 leading-tight">
                        {t('features.heading1')}{' '}
                        <span className="text-brand">{t('features.heading2')}</span>
                    </h2>
                    <p className="mt-5 text-lg text-official-600 leading-relaxed">
                        {t('features.description')}
                    </p>
                </div>

                {/* Feature Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {featureKeys.map((key) => (
                        <div
                            key={key}
                            className="group relative rounded-lg p-8 bg-white border border-official-200 hover:border-brand/30 hover:shadow-md transition-all duration-300 flex items-center justify-center text-center"
                        >
                            <h3 className="text-xl font-bold text-official-900 group-hover:text-brand transition-colors duration-300">
                                {t(`features.items.${key}`)}
                            </h3>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}

export default FeaturesSection
