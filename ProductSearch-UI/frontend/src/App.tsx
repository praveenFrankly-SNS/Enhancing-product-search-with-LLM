import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { HomePage } from '@/pages/customer/HomePage'
import { SearchPage } from '@/pages/customer/SearchPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        {/* Add more routes as needed */}
      </Routes>
    </BrowserRouter>
  )
}

export default App
