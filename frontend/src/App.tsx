import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { FIXED_TENANT } from '@/services/api'
import Layout from '@/components/Layout'
import Login from '@/pages/Login'
import InviteAccept from '@/pages/InviteAccept'
import Home from '@/pages/Home'
import Areas from '@/pages/Areas'
import Program from '@/pages/Program'
import ProgramEditor from '@/pages/ProgramEditor'
import RoutesPage from '@/pages/Routes'
import RoutesEditor from '@/pages/RoutesEditor'
import CertDetail from '@/pages/CertDetail'
import History from '@/pages/History'
import Admin from '@/pages/Admin'
import AdminUser from '@/pages/AdminUser'
import AdminActivity from '@/pages/AdminActivity'
import AdminGroups from '@/pages/AdminGroups'
import AdminTracks from '@/pages/AdminTracks'
import Leaderboard from '@/pages/Leaderboard'

const Spinner = () => <div className="spinner" />

// Plataforma single-tenant AT&T: sem seletor de empresa, sem console de plataforma.
// Raiz → login branded AT&T; depois de logar, o app.
function AppGate() {
  const { user, loading } = useAuth()
  if (loading) return <Spinner />
  if (!user) return <Login fixedSlug={FIXED_TENANT} />
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Areas />} />
        <Route path="programa" element={<Program />} />
        <Route path="simulacros" element={<Home />} />
        <Route path="rutas" element={<RoutesPage />} />
        <Route path="rutas/editar" element={<RoutesEditor />} />
        <Route path="programa/editar" element={<ProgramEditor />} />
        <Route path="cert/:id" element={<CertDetail />} />
        <Route path="historico" element={<History />} />
        <Route path="ranking" element={<Leaderboard />} />
        {user.is_admin && <Route path="admin" element={<Admin />} />}
        {user.is_admin && <Route path="admin/activity" element={<AdminActivity />} />}
        {user.is_admin && <Route path="admin/user/:email" element={<AdminUser />} />}
        {user.is_admin && <Route path="admin/grupos" element={<AdminGroups />} />}
        {user.is_admin && <Route path="admin/trilhas" element={<AdminTracks />} />}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/invite/:token" element={<InviteAccept />} />
        <Route path="/*" element={<AppGate />} />
      </Routes>
    </BrowserRouter>
  )
}
