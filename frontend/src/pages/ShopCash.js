import React, { useState, useEffect } from 'react';
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

// Inventory Item Selection Modal
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
  }, [products, searchTerm, categoryFilter]);

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

  const filterProducts = () => {
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
  };

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
                <input
                  type="text"
                  className="form-input w-full"
                  value={formData.provider}
                  onChange={(e) => setFormData({...formData, provider: e.target.value})}
                  placeholder="Provider name"
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
    </>
  );
};

// Main Shop Cash Component
const ShopCash = () => {
  const [entries, setEntries] = useState([]);
  const [summary, setSummary] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [coordinatorData, setCoordinatorData] = useState([]);
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
  };

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
          <button
            onClick={() => setIsModalOpen(true)}
            className="btn-primary"
          >
            Add New Sale
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
      </div>
    </div>
  );
};

export default ShopCash;