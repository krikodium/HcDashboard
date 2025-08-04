import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';

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

// Movement Entry Form Modal
const MovementEntryModal = ({ isOpen, onClose, onSubmit, loading, projects }) => {
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    project_name: '',
    description: '',
    income_usd: '',
    expense_usd: '',
    income_ars: '',
    expense_ars: '',
    supplier: '',
    reference_number: '',
    notes: ''
  });

  // Set default project when projects are loaded
  useEffect(() => {
    if (projects.length > 0 && !formData.project_name) {
      setFormData(prev => ({...prev, project_name: projects[0].name}));
    }
  }, [projects, formData.project_name]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      income_usd: formData.income_usd ? parseFloat(formData.income_usd) : null,
      expense_usd: formData.expense_usd ? parseFloat(formData.expense_usd) : null,
      income_ars: formData.income_ars ? parseFloat(formData.income_ars) : null,
      expense_ars: formData.expense_ars ? parseFloat(formData.expense_ars) : null,
    };
    onSubmit(submitData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="card max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold theme-text">New Deco Movement</h2>
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
              <label className="block text-sm font-medium theme-text mb-2">Project</label>
              <select
                className="form-input w-full"
                value={formData.project_name}
                onChange={(e) => setFormData({...formData, project_name: e.target.value})}
                required
              >
                <option value="">Select a project</option>
                {projects.map(project => (
                  <option key={project.id} value={project.name}>{project.name}</option>
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

// Project Creation Modal Component
const ProjectCreateModal = ({ isOpen, onClose, onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    project_type: 'Deco',
    start_date: '',
    end_date: '',
    budget_usd: '',
    budget_ars: '',
    client_name: '',
    location: '',
    notes: ''
  });

  const projectTypes = ['Deco', 'Event', 'Mixed'];

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      budget_usd: formData.budget_usd ? parseFloat(formData.budget_usd) : null,
      budget_ars: formData.budget_ars ? parseFloat(formData.budget_ars) : null,
      start_date: formData.start_date || null,
      end_date: formData.end_date || null,
    };
    onSubmit(submitData);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      project_type: 'Deco',
      start_date: '',
      end_date: '',
      budget_usd: '',
      budget_ars: '',
      client_name: '',
      location: '',
      notes: ''
    });
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="card max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold theme-text">Create New Project</h2>
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
              <label className="block text-sm font-medium theme-text mb-2">Project Name *</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Enter project name"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Project Type</label>
              <select
                className="form-input w-full"
                value={formData.project_type}
                onChange={(e) => setFormData({...formData, project_type: e.target.value})}
              >
                {projectTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Description</label>
            <textarea
              className="form-input w-full"
              rows="3"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Project description"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Client Name</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.client_name}
                onChange={(e) => setFormData({...formData, client_name: e.target.value})}
                placeholder="Client name"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Location</label>
              <input
                type="text"
                className="form-input w-full"
                value={formData.location}
                onChange={(e) => setFormData({...formData, location: e.target.value})}
                placeholder="Project location"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Start Date</label>
              <input
                type="date"
                className="form-input w-full"
                value={formData.start_date}
                onChange={(e) => setFormData({...formData, start_date: e.target.value})}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">End Date</label>
              <input
                type="date"
                className="form-input w-full"
                value={formData.end_date}
                onChange={(e) => setFormData({...formData, end_date: e.target.value})}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Budget USD</label>
              <input
                type="number"
                step="0.01"
                className="form-input w-full"
                value={formData.budget_usd}
                onChange={(e) => setFormData({...formData, budget_usd: e.target.value})}
                placeholder="0.00"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Budget ARS</label>
              <input
                type="number"
                step="0.01"
                className="form-input w-full"
                value={formData.budget_ars}
                onChange={(e) => setFormData({...formData, budget_ars: e.target.value})}
                placeholder="0.00"
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
              placeholder="Additional project notes"
            />
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex-1 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Project'}
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
const DisbursementOrderModal = ({ isOpen, onClose, onSubmit, loading, projects }) => {
  const [formData, setFormData] = useState({
    project_name: '',
    disbursement_type: 'Supplier Payment',
    amount_usd: '',
    amount_ars: '',
    supplier: '',
    description: '',
    due_date: '',
    priority: 'Normal',
    supporting_documents: []
  });

  // Set default project when projects are loaded
  useEffect(() => {
    if (projects.length > 0 && !formData.project_name) {
      setFormData(prev => ({...prev, project_name: projects[0].name}));
    }
  }, [projects, formData.project_name]);

  const disbursementTypes = [
    'Supplier Payment', 'Materials', 'Labor', 'Transport', 'Utilities', 'Maintenance', 'Other'
  ];

  const priorities = ['Low', 'Normal', 'High', 'Urgent'];

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      amount_usd: formData.amount_usd ? parseFloat(formData.amount_usd) : null,
      amount_ars: formData.amount_ars ? parseFloat(formData.amount_ars) : null,
    };
    onSubmit(submitData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="card max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold theme-text">Request Disbursement Order</h2>
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
              <label className="block text-sm font-medium theme-text mb-2">Project</label>
              <select
                className="form-input w-full"
                value={formData.project_name}
                onChange={(e) => setFormData({...formData, project_name: e.target.value})}
                required
              >
                <option value="">Select a project</option>
                {projects.map(project => (
                  <option key={project.id} value={project.name}>{project.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Disbursement Type</label>
              <select
                className="form-input w-full"
                value={formData.disbursement_type}
                onChange={(e) => setFormData({...formData, disbursement_type: e.target.value})}
                required
              >
                {disbursementTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Amount USD</label>
              <input
                type="number"
                step="0.01"
                className="form-input w-full"
                value={formData.amount_usd}
                onChange={(e) => setFormData({...formData, amount_usd: e.target.value})}
                placeholder="0.00"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Amount ARS</label>
              <input
                type="number"
                step="0.01"
                className="form-input w-full"
                value={formData.amount_ars}
                onChange={(e) => setFormData({...formData, amount_ars: e.target.value})}
                placeholder="0.00"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Supplier</label>
            <input
              type="text"
              className="form-input w-full"
              value={formData.supplier}
              onChange={(e) => setFormData({...formData, supplier: e.target.value})}
              placeholder="Supplier name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium theme-text mb-2">Description</label>
            <textarea
              className="form-input w-full"
              rows="3"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Detailed description of the disbursement request"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Due Date</label>
              <input
                type="date"
                className="form-input w-full"
                value={formData.due_date}
                onChange={(e) => setFormData({...formData, due_date: e.target.value})}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium theme-text mb-2">Priority</label>
              <select
                className="form-input w-full"
                value={formData.priority}
                onChange={(e) => setFormData({...formData, priority: e.target.value})}
              >
                {priorities.map(priority => (
                  <option key={priority} value={priority}>{priority}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex-1 disabled:opacity-50"
            >
              {loading ? 'Requesting...' : 'Request Disbursement'}
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

// Main Deco Movements Component
const DecoMovements = () => {
  const [movements, setMovements] = useState([]);
  const [disbursementOrders, setDisbursementOrders] = useState([]);
  const [projects, setProjects] = useState([]);
  const [summary, setSummary] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [projectBalanceData, setProjectBalanceData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState('');
  const [isMovementModalOpen, setIsMovementModalOpen] = useState(false);
  const [isDisbursementModalOpen, setIsDisbursementModalOpen] = useState(false);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [movementsResponse, disbursementsResponse, projectsResponse] = await Promise.all([
        axios.get('/api/deco-movements'),
        axios.get('/api/deco-movements/disbursement-order').catch(() => ({ data: [] })),
        axios.get('/api/projects').catch(() => ({ data: [] }))
      ]);
      
      setMovements(movementsResponse.data);
      setDisbursementOrders(disbursementsResponse.data || []);
      setProjects(projectsResponse.data || []);
      
      // Process data for charts
      const monthlyData = processMonthlyData(movementsResponse.data);
      const projectData = processProjectBalanceData(movementsResponse.data);
      
      setChartData(monthlyData);
      setProjectBalanceData(projectData);
      
      // Calculate summary
      const calculatedSummary = calculateSummary(movementsResponse.data, disbursementsResponse.data || []);
      setSummary(calculatedSummary);
      
      setError('');
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (formData) => {
    try {
      setIsSubmitting(true);
      await axios.post('/api/projects', formData);
      setIsProjectModalOpen(false);
      await fetchData(); // Refresh all data including projects
    } catch (error) {
      console.error('Error creating project:', error);
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Failed to create project. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const processMonthlyData = (movements) => {
    const monthlyMap = {};
    
    movements.forEach(movement => {
      const date = new Date(movement.date);
      const monthKey = format(date, 'MMM yyyy');
      
      if (!monthlyMap[monthKey]) {
        monthlyMap[monthKey] = {
          month: monthKey,
          income_usd: 0,
          expense_usd: 0,
          balance_usd: 0
        };
      }
      
      monthlyMap[monthKey].income_usd += movement.income_usd || 0;
      monthlyMap[monthKey].expense_usd += movement.expense_usd || 0;
      monthlyMap[monthKey].balance_usd = monthlyMap[monthKey].income_usd - monthlyMap[monthKey].expense_usd;
    });
    
    return Object.values(monthlyMap).sort((a, b) => {
      return new Date(a.month) - new Date(b.month);
    });
  };

  const processProjectBalanceData = (movements) => {
    const projectMap = {};
    
    movements.forEach(movement => {
      const project = movement.project_name;
      
      if (!projectMap[project]) {
        projectMap[project] = {
          name: project,
          balance_usd: 0,
          balance_ars: 0,
          movements_count: 0
        };
      }
      
      projectMap[project].balance_usd += (movement.income_usd || 0) - (movement.expense_usd || 0);
      projectMap[project].balance_ars += (movement.income_ars || 0) - (movement.expense_ars || 0);
      projectMap[project].movements_count += 1;
    });
    
    return Object.values(projectMap).sort((a, b) => b.balance_usd - a.balance_usd);
  };

  const calculateSummary = (movements, orders) => {
    return {
      total_movements: movements.length,
      total_projects: new Set(movements.map(m => m.project_name)).size,
      pending_disbursements: orders.filter(o => o.status === 'Requested').length,
      total_balance_usd: movements.reduce((sum, m) => sum + (m.income_usd || 0) - (m.expense_usd || 0), 0),
      total_balance_ars: movements.reduce((sum, m) => sum + (m.income_ars || 0) - (m.expense_ars || 0), 0),
      overdue_payments: orders.filter(o => o.is_overdue).length,
    };
  };

  const handleCreateMovement = async (formData) => {
    try {
      setIsSubmitting(true);
      await axios.post('/api/deco-movements', formData);
      setIsMovementModalOpen(false);
      await fetchData();
    } catch (error) {
      console.error('Error creating movement:', error);
      setError('Failed to create movement. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateDisbursementOrder = async (formData) => {
    try {
      setIsSubmitting(true);
      await axios.post('/api/deco-movements/disbursement-order', formData);
      setIsDisbursementModalOpen(false);
      await fetchData();
    } catch (error) {
      console.error('Error creating disbursement order:', error);
      setError('Failed to create disbursement order. Please try again.');
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
      case 'Requested':
        return `${baseClasses} bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200`;
      case 'Approved':
        return `${baseClasses} bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200`;
      case 'Processed':
        return `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`;
      case 'Rejected':
        return `${baseClasses} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200`;
    }
  };

  const getPriorityBadge = (priority) => {
    const baseClasses = "px-2 py-1 rounded text-xs font-medium";
    switch (priority) {
      case 'Urgent':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'High':
        return `${baseClasses} bg-orange-100 text-orange-800`;
      case 'Normal':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'Low':
        return `${baseClasses} bg-gray-100 text-gray-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  // Filter movements by selected project
  const filteredMovements = selectedProject 
    ? movements.filter(m => m.project_name === selectedProject)
    : movements;

  // Create project options for filter dropdown from projects and movements
  const projectOptions = ['', ...new Set([
    ...projects.map(p => p.name),
    ...movements.map(m => m.project_name)
  ])];

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold theme-text">Deco Movements</h1>
            <p className="theme-text-secondary">Project ledgers and disbursement orders</p>
          </div>
          <div className="flex space-x-4">
            <button
              onClick={() => setIsProjectModalOpen(true)}
              className="btn-secondary"
            >
              Create Project
            </button>
            <button
              onClick={() => setIsMovementModalOpen(true)}
              className="btn-primary"
            >
              Add Movement
            </button>
            <button
              onClick={() => setIsDisbursementModalOpen(true)}
              className="btn-secondary"
            >
              Request Disbursement
            </button>
          </div>
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

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Total Projects</h3>
              <p className="text-2xl font-bold theme-text">{summary.total_projects}</p>
              <p className="text-xs theme-text-secondary mt-1">{projects.length} managed</p>
            </div>
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Total Movements</h3>
              <p className="text-2xl font-bold text-blue-600">{summary.total_movements}</p>
            </div>
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Balance USD</h3>
              <p className={`text-2xl font-bold ${summary.total_balance_usd >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(summary.total_balance_usd, 'USD')}
              </p>
            </div>
            <div className="card">
              <h3 className="text-sm font-medium theme-text-secondary">Pending Disbursements</h3>
              <p className="text-2xl font-bold text-yellow-600">{summary.pending_disbursements}</p>
            </div>
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Monthly Movement Trend */}
          {chartData.length > 0 && (
            <div className="card">
              <div className="border-b theme-border pb-4 mb-6">
                <h2 className="text-xl font-semibold theme-text">Monthly Movement Trend (USD)</h2>
                <p className="text-sm theme-text-secondary">Income vs expense over time</p>
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
                      tickFormatter={(value) => `$${value.toLocaleString()}`}
                    />
                    <Tooltip 
                      formatter={(value, name) => [
                        `USD ${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
                        name === 'income_usd' ? 'Income' : name === 'expense_usd' ? 'Expense' : 'Balance'
                      ]}
                      labelStyle={{ color: '#374151' }}
                      contentStyle={{ 
                        backgroundColor: 'white', 
                        border: '1px solid #e5e7eb',
                        borderRadius: '0.5rem'
                      }}
                    />
                    <Legend />
                    <Bar dataKey="income_usd" name="Income" fill="#10b981" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="expense_usd" name="Expense" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Project Balance Distribution */}
          {projectBalanceData.length > 0 && (
            <div className="card">
              <div className="border-b theme-border pb-4 mb-6">
                <h2 className="text-xl font-semibold theme-text">Project Balance Distribution</h2>
                <p className="text-sm theme-text-secondary">Current balance by project (USD)</p>
              </div>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={projectBalanceData.filter(p => p.balance_usd > 0)}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="balance_usd"
                    >
                      {projectBalanceData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={`hsl(${180 + (index * 45)}, 60%, 50%)`} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) => [`USD ${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, 'Balance']}
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

        {/* Project Filter */}
        <div className="card mb-6">
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium theme-text">Filter by Project:</label>
            <select
              className="form-input"
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
            >
              <option value="">All Projects</option>
              {projectOptions.slice(1).map(project => (
                <option key={project} value={project}>{project}</option>
              ))}
            </select>
            {selectedProject && (
              <button
                onClick={() => setSelectedProject('')}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Clear Filter
              </button>
            )}
          </div>
        </div>

        {/* Movements Table */}
        <div className="card mb-8">
          <div className="border-b theme-border pb-4 mb-4">
            <h2 className="text-xl font-semibold theme-text">
              Movement Records {selectedProject && `- ${selectedProject}`}
            </h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="table-header">
                  <th className="text-left p-4 font-medium theme-text">Date</th>
                  <th className="text-left p-4 font-medium theme-text">Project</th>
                  <th className="text-left p-4 font-medium theme-text">Description</th>
                  <th className="text-left p-4 font-medium theme-text">Supplier</th>
                  <th className="text-right p-4 font-medium theme-text">Income USD</th>
                  <th className="text-right p-4 font-medium theme-text">Expense USD</th>
                  <th className="text-right p-4 font-medium theme-text">Balance USD</th>
                  <th className="text-center p-4 font-medium theme-text">Status</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="8" className="p-0">
                      <TableSkeleton />
                    </td>
                  </tr>
                ) : filteredMovements.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="text-center py-12 theme-text-secondary">
                      {selectedProject 
                        ? `No movements found for ${selectedProject}.`
                        : 'No movements found. Create your first movement to get started.'
                      }
                    </td>
                  </tr>
                ) : (
                  filteredMovements.map((movement) => (
                    <tr key={movement._id} className="table-row">
                      <td className="p-4 theme-text">
                        {format(new Date(movement.date), 'dd/MM/yyyy')}
                      </td>
                      <td className="p-4 theme-text font-medium">{movement.project_name}</td>
                      <td className="p-4 theme-text">{movement.description}</td>
                      <td className="p-4 theme-text">{movement.supplier || '-'}</td>
                      <td className="p-4 theme-text text-right table-cell-numeric">
                        {formatCurrency(movement.income_usd, 'USD')}
                      </td>
                      <td className="p-4 theme-text text-right table-cell-numeric">
                        {formatCurrency(movement.expense_usd, 'USD')}
                      </td>
                      <td className="p-4 theme-text text-right table-cell-numeric font-medium">
                        {formatCurrency(movement.running_balance_usd, 'USD')}
                      </td>
                      <td className="p-4 text-center">
                        <span className="px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                          Active
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Disbursement Orders Table */}
        {disbursementOrders.length > 0 && (
          <div className="card">
            <div className="border-b theme-border pb-4 mb-4">
              <h2 className="text-xl font-semibold theme-text">Disbursement Orders</h2>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="table-header">
                    <th className="text-left p-4 font-medium theme-text">Project</th>
                    <th className="text-left p-4 font-medium theme-text">Type</th>
                    <th className="text-left p-4 font-medium theme-text">Supplier</th>
                    <th className="text-right p-4 font-medium theme-text">Amount</th>
                    <th className="text-center p-4 font-medium theme-text">Priority</th>
                    <th className="text-center p-4 font-medium theme-text">Due Date</th>
                    <th className="text-center p-4 font-medium theme-text">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {disbursementOrders.map((order) => (
                    <tr key={order.id} className="table-row">
                      <td className="p-4 theme-text font-medium">{order.project_name}</td>
                      <td className="p-4 theme-text">{order.disbursement_type}</td>
                      <td className="p-4 theme-text">{order.supplier}</td>
                      <td className="p-4 theme-text text-right table-cell-numeric">
                        {order.amount_usd ? formatCurrency(order.amount_usd, 'USD') : 
                         order.amount_ars ? formatCurrency(order.amount_ars, 'ARS') : '-'}
                      </td>
                      <td className="p-4 text-center">
                        <span className={getPriorityBadge(order.priority)}>
                          {order.priority}
                        </span>
                      </td>
                      <td className="p-4 theme-text text-center">
                        {order.due_date ? format(new Date(order.due_date), 'dd/MM/yyyy') : '-'}
                      </td>
                      <td className="p-4 text-center">
                        <span className={getStatusBadge(order.status)}>
                          {order.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modals */}
        <MovementEntryModal
          isOpen={isMovementModalOpen}
          onClose={() => setIsMovementModalOpen(false)}
          onSubmit={handleCreateMovement}
          loading={isSubmitting}
          projects={projects}
        />

        <DisbursementOrderModal
          isOpen={isDisbursementModalOpen}
          onClose={() => setIsDisbursementModalOpen(false)}
          onSubmit={handleCreateDisbursementOrder}
          loading={isSubmitting}
          projects={projects}
        />

        <ProjectCreateModal
          isOpen={isProjectModalOpen}
          onClose={() => setIsProjectModalOpen(false)}
          onSubmit={handleCreateProject}
          loading={isSubmitting}
        />
      </div>
    </div>
  );
};

export default DecoMovements;