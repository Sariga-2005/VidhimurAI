import { useTranslation } from '../../i18n/useTranslation'

const Footer = () => {
    const currentYear = new Date().getFullYear()
    const { t } = useTranslation()

    return (
        <footer className="bg-official-900 border-t border-official-800 text-official-300">
            {/* Bottom Bar */}
            <div className="border-t border-official-800">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                        <p className="text-xs text-official-500 text-center sm:text-left">
                            {t('footer.copyright', { year: String(currentYear) })}
                        </p>
                        <div className="flex items-center gap-4">
                            <span className="text-xs text-official-500">{t('footer.madeIn')}</span>
                        </div>
                    </div>
                </div>
            </div>
        </footer>
    )
}

export default Footer
