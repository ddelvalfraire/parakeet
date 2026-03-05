import { BrowserRouter, Routes, Route } from "react-router"
import Landing from "@/pages/Landing"
import DashboardLayout from "@/layouts/DashboardLayout"
import Dashboard from "@/pages/Dashboard"
import IncidentDetail from "@/pages/IncidentDetail"
import Retrospective from "@/pages/Retrospective"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route element={<DashboardLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/incident/:id" element={<IncidentDetail />} />
          <Route path="/incident/:id/retro" element={<Retrospective />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
