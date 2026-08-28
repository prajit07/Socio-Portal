import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';

import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import CitizenDashboard from './pages/CitizenDashboard';
import SubmitProblem from './pages/SubmitProblem';
import ProblemTrack from './pages/ProblemTrack';
import ProblemsList from './pages/ProblemsList';
import Notifications from './pages/Notifications';
import MapView from './pages/MapView';
import GovernmentDashboard from './pages/GovernmentDashboard';
import UniversityDashboard from './pages/UniversityDashboard';
import TeamWorkspace from './pages/TeamWorkspace';
import TeamCreate from './pages/TeamCreate';
import ProposalEditor from './pages/ProposalEditor';
import IndustryDashboard from './pages/IndustryDashboard';
import CollaborationWorkspace from './pages/CollaborationWorkspace';
import AdminDashboard from './pages/AdminDashboard';
import NotFound from './pages/NotFound';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route
            path="/citizen/dashboard"
            element={
              <ProtectedRoute roles={['citizen']}>
                <CitizenDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/citizen/submit-problem"
            element={
              <ProtectedRoute roles={['citizen']}>
                <SubmitProblem />
              </ProtectedRoute>
            }
          />

          <Route
            path="/problems"
            element={
              <ProtectedRoute>
                <ProblemsList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/problems/:id"
            element={
              <ProtectedRoute>
                <ProblemTrack />
              </ProtectedRoute>
            }
          />
          <Route
            path="/map"
            element={
              <ProtectedRoute>
                <MapView />
              </ProtectedRoute>
            }
          />
          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <Notifications />
              </ProtectedRoute>
            }
          />
          <Route
            path="/gov/dashboard"
            element={
              <ProtectedRoute roles={['government']}>
                <GovernmentDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/university/dashboard"
            element={
              <ProtectedRoute roles={['university_admin', 'student', 'faculty']}>
                <UniversityDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/university/teams/new"
            element={
              <ProtectedRoute roles={['university_admin', 'student', 'faculty']}>
                <TeamCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="/university/teams/:id"
            element={
              <ProtectedRoute roles={['university_admin', 'student', 'faculty']}>
                <TeamWorkspace />
              </ProtectedRoute>
            }
          />
          <Route
            path="/university/proposals/new"
            element={
              <ProtectedRoute roles={['university_admin', 'student', 'faculty']}>
                <ProposalEditor />
              </ProtectedRoute>
            }
          />
          <Route
            path="/university/proposals/:id"
            element={
              <ProtectedRoute roles={['university_admin', 'student', 'faculty']}>
                <ProposalEditor />
              </ProtectedRoute>
            }
          />

          <Route
            path="/industry/dashboard"
            element={
              <ProtectedRoute roles={['industry']}>
                <IndustryDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/industry/collaborations/:id"
            element={
              <ProtectedRoute roles={['industry']}>
                <CollaborationWorkspace />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin"
            element={
              <ProtectedRoute roles={['admin']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />

          <Route path="/404" element={<NotFound />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
