import React from 'react';
import { NavLink } from 'react-router-dom';

const Navigation = () => {
  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/general-cash', label: 'General Cash', icon: '💰' },
    { path: '/events-cash', label: 'Events Cash', icon: '🎉' },
    { path: '/shop-cash', label: 'Shop Cash', icon: '🛒' },
    { path: '/deco-movements', label: 'Deco Movements', icon: '🎨' },
    { path: '/cash-count', label: 'Cash Count', icon: '🧮' }
  ];

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-sm w-64 min-h-screen">
      <div className="p-6">
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Navigation Menu
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Financial Management Modules
          </p>
        </div>
        
        <div className="space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 border-l-4 border-teal-500'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
                }`
              }
            >
              <span className="text-lg">{item.icon}</span>
              <span className="font-medium">{item.label}</span>
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;