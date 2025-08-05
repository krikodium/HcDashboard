import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line } from 'recharts';

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

// Deco Project Header Component (similar to EventHeader)
const DecoProjectHeader = ({ project }) => {
  if (!project) return null;

  return (
    <div className="card mb-6">
      <div className="border-b theme-border pb-4 mb-4">
        <h2 className="text-xl font-semibold theme-text">Project Details</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div>
          <label className="block text-sm font-medium theme-text-secondary mb-1">Project Name</label>
          <p className="theme-text font-semibold text-lg">{project.name}</p>
        </div>
        
        <div>
          <label className="block text-sm font-medium theme-text-secondary mb-1">Project Type</label>
          <p className="theme-text font-medium">{project.project_type}</p>
        </div>
        
        <div>
          <label className="block text-sm font-medium theme-text-secondary mb-1">Client Name</label>
          <p className="theme-text font-medium">{project.client_name || 'Not specified'}</p>
        </div>
        
        <div>
          <label className="block text-sm font-medium theme-text-secondary mb-1">Status</label>
          <span className={`status-badge ${
            project.status === 'Active' ? 'status-success' : 
            project.status === 'Completed' ? 'status-info' : 
            'status-warning'
          }`}>
            {project.status}
          </span>
        </div>
        
        {project.start_date && (
          <div>
            <label className="block text-sm font-medium theme-text-secondary mb-1">Start Date</label>
            <p className="theme-text font-medium">{format(new Date(project.start_date), 'dd/MM/yyyy')}</p>
          </div>
        )}
        
        {project.location && (
          <div>
            <label className="block text-sm font-medium theme-text-secondary mb-1">Location</label>
            <p className="theme-text font-medium">{project.location}</p>
          </div>
        )}
        
        <div>
          <label className="block text-sm font-medium theme-text-secondary mb-1">Total Movements</label>
          <p className="theme-text font-medium">{project.movements_count || 0}</p>
        </div>
        
        {project.description && (
          <div className="col-span-full">
            <label className="block text-sm font-medium theme-text-secondary mb-1">Description</label>
            <p className="theme-text">{project.description}</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Financial Status Panel (similar to Events Cash payment status)
const FinancialStatusPanel = ({ project, movements }) => {
  if (!project) return null;

  const totalIncomeUSD = movements.reduce((sum, m) => sum + (m.income_usd || 0), 0);
  const totalExpenseUSD = movements.reduce((sum, m) => sum + (m.expense_usd || 0), 0);
  const totalIncomeARS = movements.reduce((sum, m) => sum + (m.income_ars || 0), 0);
  const totalExpenseARS = movements.reduce((sum, m) => sum + (m.expense_ars || 0), 0);
  
  const balanceUSD = totalIncomeUSD - totalExpenseUSD;
  const balanceARS = totalIncomeARS - totalExpenseARS;
  
  const budgetUtilizationUSD = project.budget_usd ? (totalExpenseUSD / project.budget_usd) * 100 : 0;
  const budgetUtilizationARS = project.budget_ars ? (totalExpenseARS / project.budget_ars) * 100 : 0;

  return (
    <div className="card mb-6">
      <div className="border-b theme-border pb-4 mb-4">
        <h2 className="text-xl font-semibold theme-text">Financial Status</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* USD Section */}
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-blue-600 dark:text-blue-400 mb-2">USD Financial Summary</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm theme-text-secondary">Total Income:</span>
              <span className="font-semibold text-green-600">${totalIncomeUSD.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm theme-text-secondary">Total Expense:</span>
              <span className="font-semibold text-red-600">${totalExpenseUSD.toFixed(2)}</span>
            </div>
            <div className="flex justify-between border-t pt-2">
              <span className="text-sm font-medium theme-text">Balance:</span>
              <span className={`font-bold ${balanceUSD >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ${balanceUSD.toFixed(2)}
              </span>
            </div>
            {project.budget_usd && (
              <div className="flex justify-between">
                <span className="text-sm theme-text-secondary">Budget Used:</span>
                <span className={`font-medium ${budgetUtilizationUSD > 100 ? 'text-red-600' : 'text-blue-600'}`}>
                  {budgetUtilizationUSD.toFixed(1)}%
                </span>
              </div>
            )}
          </div>
        </div>

        {/* ARS Section */}
        <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-green-600 dark:text-green-400 mb-2">ARS Financial Summary</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm theme-text-secondary">Total Income:</span>
              <span className="font-semibold text-green-600">AR$ {totalIncomeARS.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm theme-text-secondary">Total Expense:</span>
              <span className="font-semibold text-red-600">AR$ {totalExpenseARS.toFixed(2)}</span>
            </div>
            <div className="flex justify-between border-t pt-2">
              <span className="text-sm font-medium theme-text">Balance:</span>
              <span className={`font-bold ${balanceARS >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                AR$ {balanceARS.toFixed(2)}
              </span>
            </div>
            {project.budget_ars && (
              <div className="flex justify-between">
                <span className="text-sm theme-text-secondary">Budget Used:</span>
                <span className={`font-medium ${budgetUtilizationARS > 100 ? 'text-red-600' : 'text-blue-600'}`}>
                  {budgetUtilizationARS.toFixed(1)}%
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Project Health Indicators */}
        <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-purple-600 dark:text-purple-400 mb-2">Project Health</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm theme-text-secondary">Active Days:</span>
              <span className="font-medium theme-text">
                {project.start_date ? Math.ceil((new Date() - new Date(project.start_date)) / (1000 * 60 * 60 * 24)) : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm theme-text-secondary">Movements:</span>
              <span className="font-medium theme-text">{movements.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm theme-text-secondary">Avg per Movement:</span>
              <span className="font-medium theme-text">
                ${movements.length > 0 ? (totalExpenseUSD / movements.length).toFixed(2) : '0.00'}
              </span>
            </div>
          </div>
        </div>

        {/* Budget Status */}
        {(project.budget_usd || project.budget_ars) && (
          <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-orange-600 dark:text-orange-400 mb-2">Budget Status</h3>
            <div className="space-y-2">
              {project.budget_usd && (
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm theme-text-secondary">USD Budget:</span>
                    <span className="font-medium theme-text">${project.budget_usd.toFixed(2)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${budgetUtilizationUSD > 100 ? 'bg-red-500' : budgetUtilizationUSD > 80 ? 'bg-yellow-500' : 'bg-green-500'}`}
                      style={{ width: `${Math.min(budgetUtilizationUSD, 100)}%` }}
                    ></div>
                  </div>
                </div>
              )}
              {project.budget_ars && (
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm theme-text-secondary">ARS Budget:</span>
                    <span className="font-medium theme-text">AR$ {project.budget_ars.toFixed(2)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${budgetUtilizationARS > 100 ? 'bg-red-500' : budgetUtilizationARS > 80 ? 'bg-yellow-500' : 'bg-green-500'}`}
                      style={{ width: `${Math.min(budgetUtilizationARS, 100)}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Movement Entry Modal
const MovementEntryModal = ({ isOpen, onClose, onSubmit, loading, selectedProject }) => {
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    description: '',
    income_usd: '',
    expense_usd: '',
    income_ars: '',
    expense_ars: '',
    supplier: '',
    reference_number: '',
    notes: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      project_name: selectedProject?.name,
      income_usd: formData.income_usd ? parseFloat(formData.income_usd) : null,
      expense_usd: formData.expense_usd ? parseFloat(formData.expense_usd) : null,
      income_ars: formData.income_ars ? parseFloat(formData.income_ars) : null,
      expense_ars: formData.expense_ars ? parseFloat(formData.expense_ars) : null,
    };
    onSubmit(submitData);
  };

  const resetForm = () => {
    setFormData({
      date: new Date().toISOString().split('T')[0],
      description: '',
      income_usd: '',
      expense_usd: '',
      income_ars: '',
      expense_ars: '',
      supplier: '',
      reference_number: '',
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
          <h2 className="text-2xl font-bold theme-text">New Movement Entry</h2>
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
              <label className="block text-sm font-medium theme-text mb-2">Project</label>
              <input
                type="text"
                className="form-input w-full bg-gray-100 dark:bg-gray-700"
                value={selectedProject?.name || ''}
                disabled
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
              placeholder="Movement description"
              required
            />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Supplier</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.supplier}
                onChange={(e) => setFormData({...formData, supplier: e.target.value})}
                placeholder="Supplier name"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Reference Number</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.reference_number}
                onChange={(e) => setFormData({...formData, reference_number: e.target.value})}
                placeholder="Reference/Invoice number"
              />
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
              {loading ? 'Creating...' : 'Create Movement'}
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

// Profits and Fees Management Tab Component
const ProfitsFeesTab = ({ selectedProject, onUpdateProject }) => {
  const [formData, setFormData] = useState({
    profit_percentage: '',
    fee_percentage: '',
    profit_amount_usd: '',
    profit_amount_ars: '',
    fee_amount_usd: '',
    fee_amount_ars: '',
    profit_notes: '',
    fee_notes: ''
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedProject) {
      setFormData({
        profit_percentage: selectedProject.profit_percentage || '',
        fee_percentage: selectedProject.fee_percentage || '',
        profit_amount_usd: selectedProject.profit_amount_usd || '',
        profit_amount_ars: selectedProject.profit_amount_ars || '',
        fee_amount_usd: selectedProject.fee_amount_usd || '',
        fee_amount_ars: selectedProject.fee_amount_ars || '',
        profit_notes: selectedProject.profit_notes || '',
        fee_notes: selectedProject.fee_notes || ''
      });
    }
  }, [selectedProject]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedProject) return;

    try {
      setLoading(true);
      const updateData = {
        profit_percentage: formData.profit_percentage ? parseFloat(formData.profit_percentage) : null,
        fee_percentage: formData.fee_percentage ? parseFloat(formData.fee_percentage) : null,
        profit_amount_usd: formData.profit_amount_usd ? parseFloat(formData.profit_amount_usd) : null,
        profit_amount_ars: formData.profit_amount_ars ? parseFloat(formData.profit_amount_ars) : null,
        fee_amount_usd: formData.fee_amount_usd ? parseFloat(formData.fee_amount_usd) : null,
        fee_amount_ars: formData.fee_amount_ars ? parseFloat(formData.fee_amount_ars) : null,
        profit_notes: formData.profit_notes,
        fee_notes: formData.fee_notes
      };

      await axios.patch(`/api/projects/${selectedProject.id}`, updateData);
      onUpdateProject();
    } catch (error) {
      console.error('Error updating profits and fees:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!selectedProject) {
    return (
      <div className="text-center py-12">
        <p className="theme-text-secondary">Select a project to manage profits and fees</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-xl font-semibold theme-text mb-6">Profits & Fees Management</h3>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Profit Section */}
          <div className="bg-green-50 dark:bg-green-900/20 p-6 rounded-lg">
            <h4 className="text-lg font-medium text-green-700 dark:text-green-300 mb-4">Profit Configuration</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Profit Percentage (%)</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.profit_percentage}
                  onChange={(e) => setFormData({...formData, profit_percentage: e.target.value})}
                  placeholder="15.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Fixed Profit USD</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.profit_amount_usd}
                  onChange={(e) => setFormData({...formData, profit_amount_usd: e.target.value})}
                  placeholder="1000.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Fixed Profit ARS</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.profit_amount_ars}
                  onChange={(e) => setFormData({...formData, profit_amount_ars: e.target.value})}
                  placeholder="50000.00"
                />
              </div>
            </div>
            
            <div className="mt-4">
              <label className="block text-sm font-medium theme-text mb-2">Profit Notes</label>
              <textarea
                className="form-input w-full"
                rows="3"
                value={formData.profit_notes}
                onChange={(e) => setFormData({...formData, profit_notes: e.target.value})}
                placeholder="Additional notes about profit structure..."
              />
            </div>
          </div>

          {/* Fees Section */}
          <div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-lg">
            <h4 className="text-lg font-medium text-blue-700 dark:text-blue-300 mb-4">Fee Configuration</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Fee Percentage (%)</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.fee_percentage}
                  onChange={(e) => setFormData({...formData, fee_percentage: e.target.value})}
                  placeholder="10.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Fixed Fee USD</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.fee_amount_usd}
                  onChange={(e) => setFormData({...formData, fee_amount_usd: e.target.value})}
                  placeholder="500.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium theme-text mb-2">Fixed Fee ARS</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input w-full"
                  value={formData.fee_amount_ars}
                  onChange={(e) => setFormData({...formData, fee_amount_ars: e.target.value})}
                  placeholder="25000.00"
                />
              </div>
            </div>
            
            <div className="mt-4">
              <label className="block text-sm font-medium theme-text mb-2">Fee Notes</label>
              <textarea
                className="form-input w-full"
                rows="3"
                value={formData.fee_notes}
                onChange={(e) => setFormData({...formData, fee_notes: e.target.value})}
                placeholder="Additional notes about fee structure..."
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary disabled:opacity-50"
            >
              {loading ? 'Updating...' : 'Update Profits & Fees'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main Deco Movements Component with Tabbed Interface
const DecoMovements = () => {
  const [projects, setProjects] = useState([]);
  const [movements, setMovements] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [isMovementModalOpen, setIsMovementModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      fetchMovements();
    }
  }, [selectedProject]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/projects?project_type=Deco');
      setProjects(response.data);
      if (response.data.length > 0 && !selectedProject) {
        setSelectedProject(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching projects:', error);
      setError('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const fetchMovements = async () => {
    if (!selectedProject) return;
    
    try {
      const response = await axios.get(`/api/deco-movements?project=${encodeURIComponent(selectedProject.name)}`);
      setMovements(response.data);
    } catch (error) {
      console.error('Error fetching movements:', error);
      setError('Failed to load movements');
    }
  };

  const handleCreateMovement = async (formData) => {
    try {
      setIsSubmitting(true);
      await axios.post('/api/deco-movements', formData);
      setIsMovementModalOpen(false);
      await fetchMovements();
      await fetchProjects(); // Refresh project data
    } catch (error) {
      console.error('Error creating movement:', error);
      setError('Failed to create movement');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateProject = async () => {
    await fetchProjects();
    if (selectedProject) {
      const updatedProject = projects.find(p => p.id === selectedProject.id);
      if (updatedProject) {
        setSelectedProject(updatedProject);
      }
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: 'chart-bar' },
    { id: 'movements', name: 'Movements', icon: 'list' },
    { id: 'profits-fees', name: 'Profits & Fees', icon: 'cash' },
    { id: 'analytics', name: 'Analytics', icon: 'trending-up' }
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
            <h1 className="text-3xl font-bold theme-text">Deco Movements</h1>
            <p className="theme-text-secondary">Project management and financial tracking</p>
          </div>
          <div className="flex space-x-4">
            <select
              className="form-input"
              value={selectedProject?.id || ''}
              onChange={(e) => {
                const project = projects.find(p => p.id === e.target.value);
                setSelectedProject(project);
              }}
            >
              <option value="">Select Project</option>
              {projects.map(project => (
                <option key={project.id} value={project.id}>{project.name}</option>
              ))}
            </select>
            {selectedProject && (
              <button
                onClick={() => setIsMovementModalOpen(true)}
                className="btn-primary"
              >
                Add Movement
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

        {selectedProject ? (
          <>
            {/* Project Header */}
            <DecoProjectHeader project={selectedProject} />

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
                <FinancialStatusPanel project={selectedProject} movements={movements} />
                
                {movements.length > 0 && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Recent Movements */}
                    <div className="card">
                      <h3 className="text-lg font-semibold theme-text mb-4">Recent Movements</h3>
                      <div className="space-y-3">
                        {movements.slice(0, 5).map((movement) => (
                          <div key={movement.id} className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                            <div>
                              <p className="font-medium theme-text">{movement.description}</p>
                              <p className="text-sm theme-text-secondary">{format(new Date(movement.date), 'dd/MM/yyyy')}</p>
                            </div>
                            <div className="text-right">
                              {movement.income_usd && (
                                <p className="text-green-600 font-medium">+${movement.income_usd}</p>
                              )}
                              {movement.expense_usd && (
                                <p className="text-red-600 font-medium">-${movement.expense_usd}</p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="card">
                      <h3 className="text-lg font-semibold theme-text mb-4">Quick Statistics</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center">
                          <p className="text-2xl font-bold text-green-600">{movements.filter(m => m.income_usd > 0).length}</p>
                          <p className="text-sm theme-text-secondary">Income Entries</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-red-600">{movements.filter(m => m.expense_usd > 0).length}</p>
                          <p className="text-sm theme-text-secondary">Expense Entries</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold theme-text">{new Set(movements.map(m => m.supplier)).size}</p>
                          <p className="text-sm theme-text-secondary">Suppliers</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold theme-text">
                            ${movements.length > 0 ? (movements.reduce((sum, m) => sum + (m.expense_usd || 0), 0) / movements.filter(m => m.expense_usd > 0).length).toFixed(0) : '0'}
                          </p>
                          <p className="text-sm theme-text-secondary">Avg Expense</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'movements' && (
              <div className="space-y-6">
                {/* Movements Table */}
                <div className="card">
                  <div className="table-container">
                    <table className="min-w-full">
                      <thead className="table-header">
                        <tr>
                          <th className="table-header-cell">Date</th>
                          <th className="table-header-cell">Description</th>
                          <th className="table-header-cell">Supplier</th>
                          <th className="table-header-cell">Income USD</th>
                          <th className="table-header-cell">Expense USD</th>
                          <th className="table-header-cell">Income ARS</th>
                          <th className="table-header-cell">Expense ARS</th>
                          <th className="table-header-cell">Reference</th>
                        </tr>
                      </thead>
                      <tbody>
                        {movements.map((movement) => (
                          <tr key={movement.id} className="table-row">
                            <td className="table-cell font-medium">
                              {format(new Date(movement.date), 'dd/MM/yyyy')}
                            </td>
                            <td className="table-cell">
                              <div>
                                <p className="font-medium theme-text">{movement.description}</p>
                                {movement.notes && (
                                  <p className="text-sm theme-text-secondary">{movement.notes}</p>
                                )}
                              </div>
                            </td>
                            <td className="table-cell theme-text-secondary">
                              {movement.supplier || '-'}
                            </td>
                            <td className="table-cell">
                              <span className="text-green-600 font-medium">
                                {movement.income_usd ? `$${movement.income_usd.toFixed(2)}` : '-'}
                              </span>
                            </td>
                            <td className="table-cell">
                              <span className="text-red-600 font-medium">
                                {movement.expense_usd ? `$${movement.expense_usd.toFixed(2)}` : '-'}
                              </span>
                            </td>
                            <td className="table-cell">
                              <span className="text-green-600 font-medium">
                                {movement.income_ars ? `AR$${movement.income_ars.toFixed(2)}` : '-'}
                              </span>
                            </td>
                            <td className="table-cell">
                              <span className="text-red-600 font-medium">
                                {movement.expense_ars ? `AR$${movement.expense_ars.toFixed(2)}` : '-'}
                              </span>
                            </td>
                            <td className="table-cell theme-text-secondary">
                              {movement.reference_number || '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    
                    {movements.length === 0 && (
                      <div className="text-center py-12">
                        <p className="theme-text-secondary">No movements found for this project</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'profits-fees' && (
              <ProfitsFeesTab 
                selectedProject={selectedProject} 
                onUpdateProject={handleUpdateProject}
              />
            )}

            {activeTab === 'analytics' && (
              <div className="space-y-6">
                {movements.length > 0 ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Monthly Trend Chart */}
                    <div className="chart-container">
                      <h3 className="text-lg font-semibold theme-text mb-4">Monthly Financial Trend</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={movements.reduce((acc, movement) => {
                          const month = format(new Date(movement.date), 'MMM yyyy');
                          const existing = acc.find(item => item.month === month);
                          if (existing) {
                            existing.income += (movement.income_usd || 0);
                            existing.expense += (movement.expense_usd || 0);
                          } else {
                            acc.push({
                              month,
                              income: movement.income_usd || 0,
                              expense: movement.expense_usd || 0
                            });
                          }
                          return acc;
                        }, [])}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="month" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Line type="monotone" dataKey="income" stroke="#10b981" name="Income USD" />
                          <Line type="monotone" dataKey="expense" stroke="#ef4444" name="Expense USD" />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Expense by Supplier */}
                    <div className="chart-container">
                      <h3 className="text-lg font-semibold theme-text mb-4">Expenses by Supplier</h3>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={movements.reduce((acc, movement) => {
                              if (movement.expense_usd && movement.supplier) {
                                const existing = acc.find(item => item.name === movement.supplier);
                                if (existing) {
                                  existing.value += movement.expense_usd;
                                } else {
                                  acc.push({
                                    name: movement.supplier,
                                    value: movement.expense_usd
                                  });
                                }
                              }
                              return acc;
                            }, [])}
                            cx="50%"
                            cy="50%"
                            outerRadius={100}
                            dataKey="value"
                            label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                          >
                            {['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'].map((color, index) => (
                              <Cell key={`cell-${index}`} fill={color} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value) => [`$${value.toFixed(2)}`, 'Amount']} />
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
        ) : (
          <div className="text-center py-12">
            <p className="theme-text-secondary">Please select a project to view its details</p>
          </div>
        )}

        {/* Movement Entry Modal */}
        <MovementEntryModal
          isOpen={isMovementModalOpen}
          onClose={() => setIsMovementModalOpen(false)}
          onSubmit={handleCreateMovement}
          loading={isSubmitting}
          selectedProject={selectedProject}
        />
      </div>
    </div>
  );
};

export default DecoMovements;