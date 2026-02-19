import Header from '../components/layout/Header'
import Footer from '../components/layout/Footer'
import HeroSection from '../components/landing/HeroSection'
import AboutSection from '../components/landing/AboutSection'
import FeaturesSection from '../components/landing/FeaturesSection'
import UseCasesSection from '../components/landing/UseCasesSection'

const LandingPage = () => {
    return (
        <div className="min-h-screen bg-white">
            <Header />
            <main>
                <HeroSection />
                <AboutSection />
                <FeaturesSection />
                <UseCasesSection />
            </main>
            <Footer />
        </div>
    )
}

export default LandingPage
