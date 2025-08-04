import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';

// Loading skeleton component
const TableSkeleton = () => (
  <div className="animate-pulse">
    {[...Array(5)].map((_, i) => (
      <div key={i} className="border-b theme-border">
        <div className="grid grid-cols-9 gap-4 p-4">
          {[...Array(9)].map((_, j) => (
            <div key={j} className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
          ))}
        </div>
      </div>
    ))}
  </div>
);

// Cash Count Form Modal
const CashCountModal = ({ isOpen, onClose, onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    count_date: new Date().toISOString().split('T')[0],
    deco_name: 'Pájaro',
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

  const projects = [
    'Pájaro', 'Alvear', 'Bahía Bustamante', 'Hotel Madero', 
    'Palacio Duhau', 'Four Seasons', 'Alvear Palace', 'Other'
  ];

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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="card max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold theme-text">New Cash Count (Arqueo)</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
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
              <label className="block text-sm font-medium theme-text mb-2">Deco Project</label>
              <select
                className="form-input w-full"
                value={formData.deco_name}
                onChange={(e) => setFormData({...formData, deco_name: e.target.value})}
                required
              >
                {projects.map(project => (
                  <option key={project} value={project}>{project}</option>
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

          {/* Cash Counted */}
          <div className="border theme-border rounded-lg p-4">
            <h3 className="text-lg font-medium theme-text mb-4">Cash Counted</h3>
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

          {/* Profit Breakdown */}
          <div className="border theme-border rounded-lg p-4">
            <h3 className="text-lg font-medium theme-text mb-4">Profit Breakdown</h3>
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

          {/* Commissions Breakdown */}
          <div className="border theme-border rounded-lg p-4">
            <h3 className="text-lg font-medium theme-text mb-4">Commissions Breakdown</h3>
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

          {/* Honoraria Breakdown */}
          <div className="border theme-border rounded-lg p-4">
            <h3 className="text-lg font-medium theme-text mb-4">Honoraria Breakdown</h3>
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

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium theme-text mb-2">Notes</label>
            <textarea
              className="form-input w-full"
              rows="3"
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              placeholder="Additional notes about the cash count"
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

// Main Cash Count Component
const CashCount = () => {
  const [cashCounts, setCashCounts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [discrepancyData, setDiscrepancyData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDeco, setSelectedDeco] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/deco-cash-count');
      setCashCounts(response.data);
      
      // Process data for charts
      const monthlyData = processMonthlyDiscrepancyData(response.data);
      const discrepancyByDeco = processDiscrepancyByDeco(response.data);
      
      setChartData(monthlyData);
      setDiscrepancyData(discrepancyByDeco);
      
      // Calculate summary
      const calculatedSummary = calculateSummary(response.data);
      setSummary(calculatedSummary);
      
      setError('');
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const processMonthlyDiscrepancyData = (counts) => {
    const monthlyMap = {};
    
    counts.forEach(count => {
      const date = new Date(count.count_date);
      const monthKey = format(date, 'MMM yyyy');
      
      if (!monthlyMap[monthKey]) {
        monthlyMap[monthKey] = {
          month: monthKey,
          total_counts: 0,
          discrepancy_counts: 0,
          accuracy_rate: 0
        };
      }
      
      monthlyMap[monthKey].total_counts += 1;
      if (count.has_discrepancies) {
        monthlyMap[monthKey].discrepancy_counts += 1;
      }
      
      monthlyMap[monthKey].accuracy_rate = 
        ((monthlyMap[monthKey].total_counts - monthlyMap[monthKey].discrepancy_counts) / 
         monthlyMap[monthKey].total_counts) * 100;
    });
    
    return Object.values(monthlyMap).sort((a, b) => {
      return new Date(a.month) - new Date(b.month);
    });
  };

  const processDiscrepancyByDeco = (counts) => {
    const decoMap = {};
    
    counts.forEach(count => {
      const deco = count.deco_name;
      
      if (!decoMap[deco]) {
        decoMap[deco] = {
          name: deco,
          total_counts: 0,
          with_discrepancies: 0,
          total_discrepancy_usd: 0,
          total_discrepancy_ars: 0
        };
      }
      
      decoMap[deco].total_counts += 1;
      if (count.has_discrepancies) {
        decoMap[deco].with_discrepancies += 1;
        // Sum up discrepancy amounts from ledger comparison
        if (count.ledger_comparison_usd) {
          decoMap[deco].total_discrepancy_usd += Math.abs(count.ledger_comparison_usd.difference || 0);
        }
        if (count.ledger_comparison_ars) {
          decoMap[deco].total_discrepancy_ars += Math.abs(count.ledger_comparison_ars.difference || 0);
        }
      }
    });
    
    return Object.values(decoMap);
  };

  const calculateSummary = (counts) => {
    const totalCounts = counts.length;
    const discrepancyCounts = counts.filter(c => c.has_discrepancies).length;
    const completedCounts = counts.filter(c => c.status === 'Completed').length;
    
    return {
      total_counts: totalCounts,
      completed_counts: completedCounts,
      pending_counts: totalCounts - completedCounts,
      discrepancy_counts: discrepancyCounts,
      reconciliation_rate: totalCounts > 0 ? ((totalCounts - discrepancyCounts) / totalCounts) * 100 : 0,
      total_cash_usd: counts.reduce((sum, c) => sum + (c.cash_usd_counted || 0), 0),
      total_cash_ars: counts.reduce((sum, c) => sum + (c.cash_ars_counted || 0), 0),
    };
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

  const formatCurrency = (amount, currency) => {
    if (!amount && amount !== 0) return '-';
    return `${currency} ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  };

  const getStatusBadge = (status) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    switch (status) {
      case 'Completed':
        return `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`;
      case 'Discrepancy Found':
        return `${baseClasses} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`;
      case 'In Progress':
        return `${baseClasses} bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200`;
      case 'Pending':
        return `${baseClasses} bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200`;
    }
  };

  const getDiscrepancyIndicator = (hasDiscrepancies, ledgerComparison) => {
    if (!hasDiscrepancies) {
      return <span className="text-green-600 font-medium">✓ Match</span>;
    }
    
    const difference = ledgerComparison?.difference || 0;
    const color = difference > 0 ? 'text-blue-600' : 'text-red-600';
    const symbol = difference > 0 ? '+' : '';
    
    return (
      <span className={`${color} font-medium`}>
        {symbol}{difference.toLocaleString('en-US', { minimumFractionDigits: 2 })}
      </span>
    );
  };

  // Filter cash counts by selected deco
  const filteredCashCounts = selectedDeco 
    ? cashCounts.filter(c => c.deco_name === selectedDeco)
    : cashCounts;

  const decos = ['', ...new Set(cashCounts.map(c => c.deco_name))];

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold theme-text">Cash Count (Arqueo)</h1>
            <p className="theme-text-secondary">Reconciliation and cash count management</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="btn-primary"
          >
            New Cash Count
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
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Total Counts</h3>
              <p className="text-2xl font-bold theme-text">{summary.total_counts}</p>
            </div>
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Completed</h3>
              <p className="text-2xl font-bold text-green-600">{summary.completed_counts}</p>
            </div>
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Discrepancies</h3>
              <p className="text-2xl font-bold text-red-600">{summary.discrepancy_counts}</p>
            </div>
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Accuracy Rate</h3>
              <p className="text-2xl font-bold text-blue-600">{summary.reconciliation_rate.toFixed(1)}%</p>
            </div>
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Total Cash USD</h3>
              <p className="text-2xl font-bold theme-accent">{formatCurrency(summary.total_cash_usd, 'USD')}</p>
            </div>
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Monthly Accuracy Trend */}
          {chartData.length > 0 && (
            <div className="card">
              <div className="border-b theme-border pb-4 mb-6">
                <h2 className="text-xl font-semibold theme-text">Monthly Accuracy Trend</h2>
                <p className="text-sm theme-text-secondary">Reconciliation accuracy over time</p>
              </div>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="month" 
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      axisLine={{ stroke: '#d1d5db' }}
                    />
                    <YAxis 
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      axisLine={{ stroke: '#d1d5db' }}
                      tickFormatter={(value) => `${value}%`}
                      domain={[0, 100]}
                    />
                    <Tooltip 
                      formatter={(value) => [`${value.toFixed(1)}%`, 'Accuracy Rate']}
                      labelStyle={{ color: '#374151' }}
                      contentStyle={{ 
                        backgroundColor: 'white', 
                        border: '1px solid #e5e7eb',
                        borderRadius: '0.5rem'
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="accuracy_rate" 
                      stroke="#008080" 
                      strokeWidth={3}
                      dot={{ fill: '#008080', strokeWidth: 2, r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Discrepancy by Deco */}
          {discrepancyData.length > 0 && (
            <div className="card">
              <div className="border-b theme-border pb-4 mb-6">
                <h2 className="text-xl font-semibold theme-text">Discrepancies by Deco</h2>
                <p className="text-sm theme-text-secondary">Count accuracy comparison across projects</p>
              </div>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={discrepancyData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="name" 
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      axisLine={{ stroke: '#d1d5db' }}
                    />
                    <YAxis 
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      axisLine={{ stroke: '#d1d5db' }}
                    />
                    <Tooltip 
                      formatter={(value, name) => [value, name === 'total_counts' ? 'Total Counts' : 'With Discrepancies']}
                      labelStyle={{ color: '#374151' }}
                      contentStyle={{ 
                        backgroundColor: 'white', 
                        border: '1px solid #e5e7eb',
                        borderRadius: '0.5rem'
                      }}
                    />
                    <Legend />
                    <Bar 
                      dataKey="total_counts" 
                      name="Total Counts"
                      fill="#008080" 
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar 
                      dataKey="with_discrepancies" 
                      name="With Discrepancies"
                      fill="#ef4444" 
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>

        {/* Deco Filter */}
        <div className="card mb-6">
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium theme-text">Filter by Deco:</label>
            <select
              className="form-input"
              value={selectedDeco}
              onChange={(e) => setSelectedDeco(e.target.value)}
            >
              <option value="">All Decos</option>
              {decos.slice(1).map(deco => (
                <option key={deco} value={deco}>{deco}</option>
              ))}
            </select>
            {selectedDeco && (
              <button
                onClick={() => setSelectedDeco('')}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Clear Filter
              </button>
            )}
          </div>
        </div>

        {/* Cash Counts Table */}
        <div className="card">
          <div className="border-b theme-border pb-4 mb-4">
            <h2 className="text-xl font-semibold theme-text">
              Cash Count Records {selectedDeco && `- ${selectedDeco}`}
            </h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="table-header">
                  <th className="text-left p-4 font-medium theme-text">Date</th>
                  <th className="text-left p-4 font-medium theme-text">Deco</th>
                  <th className="text-left p-4 font-medium theme-text">Type</th>
                  <th className="text-right p-4 font-medium theme-text">Cash USD</th>
                  <th className="text-right p-4 font-medium theme-text">Cash ARS</th>
                  <th className="text-right p-4 font-medium theme-text">Total Profit</th>
                  <th className="text-center p-4 font-medium theme-text">USD Match</th>
                  <th className="text-center p-4 font-medium theme-text">ARS Match</th>
                  <th className="text-center p-4 font-medium theme-text">Status</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="9" className="p-0">
                      <TableSkeleton />
                    </td>
                  </tr>
                ) : filteredCashCounts.length === 0 ? (
                  <tr>
                    <td colSpan="9" className="text-center py-12 theme-text-secondary">
                      {selectedDeco 
                        ? `No cash counts found for ${selectedDeco}.`
                        : 'No cash counts found. Create your first cash count to get started.'
                      }
                    </td>
                  </tr>
                ) : (
                  filteredCashCounts.map((count) => (
                    <tr key={count._id} className="table-row">
                      <td className="p-4 theme-text">
                        {format(new Date(count.count_date), 'dd/MM/yyyy')}
                      </td>
                      <td className="p-4 theme-text font-medium">{count.deco_name}</td>
                      <td className="p-4 theme-text">{count.count_type}</td>
                      <td className="p-4 theme-text text-right table-cell-numeric">
                        {formatCurrency(count.cash_usd_counted, 'USD')}
                      </td>
                      <td className="p-4 theme-text text-right table-cell-numeric">
                        {formatCurrency(count.cash_ars_counted, 'ARS')}
                      </td>
                      <td className="p-4 theme-text text-right table-cell-numeric">
                        <div>
                          <div>{formatCurrency(count.total_profit_usd, 'USD')}</div>
                          <div className="text-xs theme-text-secondary">
                            {formatCurrency(count.total_profit_ars, 'ARS')}
                          </div>
                        </div>
                      </td>
                      <td className="p-4 text-center">
                        {getDiscrepancyIndicator(
                          count.ledger_comparison_usd && !count.ledger_comparison_usd.matches, 
                          count.ledger_comparison_usd
                        )}
                      </td>
                      <td className="p-4 text-center">
                        {getDiscrepancyIndicator(
                          count.ledger_comparison_ars && !count.ledger_comparison_ars.matches, 
                          count.ledger_comparison_ars
                        )}
                      </td>
                      <td className="p-4 text-center">
                        <span className={getStatusBadge(count.status)}>
                          {count.status || 'Pending'}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Cash Count Modal */}
        <CashCountModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSubmit={handleCreateCashCount}
          loading={isSubmitting}
        />
      </div>
    </div>
  );
};

export default CashCount;