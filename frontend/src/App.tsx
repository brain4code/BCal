import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext.tsx';
import Login from './pages/Login.tsx';

import Dashboard from './pages/Dashboard.tsx';
import AdminDashboard from './pages/AdminDashboard.tsx';
import BookingPage from './pages/BookingPage.tsx';
import TeamBookingPage from './pages/TeamBookingPage.tsx';
import TeamSelectionPage from './pages/TeamSelectionPage.tsx';
import LandingPage from './pages/LandingPage.tsx';
import Calendar from './pages/Calendar.tsx';
import DebugPage from './pages/DebugPage.tsx';
import Layout from './components/Layout.tsx';
import './index.css';

const PrivateRoute: React.FC<{ children: React.ReactNode; adminOnly?: boolean }> = ({ 
  children, 
  adminOnly = false 
}) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  if (adminOnly && !isAdmin) {
    return <Navigate to="/dashboard" />;
  }

  return <>{children}</>;
};

const AppRoutes: React.FC = () => {
  const { isAuthenticated, isAdmin } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={
        isAuthenticated ? <Navigate to="/dashboard" /> : <Login />
      } />

      <Route path="/dashboard" element={
        <PrivateRoute>
          <Layout>
            <Dashboard />
          </Layout>
        </PrivateRoute>
      } />
      <Route path="/admin" element={
        <PrivateRoute adminOnly>
          <Layout>
            <AdminDashboard />
          </Layout>
        </PrivateRoute>
      } />
      <Route path="/calendar" element={
        <PrivateRoute>
          <Layout>
            <Calendar />
          </Layout>
        </PrivateRoute>
      } />
      <Route path="/book/:userId" element={<BookingPage />} />
              <Route path="/teams" element={<TeamSelectionPage />} />
        <Route path="/team/:teamId" element={<TeamBookingPage />} />
        <Route path="/landing" element={<LandingPage />} />
        <Route path="/debug" element={<DebugPage />} />
        <Route path="/" element={
          isAuthenticated ? <Navigate to="/dashboard" /> : <Navigate to="/landing" />
        } />
    </Routes>
  );
};

const App: React.FC = () => {
  console.log('=== APP COMPONENT LOADED ===');
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <AppRoutes />
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;
