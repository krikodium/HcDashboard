import React from 'react';
import { NavLink } from 'react-router-dom';

const Navigation = () => {
  const modules = [
    { id: 'dashboard', name: 'Dashboard', path: '/dashboard', icon: '🏠' },
    { id: 'general-cash', name: 'General Cash', path: '/general-cash', icon: '💰' },
    { id: 'events', name: 'Events Cash', path: '/events', icon: '🎉' },
    { id: 'shop', name: 'Shop Cash', path: '/shop', icon: '🛍️' },
    { id: 'deco-movements', name: 'Deco Movements', path: '/deco-movements', icon: '🎨' },
    { id: 'cash-count', name: 'Cash Count', path: '/cash-count', icon: '📊' },
  ];

  return (
    <nav className="theme-surface border-r theme-border min-h-screen w-64">
      <div className="p-4">
        <h3 className="text-lg font-semibold theme-text mb-4">Modules</h3>
        <ul className="space-y-2">
          {modules.map((module) => (
            <li key={module.id}>
              <NavLink
                to={module.path}
                className={({ isActive }) =>
                  `w-full text-left px-4 py-3 rounded-lg transition-colors flex items-center space-x-3 block ${
                    isActive
                      ? 'theme-accent-bg text-white'
                      : 'hover:theme-surface theme-text hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`
                }
              >
                <span className="text-xl">{module.icon}</span>
                <span className="font-medium">{module.name}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
};

export default Navigation;