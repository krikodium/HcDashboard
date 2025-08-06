import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line } from 'recharts';

// Loading skeleton component
const TableSkeleton = () => (
  <div className="animate-pulse">
    {[...Array(3)].map((_, i) => (
      <div key={i} className="border-b theme-border">
        <div className="grid grid-cols-6 gap-4 p-4">
          {[...Array(6)].map((_, j) => (
            <div key={j} className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
          ))}
        </div>
      </div>
    ))}
  </div>
);

// Module Selection Component
const ModuleSelector = ({ selectedModule, onModuleChange, modules }) => {
  return (
    <div className="card mb-6">
      <div className="border-b theme-border pb-4 mb-4">
        <h3 className="text-lg font-semibold theme-text">Select Module for Reconciliation</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {modules.map((module) => (
          <button
            key={module.id}
            onClick={() => onModuleChange(module)}
            className={`p-6 rounded-lg border-2 transition-all duration-200 ${
              selectedModule?.id === module.id
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-blue-300'
            }`}
          >
            <div className="flex flex-col items-center text-center">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-3 ${
                selectedModule?.id === module.id
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 theme-text'
              }`}>
                {module.icon}
              </div>
              <h4 className="font-semibold theme-text">{module.name}</h4>
              <p className="text-sm theme-text-secondary mt-1">{module.description}</p>
              {module.count > 0 && (
                <span className="mt-2 px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-xs theme-text">
                  {module.count} records
                </span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

// Cash Count Form Modal (Global)
const CashCountModal = ({ isOpen, onClose, onSubmit, loading, selectedModule, projects }) => {
  const [formData, setFormData] = useState({
    count_date: new Date().toISOString().split('T')[0],
    module_type: '',
    entity_name: '', // Project name, event name, or shop identifier
    count_type: 'Daily',
    cash_usd_counted: '',
    cash_ars_counted: '',
    profit_cash_usd: '',
    profit_cash_ars: '',
    profit_transfer_usd: '',
    profit_transfer_ars: '',
    commissions_cash_usd: '',
    commissions_cash_ars: '',
    commissions_transfer_usd: '',
    commissions_transfer_ars: '',
    honoraria_cash_usd: '',
    honoraria_cash_ars: '',
    honoraria_transfer_usd: '',
    honoraria_transfer_ars: '',
    notes: ''
  });

  // Set module type when selected module changes
  useEffect(() => {
    if (selectedModule) {
      setFormData(prev => ({
        ...prev,
        module_type: selectedModule.id
      }));
    }
  }, [selectedModule]);

  // Set default entity when projects are loaded
  useEffect(() => {
    if (projects.length > 0 && !formData.entity_name) {
      setFormData(prev => ({...prev, entity_name: projects[0].name}));
    }
  }, [projects, formData.entity_name]);

  const countTypes = ['Daily', 'Weekly', 'Monthly', 'Special', 'Audit'];

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      cash_usd_counted: parseFloat(formData.cash_usd_counted) || 0,
      cash_ars_counted: parseFloat(formData.cash_ars_counted) || 0,
      profit_cash_usd: parseFloat(formData.profit_cash_usd) || 0,
      profit_cash_ars: parseFloat(formData.profit_cash_ars) || 0,
      profit_transfer_usd: parseFloat(formData.profit_transfer_usd) || 0,
      profit_transfer_ars: parseFloat(formData.profit_transfer_ars) || 0,
      commissions_cash_usd: parseFloat(formData.commissions_cash_usd) || 0,
      commissions_cash_ars: parseFloat(formData.commissions_cash_ars) || 0,
      commissions_transfer_usd: parseFloat(formData.commissions_transfer_usd) || 0,
      commissions_transfer_ars: parseFloat(formData.commissions_transfer_ars) || 0,
      honoraria_cash_usd: parseFloat(formData.honoraria_cash_usd) || 0,
      honoraria_cash_ars: parseFloat(formData.honoraria_cash_ars) || 0,
      honoraria_transfer_usd: parseFloat(formData.honoraria_transfer_usd) || 0,
      honoraria_transfer_ars: parseFloat(formData.honoraria_transfer_ars) || 0,
    };
    onSubmit(submitData);
  };

  const resetForm = () => {
    setFormData({
      count_date: new Date().toISOString().split('T')[0],
      module_type: selectedModule?.id || '',
      entity_name: projects.length > 0 ? projects[0].name : '',
      count_type: 'Daily',
      cash_usd_counted: '',
      cash_ars_counted: '',
      profit_cash_usd: '',
      profit_cash_ars: '',
      profit_transfer_usd: '',
      profit_transfer_ars: '',
      commissions_cash_usd: '',
      commissions_cash_ars: '',
      commissions_transfer_usd: '',
      commissions_transfer_ars: '',
      honoraria_cash_usd: '',
      honoraria_cash_ars: '',
      honoraria_transfer_usd: '',
      honoraria_transfer_ars: '',
      notes: ''
    });
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="flex justify-between items-center mb-6 p-6 border-b theme-border">
          <h2 className="text-2xl font-bold theme-text">
            New Cash Count - {selectedModule?.name}
          </h2>
          <button onClick={handleClose} className="text-gray-400 hover:text-gray-600 text-2xl">
            ×
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Count Date</label>
              <input
                type="date"
                className="form-input w-full"
                value={formData.count_date}
                onChange={(e) => setFormData({...formData, count_date: e.target.value})}
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">
                {selectedModule?.id === 'deco' ? 'Project' : 
                 selectedModule?.id === 'events' ? 'Event' : 'Shop Location'}
              </label>
              <select
                className="form-input w-full"
                value={formData.entity_name}
                onChange={(e) => setFormData({...formData, entity_name: e.target.value})}
                required
              >
                <option value="">
                  Select {selectedModule?.id === 'deco' ? 'project' : 
                          selectedModule?.id === 'events' ? 'event' : 'location'}
                </option>
                {projects.map(project => (
                  <option key={project.id} value={project.name}>{project.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Count Type</label>
              <select
                className="form-input w-full"
                value={formData.count_type}
                onChange={(e) => setFormData({...formData, count_type: e.target.value})}
                required
              >
                {countTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Cash Counted Section */}
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
            <h4 className="text-lg font-medium text-blue-700 dark:text-blue-300 mb-4">Cash Counted</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Cash USD Counted</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.cash_usd_counted}
                  onChange={(e) => setFormData({...formData, cash_usd_counted: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Cash ARS Counted</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.cash_ars_counted}
                  onChange={(e) => setFormData({...formData, cash_ars_counted: e.target.value})}
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>

          {/* Profit Section */}
          <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
            <h4 className="text-lg font-medium text-green-700 dark:text-green-300 mb-4">Profit Distribution</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Profit Cash USD</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.profit_cash_usd}
                  onChange={(e) => setFormData({...formData, profit_cash_usd: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Profit Cash ARS</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.profit_cash_ars}
                  onChange={(e) => setFormData({...formData, profit_cash_ars: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Profit Transfer USD</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.profit_transfer_usd}
                  onChange={(e) => setFormData({...formData, profit_transfer_usd: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Profit Transfer ARS</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.profit_transfer_ars}
                  onChange={(e) => setFormData({...formData, profit_transfer_ars: e.target.value})}
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>

          {/* Commissions Section */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
            <h4 className="text-lg font-medium text-yellow-700 dark:text-yellow-300 mb-4">Commissions</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Commissions Cash USD</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.commissions_cash_usd}
                  onChange={(e) => setFormData({...formData, commissions_cash_usd: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Commissions Cash ARS</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.commissions_cash_ars}
                  onChange={(e) => setFormData({...formData, commissions_cash_ars: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Commissions Transfer USD</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.commissions_transfer_usd}
                  onChange={(e) => setFormData({...formData, commissions_transfer_usd: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Commissions Transfer ARS</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.commissions_transfer_ars}
                  onChange={(e) => setFormData({...formData, commissions_transfer_ars: e.target.value})}
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>

          {/* Honoraria Section */}
          <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
            <h4 className="text-lg font-medium text-purple-700 dark:text-purple-300 mb-4">Honoraria</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Honoraria Cash USD</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.honoraria_cash_usd}
                  onChange={(e) => setFormData({...formData, honoraria_cash_usd: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Honoraria Cash ARS</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.honoraria_cash_ars}
                  onChange={(e) => setFormData({...formData, honoraria_cash_ars: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Honoraria Transfer USD</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.honoraria_transfer_usd}
                  onChange={(e) => setFormData({...formData, honoraria_transfer_usd: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Honoraria Transfer ARS</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.honoraria_transfer_ars}
                  onChange={(e) => setFormData({...formData, honoraria_transfer_ars: e.target.value})}
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Notes</label>
            <textarea
              className="form-input w-full"
              rows="3"
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              placeholder="Additional reconciliation notes..."
            />
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex-1 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Cash Count'}
            </button>
            <button
              type="button"
              onClick={handleClose}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Discrepancy Analysis Component
const DiscrepancyAnalysis = ({ cashCounts, selectedModule }) => {
  const getDiscrepancyStatus = (count) => {
    const totalCounted = (count.cash_usd_counted || 0) + (count.cash_ars_counted || 0);
    const totalExpected = (count.profit_cash_usd || 0) + (count.profit_cash_ars || 0) + 
                         (count.commissions_cash_usd || 0) + (count.commissions_cash_ars || 0) +
                         (count.honoraria_cash_usd || 0) + (count.honoraria_cash_ars || 0);
    
    const difference = Math.abs(totalCounted - totalExpected);
    const percentageDiff = totalExpected > 0 ? (difference / totalExpected) * 100 : 0;
    
    if (percentageDiff <= 1) return { status: 'Match', color: 'text-green-600', severity: 'low' };
    if (percentageDiff <= 5) return { status: 'Minor Discrepancy', color: 'text-yellow-600', severity: 'medium' };
    return { status: 'Major Discrepancy', color: 'text-red-600', severity: 'high' };
  };

  const discrepancies = cashCounts.map(count => ({
    ...count,
    ...getDiscrepancyStatus(count)
  }));

  const severityStats = {
    low: discrepancies.filter(d => d.severity === 'low').length,
    medium: discrepancies.filter(d => d.severity === 'medium').length,
    high: discrepancies.filter(d => d.severity === 'high').length
  };

  return (
    <div className="space-y-6">
      {/* Discrepancy Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <h4 className="text-sm font-medium theme-text-secondary mb-2">Total Counts</h4>
          <p className="text-2xl font-bold theme-text">{cashCounts.length}</p>
        </div>
        
        <div className="card">
          <h4 className="text-sm font-medium theme-text-secondary mb-2">Matches</h4>
          <p className="text-2xl font-bold text-green-600">{severityStats.low}</p>
        </div>
        
        <div className="card">
          <h4 className="text-sm font-medium theme-text-secondary mb-2">Minor Issues</h4>
          <p className="text-2xl font-bold text-yellow-600">{severityStats.medium}</p>
        </div>
        
        <div className="card">
          <h4 className="text-sm font-medium theme-text-secondary mb-2">Major Issues</h4>
          <p className="text-2xl font-bold text-red-600">{severityStats.high}</p>
        </div>
      </div>

      {/* Discrepancy Chart */}
      {cashCounts.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold theme-text mb-4">Reconciliation Accuracy Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={discrepancies.slice(-10)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="count_date" 
                tickFormatter={(date) => format(new Date(date), 'dd/MM')}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(date) => format(new Date(date), 'dd/MM/yyyy')}
                formatter={(value, name) => [
                  name === 'accuracy' ? `${value.toFixed(1)}%` : value.toFixed(2),
                  name === 'accuracy' ? 'Accuracy' : 'Discrepancy Amount'
                ]}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey={(data) => {
                  const totalCounted = (data.cash_usd_counted || 0) + (data.cash_ars_counted || 0);
                  const totalExpected = (data.profit_cash_usd || 0) + (data.profit_cash_ars || 0) + 
                                       (data.commissions_cash_usd || 0) + (data.commissions_cash_ars || 0) +
                                       (data.honoraria_cash_usd || 0) + (data.honoraria_cash_ars || 0);
                  return totalExpected > 0 ? ((totalExpected - Math.abs(totalCounted - totalExpected)) / totalExpected) * 100 : 100;
                }}
                stroke="#10b981" 
                name="accuracy"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

// Main Cash Count Component (Global)
const CashCount = () => {
  const [cashCounts, setCashCounts] = useState([]);
  const [projects, setProjects] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  // Available modules for reconciliation
  const modules = [
    {
      id: 'deco',
      name: 'Deco Projects',
      description: 'Reconcile deco project finances',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM21 5a2 2 0 00-2-2h-4a2 2 0 00-2 2v12a4 4 0 004 4 4 4 0 004-4V5z" />
        </svg>
      ),
      count: 0
    },
    {
      id: 'events',
      name: 'Events Cash',
      description: 'Reconcile event finances and payments',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
      count: 0
    },
    {
      id: 'shop',
      name: 'Shop Cash',
      description: 'Reconcile shop sales and inventory',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
        </svg>
      ),
      count: 0
    }
  ];

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedModule) {
      fetchModuleProjects();
    }
  }, [selectedModule, fetchModuleProjects]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/deco-cash-count');
      setCashCounts(response.data);
      setError('');
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchModuleProjects = async () => {
    if (!selectedModule) return;

    try {
      let endpoint = '/api/projects';
      if (selectedModule.id === 'deco') {
        endpoint += '?project_type=Deco';
      } else if (selectedModule.id === 'events') {
        endpoint += '?project_type=Event';
      } else if (selectedModule.id === 'shop') {
        endpoint = '/api/providers'; // For shop, we might use providers or locations
      }
      
      const response = await axios.get(endpoint);
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching module projects:', error);
      setProjects([]);
    }
  };

  const handleCreateCashCount = async (formData) => {
    try {
      setIsSubmitting(true);
      await axios.post('/api/deco-cash-count', formData);
      setIsModalOpen(false);
      await fetchData();
    } catch (error) {
      console.error('Error creating cash count:', error);
      setError('Failed to create cash count. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleModuleChange = (module) => {
    setSelectedModule(module);
    setActiveTab('overview');
  };

  const filteredCashCounts = selectedModule
    ? cashCounts.filter(count => count.module_type === selectedModule.id)
    : cashCounts;

  const tabs = [
    { id: 'overview', name: 'Overview' },
    { id: 'records', name: 'Records' },
    { id: 'discrepancies', name: 'Discrepancies' },
    { id: 'analytics', name: 'Analytics' }
  ];

  if (loading) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-8"></div>
            <TableSkeleton />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold theme-text">Cash Count (Arqueo)</h1>
            <p className="theme-text-secondary">Global financial reconciliation system</p>
          </div>
          {selectedModule && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="btn-primary"
            >
              New Cash Count
            </button>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Module Selection */}
        <ModuleSelector 
          selectedModule={selectedModule}
          onModuleChange={handleModuleChange}
          modules={modules.map(module => ({
            ...module,
            count: cashCounts.filter(count => count.module_type === module.id).length
          }))}
        />

        {selectedModule && (
          <>
            {/* Tabs */}
            <div className="mb-6">
              <div className="border-b theme-border">
                <nav className="-mb-px flex space-x-8">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                        activeTab === tab.id
                          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                          : 'border-transparent theme-text-secondary hover:theme-text hover:border-gray-300'
                      }`}
                    >
                      {tab.name}
                    </button>
                  ))}
                </nav>
              </div>
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="card">
                    <h3 className="text-sm font-medium theme-text-secondary">Total Counts</h3>
                    <p className="text-2xl font-bold theme-text">{filteredCashCounts.length}</p>
                  </div>
                  
                  <div className="card">
                    <h3 className="text-sm font-medium theme-text-secondary">This Month</h3>
                    <p className="text-2xl font-bold text-blue-600">
                      {filteredCashCounts.filter(count => {
                        const countDate = new Date(count.count_date);
                        const now = new Date();
                        return countDate.getMonth() === now.getMonth() && countDate.getFullYear() === now.getFullYear();
                      }).length}
                    </p>
                  </div>
                  
                  <div className="card">
                    <h3 className="text-sm font-medium theme-text-secondary">Total Cash USD</h3>
                    <p className="text-2xl font-bold text-green-600">
                      ${filteredCashCounts.reduce((sum, count) => sum + (count.cash_usd_counted || 0), 0).toFixed(2)}
                    </p>
                  </div>
                  
                  <div className="card">
                    <h3 className="text-sm font-medium theme-text-secondary">Total Cash ARS</h3>
                    <p className="text-2xl font-bold text-green-600">
                      AR$ {filteredCashCounts.reduce((sum, count) => sum + (count.cash_ars_counted || 0), 0).toFixed(2)}
                    </p>
                  </div>
                </div>

                {/* Recent Cash Counts */}
                {filteredCashCounts.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-semibold theme-text mb-4">Recent Cash Counts</h3>
                    <div className="space-y-3">
                      {filteredCashCounts.slice(0, 5).map((count) => (
                        <div key={count.id} className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <div>
                            <p className="font-medium theme-text">{count.entity_name}</p>
                            <p className="text-sm theme-text-secondary">
                              {format(new Date(count.count_date), 'dd/MM/yyyy')} - {count.count_type}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="font-medium theme-text">
                              ${(count.cash_usd_counted || 0).toFixed(2)} USD
                            </p>
                            <p className="text-sm theme-text-secondary">
                              AR$ {(count.cash_ars_counted || 0).toFixed(2)}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'records' && (
              <div className="card">
                <div className="table-container">
                  <table className="min-w-full">
                    <thead className="table-header">
                      <tr>
                        <th className="table-header-cell">Date</th>
                        <th className="table-header-cell">Entity</th>
                        <th className="table-header-cell">Type</th>
                        <th className="table-header-cell">Cash USD</th>
                        <th className="table-header-cell">Cash ARS</th>
                        <th className="table-header-cell">Total Profit</th>
                        <th className="table-header-cell">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredCashCounts.map((count) => {
                        const totalCounted = (count.cash_usd_counted || 0) + (count.cash_ars_counted || 0);
                        const totalExpected = (count.profit_cash_usd || 0) + (count.profit_cash_ars || 0) + 
                                             (count.commissions_cash_usd || 0) + (count.commissions_cash_ars || 0) +
                                             (count.honoraria_cash_usd || 0) + (count.honoraria_cash_ars || 0);
                        const difference = Math.abs(totalCounted - totalExpected);
                        const isMatch = difference <= (totalExpected * 0.01); // 1% tolerance
                        
                        return (
                          <tr key={count.id} className="table-row">
                            <td className="table-cell font-medium">
                              {format(new Date(count.count_date), 'dd/MM/yyyy')}
                            </td>
                            <td className="table-cell">
                              <div>
                                <p className="font-medium theme-text">{count.entity_name}</p>
                                <p className="text-sm theme-text-secondary">{selectedModule.name}</p>
                              </div>
                            </td>
                            <td className="table-cell">
                              <span className="status-badge status-info">{count.count_type}</span>
                            </td>
                            <td className="table-cell font-medium text-green-600">
                              ${(count.cash_usd_counted || 0).toFixed(2)}
                            </td>
                            <td className="table-cell font-medium text-green-600">
                              AR$ {(count.cash_ars_counted || 0).toFixed(2)}
                            </td>
                            <td className="table-cell">
                              <div className="text-sm">
                                <p>${((count.profit_cash_usd || 0) + (count.profit_transfer_usd || 0)).toFixed(2)} USD</p>
                                <p>AR$ {((count.profit_cash_ars || 0) + (count.profit_transfer_ars || 0)).toFixed(2)}</p>
                              </div>
                            </td>
                            <td className="table-cell">
                              <span className={`font-semibold ${isMatch ? 'text-green-600' : 'text-red-600'}`}>
                                {isMatch ? 'Match' : 'Discrepancy'}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  
                  {filteredCashCounts.length === 0 && (
                    <div className="text-center py-12">
                      <p className="theme-text-secondary">No cash count records found for {selectedModule.name}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'discrepancies' && (
              <DiscrepancyAnalysis 
                cashCounts={filteredCashCounts} 
                selectedModule={selectedModule}
              />
            )}

            {activeTab === 'analytics' && (
              <div className="space-y-6">
                {filteredCashCounts.length > 0 ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Monthly Trend */}
                    <div className="card">
                      <h3 className="text-lg font-semibold theme-text mb-4">Monthly Cash Count Trend</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={filteredCashCounts.reduce((acc, count) => {
                          const month = format(new Date(count.count_date), 'MMM yyyy');
                          const existing = acc.find(item => item.month === month);
                          if (existing) {
                            existing.total_usd += (count.cash_usd_counted || 0);
                            existing.total_ars += (count.cash_ars_counted || 0);
                            existing.count += 1;
                          } else {
                            acc.push({
                              month,
                              total_usd: count.cash_usd_counted || 0,
                              total_ars: count.cash_ars_counted || 0,
                              count: 1
                            });
                          }
                          return acc;
                        }, [])}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="month" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="total_usd" fill="#3b82f6" name="USD" />
                          <Bar dataKey="total_ars" fill="#10b981" name="ARS" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Count Types Distribution */}
                    <div className="card">
                      <h3 className="text-lg font-semibold theme-text mb-4">Count Types Distribution</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={filteredCashCounts.reduce((acc, count) => {
                              const existing = acc.find(item => item.name === count.count_type);
                              if (existing) {
                                existing.value += 1;
                              } else {
                                acc.push({ name: count.count_type, value: 1 });
                              }
                              return acc;
                            }, [])}
                            cx="50%"
                            cy="50%"
                            outerRadius={100}
                            dataKey="value"
                            label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                          >
                            {['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'].map((color, index) => (
                              <Cell key={`cell-${index}`} fill={color} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="theme-text-secondary">No data available for analytics</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Cash Count Modal */}
        <CashCountModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSubmit={handleCreateCashCount}
          loading={isSubmitting}
          selectedModule={selectedModule}
          projects={projects}
        />
      </div>
    </div>
  );
};

export default CashCount;