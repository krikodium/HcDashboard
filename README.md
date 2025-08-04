# Hermanas Caradonti Admin Tool

A comprehensive administrative dashboard for Hermanas Caradonti, an events and décor company managing three business lines: Decos (interior décor), Events (private parties), and Shop (showroom retail).

## Features

### Core Modules
- **General Cash**: Daily cash entries with approval workflows
- **Events Cash**: Event budgets and payment tracking with ledger management
- **Shop Cash**: Retail sales with profit calculations and inventory integration
- **Deco Movements**: Project ledgers and disbursement order management
- **Deco Cash Count (Arqueo)**: Reconciliation with discrepancy detection

### Technical Features
- **Authentication**: JWT-based with role management (super-admin, area-admin, employee)
- **Dual Currency**: ARS/USD support with manual entry
- **Notifications**: WhatsApp (Twilio) and Email (SendGrid) integration
- **Responsive Design**: Dark/light mode with clean, professional UI
- **Real-time Updates**: Live data synchronization across modules

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **MongoDB**: Document database with Motor async driver
- **Pydantic**: Data validation and serialization
- **JWT**: Secure authentication
- **Twilio**: WhatsApp notifications
- **SendGrid**: Email notifications

### Frontend
- **React 18**: Modern React with hooks
- **React Router**: Client-side routing
- **Tailwind CSS**: Utility-first styling
- **Axios**: HTTP client
- **date-fns**: Date manipulation

## Getting Started

### Prerequisites
- Node.js 16+ and yarn
- Python 3.11+
- MongoDB (local or Docker)

### Development Setup

1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   python server.py
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   yarn install
   yarn start
   ```

3. **Database**
   - MongoDB running on localhost:27017
   - Database: hermanas_caradonti

### Production Deployment

Use Docker Compose for production deployment:

```bash
docker-compose up -d
```

## Default Credentials

**Test User:**
- Username: `mateo`
- Password: `prueba123`
- Role: Super Admin

*⚠️ Change these credentials before production deployment*

## API Documentation

The backend provides comprehensive REST APIs:

- **Authentication**: `/api/auth/*`
- **General Cash**: `/api/general-cash/*`
- **Events Cash**: `/api/events-cash/*`
- **Shop Cash**: `/api/shop-cash/*`
- **Deco Movements**: `/api/deco-movements/*`
- **Cash Count**: `/api/deco-cash-count/*`

Access interactive API docs at: `http://localhost:8001/docs`

## Environment Variables

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
JWT_SECRET_KEY=your-secret-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
SENDGRID_API_KEY=your-sendgrid-key
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_NAME=Hermanas Caradonti Admin Tool
```

## Key Features Implemented

### Phase 1: Project Foundation ✅
- Complete full-stack architecture
- JWT authentication with user roles
- Dark/light mode toggle
- Professional UI with teal accent colors
- MongoDB integration

### Phase 2: Database Models & APIs ✅
- Comprehensive Pydantic models for all 5 modules
- 25+ REST API endpoints with full CRUD operations
- Advanced business logic (balance calculations, approval workflows)
- Notification system integration
- Dual-currency support

### Phase 3: Advanced Frontend Components ✅
- Dynamic routing with React Router
- Complete General Cash module with:
  - Responsive data table with sorting and filtering
  - Modal form for entry creation
  - Real-time summary statistics
  - Approval workflow buttons
  - Professional loading states and error handling

## Business Logic

### Approval Workflows
- Automatic approval detection based on thresholds
- Two-tier approval: Fede approval and Sisters approval
- Real-time notifications via WhatsApp/Email

### Financial Calculations
- Running balance calculations for events
- Profit margin calculations (2% commission) for shop
- Multi-currency ledger management
- Discrepancy detection in cash counts

### User Experience
- Skeleton loaders for smooth UX
- Real-time data updates
- Responsive mobile-friendly design
- Professional minimalist aesthetic
- Comprehensive error handling

## Development Status

- ✅ **Phase 1**: Foundation (Authentication, UI, Backend setup)
- ✅ **Phase 2**: Database models and API endpoints
- ✅ **Phase 3**: Advanced frontend components and General Cash module
- 🚧 **Phase 4**: Remaining modules (Events, Shop, Deco, Cash Count)
- 🚧 **Phase 5**: Advanced features and deployment

## Production Considerations

- Change default credentials
- Update JWT secret keys
- Configure real Twilio and SendGrid API keys
- Set up proper MongoDB authentication
- Configure CORS for production domains
- Enable HTTPS and security headers

## License

Proprietary - Hermanas Caradonti Internal Tool

---

**Version**: 1.0.0  
**Last Updated**: August 2025