# LapisAI Frontend

React-based dashboard untuk Customer Churn Prediction system dengan Sentimen Analysis dari YouTube Live Chat.

## 📦 Teknologi

- **React 18** - UI framework
- **Vite** - Build tool & dev server
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Axios** - HTTP client

## 🚀 Quick Start

### Prerequisites

- Node.js 16+
- npm atau yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Server akan jalan di `http://localhost:3000`

### Build for Production

```bash
npm run build
npm run preview
```

## 📁 Project Structure

```
src/
├── App.jsx                 # Main app with routing
├── index.jsx              # React entry point
├── index.css              # Global styles
└── components/
    ├── LoginPage.jsx      # Authentication page
    ├── DashboardView.jsx  # Main dashboard with charts
    ├── PredictionView.jsx # Churn prediction engine
    ├── SentimentView.jsx  # YouTube chat sentiment analysis
    └── Sparkline.jsx      # Chart helper component
```

## 🎨 UI Features

### 1. **Login Page**

- Clean authentication interface
- Gradient background with 3D card effect
- Pre-filled demo credentials

### 2. **Dashboard**

- Summary statistics with sparklines
- Customer churn list with status badges
- Real-time feedback feed with sentiment labels

### 3. **Prediction Engine**

- Customer ID lookup
- Feature input form (payment delay, NPS, etc)
- Churn probability prediction
- Risk factors breakdown
- Recommended retention actions
- Related segment modals

### 4. **Sentiment Intelligence**

- YouTube live chat real-time analysis
- Sentiment distribution charts
- Emotion detection breakdown
- Trends visualization
- Key insights panel

## 🔌 API Integration

Frontend disiapkan untuk connect ke backend API:

```javascript
// Update API endpoints di components
const API_BASE = "http://localhost:8000";

// Example: Fetch customer data
const fetchCustomer = async (customerId) => {
  const response = await axios.get(`${API_BASE}/api/customer/${customerId}`);
  return response.data;
};
```

## 🎯 Next Steps

1. **Backend Connection**: Update components untuk consume real API endpoints
2. **State Management**: Add Redux/Zustand untuk global state
3. **Authentication**: Integrate dengan backend auth system
4. **Real-time Data**: Add WebSocket untuk live updates
5. **Mobile Responsive**: Full mobile optimization

## 📝 License

Proprietary - Customer Churn Prediction System
