import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Dashboard = () => {
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
    <div className="p-8">
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
              { name: 'General Cash', desc: 'Daily cash entries and approvals', path: '/general-cash' },
              { name: 'Events Cash', desc: 'Event budgets and payment tracking', path: '/events' },
              { name: 'Shop Cash', desc: 'Retail sales and inventory', path: '/shop' },
              { name: 'Deco Movements', desc: 'Project ledgers and disbursements', path: '/deco-movements' },
              { name: 'Cash Count', desc: 'Reconciliation and arqueo', path: '/cash-count' },
            ].map((module, index) => (
              <div key={index} className="border theme-border rounded-lg p-4 hover:theme-surface transition-colors">
                <div className="flex items-center space-x-3 mb-2">
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

export default Dashboard;