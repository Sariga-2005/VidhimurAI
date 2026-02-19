import { useTranslation } from '../../i18n/useTranslation'

const useCaseKeys = ['citizens', 'lawyers', 'students', 'ngos'] as const

const UseCasesSection = () => {
    const { t } = useTranslation()

    return (
        <section id="use-cases" className="py-20 sm:py-28 bg-white border-t border-official-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Section Header */}
                <div className="text-center max-w-3xl mx-auto mb-16">
                    <span className="text-brand text-sm font-semibold tracking-widest uppercase">{t('useCases.label')}</span>
                    <h2 className="mt-3 text-3xl sm:text-4xl md:text-5xl font-bold text-official-900 leading-tight">
                        {t('useCases.heading1')}{' '}
                        <span className="text-brand">{t('useCases.heading2')}</span>
                    </h2>
                    <p className="mt-5 text-lg text-official-600 leading-relaxed">
                        {t('useCases.description')}
                    </p>
                </div>

                {/* Use Case Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {useCaseKeys.map((key) => (
                        <div
                            key={key}
                            className="group relative rounded-lg p-7 bg-official-50 border border-official-200 hover:border-brand/30 hover:-translate-y-1 transition-all duration-300 flex items-center justify-center text-center"
                        >
                            <h3 className="text-xl font-bold text-official-900">{t(`useCases.items.${key}`)}</h3>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}

export default UseCasesSection
