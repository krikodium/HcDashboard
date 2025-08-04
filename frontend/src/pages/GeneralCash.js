import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Loading skeleton component
const TableSkeleton = () => (
  <div className="animate-pulse">
    {[...Array(5)].map((_, i) => (
      <div key={i} className="border-b theme-border">
        <div className="grid grid-cols-8 gap-4 p-4">
          {[...Array(8)].map((_, j) => (
            <div key={j} className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
          ))}
        </div>
      </div>
    ))}
  </div>
);

// Entry form modal
const EntryFormModal = ({ isOpen, onClose, onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    description: '',
    application: 'Gastos Generales',
    provider: '',
    income_ars: '',
    income_usd: '',
    expense_ars: '',
    expense_usd: ''
  });

  const applications = [
    'Aportes Socias',
    'Sueldos Admin.',
    'Venta USD',
    'Gastos Generales',
    'Viáticos',
    'Honorarios',
    'Impuestos',
    'Otros'
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      income_ars: formData.income_ars ? parseFloat(formData.income_ars) : null,
      income_usd: formData.income_usd ? parseFloat(formData.income_usd) : null,
      expense_ars: formData.expense_ars ? parseFloat(formData.expense_ars) : null,
      expense_usd: formData.expense_usd ? parseFloat(formData.expense_usd) : null,
    };
    onSubmit(submitData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="card max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold theme-text">New General Cash Entry</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Date</label>
              <input
                type="date"
                className="form-input w-full"
                value={formData.date}
                onChange={(e) => setFormData({...formData, date: e.target.value})}
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Application</label>
              <select
                className="form-input w-full"
                value={formData.application}
                onChange={(e) => setFormData({...formData, application: e.target.value})}
                required
              >
                {applications.map(app => (
                  <option key={app} value={app}>{app}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Description</label>
            <input
              type="text"
              className="form-input w-full"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Enter description"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Provider</label>
            <input
              type="text"
              className="form-input w-full"
              value={formData.provider}
              onChange={(e) => setFormData({...formData, provider: e.target.value})}
              placeholder="Enter provider name"
              required
            />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Income ARS</label>
              <input
                type="number"
                step="0.01"
                className="form-input w-full"
                value={formData.income_ars}
                onChange={(e) => setFormData({...formData, income_ars: e.target.value})}
                placeholder="0.00"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Income USD</label>
              <input
                type="number"
                step="0.01"
                className="form-input w-full"
                value={formData.income_usd}
                onChange={(e) => setFormData({...formData, income_usd: e.target.value})}
                placeholder="0.00"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Expense ARS</label>
              <input
                type="number"
                step="0.01"
                className="form-input w-full"
                value={formData.expense_ars}
                onChange={(e) => setFormData({...formData, expense_ars: e.target.value})}
                placeholder="0.00"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Expense USD</label>
              <input
                type="number"
                step="0.01"
                className="form-input w-full"
                value={formData.expense_usd}
                onChange={(e) => setFormData({...formData, expense_usd: e.target.value})}
                placeholder="0.00"
              />
            </div>
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex-1 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Entry'}
            </button>
            <button
              type="button"
              onClick={onClose}
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

const GeneralCash = () => {
  const [entries, setEntries] = useState([]);
  const [summary, setSummary] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [entriesResponse, summaryResponse] = await Promise.all([
        axios.get('/api/general-cash'),
        axios.get('/api/general-cash/summary')
      ]);
      
      setEntries(entriesResponse.data);
      setSummary(summaryResponse.data);
      
      // Process data for chart
      const monthlyData = processMonthlyData(entriesResponse.data);
      setChartData(monthlyData);
      
      setError('');
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Process entries for monthly income vs expense chart
  const processMonthlyData = (entries) => {
    const monthlyMap = {};
    
    entries.forEach(entry => {
      const date = new Date(entry.date);
      const monthKey = format(date, 'MMM yyyy');
      
      if (!monthlyMap[monthKey]) {
        monthlyMap[monthKey] = {
          month: monthKey,
          income: 0,
          expense: 0,
        };
      }
      
      monthlyMap[monthKey].income += entry.income_ars || 0;
      monthlyMap[monthKey].expense += entry.expense_ars || 0;
    });
    
    // Convert to array and sort by date
    return Object.values(monthlyMap).sort((a, b) => {
      return new Date(a.month) - new Date(b.month);
    });
  };

  const handleCreateEntry = async (formData) => {
    try {
      setIsSubmitting(true);
      await axios.post('/api/general-cash', formData);
      setIsModalOpen(false);
      await fetchData(); // Refresh data including chart
    } catch (error) {
      console.error('Error creating entry:', error);
      setError('Failed to create entry. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApproval = async (entryId, approvalType) => {
    try {
      await axios.post(`/api/general-cash/${entryId}/approve?approval_type=${approvalType}`);
      await fetchData(); // Refresh data
    } catch (error) {
      console.error('Error approving entry:', error);
      setError('Failed to approve entry. Please try again.');
    }
  };

  const formatCurrency = (amount, currency) => {
    if (!amount) return '-';
    return `${currency} ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  };

  const getStatusBadge = (status) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    switch (status) {
      case 'Pending':
        return `${baseClasses} bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200`;
      case 'Approved by Fede':
        return `${baseClasses} bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200`;
      case 'Approved by Sisters':
        return `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200`;
    }
  };

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold theme-text">General Cash</h1>
            <p className="theme-text-secondary">Daily cash entries and approvals</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="btn-primary"
          >
            Add New Entry
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Total Entries</h3>
              <p className="text-2xl font-bold theme-text">{summary.total_entries}</p>
            </div>
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Pending Approvals</h3>
              <p className="text-2xl font-bold text-yellow-600">{summary.pending_approvals}</p>
            </div>
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Net Balance ARS</h3>
              <p className={`text-2xl font-bold ${summary.net_balance_ars >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(summary.net_balance_ars, 'ARS')}
              </p>
            </div>
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Net Balance USD</h3>
              <p className={`text-2xl font-bold ${summary.net_balance_usd >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(summary.net_balance_usd, 'USD')}
              </p>
            </div>
          </div>
        )}

        {/* Monthly Income vs Expense Chart */}
        {chartData.length > 0 && (
          <div className="card mb-8">
            <div className="border-b theme-border pb-4 mb-6">
              <h2 className="text-xl font-semibold theme-text">Monthly Income vs Expense (ARS)</h2>
              <p className="text-sm theme-text-secondary">Track monthly financial performance</p>
            </div>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="month" 
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    axisLine={{ stroke: '#d1d5db' }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    axisLine={{ stroke: '#d1d5db' }}
                    tickFormatter={(value) => `${value.toLocaleString()}`}
                  />
                  <Tooltip 
                    formatter={(value, name) => [
                      `ARS ${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
                      name === 'income' ? 'Income' : 'Expense'
                    ]}
                    labelStyle={{ color: '#374151' }}
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '0.5rem'
                    }}
                  />
                  <Legend />
                  <Bar 
                    dataKey="income" 
                    name="Income"
                    fill="#10b981" 
                    radius={[4, 4, 0, 0]}
                  />
                  <Bar 
                    dataKey="expense" 
                    name="Expense"
                    fill="#ef4444" 
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Entries Table */}
        <div className="card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="table-header">
                  <th className="text-left p-4 font-medium theme-text">Date</th>
                  <th className="text-left p-4 font-medium theme-text">Description</th>
                  <th className="text-left p-4 font-medium theme-text">Application</th>
                  <th className="text-left p-4 font-medium theme-text">Provider</th>
                  <th className="text-right p-4 font-medium theme-text">Income ARS</th>
                  <th className="text-right p-4 font-medium theme-text">Expense ARS</th>
                  <th className="text-center p-4 font-medium theme-text">Status</th>
                  <th className="text-center p-4 font-medium theme-text">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="8" className="p-0">
                      <TableSkeleton />
                    </td>
                  </tr>
                ) : entries.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="text-center py-12 theme-text-secondary">
                      No entries found. Create your first entry to get started.
                    </td>
                  </tr>
                ) : (
                  entries.map((entry) => (
                    <tr key={entry._id} className="table-row">
                      <td className="p-4 theme-text">
                        {format(new Date(entry.date), 'dd/MM/yyyy')}
                      </td>
                      <td className="p-4 theme-text">{entry.description}</td>
                      <td className="p-4 theme-text">{entry.application}</td>
                      <td className="p-4 theme-text">{entry.provider}</td>
                      <td className="p-4 theme-text text-right table-cell-numeric">
                        {formatCurrency(entry.income_ars, 'ARS')}
                      </td>
                      <td className="p-4 theme-text text-right table-cell-numeric">
                        {formatCurrency(entry.expense_ars, 'ARS')}
                      </td>
                      <td className="p-4 text-center">
                        <span className={getStatusBadge(entry.approval_status)}>
                          {entry.approval_status}
                        </span>
                      </td>
                      <td className="p-4 text-center">
                        {entry.approval_status === 'Pending' && (
                          <div className="flex space-x-2 justify-center">
                            <button
                              onClick={() => handleApproval(entry._id, 'fede')}
                              className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-xs hover:bg-blue-200"
                            >
                              Approve (Fede)
                            </button>
                            <button
                              onClick={() => handleApproval(entry._id, 'sisters')}
                              className="px-3 py-1 bg-green-100 text-green-800 rounded text-xs hover:bg-green-200"
                            >
                              Approve (Sisters)
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Entry Form Modal */}
        <EntryFormModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSubmit={handleCreateEntry}
          loading={isSubmitting}
        />
      </div>
    </div>
  );
};

export default GeneralCash;