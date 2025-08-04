import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import './App.css';

// Theme Context
const ThemeContext = createContext();
const AuthContext = createContext();

// Custom hooks
const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// API configuration
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
axios.defaults.baseURL = API_BASE_URL;

// Set default authorization header
const setAuthToken = (token) => {
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    localStorage.setItem('token', token);
  } else {
    delete axios.defaults.headers.common['Authorization'];
    localStorage.removeItem('token');
  }
};

// Theme Provider Component
const ThemeProvider = ({ children }) => {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    localStorage.setItem('theme', JSON.stringify(isDark));
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  const toggleTheme = () => setIsDark(!isDark);

  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Auth Provider Component
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setAuthToken(token);
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get('/api/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials) => {
    try {
      const response = await axios.post('/api/auth/login', credentials);
      const { access_token, user: userData } = response.data;
      
      setAuthToken(access_token);
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const logout = () => {
    setAuthToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component
const LoginForm = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const { isDark, toggleTheme } = useTheme();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const result = await login(credentials);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center theme-surface">
      <div className="absolute top-4 right-4">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg theme-border border-2 theme-text hover:theme-accent-bg hover:text-white transition-colors"
          title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          {isDark ? '☀️' : '🌙'}
        </button>
      </div>
      
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold theme-text mb-2">🏢</h1>
          <h2 className="text-3xl font-bold theme-text">Hermanas Caradonti</h2>
          <p className="mt-2 theme-text-secondary">Admin Dashboard</p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium theme-text mb-2">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                className="form-input w-full text-lg"
                placeholder="Enter your username"
                value={credentials.username}
                onChange={(e) => setCredentials({...credentials, username: e.target.value})}
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium theme-text mb-2">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="form-input w-full text-lg"
                placeholder="Enter your password"
                value={credentials.password}
                onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              />
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full text-lg py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
          
          <div className="text-center mt-4">
            <p className="text-sm theme-text-secondary">
              Test credentials: <strong>mateo</strong> / <strong>prueba123</strong>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

// Header Component
const Header = () => {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();

  return (
    <header className="theme-surface border-b theme-border shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🏢</span>
            <div>
              <h1 className="text-xl font-bold theme-text">Hermanas Caradonti</h1>
              <p className="text-sm theme-text-secondary">Admin Dashboard</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg theme-border border hover:theme-accent-bg hover:text-white transition-colors"
              title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {isDark ? '☀️' : '🌙'}
            </button>
            
            <div className="flex items-center space-x-3">
              <div className="text-right">
                <p className="text-sm font-medium theme-text">{user?.username}</p>
                <p className="text-xs theme-text-secondary">
                  {user?.roles?.includes('super-admin') ? 'Super Admin' : 
                   user?.roles?.includes('area-admin') ? 'Area Admin' : 'Employee'}
                </p>
              </div>
              
              <button
                onClick={logout}
                className="btn-secondary px-3 py-1 text-sm"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

// Navigation Component
const Navigation = () => {
  const [activeModule, setActiveModule] = useState('general-cash');
  
  const modules = [
    { id: 'general-cash', name: 'General Cash', icon: '💰' },
    { id: 'events-cash', name: 'Events Cash', icon: '🎉' },
    { id: 'shop-cash', name: 'Shop Cash', icon: '🛍️' },
    { id: 'deco-movements', name: 'Deco Movements', icon: '🎨' },
    { id: 'deco-cash-count', name: 'Cash Count', icon: '📊' },
  ];

  return (
    <nav className="theme-surface border-r theme-border min-h-screen w-64">
      <div className="p-4">
        <h3 className="text-lg font-semibold theme-text mb-4">Modules</h3>
        <ul className="space-y-2">
          {modules.map((module) => (
            <li key={module.id}>
              <button
                onClick={() => setActiveModule(module.id)}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors flex items-center space-x-3 ${
                  activeModule === module.id
                    ? 'theme-accent-bg text-white'
                    : 'hover:theme-surface theme-text'
                }`}
              >
                <span className="text-xl">{module.icon}</span>
                <span className="font-medium">{module.name}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
};

// Dashboard Content Component
const DashboardContent = () => {
  const [backendStatus, setBackendStatus] = useState('checking...');

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await axios.get('/api/test');
        setBackendStatus('✅ Connected');
      } catch (error) {
        setBackendStatus('❌ Disconnected');
      }
    };
    
    checkBackend();
  }, []);

  return (
    <div className="flex-1 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h2 className="text-3xl font-bold theme-text mb-2">Welcome to Admin Dashboard</h2>
          <p className="theme-text-secondary">Manage your events, décor, and shop operations</p>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card">
            <h3 className="text-lg font-semibold theme-text mb-2">System Status</h3>
            <p className="theme-text-secondary">Backend: {backendStatus}</p>
          </div>
          
          <div className="card">
            <h3 className="text-lg font-semibold theme-text mb-2">Quick Stats</h3>
            <p className="theme-text-secondary">5 Modules Available</p>
          </div>
          
          <div className="card">
            <h3 className="text-lg font-semibold theme-text mb-2">Recent Activity</h3>
            <p className="theme-text-secondary">Dashboard initialized</p>
          </div>
        </div>

        {/* Module Preview */}
        <div className="card">
          <h3 className="text-xl font-semibold theme-text mb-4">Available Modules</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { name: 'General Cash', desc: 'Daily cash entries and approvals', icon: '💰' },
              { name: 'Events Cash', desc: 'Event budgets and payment tracking', icon: '🎉' },
              { name: 'Shop Cash', desc: 'Retail sales and inventory', icon: '🛍️' },
              { name: 'Deco Movements', desc: 'Project ledgers and disbursements', icon: '🎨' },
              { name: 'Cash Count', desc: 'Reconciliation and arqueo', icon: '📊' },
            ].map((module, index) => (
              <div key={index} className="border theme-border rounded-lg p-4 hover:theme-surface transition-colors">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-2xl">{module.icon}</span>
                  <h4 className="font-semibold theme-text">{module.name}</h4>
                </div>
                <p className="text-sm theme-text-secondary">{module.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  return (
    <div className="min-h-screen theme-background">
      <Header />
      <div className="flex">
        <Navigation />
        <DashboardContent />
      </div>
    </div>
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

const AppContent = () => {
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

  return user ? <Dashboard /> : <LoginForm />;
};

export default App;