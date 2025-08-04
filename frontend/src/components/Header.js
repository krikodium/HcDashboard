import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

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

export default Header;