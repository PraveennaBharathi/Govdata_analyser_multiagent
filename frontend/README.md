# GovData Analytics - Frontend

An elegant, modern web application for analyzing government data using AI agents with real-time monitoring and interactive visualizations.

## 🎨 Features

- **Natural Language Query Interface** - Ask questions in plain English
- **Real-Time Agent Monitoring** - Watch AI agents work with live progress updates
- **Interactive Data Visualizations** - Beautiful charts and graphs
- **Analysis History** - Browse and export previous analyses
- **Responsive Design** - Works perfectly on all devices
- **Modern UI** - Built with Next.js, TypeScript, and Tailwind CSS

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Backend server running on `http://localhost:8000`

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
npm start
```

## 📦 Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Custom components with shadcn/ui patterns
- **Icons**: Lucide React
- **Charts**: Recharts
- **Animations**: Framer Motion

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js app router pages
│   │   ├── page.tsx        # Main dashboard
│   │   ├── history/        # Analysis history page
│   │   ├── layout.tsx      # Root layout
│   │   └── globals.css     # Global styles
│   ├── components/          # React components
│   │   ├── ui/             # Base UI components
│   │   ├── QueryInput.tsx  # Natural language input
│   │   ├── AgentMonitor.tsx # Real-time agent activity
│   │   ├── ResultsView.tsx  # Analysis results display
│   │   └── HistoryList.tsx  # Query history
│   ├── lib/                 # Utilities
│   │   ├── api.ts          # API client
│   │   └── utils.ts        # Helper functions
│   └── types/               # TypeScript types
│       └── index.ts        # Type definitions
├── public/                  # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## 🎯 Key Components

### QueryInput
Natural language query interface with example queries and auto-suggestions.

### AgentMonitor
Real-time visualization of AI agent workflow with progress tracking:
- Parse query
- Plan analysis
- Extract data
- Analyze data
- Generate results

### ResultsView
Interactive display of analysis results including:
- Conversational summary
- Statistical insights
- Correlation analysis
- Pattern detection
- Interactive charts
- Structured reports

### HistoryList
Browse previous analyses with filtering and export capabilities.

## 🔌 API Integration

The frontend connects to the backend API at `http://localhost:8000`:

- `POST /query/async` - Submit async query
- `GET /task/{task_id}` - Poll task status
- `GET /queries` - Get analysis history
- `GET /queries/{id}` - Get specific analysis

## 🎨 Design System

### Colors
- **Primary**: Blue (#3B82F6)
- **Success**: Green (#10B981)
- **Warning**: Yellow (#F59E0B)
- **Error**: Red (#EF4444)
- **Neutral**: Gray scale

### Typography
- **Font**: System font stack (optimized for readability)
- **Headings**: Bold, clear hierarchy
- **Body**: 16px base size

### Spacing
- Consistent 4px grid system
- Generous whitespace for clarity

## 🔧 Configuration

### Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### API Proxy

The `next.config.js` includes a proxy configuration to avoid CORS issues:

```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8000/:path*',
    },
  ]
}
```

## 📱 Responsive Design

- **Mobile**: Optimized for small screens
- **Tablet**: Adaptive layout
- **Desktop**: Full feature set with multi-column layout

## ⚡ Performance

- **Code Splitting**: Automatic with Next.js
- **Image Optimization**: Next.js Image component
- **Lazy Loading**: Components loaded on demand
- **Caching**: Efficient API response caching

## 🧪 Development

### Running Tests

```bash
npm test
```

### Linting

```bash
npm run lint
```

### Type Checking

```bash
npx tsc --noEmit
```

## 📝 Usage Examples

### Submit a Query

```typescript
import { apiClient } from '@/lib/api'

const result = await apiClient.submitQueryAsync(
  "Analyze employment trends from 2020 to 2024"
)

console.log(result.task_id) // Use for polling
```

### Poll Task Status

```typescript
await apiClient.pollTaskStatus(
  taskId,
  (status) => {
    console.log(`Progress: ${status.progress}%`)
  }
)
```

### Export Results

```typescript
const blob = await apiClient.exportQuery(queryId, 'json')
downloadBlob(blob, 'analysis.json')
```

## 🎉 Features Showcase

### 1. Natural Language Queries
Ask questions naturally:
- "Show me employment trends"
- "Compare GDP growth across sectors"
- "What are the key economic indicators?"

### 2. Real-Time Monitoring
Watch AI agents work in real-time:
- See each step of the analysis
- Track progress (0-100%)
- View reasoning and decisions

### 3. Interactive Visualizations
Beautiful, interactive charts:
- Trend lines
- Correlation heatmaps
- Pattern visualizations
- Export as images

### 4. Comprehensive Results
Get detailed insights:
- Conversational summary
- Statistical analysis
- Policy recommendations
- Data source citations

## 🚧 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Module Not Found
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Build Errors
```bash
# Clean build
rm -rf .next
npm run build
```

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📞 Support

For issues and questions:
- GitHub Issues
- Documentation
- Email support

---

**Built with ❤️ using Next.js, TypeScript, and Tailwind CSS**
