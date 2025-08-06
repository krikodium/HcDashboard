import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// Loading skeleton component
const TableSkeleton = () => (
  <div className="animate-pulse">
    {[...Array(5)].map((_, i) => (
      <div key={i} className="border-b theme-border">
        <div className="grid grid-cols-10 gap-4 p-4">
          {[...Array(10)].map((_, j) => (
            <div key={j} className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
          ))}
        </div>
      </div>
    ))}
  </div>
);

// Provider Autocomplete Component
const ProviderAutocomplete = ({ value, onChange, onCreateNew, required = false }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchProviders = async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get(`/api/providers/autocomplete?q=${encodeURIComponent(query)}&limit=10`);
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
  };

  const handleSelectSuggestion = (provider) => {
    onChange(provider.name);
    setShowSuggestions(false);
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
            required={required}
          />
          
          {loading && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
            </div>
          )}
          
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border theme-border rounded-md shadow-lg max-h-60 overflow-y-auto">
              {suggestions.map((provider) => (
                <div
                  key={provider.id}
                  className="px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer theme-text"
                  onMouseDown={() => handleSelectSuggestion(provider)}
                >
                  <div className="font-medium">{provider.name}</div>
                  {provider.contact_person && (
                    <div className="text-sm theme-text-secondary">Contact: {provider.contact_person}</div>
                  )}
                  {provider.email && (
                    <div className="text-sm theme-text-secondary">{provider.email}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
        
        <button
          type="button"
          onClick={onCreateNew}
          className="btn-secondary text-sm whitespace-nowrap"
        >
          New Provider
        </button>
      </div>
    </div>
  );
};

// Provider Management Modal
const ProviderModal = ({ isOpen, onClose, onSubmit, loading, provider = null }) => {
  const [formData, setFormData] = useState({
    name: '',
    provider_type: 'Supplier',
    contact_person: '',
    email: '',
    phone: '',
    address: '',
    tax_id: '',
    payment_terms: '',
    notes: ''
  });

  useEffect(() => {
    if (provider) {
      setFormData({
        name: provider.name || '',
        provider_type: provider.provider_type || 'Supplier',
        contact_person: provider.contact_person || '',
        email: provider.email || '',
        phone: provider.phone || '',
        address: provider.address || '',
        tax_id: provider.tax_id || '',
        payment_terms: provider.payment_terms || '',
        notes: provider.notes || ''
      });
    } else {
      setFormData({
        name: '',
        provider_type: 'Supplier',
        contact_person: '',
        email: '',
        phone: '',
        address: '',
        tax_id: '',
        payment_terms: '',
        notes: ''
      });
    }
  }, [provider, isOpen]);

  const providerTypes = ['Supplier', 'Vendor', 'Contractor', 'Service Provider', 'Manufacturer', 'Distributor', 'Other'];

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="card max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold theme-text">
            {provider ? 'Edit Provider' : 'New Provider'}
          </h2>
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
              <label className="block text-sm font-medium theme-text mb-2">Provider Name *</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Provider name"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Provider Type</label>
              <select
                className="form-input w-full"
                value={formData.provider_type}
                onChange={(e) => setFormData({...formData, provider_type: e.target.value})}
              >
                {providerTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Contact Person</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.contact_person}
                onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
                placeholder="Contact person name"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Email</label>
              <input
                type="email"
                className="form-input w-full"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="contact@provider.com"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Phone</label>
              <input
                type="tel"
                className="form-input w-full"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                placeholder="+54 11 1234-5678"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Tax ID</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.tax_id}
                onChange={(e) => setFormData({...formData, tax_id: e.target.value})}
                placeholder="Tax ID or CUIT"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Address</label>
            <input
              type="text"
              className="form-input w-full"
              value={formData.address}
              onChange={(e) => setFormData({...formData, address: e.target.value})}
              placeholder="Full address"
            />
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Payment Terms</label>
            <input
              type="text"
              className="form-input w-full"
              value={formData.payment_terms}
              onChange={(e) => setFormData({...formData, payment_terms: e.target.value})}
              placeholder="e.g., 30 days, Immediate, etc."
            />
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Notes</label>
            <textarea
              className="form-input w-full"
              rows="3"
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              placeholder="Additional notes about the provider"
            />
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex-1 disabled:opacity-50"
            >
              {loading ? 'Saving...' : (provider ? 'Update Provider' : 'Create Provider')}
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
const InventoryModal = ({ isOpen, onClose, onSelectItem }) => {
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const categories = ['Décor', 'Furniture', 'Lighting', 'Textiles', 'Accessories', 'Plants', 'Art', 'Other'];

  useEffect(() => {
    if (isOpen) {
      fetchProducts();
    }
  }, [isOpen]);

  useEffect(() => {
    filterProducts();
  }, [filterProducts]);

  const fetchProducts = async () => {
    setLoading(true);
    // Mock inventory data since we don't have a full inventory API yet
    const mockProducts = [
      { id: '1', sku: 'DEC-001', name: 'Decorative Vase', category: 'Décor', cost_ars: 15000, cost_usd: 150, current_stock: 25 },
      { id: '2', sku: 'FUR-002', name: 'Wooden Coffee Table', category: 'Furniture', cost_ars: 85000, cost_usd: 850, current_stock: 8 },
      { id: '3', sku: 'LIG-003', name: 'Modern Floor Lamp', category: 'Lighting', cost_ars: 45000, cost_usd: 450, current_stock: 12 },
      { id: '4', sku: 'TEX-004', name: 'Silk Cushion Cover', category: 'Textiles', cost_ars: 8000, cost_usd: 80, current_stock: 50 },
      { id: '5', sku: 'ACC-005', name: 'Bronze Picture Frame', category: 'Accessories', cost_ars: 12000, cost_usd: 120, current_stock: 30 },
      { id: '6', sku: 'PLN-006', name: 'Succulent Garden Set', category: 'Plants', cost_ars: 6000, cost_usd: 60, current_stock: 40 },
      { id: '7', sku: 'ART-007', name: 'Abstract Canvas Print', category: 'Art', cost_ars: 35000, cost_usd: 350, current_stock: 15 },
      { id: '8', sku: 'DEC-008', name: 'Crystal Chandelier', category: 'Lighting', cost_ars: 120000, cost_usd: 1200, current_stock: 3 },
      { id: '9', sku: 'FUR-009', name: 'Vintage Armchair', category: 'Furniture', cost_ars: 95000, cost_usd: 950, current_stock: 6 },
      { id: '10', sku: 'ACC-010', name: 'Ceramic Sculpture', category: 'Accessories', cost_ars: 25000, cost_usd: 250, current_stock: 18 }
    ];
    setProducts(mockProducts);
    setLoading(false);
  };

  const filterProducts = useCallback(() => {
    let filtered = products;

    if (searchTerm) {
      filtered = filtered.filter(product =>
        product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        product.sku.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (categoryFilter) {
      filtered = filtered.filter(product => product.category === categoryFilter);
    }

    setFilteredProducts(filtered);
    setCurrentPage(1);
  }, [products, searchTerm, categoryFilter]);

  const getCurrentPageItems = () => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredProducts.slice(startIndex, endIndex);
  };

  const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="card max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold theme-text">Select Product from Inventory</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Search and Filter */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium theme-text mb-2">Search Products</label>
            <input
              type="text"
              className="form-input w-full"
              placeholder="Search by name or SKU..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium theme-text mb-2">Filter by Category</label>
            <select
              className="form-input w-full"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Products Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="table-header">
                <th className="text-left p-4 font-medium theme-text">SKU</th>
                <th className="text-left p-4 font-medium theme-text">Product Name</th>
                <th className="text-left p-4 font-medium theme-text">Category</th>
                <th className="text-right p-4 font-medium theme-text">Cost ARS</th>
                <th className="text-right p-4 font-medium theme-text">Cost USD</th>
                <th className="text-center p-4 font-medium theme-text">Stock</th>
                <th className="text-center p-4 font-medium theme-text">Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className="p-0">
                    <TableSkeleton />
                  </td>
                </tr>
              ) : getCurrentPageItems().length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-12 theme-text-secondary">
                    No products found matching your criteria.
                  </td>
                </tr>
              ) : (
                getCurrentPageItems().map((product) => (
                  <tr key={product.id} className="table-row">
                    <td className="p-4 theme-text font-mono">{product.sku}</td>
                    <td className="p-4 theme-text">{product.name}</td>
                    <td className="p-4 theme-text">{product.category}</td>
                    <td className="p-4 theme-text text-right table-cell-numeric">
                      ARS {product.cost_ars.toLocaleString()}
                    </td>
                    <td className="p-4 theme-text text-right table-cell-numeric">
                      USD {product.cost_usd.toLocaleString()}
                    </td>
                    <td className="p-4 theme-text text-center">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        product.current_stock > 10 ? 'bg-green-100 text-green-800' :
                        product.current_stock > 5 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {product.current_stock}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <button
                        onClick={() => onSelectItem(product)}
                        className="px-3 py-1 bg-teal-100 text-teal-800 rounded text-sm hover:bg-teal-200"
                      >
                        Select
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-between items-center mt-6">
            <div className="text-sm theme-text-secondary">
              Showing {getCurrentPageItems().length} of {filteredProducts.length} products
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentPage(page => Math.max(1, page - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 border theme-border rounded disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-3 py-1 theme-text">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(page => Math.min(totalPages, page + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 border theme-border rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Sale Entry Form Modal
const SaleEntryModal = ({ isOpen, onClose, onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    provider: '',
    client: '',
    billing_data: {
      cuit: '',
      email: '',
      address: '',
      phone: ''
    },
    internal_coordinator: '',
    quantity: 1,
    item_description: '',
    sku: '',
    sold_amount_ars: '',
    sold_amount_usd: '',
    payment_method: 'Efectivo',
    cost_ars: '',
    cost_usd: '',
    comments: ''
  });

  const [isInventoryModalOpen, setIsInventoryModalOpen] = useState(false);
  const [showProviderModal, setShowProviderModal] = useState(false);
  const [isCreatingProvider, setIsCreatingProvider] = useState(false);
  const [calculatedAmounts, setCalculatedAmounts] = useState({
    net_sale_ars: 0,
    net_sale_usd: 0,
    commission_ars: 0,
    commission_usd: 0,
    profit_ars: 0,
    profit_usd: 0
  });

  const paymentMethods = ['Efectivo', 'Transferencia', 'Tarjeta'];

  // Calculate derived amounts whenever relevant fields change
  useEffect(() => {
    const soldArs = parseFloat(formData.sold_amount_ars) || 0;
    const soldUsd = parseFloat(formData.sold_amount_usd) || 0;
    const costArs = parseFloat(formData.cost_ars) || 0;
    const costUsd = parseFloat(formData.cost_usd) || 0;
    
    const netSaleArs = soldArs - costArs;
    const netSaleUsd = soldUsd - costUsd;
    const commissionRate = 0.02; // 2%
    const commissionArs = netSaleArs * commissionRate;
    const commissionUsd = netSaleUsd * commissionRate;
    const profitArs = netSaleArs - commissionArs;
    const profitUsd = netSaleUsd - commissionUsd;

    setCalculatedAmounts({
      net_sale_ars: netSaleArs,
      net_sale_usd: netSaleUsd,
      commission_ars: commissionArs,
      commission_usd: commissionUsd,
      profit_ars: profitArs,
      profit_usd: profitUsd
    });
  }, [formData.sold_amount_ars, formData.sold_amount_usd, formData.cost_ars, formData.cost_usd]);

  const handleSelectItem = (product) => {
    setFormData({
      ...formData,
      item_description: product.name,
      sku: product.sku,
      cost_ars: product.cost_ars.toString(),
      cost_usd: product.cost_usd.toString()
    });
    setIsInventoryModalOpen(false);
  };

  const handleCreateProvider = async (providerData) => {
    try {
      setIsCreatingProvider(true);
      const response = await axios.post('/api/providers', providerData);
      setFormData(prev => ({
        ...prev,
        provider: response.data.name
      }));
      setShowProviderModal(false);
    } catch (error) {
      console.error('Error creating provider:', error);
      // You might want to show an error message to the user here
    } finally {
      setIsCreatingProvider(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      quantity: parseInt(formData.quantity),
      sold_amount_ars: formData.sold_amount_ars ? parseFloat(formData.sold_amount_ars) : null,
      sold_amount_usd: formData.sold_amount_usd ? parseFloat(formData.sold_amount_usd) : null,
      cost_ars: formData.cost_ars ? parseFloat(formData.cost_ars) : null,
      cost_usd: formData.cost_usd ? parseFloat(formData.cost_usd) : null,
    };
    onSubmit(submitData);
  };

  const formatCurrency = (amount, currency) => {
    return `${currency} ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="card max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold theme-text">New Sale Entry</h2>
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
                <ProviderAutocomplete
                  value={formData.provider}
                  onChange={(value) => setFormData({...formData, provider: value})}
                  onCreateNew={() => setShowProviderModal(true)}
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Client</label>
                <input
                  type="text"
                  className="form-input w-full"
                  value={formData.client}
                  onChange={(e) => setFormData({...formData, client: e.target.value})}
                  placeholder="Client name"
                  required
                />
              </div>
            </div>

            {/* Billing Information */}
            <div className="border theme-border rounded-lg p-4">
              <h3 className="text-lg font-medium theme-text mb-4">Billing Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium theme-text mb-2">CUIT</label>
                  <input
                    type="text"
                    className="form-input w-full"
                    value={formData.billing_data.cuit}
                    onChange={(e) => setFormData({
                      ...formData,
                      billing_data: {...formData.billing_data, cuit: e.target.value}
                    })}
                    placeholder="XX-XXXXXXXX-X"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium theme-text mb-2">Email</label>
                  <input
                    type="email"
                    className="form-input w-full"
                    value={formData.billing_data.email}
                    onChange={(e) => setFormData({
                      ...formData,
                      billing_data: {...formData.billing_data, email: e.target.value}
                    })}
                    placeholder="client@email.com"
                  />
                </div>
              </div>
            </div>

            {/* Product Information */}
            <div className="border theme-border rounded-lg p-4">
              <h3 className="text-lg font-medium theme-text mb-4">Product Information</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium theme-text mb-2">Internal Coordinator</label>
                  <input
                    type="text"
                    className="form-input w-full"
                    value={formData.internal_coordinator}
                    onChange={(e) => setFormData({...formData, internal_coordinator: e.target.value})}
                    placeholder="Décor/Architect name"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium theme-text mb-2">Quantity</label>
                  <input
                    type="number"
                    min="1"
                    className="form-input w-full"
                    value={formData.quantity}
                    onChange={(e) => setFormData({...formData, quantity: e.target.value})}
                    required
                  />
                </div>
              </div>

              <div className="flex space-x-4 mb-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium theme-text mb-2">Item Description</label>
                  <input
                    type="text"
                    className="form-input w-full"
                    value={formData.item_description}
                    onChange={(e) => setFormData({...formData, item_description: e.target.value})}
                    placeholder="Product description"
                    required
                  />
                </div>
                <div className="flex items-end">
                  <button
                    type="button"
                    onClick={() => setIsInventoryModalOpen(true)}
                    className="btn-secondary"
                  >
                    Select from Inventory
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium theme-text mb-2">SKU / Product Code</label>
                <input
                  type="text"
                  className="form-input w-full"
                  value={formData.sku}
                  onChange={(e) => setFormData({...formData, sku: e.target.value})}
                  placeholder="Product SKU"
                />
              </div>
            </div>

            {/* Financial Information */}
            <div className="border theme-border rounded-lg p-4">
              <h3 className="text-lg font-medium theme-text mb-4">Financial Information</h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium theme-text mb-2">Sold Amount ARS</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-input w-full"
                    value={formData.sold_amount_ars}
                    onChange={(e) => setFormData({...formData, sold_amount_ars: e.target.value})}
                    placeholder="0.00"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium theme-text mb-2">Sold Amount USD</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-input w-full"
                    value={formData.sold_amount_usd}
                    onChange={(e) => setFormData({...formData, sold_amount_usd: e.target.value})}
                    placeholder="0.00"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium theme-text mb-2">Cost ARS</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-input w-full"
                    value={formData.cost_ars}
                    onChange={(e) => setFormData({...formData, cost_ars: e.target.value})}
                    placeholder="0.00"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium theme-text mb-2">Cost USD</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-input w-full"
                    value={formData.cost_usd}
                    onChange={(e) => setFormData({...formData, cost_usd: e.target.value})}
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium theme-text mb-2">Payment Method</label>
                <select
                  className="form-input w-full md:w-1/3"
                  value={formData.payment_method}
                  onChange={(e) => setFormData({...formData, payment_method: e.target.value})}
                  required
                >
                  {paymentMethods.map(method => (
                    <option key={method} value={method}>{method}</option>
                  ))}
                </select>
              </div>

              {/* Calculated Amounts Display */}
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-medium theme-text mb-3">Calculated Amounts</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="theme-text-secondary">Net Sale ARS:</span>
                    <p className="font-medium theme-text">{formatCurrency(calculatedAmounts.net_sale_ars, 'ARS')}</p>
                  </div>
                  <div>
                    <span className="theme-text-secondary">Net Sale USD:</span>
                    <p className="font-medium theme-text">{formatCurrency(calculatedAmounts.net_sale_usd, 'USD')}</p>
                  </div>
                  <div>
                    <span className="theme-text-secondary">Commission (2%):</span>
                    <p className="font-medium theme-text">
                      {formatCurrency(calculatedAmounts.commission_ars, 'ARS')} / {formatCurrency(calculatedAmounts.commission_usd, 'USD')}
                    </p>
                  </div>
                  <div>
                    <span className="theme-text-secondary">Profit ARS:</span>
                    <p className="font-medium text-green-600">{formatCurrency(calculatedAmounts.profit_ars, 'ARS')}</p>
                  </div>
                  <div>
                    <span className="theme-text-secondary">Profit USD:</span>
                    <p className="font-medium text-green-600">{formatCurrency(calculatedAmounts.profit_usd, 'USD')}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Comments */}
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Comments</label>
              <textarea
                className="form-input w-full"
                rows="3"
                value={formData.comments}
                onChange={(e) => setFormData({...formData, comments: e.target.value})}
                placeholder="Additional notes or comments"
              />
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="btn-primary flex-1 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Sale Entry'}
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

      {/* Inventory Selection Modal */}
      <InventoryModal
        isOpen={isInventoryModalOpen}
        onClose={() => setIsInventoryModalOpen(false)}
        onSelectItem={handleSelectItem}
      />
      
      {/* Provider Management Modal */}
      <ProviderModal
        isOpen={showProviderModal}
        onClose={() => setShowProviderModal(false)}
        onSubmit={handleCreateProvider}
        loading={isCreatingProvider}
      />
    </>
  );
};

// Main Shop Cash Component with Tabbed Interface
const ShopCash = () => {
  const [entries, setEntries] = useState([]);
  const [summary, setSummary] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [coordinatorData, setCoordinatorData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('sales'); // New state for tab management

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/shop-cash');
      setEntries(response.data);
      
      // Process data for charts
      const monthlyData = processMonthlyProfitData(response.data);
      const coordinatorProfitData = processCoordinatorData(response.data);
      
      setChartData(monthlyData);
      setCoordinatorData(coordinatorProfitData);
      
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
  }, []);

  useEffect(() => {
    if (activeTab === 'sales') {
      fetchData();
    }
  }, [activeTab, fetchData]);

  const processMonthlyProfitData = (entries) => {
    const monthlyMap = {};
    
    entries.forEach(entry => {
      const date = new Date(entry.date);
      const monthKey = format(date, 'MMM yyyy');
      
      if (!monthlyMap[monthKey]) {
        monthlyMap[monthKey] = {
          month: monthKey,
          profit_ars: 0,
          profit_usd: 0,
          sales_count: 0
        };
      }
      
      monthlyMap[monthKey].profit_ars += entry.profit_ars || 0;
      monthlyMap[monthKey].profit_usd += entry.profit_usd || 0;
      monthlyMap[monthKey].sales_count += 1;
    });
    
    return Object.values(monthlyMap).sort((a, b) => {
      return new Date(a.month) - new Date(b.month);
    });
  };

  const processCoordinatorData = (entries) => {
    const coordinatorMap = {};
    
    entries.forEach(entry => {
      const coordinator = entry.internal_coordinator || 'Unknown';
      
      if (!coordinatorMap[coordinator]) {
        coordinatorMap[coordinator] = {
          name: coordinator,
          profit_ars: 0,
          profit_usd: 0,
          sales_count: 0
        };
      }
      
      coordinatorMap[coordinator].profit_ars += entry.profit_ars || 0;
      coordinatorMap[coordinator].profit_usd += entry.profit_usd || 0;
      coordinatorMap[coordinator].sales_count += 1;
    });
    
    return Object.values(coordinatorMap).sort((a, b) => b.profit_ars - a.profit_ars);
  };

  const calculateSummary = (entries) => {
    return {
      total_sales: entries.length,
      total_revenue_ars: entries.reduce((sum, entry) => sum + (entry.sold_amount_ars || 0), 0),
      total_revenue_usd: entries.reduce((sum, entry) => sum + (entry.sold_amount_usd || 0), 0),
      total_profit_ars: entries.reduce((sum, entry) => sum + (entry.profit_ars || 0), 0),
      total_profit_usd: entries.reduce((sum, entry) => sum + (entry.profit_usd || 0), 0),
      total_commission_ars: entries.reduce((sum, entry) => sum + (entry.commission_ars || 0), 0),
      total_commission_usd: entries.reduce((sum, entry) => sum + (entry.commission_usd || 0), 0),
    };
  };

  const handleCreateEntry = async (formData) => {
    try {
      setIsSubmitting(true);
      await axios.post('/api/shop-cash', formData);
      setIsModalOpen(false);
      await fetchData();
    } catch (error) {
      console.error('Error creating entry:', error);
      setError('Failed to create entry. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatCurrency = (amount, currency) => {
    if (!amount) return '-';
    return `${currency} ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  };

  const getStatusBadge = (status) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    switch (status) {
      case 'Confirmed':
        return `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`;
      case 'Delivered':
        return `${baseClasses} bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200`;
      case 'Pending':
        return `${baseClasses} bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200`;
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
            <h1 className="text-3xl font-bold theme-text">Shop Cash</h1>
            <p className="theme-text-secondary">Retail sales and inventory management</p>
          </div>
          {activeTab === 'sales' && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="btn-primary"
            >
              Add New Sale
            </button>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="card mb-6">
          <div className="border-b theme-border">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('sales')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'sales'
                    ? 'border-teal-500 text-teal-600 dark:text-teal-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                Sales Management
              </button>
              <button
                onClick={() => setActiveTab('inventory')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'inventory'
                    ? 'border-teal-500 text-teal-600 dark:text-teal-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                Inventory Management
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'sales' ? (
          <>
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
                  <h3 className="text-sm font-medium theme-text-secondary">Total Sales</h3>
                  <p className="text-2xl font-bold theme-text">{summary.total_sales}</p>
                </div>
                <div className="card">
                  <h3 className="text-sm font-medium theme-text-secondary">Revenue ARS</h3>
                  <p className="text-2xl font-bold text-blue-600">{formatCurrency(summary.total_revenue_ars, 'ARS')}</p>
                </div>
                <div className="card">
                  <h3 className="text-sm font-medium theme-text-secondary">Profit ARS</h3>
                  <p className="text-2xl font-bold text-green-600">{formatCurrency(summary.total_profit_ars, 'ARS')}</p>
                </div>
                <div className="card">
                  <h3 className="text-sm font-medium theme-text-secondary">Commission ARS</h3>
                  <p className="text-2xl font-bold text-purple-600">{formatCurrency(summary.total_commission_ars, 'ARS')}</p>
                </div>
              </div>
            )}

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Monthly Profit Chart */}
              {chartData.length > 0 && (
                <div className="card">
                  <div className="border-b theme-border pb-4 mb-6">
                    <h2 className="text-xl font-semibold theme-text">Monthly Profit Trend (ARS)</h2>
                    <p className="text-sm theme-text-secondary">Track profit performance over time</p>
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
                          formatter={(value) => [`ARS ${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, 'Profit']}
                          labelStyle={{ color: '#374151' }}
                          contentStyle={{ 
                            backgroundColor: 'white', 
                            border: '1px solid #e5e7eb',
                            borderRadius: '0.5rem'
                          }}
                        />
                        <Bar 
                          dataKey="profit_ars" 
                          fill="#008080" 
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Coordinator Performance Chart */}
              {coordinatorData.length > 0 && (
                <div className="card">
                  <div className="border-b theme-border pb-4 mb-6">
                    <h2 className="text-xl font-semibold theme-text">Profit by Coordinator</h2>
                    <p className="text-sm theme-text-secondary">Performance comparison across coordinators</p>
                  </div>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={coordinatorData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="profit_ars"
                        >
                          {coordinatorData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={`hsl(${180 + (index * 45)}, 60%, 50%)`} />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(value) => [`ARS ${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, 'Profit']}
                          labelStyle={{ color: '#374151' }}
                          contentStyle={{ 
                            backgroundColor: 'white', 
                            border: '1px solid #e5e7eb',
                            borderRadius: '0.5rem'
                          }}
                        />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>

            {/* Sales Table */}
            <div className="card">
              <div className="border-b theme-border pb-4 mb-4">
                <h2 className="text-xl font-semibold theme-text">Sales Records</h2>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="table-header">
                      <th className="text-left p-4 font-medium theme-text">Date</th>
                      <th className="text-left p-4 font-medium theme-text">Client</th>
                      <th className="text-left p-4 font-medium theme-text">Item</th>
                      <th className="text-left p-4 font-medium theme-text">Coordinator</th>
                      <th className="text-right p-4 font-medium theme-text">Sold ARS</th>
                      <th className="text-right p-4 font-medium theme-text">Cost ARS</th>
                      <th className="text-right p-4 font-medium theme-text">Net Sale</th>
                      <th className="text-right p-4 font-medium theme-text">Profit</th>
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
                    ) : entries.length === 0 ? (
                      <tr>
                        <td colSpan="9" className="text-center py-12 theme-text-secondary">
                          No sales found. Create your first sale to get started.
                        </td>
                      </tr>
                    ) : (
                      entries.map((entry) => (
                        <tr key={entry._id} className="table-row">
                          <td className="p-4 theme-text">
                            {format(new Date(entry.date), 'dd/MM/yyyy')}
                          </td>
                          <td className="p-4 theme-text">{entry.client}</td>
                          <td className="p-4 theme-text">
                            <div>
                              <p className="font-medium">{entry.item_description}</p>
                              {entry.sku && <p className="text-xs theme-text-secondary">SKU: {entry.sku}</p>}
                            </div>
                          </td>
                          <td className="p-4 theme-text">{entry.internal_coordinator}</td>
                          <td className="p-4 theme-text text-right table-cell-numeric">
                            {formatCurrency(entry.sold_amount_ars, 'ARS')}
                          </td>
                          <td className="p-4 theme-text text-right table-cell-numeric">
                            {formatCurrency(entry.cost_ars, 'ARS')}
                          </td>
                          <td className="p-4 theme-text text-right table-cell-numeric">
                            {formatCurrency(entry.net_sale_ars, 'ARS')}
                          </td>
                          <td className="p-4 theme-text text-right table-cell-numeric font-medium text-green-600">
                            {formatCurrency(entry.profit_ars, 'ARS')}
                          </td>
                          <td className="p-4 text-center">
                            <span className={getStatusBadge(entry.status)}>
                              {entry.status || 'Pending'}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Sale Entry Modal */}
            <SaleEntryModal
              isOpen={isModalOpen}
              onClose={() => setIsModalOpen(false)}
              onSubmit={handleCreateEntry}
              loading={isSubmitting}
            />
          </>
        ) : (
          <InventoryManagement />
        )}
      </div>
    </div>
  );
};

// Inventory Management Component
const InventoryManagement = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    category: '',
    provider_name: '',
    stock_status: '',
    sort_by: 'provider_name', // Default sort by provider
    sort_order: 'asc'
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [isAddProductModalOpen, setIsAddProductModalOpen] = useState(false);
  const [isEditProductModalOpen, setIsEditProductModalOpen] = useState(false);
  const [isBulkImportModalOpen, setIsBulkImportModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [inventorySummary, setInventorySummary] = useState(null);
  const [error, setError] = useState('');

  const categories = ['Décor', 'Furniture', 'Lighting', 'Textiles', 'Accessories', 'Plants', 'Art', 'Tableware', 'Seasonal', 'Other'];
  const sortOptions = [
    { value: 'name', label: 'Name' },
    { value: 'sku', label: 'SKU' },
    { value: 'category', label: 'Category' },
    { value: 'provider_name', label: 'Provider' },
    { value: 'current_stock', label: 'Stock Level' },
    { value: 'total_sold', label: 'Most Sold' },
    { value: 'created_at', label: 'Date Added' }
  ];

  useEffect(() => {
    fetchProducts();
    fetchInventorySummary();
  }, [filters, fetchProducts, fetchInventorySummary]);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      if (searchTerm) params.append('search', searchTerm);

      const response = await axios.get(`/api/inventory/products?${params.toString()}`);
      setProducts(response.data);
      setError('');
    } catch (error) {
      console.error('Error fetching products:', error);
      setError('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  const fetchInventorySummary = async () => {
    try {
      const response = await axios.get('/api/inventory/summary');
      setInventorySummary(response.data);
    } catch (error) {
      console.error('Error fetching inventory summary:', error);
    }
  };

  const handleAddProduct = async (productData) => {
    try {
      await axios.post('/api/inventory/products', productData);
      setIsAddProductModalOpen(false);
      fetchProducts();
      fetchInventorySummary();
    } catch (error) {
      console.error('Error adding product:', error);
      setError('Failed to add product');
    }
  };

  const handleEditProduct = async (productData) => {
    try {
      await axios.put(`/api/inventory/products/${selectedProduct.id}`, productData);
      setIsEditProductModalOpen(false);
      setSelectedProduct(null);
      fetchProducts();
      fetchInventorySummary();
    } catch (error) {
      console.error('Error updating product:', error);
      setError('Failed to update product');
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      try {
        await axios.delete(`/api/inventory/products/${productId}`);
        fetchProducts();
        fetchInventorySummary();
      } catch (error) {
        console.error('Error deleting product:', error);
        setError('Failed to delete product');
      }
    }
  };

  const formatCurrency = (amount, currency) => {
    if (!amount) return '-';
    return `${currency} ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  };

  const getStockStatusBadge = (product) => {
    const stock = product.current_stock;
    const threshold = product.min_stock_threshold;
    
    if (stock === 0) {
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">Out of Stock</span>;
    } else if (stock <= threshold) {
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">Low Stock</span>;
    } else {
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">In Stock</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      {inventorySummary && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="card">
            <h3 className="text-sm font-medium theme-text-secondary">Total Products</h3>
            <p className="text-2xl font-bold theme-text">{inventorySummary.total_products}</p>
          </div>
          <div className="card">
            <h3 className="text-sm font-medium theme-text-secondary">Low Stock Items</h3>
            <p className="text-2xl font-bold text-yellow-600">{inventorySummary.low_stock_items}</p>
          </div>
          <div className="card">
            <h3 className="text-sm font-medium theme-text-secondary">Out of Stock</h3>
            <p className="text-2xl font-bold text-red-600">{inventorySummary.out_of_stock_items}</p>
          </div>
          <div className="card">
            <h3 className="text-sm font-medium theme-text-secondary">Stock Value ARS</h3>
            <p className="text-2xl font-bold text-blue-600">{formatCurrency(inventorySummary.total_stock_value_ars, 'ARS')}</p>
          </div>
          <div className="card">
            <h3 className="text-sm font-medium theme-text-secondary">Stock Value USD</h3>
            <p className="text-2xl font-bold text-green-600">{formatCurrency(inventorySummary.total_stock_value_usd, 'USD')}</p>
          </div>
        </div>
      )}

      {/* Controls and Filters */}
      <div className="card">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
          <h2 className="text-xl font-semibold theme-text">Inventory Management</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setIsBulkImportModalOpen(true)}
              className="btn-secondary"
            >
              Bulk Import CSV
            </button>
            <button
              onClick={() => setIsAddProductModalOpen(true)}
              className="btn-primary"
            >
              Add Product
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium theme-text mb-2">Search</label>
            <input
              type="text"
              className="form-input w-full"
              placeholder="Search products..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && fetchProducts()}
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

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Provider</label>
            <input
              type="text"
              className="form-input w-full"
              placeholder="Provider name..."
              value={filters.provider_name}
              onChange={(e) => setFilters({...filters, provider_name: e.target.value})}
            />
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Stock Status</label>
            <select
              className="form-input w-full"
              value={filters.stock_status}
              onChange={(e) => setFilters({...filters, stock_status: e.target.value})}
            >
              <option value="">All Status</option>
              <option value="IN_STOCK">In Stock</option>
              <option value="LOW_STOCK">Low Stock</option>
              <option value="OUT_OF_STOCK">Out of Stock</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Sort By</label>
            <select
              className="form-input w-full"
              value={filters.sort_by}
              onChange={(e) => setFilters({...filters, sort_by: e.target.value})}
            >
              {sortOptions.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Order</label>
            <select
              className="form-input w-full"
              value={filters.sort_order}
              onChange={(e) => setFilters({...filters, sort_order: e.target.value})}
            >
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </div>
        </div>

        {/* Products Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="table-header">
                <th className="text-left p-4 font-medium theme-text">SKU</th>
                <th className="text-left p-4 font-medium theme-text">Product Name</th>
                <th className="text-left p-4 font-medium theme-text">Category</th>
                <th className="text-left p-4 font-medium theme-text">Provider</th>
                <th className="text-center p-4 font-medium theme-text">Stock</th>
                <th className="text-center p-4 font-medium theme-text">Status</th>
                <th className="text-right p-4 font-medium theme-text">Cost ARS</th>
                <th className="text-right p-4 font-medium theme-text">Price ARS</th>
                <th className="text-center p-4 font-medium theme-text">Total Sold</th>
                <th className="text-center p-4 font-medium theme-text">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="10" className="p-0">
                    <TableSkeleton />
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan="10" className="text-center py-12 theme-text-secondary">
                    No products found. Add your first product to get started.
                  </td>
                </tr>
              ) : (
                products.map((product) => (
                  <tr key={product.id} className="table-row">
                    <td className="p-4 theme-text font-mono">{product.sku}</td>
                    <td className="p-4 theme-text">
                      <div>
                        <p className="font-medium">{product.name}</p>
                        {product.description && (
                          <p className="text-xs theme-text-secondary truncate max-w-xs">{product.description}</p>
                        )}
                      </div>
                    </td>
                    <td className="p-4 theme-text">{product.category}</td>
                    <td className="p-4 theme-text">{product.provider_name || '-'}</td>
                    <td className="p-4 text-center theme-text font-medium">{product.current_stock}</td>
                    <td className="p-4 text-center">{getStockStatusBadge(product)}</td>
                    <td className="p-4 theme-text text-right table-cell-numeric">
                      {formatCurrency(product.cost_ars, 'ARS')}
                    </td>
                    <td className="p-4 theme-text text-right table-cell-numeric">
                      {formatCurrency(product.selling_price_ars, 'ARS')}
                    </td>
                    <td className="p-4 text-center theme-text font-medium">{product.total_sold || 0}</td>
                    <td className="p-4 text-center">
                      <div className="flex justify-center space-x-1">
                        <button
                          onClick={() => {
                            setSelectedProduct(product);
                            setIsEditProductModalOpen(true);
                          }}
                          className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs hover:bg-blue-200"
                          title="Edit Product"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteProduct(product.id)}
                          className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs hover:bg-red-200"
                          title="Delete Product"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modals */}
      <ProductModal
        isOpen={isAddProductModalOpen}
        onClose={() => setIsAddProductModalOpen(false)}
        onSubmit={handleAddProduct}
        title="Add New Product"
      />

      <ProductModal
        isOpen={isEditProductModalOpen}
        onClose={() => {
          setIsEditProductModalOpen(false);
          setSelectedProduct(null);
        }}
        onSubmit={handleEditProduct}
        product={selectedProduct}
        title="Edit Product"
      />

      <BulkImportModal
        isOpen={isBulkImportModalOpen}
        onClose={() => setIsBulkImportModalOpen(false)}
        onSuccess={() => {
          fetchProducts();
          fetchInventorySummary();
        }}
      />
    </div>
  );
};

// Product Modal Component for Add/Edit
const ProductModal = ({ isOpen, onClose, onSubmit, product = null, title }) => {
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    description: '',
    category: 'Décor',
    provider_name: '',
    cost_ars: '',
    cost_usd: '',
    selling_price_ars: '',
    selling_price_usd: '',
    current_stock: '0',
    min_stock_threshold: '5',
    location: '',
    condition: 'New',
    notes: ''
  });
  const [loading, setLoading] = useState(false);

  const categories = ['Décor', 'Furniture', 'Lighting', 'Textiles', 'Accessories', 'Plants', 'Art', 'Tableware', 'Seasonal', 'Other'];
  const conditions = ['New', 'Excellent', 'Good', 'Fair', 'Poor'];

  useEffect(() => {
    if (product) {
      setFormData({
        sku: product.sku || '',
        name: product.name || '',
        description: product.description || '',
        category: product.category || 'Décor',
        provider_name: product.provider_name || '',
        cost_ars: product.cost_ars?.toString() || '',
        cost_usd: product.cost_usd?.toString() || '',
        selling_price_ars: product.selling_price_ars?.toString() || '',
        selling_price_usd: product.selling_price_usd?.toString() || '',
        current_stock: product.current_stock?.toString() || '0',
        min_stock_threshold: product.min_stock_threshold?.toString() || '5',
        location: product.location || '',
        condition: product.condition || 'New',
        notes: product.notes || ''
      });
    } else {
      setFormData({
        sku: '',
        name: '',
        description: '',
        category: 'Décor',
        provider_name: '',
        cost_ars: '',
        cost_usd: '',
        selling_price_ars: '',
        selling_price_usd: '',
        current_stock: '0',
        min_stock_threshold: '5',
        location: '',
        condition: 'New',
        notes: ''
      });
    }
  }, [product, isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const submitData = {
        ...formData,
        cost_ars: formData.cost_ars ? parseFloat(formData.cost_ars) : null,
        cost_usd: formData.cost_usd ? parseFloat(formData.cost_usd) : null,
        selling_price_ars: formData.selling_price_ars ? parseFloat(formData.selling_price_ars) : null,
        selling_price_usd: formData.selling_price_usd ? parseFloat(formData.selling_price_usd) : null,
        current_stock: parseInt(formData.current_stock) || 0,
        min_stock_threshold: parseInt(formData.min_stock_threshold) || 5
      };

      await onSubmit(submitData);
    } catch (error) {
      console.error('Error submitting product:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="card max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold theme-text">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">SKU *</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.sku}
                onChange={(e) => setFormData({...formData, sku: e.target.value})}
                placeholder="PROD-001"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium theme-text mb-2">Product Name *</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Product name"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Description</label>
            <textarea
              className="form-input w-full"
              rows="3"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Product description"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Category *</label>
              <select
                className="form-input w-full"
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                required
              >
                {categories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium theme-text mb-2">Provider</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.provider_name}
                onChange={(e) => setFormData({...formData, provider_name: e.target.value})}
                placeholder="Provider name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium theme-text mb-2">Condition</label>
              <select
                className="form-input w-full"
                value={formData.condition}
                onChange={(e) => setFormData({...formData, condition: e.target.value})}
              >
                {conditions.map(condition => (
                  <option key={condition} value={condition}>{condition}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Pricing */}
          <div className="border theme-border rounded-lg p-4">
            <h3 className="text-lg font-medium theme-text mb-4">Pricing</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Cost ARS</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.cost_ars}
                  onChange={(e) => setFormData({...formData, cost_ars: e.target.value})}
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium theme-text mb-2">Cost USD</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.cost_usd}
                  onChange={(e) => setFormData({...formData, cost_usd: e.target.value})}
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium theme-text mb-2">Selling Price ARS</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.selling_price_ars}
                  onChange={(e) => setFormData({...formData, selling_price_ars: e.target.value})}
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium theme-text mb-2">Selling Price USD</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.selling_price_usd}
                  onChange={(e) => setFormData({...formData, selling_price_usd: e.target.value})}
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>

          {/* Stock Management */}
          <div className="border theme-border rounded-lg p-4">
            <h3 className="text-lg font-medium theme-text mb-4">Stock Management</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Current Stock</label>
                <input
                  type="number"
                  min="0"
                  className="form-input w-full"
                  value={formData.current_stock}
                  onChange={(e) => setFormData({...formData, current_stock: e.target.value})}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium theme-text mb-2">Min Stock Threshold</label>
                <input
                  type="number"
                  min="0"
                  className="form-input w-full"
                  value={formData.min_stock_threshold}
                  onChange={(e) => setFormData({...formData, min_stock_threshold: e.target.value})}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium theme-text mb-2">Location</label>
                <input
                  type="text"
                  className="form-input w-full"
                  value={formData.location}
                  onChange={(e) => setFormData({...formData, location: e.target.value})}
                  placeholder="Warehouse A - Shelf 1"
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
              placeholder="Additional notes"
            />
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex-1 disabled:opacity-50"
            >
              {loading ? 'Saving...' : (product ? 'Update Product' : 'Create Product')}
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

// Bulk Import Modal Component
const BulkImportModal = ({ isOpen, onClose, onSuccess }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [updateExisting, setUpdateExisting] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'text/csv') {
      setFile(selectedFile);
      setResults(null);
    } else {
      alert('Please select a valid CSV file');
      e.target.value = '';
    }
  };

  const handleImport = async () => {
    if (!file) {
      alert('Please select a CSV file');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('update_existing', updateExisting);

    try {
      const response = await axios.post('/api/inventory/bulk-import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        params: {
          update_existing: updateExisting
        }
      });

      setResults(response.data);
      if (response.data.successful_imports > 0) {
        onSuccess();
      }
    } catch (error) {
      console.error('Error importing products:', error);
      alert('Failed to import products. Please check your file format.');
    } finally {
      setLoading(false);
    }
  };

  const downloadTemplate = () => {
    const csvHeaders = [
      'sku', 'name', 'description', 'category', 'provider_name',
      'cost_ars', 'cost_usd', 'selling_price_ars', 'selling_price_usd',
      'current_stock', 'min_stock_threshold', 'location', 'condition', 'notes'
    ];
    
    const sampleData = [
      'VASE-001', 'Decorative Ceramic Vase', 'Beautiful ceramic vase for events', 'Décor', 'Ceramicas SA',
      '2500', '15', '4000', '25', '10', '3', 'Warehouse A - Shelf 1', 'New', 'Handle with care'
    ];

    const csvContent = [
      csvHeaders.join(','),
      sampleData.join(',')
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'inventory_template.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const resetModal = () => {
    setFile(null);
    setResults(null);
    setUpdateExisting(false);
  };

  const handleClose = () => {
    resetModal();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="card max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold theme-text">Bulk Import Products</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {!results ? (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium theme-text mb-3">Import Instructions</h3>
              <ul className="list-disc list-inside text-sm theme-text-secondary space-y-1">
                <li>Upload a CSV file with product information</li>
                <li>The CSV must include headers: sku, name, category, etc.</li>
                <li>SKU field is required and must be unique</li>
                <li>Category must be one of: Décor, Furniture, Lighting, Textiles, Accessories, Plants, Art, Tableware, Seasonal, Other</li>
                <li>Numeric fields should contain valid numbers (costs, prices, stock)</li>
              </ul>
            </div>

            <div>
              <button
                onClick={downloadTemplate}
                className="btn-secondary mb-4"
              >
                Download CSV Template
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium theme-text mb-2">Select CSV File</label>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="form-input w-full"
              />
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="update_existing"
                checked={updateExisting}
                onChange={(e) => setUpdateExisting(e.target.checked)}
                className="form-checkbox"
              />
              <label htmlFor="update_existing" className="text-sm theme-text">
                Update existing products (if SKU matches)
              </label>
            </div>

            <div className="flex space-x-4">
              <button
                onClick={handleImport}
                disabled={!file || loading}
                className="btn-primary flex-1 disabled:opacity-50"
              >
                {loading ? 'Importing...' : 'Import Products'}
              </button>
              <button
                onClick={handleClose}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <h3 className="text-lg font-medium theme-text">Import Results</h3>
            
            <div className="grid grid-cols-3 gap-4">
              <div className="card bg-blue-50 dark:bg-blue-900/20">
                <h4 className="text-sm font-medium text-blue-700 dark:text-blue-300">Total Rows</h4>
                <p className="text-2xl font-bold text-blue-800 dark:text-blue-200">{results.total_rows}</p>
              </div>
              <div className="card bg-green-50 dark:bg-green-900/20">
                <h4 className="text-sm font-medium text-green-700 dark:text-green-300">Successful</h4>
                <p className="text-2xl font-bold text-green-800 dark:text-green-200">{results.successful_imports}</p>
              </div>
              <div className="card bg-red-50 dark:bg-red-900/20">
                <h4 className="text-sm font-medium text-red-700 dark:text-red-300">Failed</h4>
                <p className="text-2xl font-bold text-red-800 dark:text-red-200">{results.failed_imports}</p>
              </div>
            </div>

            {results.created_products.length > 0 && (
              <div>
                <h4 className="font-medium theme-text mb-2">Created Products ({results.created_products.length})</h4>
                <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded max-h-32 overflow-y-auto">
                  <p className="text-sm text-green-700 dark:text-green-300">
                    {results.created_products.join(', ')}
                  </p>
                </div>
              </div>
            )}

            {results.updated_products.length > 0 && (
              <div>
                <h4 className="font-medium theme-text mb-2">Updated Products ({results.updated_products.length})</h4>
                <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded max-h-32 overflow-y-auto">
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    {results.updated_products.join(', ')}
                  </p>
                </div>
              </div>
            )}

            {results.errors.length > 0 && (
              <div>
                <h4 className="font-medium theme-text mb-2">Errors ({results.errors.length})</h4>
                <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded max-h-32 overflow-y-auto">
                  {results.errors.map((error, index) => (
                    <p key={index} className="text-sm text-red-700 dark:text-red-300">
                      Row {error.row} (SKU: {error.sku}): {error.error}
                    </p>
                  ))}
                </div>
              </div>
            )}

            <div className="flex space-x-4">
              <button
                onClick={() => {
                  resetModal();
                }}
                className="btn-secondary flex-1"
              >
                Import More
              </button>
              <button
                onClick={handleClose}
                className="btn-primary flex-1"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShopCash;