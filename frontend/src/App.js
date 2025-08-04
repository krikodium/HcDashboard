import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import GeneralCash from './pages/GeneralCash';
import EventsCash from './pages/EventsCash';
import ShopCash from './pages/ShopCash';
import DecoMovements from './pages/DecoMovements';
import CashCount from './pages/CashCount';
import LoginForm from './components/LoginForm';
import { useAuth } from './contexts/AuthContext';
import './App.css';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center theme-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-theme-accent mx-auto mb-4"></div>
          <p className="theme-text-secondary">Loading...</p>
        </div>
      </div>
    );
  }

  return user ? children : <LoginForm />;
};

// App Content with Router
const AppContent = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginForm />} />
        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="general-cash" element={<GeneralCash />} />
          <Route path="events" element={<EventsCash />} />
          <Route path="shop" element={<ShopCash />} />
          <Route path="deco-movements" element={<DecoMovements />} />
          <Route path="cash-count" element={<CashCount />} />
        </Route>
      </Routes>
    </Router>
  );
};

// Main App Component
const App = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;