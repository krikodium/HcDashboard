import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

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

// Application Category Autocomplete Component
const ApplicationAutocomplete = ({ value, onChange, onCreateNew, entryType, required = false }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isCreatingNew, setIsCreatingNew] = useState(false);

  const fetchCategories = async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      setLoading(true);
      const categoryType = entryType === 'income' ? 'Income' : entryType === 'expense' ? 'Expense' : 'Both';
      const response = await axios.get(`/api/application-categories/autocomplete?q=${encodeURIComponent(query)}&category_type=${categoryType}&limit=10`);
      setSuggestions(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    onChange(newValue);
    
    if (newValue.length >= 2) {
      fetchCategories(newValue);
      setShowSuggestions(true);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
    
    // Check if this is a completely new category
    setIsCreatingNew(newValue.length > 0 && !suggestions.some(s => s.name.toLowerCase() === newValue.toLowerCase()));
  };

  const handleSelectSuggestion = async (suggestion) => {
    onChange(suggestion.name);
    setShowSuggestions(false);
    setIsCreatingNew(false);
    
    // Increment usage count for selected category
    try {
      const categories = await axios.get('/api/application-categories');
      const category = categories.data.find(cat => cat.name === suggestion.name);
      if (category) {
        await axios.patch(`/api/application-categories/${category.id}/increment-usage`);
      }
    } catch (error) {
      console.error('Error incrementing usage:', error);
    }
  };

  const handleInputBlur = () => {
    // Delay hiding suggestions to allow clicking on them
    setTimeout(() => setShowSuggestions(false), 200);
  };

  const handleInputFocus = () => {
    if (value.length >= 2 && suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  const handleCreateNewCategory = async () => {
    if (!value || value.length < 2) return;
    
    try {
      const categoryType = entryType === 'income' ? 'Income' : entryType === 'expense' ? 'Expense' : 'Both';
      await axios.post('/api/application-categories', {
        name: value,
        category_type: categoryType,
        description: `User-created ${categoryType.toLowerCase()} category`
      });
      setIsCreatingNew(false);
      if (onCreateNew) onCreateNew(value);
    } catch (error) {
      console.error('Error creating category:', error);
    }
  };

  return (
    <div className="relative">
      <div className="flex space-x-2">
        <div className="flex-1 relative">
          <input
            type="text"
            className="form-input w-full"
            value={value}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            onFocus={handleInputFocus}
            placeholder="Type application/category name..."
            required={required}
          />
          
          {loading && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
            </div>
          )}
          
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border theme-border rounded-md shadow-lg max-h-60 overflow-y-auto">
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className="px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer theme-text"
                  onMouseDown={() => handleSelectSuggestion(suggestion)}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{suggestion.name}</span>
                    <div className="text-xs theme-text-secondary flex items-center space-x-2">
                      <span className={`status-badge ${
                        suggestion.category_type === 'Income' ? 'status-success' : 
                        suggestion.category_type === 'Expense' ? 'status-error' : 'status-info'
                      }`}>
                        {suggestion.category_type}
                      </span>
                      {suggestion.usage_count > 0 && (
                        <span className="text-xs">Used {suggestion.usage_count} times</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {isCreatingNew && value.length >= 2 && (
            <div className="absolute z-50 w-full mt-1 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md shadow-lg p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-700 dark:text-blue-300">
                  Create new category: "{value}"
                </span>
                <button
                  type="button"
                  onClick={handleCreateNewCategory}
                  className="text-xs btn-primary py-1 px-2"
                >
                  Create
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Date Filter Component
const DateFilterComponent = ({ selectedYear, selectedMonth, onYearChange, onMonthChange, availableYears, availableMonths }) => {
  const months = [
    { value: '', label: 'All Months' },
    { value: '1', label: 'January' },
    { value: '2', label: 'February' },
    { value: '3', label: 'March' },
    { value: '4', label: 'April' },
    { value: '5', label: 'May' },
    { value: '6', label: 'June' },
    { value: '7', label: 'July' },
    { value: '8', label: 'August' },
    { value: '9', label: 'September' },
    { value: '10', label: 'October' },
    { value: '11', label: 'November' },
    { value: '12', label: 'December' }
  ];

  return (
    <div className="flex space-x-4 items-center">
      <div className="flex items-center space-x-2">
        <label className="text-sm font-medium theme-text">Year:</label>
        <select
          className="form-input"
          value={selectedYear}
          onChange={(e) => onYearChange(e.target.value)}
        >
          <option value="">All Years</option>
          {availableYears.map(year => (
            <option key={year} value={year}>{year}</option>
          ))}
        </select>
      </div>
      
      <div className="flex items-center space-x-2">
        <label className="text-sm font-medium theme-text">Month:</label>
        <select
          className="form-input"
          value={selectedMonth}
          onChange={(e) => onMonthChange(e.target.value)}
        >
          {months.map(month => (
            <option key={month.value} value={month.value}>{month.label}</option>
          ))}
        </select>
      </div>
      
      {(selectedYear || selectedMonth) && (
        <button
          onClick={() => {
            onYearChange('');
            onMonthChange('');
          }}
          className="btn-secondary text-sm"
        >
          Clear Filters
        </button>
      )}
    </div>
  );
};

// Entry form modal with enhanced application field
const EntryFormModal = ({ isOpen, onClose, onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    description: '',
    application: '',
    provider: '',
    income_ars: '',
    income_usd: '',
    expense_ars: '',
    expense_usd: '',
    order_link: '',
    notes: ''
  });

  // Determine entry type based on form data
  const getEntryType = () => {
    const hasIncome = formData.income_ars || formData.income_usd;
    const hasExpense = formData.expense_ars || formData.expense_usd;
    
    if (hasIncome && !hasExpense) return 'income';
    if (hasExpense && !hasIncome) return 'expense';
    return 'both';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Create new category if it's a new one
    const entryType = getEntryType();
    if (formData.application && entryType !== 'both') {
      try {
        // Check if category exists
        const response = await axios.get(`/api/application-categories/autocomplete?q=${encodeURIComponent(formData.application)}&limit=1`);
        const exists = response.data.some(cat => cat.name.toLowerCase() === formData.application.toLowerCase());
        
        if (!exists) {
          // Create new category
          const categoryType = entryType === 'income' ? 'Income' : 'Expense';
          await axios.post('/api/application-categories', {
            name: formData.application,
            category_type: categoryType,
            description: `User-created ${categoryType.toLowerCase()} category`
          });
        }
      } catch (error) {
        console.error('Error handling category:', error);
      }
    }
    
    const submitData = {
      ...formData,
      income_ars: formData.income_ars ? parseFloat(formData.income_ars) : null,
      income_usd: formData.income_usd ? parseFloat(formData.income_usd) : null,
      expense_ars: formData.expense_ars ? parseFloat(formData.expense_ars) : null,
      expense_usd: formData.expense_usd ? parseFloat(formData.expense_usd) : null,
    };
    onSubmit(submitData);
  };

  const resetForm = () => {
    setFormData({
      date: new Date().toISOString().split('T')[0],
      description: '',
      application: '',
      provider: '',
      income_ars: '',
      income_usd: '',
      expense_ars: '',
      expense_usd: '',
      order_link: '',
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
          <h2 className="text-2xl font-bold theme-text">New General Cash Entry</h2>
          <button onClick={handleClose} className="text-gray-400 hover:text-gray-600 text-2xl">
            ×
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
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
              <label className="block text-sm font-medium theme-text mb-2">Provider</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.provider}
                onChange={(e) => setFormData({...formData, provider: e.target.value})}
                placeholder="Provider name"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Description</label>
            <input
              type="text"
              className="form-input w-full"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Entry description"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">
              Application / Category *
            </label>
            <ApplicationAutocomplete
              value={formData.application}
              onChange={(value) => setFormData({...formData, application: value})}
              entryType={getEntryType()}
              required={true}
              onCreateNew={(categoryName) => {
                console.log('New category created:', categoryName);
              }}
            />
            <p className="text-xs theme-text-secondary mt-1">
              Start typing to see suggestions, or enter a new category name to create it
            </p>
          </div>

          {/* Income Section */}
          <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
            <h4 className="text-lg font-medium text-green-700 dark:text-green-300 mb-4">Income</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
            </div>
          </div>

          {/* Expense Section */}
          <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
            <h4 className="text-lg font-medium text-red-700 dark:text-red-300 mb-4">Expense</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Order Link</label>
            <input
              type="url"
              className="form-input w-full"
              value={formData.order_link}
              onChange={(e) => setFormData({...formData, order_link: e.target.value})}
              placeholder="https://..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Notes</label>
            <textarea
              className="form-input w-full"
              rows="3"
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              placeholder="Additional notes"
            />
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

// Main General Cash Component
const GeneralCash = () => {
  const [entries, setEntries] = useState([]);
  const [filteredEntries, setFilteredEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  // Filter states
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedMonth, setSelectedMonth] = useState('');
  const [availableYears, setAvailableYears] = useState([]);

  useEffect(() => {
    fetchEntries();
  }, []);

  const applyFilters = useCallback(() => {
    let filtered = [...entries];
    
    if (selectedYear) {
      filtered = filtered.filter(entry => new Date(entry.date).getFullYear().toString() === selectedYear);
    }
    
    if (selectedMonth) {
      filtered = filtered.filter(entry => (new Date(entry.date).getMonth() + 1).toString() === selectedMonth);
    }
    
    setFilteredEntries(filtered);
  }, [entries, selectedYear, selectedMonth]);

  useEffect(() => {
    applyFilters();
  }, [applyFilters]);

  const fetchEntries = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/general-cash');
      setEntries(response.data);
      
      // Extract available years from data
      const years = [...new Set(response.data.map(entry => new Date(entry.date).getFullYear()))].sort((a, b) => b - a);
      setAvailableYears(years);
      
      setError('');
    } catch (error) {
      console.error('Error fetching entries:', error);
      setError('Failed to load entries. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEntry = async (formData) => {
    try {
      setIsSubmitting(true);
      await axios.post('/api/general-cash', formData);
      setIsModalOpen(false);
      await fetchEntries();
    } catch (error) {
      console.error('Error creating entry:', error);
      setError('Failed to create entry. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApprove = async (entryId) => {
    try {
      await axios.patch(`/api/general-cash/${entryId}`, { approval_status: 'APPROVED' });
      await fetchEntries();
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
    const baseClasses = "status-badge";
    switch (status) {
      case 'APPROVED':
        return `${baseClasses} status-success`;
      case 'PENDING':
        return `${baseClasses} status-warning`;
      case 'REJECTED':
        return `${baseClasses} status-error`;
      default:
        return `${baseClasses} status-info`;
    }
  };

  // Process data for charts
  const processChartData = (entries) => {
    const chartData = {};
    
    entries.forEach(entry => {
      const date = new Date(entry.date);
      const monthKey = format(date, 'MMM yyyy');
      
      if (!chartData[monthKey]) {
        chartData[monthKey] = {
          month: monthKey,
          income_ars: 0,
          income_usd: 0,
          expense_ars: 0,
          expense_usd: 0,
          net_ars: 0,
          net_usd: 0
        };
      }
      
      chartData[monthKey].income_ars += entry.income_ars || 0;
      chartData[monthKey].income_usd += entry.income_usd || 0;
      chartData[monthKey].expense_ars += entry.expense_ars || 0;
      chartData[monthKey].expense_usd += entry.expense_usd || 0;
      chartData[monthKey].net_ars = chartData[monthKey].income_ars - chartData[monthKey].expense_ars;
      chartData[monthKey].net_usd = chartData[monthKey].income_usd - chartData[monthKey].expense_usd;
    });
    
    return Object.values(chartData).sort((a, b) => new Date(a.month) - new Date(b.month));
  };

  const chartData = processChartData(filteredEntries);

  // Calculate summary statistics
  const summary = {
    totalEntries: filteredEntries.length,
    totalIncomeARS: filteredEntries.reduce((sum, entry) => sum + (entry.income_ars || 0), 0),
    totalIncomeUSD: filteredEntries.reduce((sum, entry) => sum + (entry.income_usd || 0), 0),
    totalExpenseARS: filteredEntries.reduce((sum, entry) => sum + (entry.expense_ars || 0), 0),
    totalExpenseUSD: filteredEntries.reduce((sum, entry) => sum + (entry.expense_usd || 0), 0),
    pendingApprovals: filteredEntries.filter(entry => entry.approval_status === 'PENDING').length,
    approvedEntries: filteredEntries.filter(entry => entry.approval_status === 'APPROVED').length
  };

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
            <h1 className="text-3xl font-bold theme-text">General Cash</h1>
            <p className="theme-text-secondary">Financial entries and transaction management</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="btn-primary"
          >
            Add Entry
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
            <button 
              onClick={() => setError('')}
              className="float-right text-red-900 hover:text-red-700"
            >
              ×
            </button>
          </div>
        )}

        {/* Date Filters */}
        <div className="card mb-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold theme-text">Filter by Date</h3>
            <DateFilterComponent
              selectedYear={selectedYear}
              selectedMonth={selectedMonth}
              onYearChange={setSelectedYear}
              onMonthChange={setSelectedMonth}
              availableYears={availableYears}
            />
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card">
            <h3 className="text-sm font-medium theme-text-secondary">Total Entries</h3>
            <p className="text-2xl font-bold theme-text">{summary.totalEntries}</p>
            <p className="text-xs theme-text-secondary mt-1">
              {selectedYear || selectedMonth ? 'Filtered' : 'All time'}
            </p>
          </div>
          
          <div className="card">
            <h3 className="text-sm font-medium theme-text-secondary">Income</h3>
            <div className="space-y-1">
              <p className="text-lg font-bold text-green-600">
                {formatCurrency(summary.totalIncomeARS, 'ARS')}
              </p>
              <p className="text-lg font-bold text-green-600">
                {formatCurrency(summary.totalIncomeUSD, 'USD')}
              </p>
            </div>
          </div>
          
          <div className="card">
            <h3 className="text-sm font-medium theme-text-secondary">Expenses</h3>
            <div className="space-y-1">
              <p className="text-lg font-bold text-red-600">
                {formatCurrency(summary.totalExpenseARS, 'ARS')}
              </p>
              <p className="text-lg font-bold text-red-600">
                {formatCurrency(summary.totalExpenseUSD, 'USD')}
              </p>
            </div>
          </div>
          
          <div className="card">
            <h3 className="text-sm font-medium theme-text-secondary">Net Balance</h3>
            <div className="space-y-1">
              <p className={`text-lg font-bold ${
                (summary.totalIncomeARS - summary.totalExpenseARS) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(summary.totalIncomeARS - summary.totalExpenseARS, 'ARS')}
              </p>
              <p className={`text-lg font-bold ${
                (summary.totalIncomeUSD - summary.totalExpenseUSD) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(summary.totalIncomeUSD - summary.totalExpenseUSD, 'USD')}
              </p>
            </div>
          </div>
        </div>

        {/* Charts */}
        {chartData.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Income vs Expense Chart (ARS) */}
            <div className="card">
              <h3 className="text-lg font-semibold theme-text mb-4">Monthly Trend (ARS)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`AR$ ${value.toLocaleString()}`, '']} />
                  <Legend />
                  <Bar dataKey="income_ars" fill="#10b981" name="Income ARS" />
                  <Bar dataKey="expense_ars" fill="#ef4444" name="Expense ARS" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Income vs Expense Chart (USD) */}
            <div className="card">
              <h3 className="text-lg font-semibold theme-text mb-4">Monthly Trend (USD)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`$ ${value.toLocaleString()}`, '']} />
                  <Legend />
                  <Bar dataKey="income_usd" fill="#3b82f6" name="Income USD" />
                  <Bar dataKey="expense_usd" fill="#f59e0b" name="Expense USD" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Net Balance Trend */}
            <div className="card lg:col-span-2">
              <h3 className="text-lg font-semibold theme-text mb-4">Net Balance Trend</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="net_ars" stroke="#10b981" name="Net ARS" strokeWidth={2} />
                  <Line type="monotone" dataKey="net_usd" stroke="#3b82f6" name="Net USD" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Entries Table */}
        <div className="card">
          <div className="table-container">
            <table className="min-w-full">
              <thead className="table-header">
                <tr>
                  <th className="table-header-cell">Date</th>
                  <th className="table-header-cell">Description</th>
                  <th className="table-header-cell">Application</th>
                  <th className="table-header-cell">Provider</th>
                  <th className="table-header-cell">Income ARS</th>
                  <th className="table-header-cell">Expense ARS</th>
                  <th className="table-header-cell">Income USD</th>
                  <th className="table-header-cell">Expense USD</th>
                  <th className="table-header-cell">Status</th>
                  <th className="table-header-cell">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredEntries.map((entry) => (
                  <tr key={entry.id} className="table-row">
                    <td className="table-cell font-medium">
                      {format(new Date(entry.date), 'dd/MM/yyyy')}
                    </td>
                    <td className="table-cell">
                      <div>
                        <p className="font-medium theme-text">{entry.description}</p>
                        {entry.notes && (
                          <p className="text-sm theme-text-secondary">{entry.notes}</p>
                        )}
                      </div>
                    </td>
                    <td className="table-cell">
                      <span className="text-sm font-medium theme-text">{entry.application}</span>
                    </td>
                    <td className="table-cell theme-text-secondary">
                      {entry.provider || '-'}
                    </td>
                    <td className="table-cell">
                      <span className="text-green-600 font-medium">
                        {entry.income_ars ? formatCurrency(entry.income_ars, 'ARS') : '-'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className="text-red-600 font-medium">
                        {entry.expense_ars ? formatCurrency(entry.expense_ars, 'ARS') : '-'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className="text-green-600 font-medium">
                        {entry.income_usd ? formatCurrency(entry.income_usd, 'USD') : '-'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className="text-red-600 font-medium">
                        {entry.expense_usd ? formatCurrency(entry.expense_usd, 'USD') : '-'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className={getStatusBadge(entry.approval_status)}>
                        {entry.approval_status}
                      </span>
                    </td>
                    <td className="table-cell">
                      {entry.approval_status === 'PENDING' && (
                        <button
                          onClick={() => handleApprove(entry.id)}
                          className="btn-success text-xs py-1 px-2"
                        >
                          Approve
                        </button>
                      )}
                      {entry.order_link && (
                        <a
                          href={entry.order_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-secondary text-xs py-1 px-2 ml-2"
                        >
                          View Order
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {filteredEntries.length === 0 && (
              <div className="text-center py-12">
                <p className="theme-text-secondary">
                  {selectedYear || selectedMonth ? 'No entries found for the selected period' : 'No entries found'}
                </p>
              </div>
            )}
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