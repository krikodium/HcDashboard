import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z' },
    { path: '/general-cash', label: 'General Cash', icon: 'M12 2C13.1 2 14 2.9 14 4V5H20C20.6 5 21 5.4 21 6S20.6 7 20 7H14V8C14 9.1 13.1 10 12 10S10 9.1 10 8V7H4C3.4 7 3 6.6 3 6S3.4 5 4 5H10V4C10 2.9 10.9 2 12 2Z' },
    { path: '/events-cash', label: 'Events Cash', icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
    { path: '/shop-cash', label: 'Shop Cash', icon: 'M16 11V7a4 4 0 00-8 0v4M5 9h14a2 2 0 012 2v7a2 2 0 01-2 2H5a2 2 0 01-2-2v-7a2 2 0 012-2z' },
    { path: '/deco-movements', label: 'Deco Movements', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
    { path: '/cash-count', label: 'Cash Count', icon: 'M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z' }
  ];

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-sm border-r border-gray-200 dark:border-gray-700 w-64 min-h-screen">
      <div className="p-6">
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Navigation
          </h2>
        </div>
        
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.path}>
              <Link
                to={item.path}
                className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                    : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <svg
                  className="w-5 h-5 mr-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
                </svg>
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
};

export default Navigation;