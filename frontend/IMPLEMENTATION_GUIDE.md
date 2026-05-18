# Frontend Implementation Guide

## ✅ Project Created Successfully!

React frontend untuk LapisAI Customer Churn Prediction telah dibuat dengan struktur production-ready.

---

## 📂 Directory Structure

```
frontend/
├── package.json              # Dependencies & scripts
├── vite.config.js           # Vite build configuration
├── tailwind.config.js       # Tailwind CSS config
├── postcss.config.js        # PostCSS config
├── index.html               # HTML entry point
├── .gitignore               # Git ignore rules
├── README.md                # Project documentation
│
└── src/
    ├── index.jsx            # React root (281 bytes)
    ├── index.css            # Global Tailwind CSS
    ├── App.jsx              # Main app component (5.3 KB)
    │                        # - Tab routing (Dashboard/Prediction/Sentiment)
    │                        # - Sidebar navigation
    │                        # - Header with search & logout
    │
    └── components/
        ├── LoginPage.jsx        # Sign-in page (4.1 KB)
        │                        # - Email/Password form
        │                        # - Gradient illustration
        │                        # - Demo credentials
        │
        ├── DashboardView.jsx    # Main dashboard (7.7 KB)
        │                        # - Summary stats with sparklines
        │                        # - Customer churn list
        │                        # - Customer feedback feed
        │
        ├── PredictionView.jsx   # Churn prediction (17.8 KB)
        │                        # - Customer lookup form
        │                        # - Feature input form
        │                        # - Prediction results
        │                        # - Risk factors breakdown
        │                        # - Modal data tables
        │
        ├── SentimentView.jsx    # NLP sentiment analysis (13.5 KB)
        │                        # - YouTube live chat display
        │                        # - Sentiment distribution
        │                        # - Emotion breakdown
        │                        # - Trend visualization
        │                        # - Key insights
        │
        └── Sparkline.jsx        # Chart component (1.1 KB)
                                 # - Inline sparkline charts
                                 # - Color variants
```

---

## 🎯 Component Overview

### 1️⃣ **App.jsx** - Main Application

- **Purpose**: Root component dengan tab navigation
- **Features**:
  - Multi-tab interface (Dashboard/Prediction/Sentiment)
  - Persistent sidebar navigation
  - Header dengan search & user profile
  - Authentication state management
- **State**: `isAuthenticated`, `activeTab`

### 2️⃣ **LoginPage.jsx** - Authentication

- **Purpose**: Sign-in interface
- **Features**:
  - Email & password input
  - Gradient background with animation
  - 3D card illustration
  - Demo credentials (Admin123 / any password)
- **Props**: `onLogin` callback

### 3️⃣ **DashboardView.jsx** - Overview

- **Purpose**: Main dashboard dengan overview data
- **Features**:
  - 3x Summary stats (Customers at Risk, Revenue at Risk, NPS)
  - Sparkline charts untuk trend
  - Customer churn list dengan status
  - Customer feedback feed dengan sentiment labels
- **Data**: Mock data (ready untuk API integration)

### 4️⃣ **PredictionView.jsx** - Churn Prediction

- **Purpose**: Advanced churn prediction engine
- **Features**:
  - Customer ID search form
  - Dynamic feature extraction
  - Churn probability calculation (78.5% demo)
  - Revenue impact calculation
  - Risk factors breakdown (SHAP-style)
  - Recommended retention actions
  - Segment exploration modals
    - Payment Delay Drivers
    - Churn Forecast
    - Enterprise At-Risk MRR
    - Unresolved Technical Issues
- **Modals**: 4 interactive data table modals

### 5️⃣ **SentimentView.jsx** - NLP Analysis

- **Purpose**: YouTube chat sentiment & emotion analysis
- **Features**:
  - Live chat display (11 sample messages)
  - Sentiment distribution (Positive/Negative/Netral)
  - Emotion detection breakdown (7 emotions)
  - Sentiment trend visualization (5-minute breakdown)
  - Expandable comment details
  - Key insights panel
- **Data**: Indonesian YouTube chat (5 menit)

### 6️⃣ **Sparkline.jsx** - Helper Component

- **Purpose**: Reusable inline chart component
- **Features**:
  - SVG-based sparkline
  - Custom color variants
  - Highlight point indicator
  - Responsive sizing

---

## 🔧 Dependencies

### Production

```json
{
  "react": "^18.2.0", // UI framework
  "react-dom": "^18.2.0", // DOM rendering
  "lucide-react": "^0.263.1", // Icon library
  "axios": "^1.6.0" // HTTP client
}
```

### Development

```json
{
  "@vitejs/plugin-react": "^4.2.0", // Vite React integration
  "vite": "^5.0.0", // Build tool
  "tailwindcss": "^3.3.0", // Utility CSS
  "postcss": "^8.4.31", // CSS processing
  "autoprefixer": "^10.4.16" // Browser prefixes
}
```

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Development Mode

```bash
npm run dev
```

- App runs on `http://localhost:3000`
- Auto-reload on file changes
- API proxy configured for `http://localhost:8000`

### 3. Production Build

```bash
npm run build
npm run preview
```

---

## 🔌 API Integration Points

Components sudah siap untuk connect ke backend:

### DashboardView.jsx

```javascript
// Replace mock data dengan API calls:
useEffect(() => {
  fetchCustomerChurnData(); // GET /api/churn/customers
  fetchFeedbackData(); // GET /api/feedback/list
  fetchSummaryStats(); // GET /api/dashboard/summary
}, []);
```

### PredictionView.jsx

```javascript
const handleFetch = async (customerId) => {
  const data = await axios.get(`/api/customer/${customerId}`);
  // data.paymentDelay, .lastLogin, .nps, .ticketRatio, .revAtRisk
};

const handlePredict = async () => {
  const result = await axios.post("/api/predict/churn", formData);
  // result.probability, .revenue_at_risk, .risk_factors, .recommendations
};
```

### SentimentView.jsx

```javascript
// Real-time sentiment from YouTube/backend:
useEffect(() => {
  fetchSentimentAnalysis(); // GET /api/sentiment/analysis
  fetchEmotionData(); // GET /api/sentiment/emotions
  subscribeLiveChat(); // WebSocket for live updates
}, []);
```

---

## 🎨 Design System

### Colors (Tailwind)

- **Primary**: Indigo-600 (`#6366f1`)
- **Success**: Emerald-600 (`#059669`)
- **Warning**: Amber-500 (`#f59e0b`)
- **Danger**: Rose-500 (`#f43f5e`)
- **Neutral**: Slate-600 (`#475569`)

### Typography

- **Headlines**: Font-black, tracking-tight
- **Body**: Font-medium, text-sm/text-base
- **Labels**: Font-semibold, text-xs/text-sm

### Spacing

- **Gap**: 4px-24px (Tailwind scale)
- **Padding**: 16px-32px (p-4 to p-8)
- **Radius**: 8px-24px (rounded-lg to rounded-2xl)

---

## ✨ Key Features Implemented

### ✅ Component Architecture

- Functional components dengan React hooks
- Clear separation of concerns
- Reusable Sparkline component
- Modal component pattern

### ✅ UI/UX

- Responsive grid layouts
- Hover states & transitions
- Color-coded status badges
- Expandable/collapsible sections
- Icon integration (Lucide)

### ✅ Data Visualization

- Sparkline charts
- Progress bars
- Color-coded sentiment badges
- Emotion distribution bars
- Trend visualization

### ✅ Interactivity

- Tab navigation
- Form inputs & validation
- Modal dialogs
- Expandable rows
- Button states (loading, disabled)

### ✅ Styling

- Tailwind CSS utility classes
- Dark/light color schemes
- Shadow & border effects
- Animations & transitions
- Mobile responsive (grid cols)

---

## 🔐 Authentication

Default credentials (demo):

- **Username**: Admin123
- **Password**: Any value

⚠️ **TODO**: Integrate dengan backend auth system (JWT/Session)

---

## 📱 Responsive Design

Grid breakpoints:

- **Mobile**: 1 column (default)
- **Tablet**: 2 columns (`md:`)
- **Desktop**: 3-4 columns (`lg:`, `xl:`)

---

## 🎯 Next Steps for Integration

1. **Backend API Setup**
   - Create REST endpoints
   - Configure CORS
   - Authentication (JWT/OAuth)

2. **Environment Configuration**
   - Create `.env.local` file
   - Set API_BASE_URL
   - Configure API keys

3. **State Management**
   - Add Redux/Zustand untuk complex state
   - Cache customer predictions
   - Store user preferences

4. **Real-time Features**
   - WebSocket untuk live chat
   - Auto-refresh sentiment data
   - Real-time notifications

5. **Error Handling**
   - API error boundaries
   - User-friendly error messages
   - Retry logic

6. **Performance**
   - Code splitting
   - Image optimization
   - Lazy loading components

7. **Testing**
   - Unit tests (Jest + React Testing Library)
   - Integration tests
   - E2E tests (Cypress)

8. **Deployment**
   - Docker containerization
   - CI/CD pipeline (GitHub Actions)
   - Production environment setup

---

## 📞 Support

Untuk pertanyaan atau issues, silakan create GitHub issue atau contact development team.

---

**Status**: ✅ Ready for Development  
**Last Updated**: 2024  
**Version**: 1.0.0
