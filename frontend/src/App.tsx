import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import ResearchPage from './pages/ResearchPage'
import EmpowerPage from './pages/EmpowerPage'

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/research" element={<ResearchPage />} />
                <Route path="/empower" element={<EmpowerPage />} />
            </Routes>
        </BrowserRouter>
    )
}

export default App
