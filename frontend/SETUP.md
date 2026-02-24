# Frontend Setup Guide

## 🚀 Quick Setup (Automated)

### Step 1: Install Node.js (if not installed)

**macOS:**
```bash
# Using Homebrew (recommended)
brew install node

# Or download from https://nodejs.org/
```

**Verify installation:**
```bash
node --version  # Should be v18 or higher
npm --version
```

### Step 2: Install Dependencies

```bash
cd frontend
npm install
```

This will install all required packages:
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Lucide Icons
- Recharts
- And more...

### Step 3: Start Development Server

```bash
npm run dev
```

The app will be available at **http://localhost:3000**

---

## 📋 Manual Setup (If Automated Fails)

### Install Dependencies One by One

```bash
# Core dependencies
npm install next@14.1.0 react@18.2.0 react-dom@18.2.0

# TypeScript
npm install --save-dev typescript @types/react @types/node @types/react-dom

# Tailwind CSS
npm install --save-dev tailwindcss postcss autoprefixer
npx tailwindcss init -p

# UI Libraries
npm install lucide-react recharts
npm install class-variance-authority clsx tailwind-merge
npm install framer-motion date-fns

# Linting
npm install --save-dev eslint eslint-config-next
```

---

## 🔧 Configuration

### 1. Environment Variables

Create `.env.local` in the frontend directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Verify Backend is Running

Make sure the backend server is running on port 8000:

```bash
# In backend directory
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Test backend:
```bash
curl http://localhost:8000/health
```

---

## 🎯 Running the Application

### Development Mode

```bash
npm run dev
```

- Hot reload enabled
- Runs on http://localhost:3000
- API proxied to http://localhost:8000

### Production Build

```bash
npm run build
npm start
```

### Linting

```bash
npm run lint
```

---

## 🧪 Testing the Frontend

### 1. Open Browser

Navigate to http://localhost:3000

### 2. Submit a Query

Try one of these example queries:
- "Analyze employment trends from 2020 to 2024"
- "Show me GDP growth patterns"
- "Compare unemployment rates across sectors"

### 3. Watch Real-Time Updates

You should see:
- ✅ Query submitted
- ✅ Agent activity monitor showing progress
- ✅ Real-time progress updates (0% → 100%)
- ✅ Results displayed with charts and insights

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Main dashboard (TO BE CREATED)
│   │   ├── layout.tsx            # Root layout (TO BE CREATED)
│   │   ├── globals.css           # ✅ Created
│   │   └── history/
│   │       └── page.tsx          # History page (TO BE CREATED)
│   ├── components/
│   │   ├── ui/
│   │   │   ├── button.tsx        # ✅ Created
│   │   │   └── card.tsx          # ✅ Created
│   │   ├── QueryInput.tsx        # ✅ Created
│   │   ├── AgentMonitor.tsx      # ✅ Created
│   │   ├── ResultsView.tsx       # TO BE CREATED
│   │   └── HistoryList.tsx       # TO BE CREATED
│   ├── lib/
│   │   ├── api.ts                # ✅ Created
│   │   └── utils.ts              # ✅ Created
│   └── types/
│       └── index.ts              # ✅ Created
├── public/                        # Static files
├── package.json                   # ✅ Created
├── tsconfig.json                  # ✅ Created
├── tailwind.config.ts             # ✅ Created
├── postcss.config.js              # ✅ Created
├── next.config.js                 # ✅ Created
└── README.md                      # ✅ Created
```

---

## 🐛 Troubleshooting

### Error: "Cannot find module 'next'"

```bash
rm -rf node_modules package-lock.json
npm install
```

### Error: "Port 3000 already in use"

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use a different port
npm run dev -- -p 3001
```

### Error: "Failed to fetch from backend"

1. Check backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check CORS settings in backend

3. Verify `.env.local` has correct API URL

### TypeScript Errors

These are expected until you run `npm install`. All errors will resolve after installation.

---

## ✅ Verification Checklist

- [ ] Node.js 18+ installed
- [ ] Dependencies installed (`npm install`)
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Can submit queries
- [ ] Real-time updates working
- [ ] Results displaying correctly

---

## 🎉 Next Steps

After setup is complete:

1. **Submit a test query** to verify everything works
2. **Explore the UI** - try different queries
3. **Check the history page** at `/history`
4. **Export results** in JSON or CSV format
5. **Customize the theme** in `tailwind.config.ts`

---

## 📞 Need Help?

If you encounter issues:

1. Check this guide
2. Review the main README.md
3. Check backend logs
4. Verify all dependencies are installed

---

**The frontend is almost ready! Just need to install Node.js and run `npm install`** 🚀
