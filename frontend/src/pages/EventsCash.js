import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

// Loading skeleton component
const TableSkeleton = () => (
  <div className="animate-pulse">
    {[...Array(3)].map((_, i) => (
      <div key={i} className="border-b theme-border">
        <div className="grid grid-cols-7 gap-4 p-4">
          {[...Array(7)].map((_, j) => (
            <div key={j} className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
          ))}
        </div>
      </div>
    ))}
  </div>
);

// Event Provider Autocomplete Component
const EventProviderAutocomplete = ({ value, onChange, onProviderSelect, category, disabled = false }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState(null);

  const fetchProviders = async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      setLoading(true);
      const params = { q: query, limit: 10 };
      if (category) params.category = category;
      
      const response = await axios.get('/api/event-providers/autocomplete', { params });
      setSuggestions(response.data);
    } catch (error) {
      console.error('Error fetching providers:', error);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    onChange(newValue);
    
    if (newValue.length >= 2) {
      fetchProviders(newValue);
      setShowSuggestions(true);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
    
    // Clear selected provider if input changes
    if (selectedProvider && selectedProvider.name !== newValue) {
      setSelectedProvider(null);
      if (onProviderSelect) onProviderSelect(null);
    }
  };

  const handleSelectSuggestion = (provider) => {
    onChange(provider.name);
    setSelectedProvider(provider);
    setShowSuggestions(false);
    if (onProviderSelect) onProviderSelect(provider);
  };

  const handleInputBlur = () => {
    setTimeout(() => setShowSuggestions(false), 200);
  };

  const handleInputFocus = () => {
    if (value.length >= 2 && suggestions.length > 0) {
      setShowSuggestions(true);
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
            placeholder="Type provider name..."
            disabled={disabled}
          />
          
          {loading && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
            </div>
          )}
          
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border theme-border rounded-md shadow-lg max-h-60 overflow-y-auto">
              {suggestions.map((provider, index) => (
                <div
                  key={index}
                  className="px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer theme-text"
                  onMouseDown={() => handleSelectSuggestion(provider)}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="font-medium">{provider.name}</span>
                      {provider.contact_person && (
                        <div className="text-xs theme-text-secondary">Contact: {provider.contact_person}</div>
                      )}
                    </div>
                    <div className="text-xs theme-text-secondary flex items-center space-x-2">
                      <span className={`status-badge ${
                        provider.category === 'Catering' ? 'status-success' : 
                        provider.category === 'Decoration' ? 'status-info' : 
                        provider.category === 'Music' ? 'status-warning' : 'status-secondary'
                      }`}>
                        {provider.category}
                      </span>
                      {provider.usage_count > 0 && (
                        <span className="text-xs">Used {provider.usage_count} times</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {selectedProvider && (
        <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-md border border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between text-sm">
            <div>
              <span className="font-medium text-blue-700 dark:text-blue-300">Selected: {selectedProvider.name}</span>
              <div className="text-xs text-blue-600 dark:text-blue-400">
                Category: {selectedProvider.category} | Type: {selectedProvider.provider_type}
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                setSelectedProvider(null);
                onChange('');
                if (onProviderSelect) onProviderSelect(null);
              }}
              className="text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Event Header Component
const EventHeader = ({ event }) => {
  if (!event) return null;

  const { header } = event;

  return (
    <div className="card mb-6">
      <div className="border-b theme-border pb-4 mb-4">
        <h2 className="text-xl font-semibold theme-text">Event Details</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div>
          <label className="block text-sm font-medium theme-text-secondary mb-1">Event Date</label>
          <p className="theme-text font-medium">{format(new Date(header.event_date), 'dd/MM/yyyy')}</p>
        </div>
        
        <div>
          <label className="block text-sm font-medium theme-text-secondary mb-1">Event Type</label>
          <p className="theme-text font-medium">{header.event_type}</p>
        </div>
        
        <div>
          <label className="block text-sm font-medium theme-text-secondary mb-1">Client Name</label>
          <p className="theme-text font-medium">{header.client_name}</p>
        </div>
        
        <div>
          <label className="block text-sm font-medium theme-text-secondary mb-1">Organizer</label>
          <p className="theme-text font-medium">{header.organizer}</p>
        </div>
        
        <div>
          <label className="block text-sm font-medium theme-text-secondary mb-1">Location</label>
          <p className="theme-text font-medium">{header.localidad}, {header.province}</p>
        </div>
        
        <div>
          <label className="block text-sm font-medium theme-text-secondary mb-1">Budget Number</label>
          <p className="theme-text font-medium">{header.budget_number}</p>
        </div>
        
        <div className="lg:col-span-2">
          <label className="block text-sm font-medium theme-text-secondary mb-1">Payment Terms</label>
          <p className="theme-text">{header.payment_terms}</p>
        </div>
        
        <div>
          <label className="block text-sm font-medium theme-text-secondary mb-1">Total Budget (No IVA)</label>
          <p className="text-xl font-bold theme-accent">
            ARS {header.total_budget_no_iva?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </p>
        </div>
      </div>
    </div>
  );
};

// Payment Status Panel Component
const PaymentStatusPanel = ({ event }) => {
  if (!event || !event.payment_status) return null;

  const { payment_status } = event;
  const balanceDue = payment_status.total_budget - (payment_status.anticipo_received + payment_status.segundo_pago + payment_status.tercer_pago);

  const formatCurrency = (amount) => {
    return `ARS ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  };

  const getStatusColor = () => {
    if (balanceDue <= 0) return 'text-green-600';
    if (payment_status.anticipo_received > 0) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Data for payment status chart
  const chartData = [
    { name: 'Anticipo', value: payment_status.anticipo_received, color: '#008080' },
    { name: '2º Pago', value: payment_status.segundo_pago, color: '#20B2AA' },
    { name: '3º Pago', value: payment_status.tercer_pago, color: '#48D1CC' },
    { name: 'Balance Due', value: Math.max(0, balanceDue), color: '#E5E7EB' },
  ].filter(item => item.value > 0);

  return (
    <div className="card mb-6">
      <div className="border-b theme-border pb-4 mb-6">
        <h2 className="text-xl font-semibold theme-text">Payment Status</h2>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Payment Cards */}
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-medium theme-text-secondary">Total Budget</h3>
              <p className="text-lg font-bold theme-text">{formatCurrency(payment_status.total_budget)}</p>
            </div>
            
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
              <h3 className="text-sm font-medium theme-text-secondary">Anticipo Received</h3>
              <p className="text-lg font-bold text-green-600">{formatCurrency(payment_status.anticipo_received)}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <h3 className="text-sm font-medium theme-text-secondary">2º Pago</h3>
              <p className="text-lg font-bold text-blue-600">{formatCurrency(payment_status.segundo_pago)}</p>
            </div>
            
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
              <h3 className="text-sm font-medium theme-text-secondary">3º Pago</h3>
              <p className="text-lg font-bold text-purple-600">{formatCurrency(payment_status.tercer_pago)}</p>
            </div>
          </div>
          
          <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4 border-2 border-dashed theme-border">
            <h3 className="text-sm font-medium theme-text-secondary">Balance Due</h3>
            <p className={`text-xl font-bold ${getStatusColor()}`}>{formatCurrency(balanceDue)}</p>
          </div>
        </div>
        
        {/* Payment Status Chart */}
        <div className="flex flex-col items-center">
          <h3 className="text-lg font-medium theme-text mb-4">Payment Breakdown</h3>
          <div className="w-full h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => formatCurrency(value)}
                  labelStyle={{ color: '#374151' }}
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '0.5rem'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-4 mt-2">
            {chartData.map((entry, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }}></div>
                <span className="text-sm theme-text-secondary">{entry.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Ledger Entry Form Modal Component
const LedgerEntryModal = ({ isOpen, onClose, onSubmit, loading, eventId }) => {
  const [formData, setFormData] = useState({
    payment_method: 'Efectivo',
    date: new Date().toISOString().split('T')[0],
    detail: '',
    income_ars: '',
    expense_ars: '',
    income_usd: '',
    expense_usd: '',
    provider_name: '',
    is_client_payment: false
  });
  
  const [selectedProvider, setSelectedProvider] = useState(null);

  const paymentMethods = ['Efectivo', 'Transferencia', 'Tarjeta'];

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      income_ars: formData.income_ars ? parseFloat(formData.income_ars) : null,
      expense_ars: formData.expense_ars ? parseFloat(formData.expense_ars) : null,
      income_usd: formData.income_usd ? parseFloat(formData.income_usd) : null,
      expense_usd: formData.expense_usd ? parseFloat(formData.expense_usd) : null,
      provider_id: selectedProvider?.id || null,
      is_client_payment: formData.is_client_payment
    };
    onSubmit(submitData);
  };

  const resetForm = () => {
    setFormData({
      payment_method: 'Efectivo',
      date: new Date().toISOString().split('T')[0],
      detail: '',
      income_ars: '',
      expense_ars: '',
      income_usd: '',
      expense_usd: '',
      provider_name: '',
      is_client_payment: false
    });
    setSelectedProvider(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleProviderSelect = (provider) => {
    setSelectedProvider(provider);
  };

  const isIncomeTransaction = formData.income_ars || formData.income_usd;
  const isExpenseTransaction = formData.expense_ars || formData.expense_usd;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="card max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold theme-text">Add Ledger Entry</h2>
          <button
            onClick={handleClose}
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
              <label className="block text-sm font-medium theme-text mb-2">Payment Method</label>
              <select
                className="form-input w-full"
                value={formData.payment_method}
                onChange={(e) => setFormData({...formData, payment_method: e.target.value})}
                required
              >
                {paymentMethods.map(method => (
                  <option key={method} value={method}>{method}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Detail</label>
            <input
              type="text"
              className="form-input w-full"
              value={formData.detail}
              onChange={(e) => setFormData({...formData, detail: e.target.value})}
              placeholder="Enter transaction details"
              required
            />
          </div>

          {/* Provider Selection - Only show for expense transactions */}
          {isExpenseTransaction && (
            <div>
              <label className="block text-sm font-medium theme-text mb-2">
                Provider/Vendor
              </label>
              <EventProviderAutocomplete
                value={formData.provider_name}
                onChange={(value) => setFormData({...formData, provider_name: value})}
                onProviderSelect={handleProviderSelect}
              />
              <p className="text-xs theme-text-secondary mt-1">
                Select a provider for expense tracking and reporting
              </p>
            </div>
          )}

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

          {/* Client Payment Checkbox - Only show for income transactions */}
          {isIncomeTransaction && (
            <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg border border-green-200 dark:border-green-800">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="client_payment"
                  className="form-checkbox h-4 w-4 text-green-600"
                  checked={formData.is_client_payment}
                  onChange={(e) => setFormData({...formData, is_client_payment: e.target.checked})}
                />
                <label htmlFor="client_payment" className="text-sm font-medium text-green-700 dark:text-green-300">
                  This is a client payment
                </label>
              </div>
              {formData.is_client_payment && (
                <div className="mt-2 text-xs text-green-600 dark:text-green-400">
                  ✓ This payment will automatically update the Payment Status Panel and reduce the outstanding balance
                </div>
              )}
            </div>
          )}

          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex-1 disabled:opacity-50"
            >
              {loading ? 'Adding...' : 'Add Entry'}
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

// Event Creation Modal Component
const EventCreateModal = ({ isOpen, onClose, onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    event_date: new Date().toISOString().split('T')[0],
    organizer: '',
    client_name: '',
    client_razon_social: '',
    event_type: 'Birthday',
    province: '',
    localidad: '',
    viaticos_armado: '',
    hc_fees: '',
    total_budget_no_iva: '',
    budget_number: '',
    payment_terms: ''
  });

  const eventTypes = ['Birthday', 'Quinceañera', 'Wedding', 'Sports Event', 'Corporate Event', 'Other'];

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = {
      header: {
        ...formData,
        viaticos_armado: formData.viaticos_armado ? parseFloat(formData.viaticos_armado) : null,
        hc_fees: formData.hc_fees ? parseFloat(formData.hc_fees) : null,
        total_budget_no_iva: parseFloat(formData.total_budget_no_iva),
      }
    };
    onSubmit(submitData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="card max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold theme-text">Create New Event</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Event Date</label>
              <input
                type="date"
                className="form-input w-full"
                value={formData.event_date}
                onChange={(e) => setFormData({...formData, event_date: e.target.value})}
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Event Type</label>
              <select
                className="form-input w-full"
                value={formData.event_type}
                onChange={(e) => setFormData({...formData, event_type: e.target.value})}
                required
              >
                {eventTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Budget Number</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.budget_number}
                onChange={(e) => setFormData({...formData, budget_number: e.target.value})}
                placeholder="BUD-2025-001"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Client Name</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.client_name}
                onChange={(e) => setFormData({...formData, client_name: e.target.value})}
                placeholder="Enter client name"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Organizer</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.organizer}
                onChange={(e) => setFormData({...formData, organizer: e.target.value})}
                placeholder="Enter organizer name"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Province</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.province}
                onChange={(e) => setFormData({...formData, province: e.target.value})}
                placeholder="Buenos Aires"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Localidad</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.localidad}
                onChange={(e) => setFormData({...formData, localidad: e.target.value})}
                placeholder="Palermo"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Total Budget (No IVA)</label>
            <input
              type="number"
              step="0.01"
              className="form-input w-full"
              value={formData.total_budget_no_iva}
              onChange={(e) => setFormData({...formData, total_budget_no_iva: e.target.value})}
              placeholder="150000.00"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Payment Terms</label>
            <textarea
              className="form-input w-full"
              rows="3"
              value={formData.payment_terms}
              onChange={(e) => setFormData({...formData, payment_terms: e.target.value})}
              placeholder="30% anticipo, 40% a los 15 días, 30% al finalizar"
              required
            />
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex-1 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Event'}
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

// Main Events Cash Component
const EventsCash = () => {
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isLedgerModalOpen, setIsLedgerModalOpen] = useState(false);
  const [isEventModalOpen, setIsEventModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview'); // New state for tab management

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/events-cash');
      setEvents(response.data);
      if (response.data.length > 0 && !selectedEvent) {
        setSelectedEvent(response.data[0]);
      }
      setError('');
    } catch (error) {
      console.error('Error fetching events:', error);
      setError('Failed to load events. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEvent = async (formData) => {
    try {
      setIsSubmitting(true);
      const response = await axios.post('/api/events-cash', formData);
      setIsEventModalOpen(false);
      await fetchEvents();
      setSelectedEvent(response.data);
    } catch (error) {
      console.error('Error creating event:', error);
      setError('Failed to create event. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddLedgerEntry = async (formData) => {
    try {
      setIsSubmitting(true);
      await axios.post(`/api/events-cash/${selectedEvent._id}/ledger`, formData);
      setIsLedgerModalOpen(false);
      await fetchEvents();
      // Update selected event
      const updatedEvents = await axios.get('/api/events-cash');
      const updatedEvent = updatedEvents.data.find(e => e._id === selectedEvent._id);
      setSelectedEvent(updatedEvent);
    } catch (error) {
      console.error('Error adding ledger entry:', error);
      setError('Failed to add ledger entry. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatCurrency = (amount, currency) => {
    if (!amount) return '-';
    return `${currency} ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  };

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold theme-text">Events Cash</h1>
            <p className="theme-text-secondary">Event budgets and payment tracking</p>
          </div>
          <div className="flex space-x-4">
            <button
              onClick={() => setIsEventModalOpen(true)}
              className="btn-primary"
            >
              Create New Event
            </button>
            {selectedEvent && (
              <button
                onClick={() => setIsLedgerModalOpen(true)}
                className="btn-secondary"
              >
                Add Ledger Entry
              </button>
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Event Selection */}
        {events.length > 0 && (
          <div className="card mb-6">
            <h3 className="text-lg font-medium theme-text mb-4">Select Event</h3>
            <div className="flex flex-wrap gap-2">
              {events.map((event) => (
                <button
                  key={event._id}
                  onClick={() => setSelectedEvent(event)}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    selectedEvent?._id === event._id
                      ? 'theme-accent-bg text-white'
                      : 'bg-gray-100 dark:bg-gray-700 theme-text hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {event.header.client_name} - {event.header.event_type}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading ? (
          <div className="card">
            <TableSkeleton />
          </div>
        ) : events.length === 0 ? (
          <div className="card">
            <div className="text-center py-12">
              <h3 className="text-xl font-semibold theme-text mb-4">No Events Found</h3>
              <p className="theme-text-secondary mb-6">
                Create your first event to start tracking payments and budgets.
              </p>
              <button
                onClick={() => setIsEventModalOpen(true)}
                className="btn-primary"
              >
                Create First Event
              </button>
            </div>
          </div>
        ) : selectedEvent ? (
          <>
            {/* Event Header */}
            <EventHeader event={selectedEvent} />
            
            {/* Payment Status Panel */}
            <PaymentStatusPanel event={selectedEvent} />
            
            {/* Ledger Table */}
            <div className="card">
              <div className="border-b theme-border pb-4 mb-4">
                <h2 className="text-xl font-semibold theme-text">Transaction Ledger</h2>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="table-header">
                      <th className="text-left p-4 font-medium theme-text">Date</th>
                      <th className="text-left p-4 font-medium theme-text">Payment Method</th>
                      <th className="text-left p-4 font-medium theme-text">Detail</th>
                      <th className="text-right p-4 font-medium theme-text">Income ARS</th>
                      <th className="text-right p-4 font-medium theme-text">Expense ARS</th>
                      <th className="text-right p-4 font-medium theme-text">Balance ARS</th>
                      <th className="text-right p-4 font-medium theme-text">Balance USD</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedEvent.ledger_entries.length === 0 ? (
                      <tr>
                        <td colSpan="7" className="text-center py-12 theme-text-secondary">
                          No ledger entries found. Add your first transaction to get started.
                        </td>
                      </tr>
                    ) : (
                      selectedEvent.ledger_entries.map((entry, index) => (
                        <tr key={entry.id || index} className="table-row">
                          <td className="p-4 theme-text">
                            {format(new Date(entry.date), 'dd/MM/yyyy')}
                          </td>
                          <td className="p-4 theme-text">{entry.payment_method}</td>
                          <td className="p-4 theme-text">{entry.detail}</td>
                          <td className="p-4 theme-text text-right table-cell-numeric">
                            {formatCurrency(entry.income_ars, 'ARS')}
                          </td>
                          <td className="p-4 theme-text text-right table-cell-numeric">
                            {formatCurrency(entry.expense_ars, 'ARS')}
                          </td>
                          <td className="p-4 theme-text text-right table-cell-numeric font-medium">
                            {formatCurrency(entry.running_balance_ars, 'ARS')}
                          </td>
                          <td className="p-4 theme-text text-right table-cell-numeric font-medium">
                            {formatCurrency(entry.running_balance_usd, 'USD')}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : null}

        {/* Modals */}
        <EventCreateModal
          isOpen={isEventModalOpen}
          onClose={() => setIsEventModalOpen(false)}
          onSubmit={handleCreateEvent}
          loading={isSubmitting}
        />

        <LedgerEntryModal
          isOpen={isLedgerModalOpen}
          onClose={() => setIsLedgerModalOpen(false)}
          onSubmit={handleAddLedgerEntry}
          loading={isSubmitting}
          eventId={selectedEvent?._id}
        />
      </div>
    </div>
  );
};

// Expense Report View Component
const ExpenseReportView = ({ selectedEvent }) => {
  const [expenseData, setExpenseData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    category: ''
  });

  const categories = ['Catering', 'Decoration', 'Music', 'Photography', 'Venue', 'Transportation', 'Lighting', 'Flowers', 'Security', 'Cleaning', 'Equipment Rental', 'Other'];

  const fetchExpenseData = async () => {
    if (!selectedEvent) return;

    try {
      setLoading(true);
      const params = {};
      if (filters.start_date) params.start_date = filters.start_date;
      if (filters.end_date) params.end_date = filters.end_date;
      if (filters.category) params.category = filters.category;

      const response = await axios.get(`/api/events-cash/${selectedEvent._id}/expenses-summary`, { params });
      setExpenseData(response.data);
    } catch (error) {
      console.error('Error fetching expense data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedEvent) {
      fetchExpenseData();
    }
  }, [selectedEvent, filters]);

  const formatCurrency = (amount, currency = 'ARS') => {
    if (!amount) return `${currency} 0.00`;
    return `${currency} ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  };

  const prepareChartData = () => {
    if (!expenseData || !expenseData.expenses_by_date) return [];
    
    return Object.entries(expenseData.expenses_by_date).map(([date, data]) => ({
      date: format(new Date(date), 'dd/MM'),
      ars: data.ars,
      usd: data.usd,
      count: data.count
    })).sort((a, b) => new Date(a.date) - new Date(b.date));
  };

  if (!selectedEvent) {
    return (
      <div className="card">
        <div className="text-center py-12">
          <h3 className="text-xl font-semibold theme-text mb-4">No Event Selected</h3>
          <p className="theme-text-secondary">Please select an event to view expense reports.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="card">
        <h3 className="text-lg font-semibold theme-text mb-4">Expense Report Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium theme-text mb-2">Start Date</label>
            <input
              type="date"
              className="form-input w-full"
              value={filters.start_date}
              onChange={(e) => setFilters({...filters, start_date: e.target.value})}
            />
          </div>
          <div>
            <label className="block text-sm font-medium theme-text mb-2">End Date</label>
            <input
              type="date"
              className="form-input w-full"
              value={filters.end_date}
              onChange={(e) => setFilters({...filters, end_date: e.target.value})}
            />
          </div>
          <div>
            <label className="block text-sm font-medium theme-text mb-2">Category</label>
            <select
              className="form-input w-full"
              value={filters.category}
              onChange={(e) => setFilters({...filters, category: e.target.value})}
            >
              <option value="">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ start_date: '', end_date: '', category: '' })}
              className="btn-secondary w-full"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="card">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      ) : expenseData ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Total Expenses</h3>
              <div className="space-y-1">
                <p className="text-lg font-bold text-red-600">{formatCurrency(expenseData.total_expenses_ars, 'ARS')}</p>
                <p className="text-lg font-bold text-red-600">{formatCurrency(expenseData.total_expenses_usd, 'USD')}</p>
              </div>
            </div>
            
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Expense Entries</h3>
              <p className="text-2xl font-bold theme-text">{expenseData.total_entries}</p>
            </div>
            
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Budget Used</h3>
              <p className="text-2xl font-bold theme-accent">{expenseData.percentage_of_budget.toFixed(1)}%</p>
            </div>
            
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Event</h3>
              <p className="text-lg font-bold theme-text">{expenseData.event_name}</p>
            </div>
          </div>

          {/* Expense Chart */}
          {prepareChartData().length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold theme-text mb-4">Expense Trends</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Expense by Date Chart (ARS) */}
                <div>
                  <h4 className="text-md font-medium theme-text mb-2">Daily Expenses (ARS)</h4>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={prepareChartData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip formatter={(value) => [`AR$ ${value.toLocaleString()}`, 'Amount']} />
                      <Bar dataKey="ars" fill="#ef4444" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Expense by Date Chart (USD) */}
                <div>
                  <h4 className="text-md font-medium theme-text mb-2">Daily Expenses (USD)</h4>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={prepareChartData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip formatter={(value) => [`$ ${value.toLocaleString()}`, 'Amount']} />
                      <Bar dataKey="usd" fill="#f59e0b" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* Filter Information */}
          {(filters.start_date || filters.end_date || filters.category) && (
            <div className="card bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
              <h3 className="text-md font-medium text-blue-700 dark:text-blue-300 mb-2">Active Filters</h3>
              <div className="flex flex-wrap gap-2">
                {filters.start_date && (
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-300 rounded text-sm">
                    From: {format(new Date(filters.start_date), 'dd/MM/yyyy')}
                  </span>
                )}
                {filters.end_date && (
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-300 rounded text-sm">
                    To: {format(new Date(filters.end_date), 'dd/MM/yyyy')}
                  </span>
                )}
                {filters.category && (
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-300 rounded text-sm">
                    Category: {filters.category}
                  </span>
                )}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="card">
          <div className="text-center py-12">
            <h3 className="text-xl font-semibold theme-text mb-4">No Expense Data</h3>
            <p className="theme-text-secondary">No expense entries found for the selected filters.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventsCash;