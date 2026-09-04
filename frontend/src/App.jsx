import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import { PageLoader } from './components/ui';

// Route-level code splitting: each page loads on demand instead of
// bloating the initial bundle (see vite.config.js manualChunks).
const Landing = lazy(() => import('./pages/Landing'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const CitizenDashboard = lazy(() => import('./pages/CitizenDashboard'));
const SubmitProblem = lazy(() => import('./pages/SubmitProblem'));
const ProblemTrack = lazy(() => import('./pages/ProblemTrack'));
const ProblemsList = lazy(() => import('./pages/ProblemsList'));
const Notifications = lazy(() => import('./pages/Notifications'));
const MapView = lazy(() => import('./pages/MapView'));
const GovernmentDashboard = lazy(() => import('./pages/GovernmentDashboard'));
const GovAnalytics = lazy(() => import('./pages/GovAnalytics'));
const ImpactReports = lazy(() => import('./pages/ImpactReports'));
const PublicMap = lazy(() => import('./pages/PublicMap'));
const UniversityDashboard = lazy(() => import('./pages/UniversityDashboard'));
const TeamWorkspace = lazy(() => import('./pages/TeamWorkspace'));
const TeamCreate = lazy(() => import('./pages/TeamCreate'));
const ProposalEditor = lazy(() => import('./pages/ProposalEditor'));
const IndustryDashboard = lazy(() => import('./pages/IndustryDashboard'));
const CollaborationWorkspace = lazy(() => import('./pages/CollaborationWorkspace'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const ProfileSettings = lazy(() => import('./pages/ProfileSettings'));
const SolutionDetail = lazy(() => import('./pages/SolutionDetail'));
const NotFound = lazy(() => import('./pages/NotFound'));

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
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
            path="/problems/:problemId/solutions/:solutionId"
            element={
              <ProtectedRoute>
                <SolutionDetail />
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
          <Route path="/problems/map" element={<PublicMap />} />
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
            path="/gov/analytics"
            element={
              <ProtectedRoute roles={['government']}>
                <GovAnalytics />
              </ProtectedRoute>
            }
          />
          <Route
            path="/gov/impact-reports"
            element={
              <ProtectedRoute roles={['government']}>
                <ImpactReports />
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

          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <ProfileSettings />
              </ProtectedRoute>
            }
          />

          <Route path="/404" element={<NotFound />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
