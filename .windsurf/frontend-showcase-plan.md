# Frontend Showcase Plan

Static React application for demonstrating the Garmin Analysis platform capabilities without exposing the backend or AI agent to public access.

## Overview

This is a **pure showcase frontend** - a static React application that demonstrates the platform's UI/UX and capabilities using mock data. No backend connectivity required, ensuring security (no public access to AI agent tokens) and enabling free static hosting.

## Why a Static Showcase?

- **Security**: No public exposure of MCP server or AI agent (prevents token burning)
- **Cost**: Free static hosting (Vercel, Netlify, GitHub Pages)
- **Simplicity**: No backend deployment needed for the showcase
- **Performance**: Instant load times, no API latency
- **Resume Value**: Demonstrates full-stack capability while protecting production systems

## Tech Stack

- **Framework**: React 18+ with Vite (fast, modern build tool)
- **Styling**: TailwindCSS + shadcn/ui (beautiful components, modern design)
- **Charts**: Recharts (heart rate visualizations, interval charts)
- **State Management**: React Query (for managing mock data fetching)
- **Icons**: Lucide React (modern icon set)
- **Deployment**: Vercel/Netlify/GitHub Pages (static hosting)

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn/ui components
│   │   ├── Dashboard.tsx    # Main dashboard
│   │   ├── ActivityList.tsx # Activity list with mock sync
│   │   ├── ActivityDetail.tsx # Activity detail with HR chart
│   │   ├── IntervalDetection.tsx # Interval visualization
│   │   ├── AIChat.tsx       # Mock AI chat interface
│   │   └── Architecture.tsx # System architecture diagram
│   ├── data/
│   │   ├── mockActivities.ts # Mock activity data
│   │   ├── mockHeartRate.ts  # Mock HR time series
│   │   ├── mockIntervals.ts  # Mock detected intervals
│   │   └── mockChat.ts       # Mock AI conversations
│   ├── lib/
│   │   └── utils.ts         # Utility functions
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── public/
│   └── images/              # Screenshots, diagrams
├── package.json
├── tailwind.config.js
├── vite.config.ts
└── README.md
```

## Screens to Build

### 1. Dashboard (`/`)
- **Activity Summary**: Stats cards (total activities, this week, avg HR)
- **Recent Activities**: List of 5-10 recent mock activities
- **Sync Button**: Animated sync button with loading state → success toast
- **Quick Actions**: Buttons to navigate to other screens

### 2. Activity List (`/activities`)
- **Filterable List**: Activity type, date range filters (mock)
- **Activity Cards**: Type icon, date, duration, distance, avg HR
- **Pagination**: Mock pagination UI
- **Sort Options**: Date, duration, distance (mock)

### 3. Activity Detail (`/activities/:id`)
- **Activity Header**: Type, date, duration, distance, pace
- **Heart Rate Chart**: Line chart showing HR over time (mock data)
- **Detected Intervals**: Visual representation of intervals (colored zones on chart)
- **Statistics Table**: Min/max/avg HR, cadence, power (mock data)
- **AI Insights**: Pre-written AI analysis text

### 4. Interval Detection (`/analysis/intervals`)
- **Activity Selector**: Dropdown to select activity (mock)
- **Penalty Slider**: Interactive slider for detection sensitivity
- **Model Selector**: Radio buttons for RBF/Linear/Normal models
- **Detect Button**: Triggers animation → shows mock results
- **Interval Visualization**: Chart with colored zones for each interval
- **Interval Table**: Start, end, duration, HR stats for each interval

### 5. AI Chat Interface (`/ai-chat`)
- **Chat Interface**: Message input, message history
- **Pre-written Conversations**: 3-5 example conversations:
  - "Analyze my last run"
  - "Compare my recent cycling sessions"
  - "What's my training load this week?"
- **Typing Animation**: Simulated AI response delay
- **Message Types**: User messages (right), AI responses (left with avatar)

### 6. Architecture (`/architecture`)
- **System Diagram**: Static SVG or image showing:
  - Garmin Connect API
  - FastAPI Backend (MCP Server)
  - PostgreSQL Database
  - ZeroClaw AI Agent
  - React Frontend (this showcase)
- **Tech Stack List**: Badges for each technology
- **Data Flow**: Arrows showing how data moves through the system

## Mock Data Strategy

### Activities (`mockActivities.ts`)
```typescript
export const mockActivities = [
  {
    id: "1",
    type: "running",
    date: "2025-05-10",
    duration: 1800, // seconds
    distance: 5200, // meters
    avgHR: 145,
    maxHR: 172,
    pace: "5:45",
  },
  // ... 15-20 realistic activities
];
```

### Heart Rate Data (`mockHeartRate.ts`)
```typescript
export const mockHeartRateData = {
  "1": [120, 122, 125, 130, 135, 140, 145, 150, 148, 145, ...],
  // Generate realistic HR patterns for different activities
};
```

### Detected Intervals (`mockIntervals.ts`)
```typescript
export const mockIntervals = {
  "1": [
    { start: 0, end: 120, hrMean: 130, label: "Warm-up" },
    { start: 120, end: 600, hrMean: 160, label: "Tempo" },
    { start: 600, end: 720, hrMean: 140, label: "Cool-down" },
  ],
  // ... intervals for different activities
};
```

### AI Chat (`mockChat.ts`)
```typescript
export const mockConversations = [
  {
    id: 1,
    title: "Analyze Last Run",
    messages: [
      { role: "user", content: "Analyze my last run" },
      { role: "assistant", content: "Your last run on May 10th was 5.2km in 30 minutes..." },
    ],
  },
  // ... 3-5 example conversations
];
```

## Implementation Steps

### Phase 1: Project Setup
- [ ] Initialize React + Vite project
- [ ] Install dependencies (TailwindCSS, shadcn/ui, Recharts, Lucide)
- [ ] Set up project structure
- [ ] Configure TailwindCSS
- [ ] Set up shadcn/ui components

### Phase 2: Mock Data
- [ ] Create mockActivities.ts with 15-20 realistic activities
- [ ] Create mockHeartRate.ts with HR time series data
- [ ] Create mockIntervals.ts with detected intervals
- [ ] Create mockChat.ts with example conversations
- [ ] Create data utility functions

### Phase 3: Core Components
- [ ] Build Dashboard component with stats cards
- [ ] Build ActivityList component with filters
- [ ] Build ActivityDetail component with HR chart
- [ ] Build IntervalDetection component with visualization
- [ ] Build AIChat component with pre-written conversations
- [ ] Build Architecture component with system diagram

### Phase 4: Navigation & Layout
- [ ] Set up React Router
- [ ] Create navigation header
- [ ] Create responsive layout
- [ ] Add page transitions

### Phase 5: Polish & Interactivity
- [ ] Add loading animations
- [ ] Add toast notifications
- [ ] Add hover states
- [ ] Add mobile responsiveness
- [ ] Add dark mode support

### Phase 6: Deployment
- [ ] Build production bundle
- [ ] Deploy to Vercel/Netlify/GitHub Pages
- [ ] Test deployment
- [ ] Add custom domain (optional)

## Design Guidelines

### Color Scheme
- **Primary**: Blue/Indigo (trustworthy, fitness-related)
- **Secondary**: Green/Teal (health, success)
- **Accent**: Orange/Red (heart rate, intensity)
- **Background**: Light gray/white (clean, modern)
- **Dark Mode**: Dark slate/gray (easy on eyes)

### Typography
- **Font**: Inter or system-ui (clean, readable)
- **Headings**: Bold, larger sizes
- **Body**: Regular, comfortable line height
- **Numbers**: Monospace for metrics

### Components
- Use shadcn/ui components for consistency
- Rounded corners (medium radius)
- Subtle shadows
- Smooth transitions
- Clear visual hierarchy

## Deployment Options

### Vercel (Recommended)
```bash
npm install -g vercel
vercel deploy
```
- Free tier available
- Automatic HTTPS
- Custom domains
- Preview deployments

### Netlify
```bash
npm install -g netlify-cli
netlify deploy --prod
```
- Free tier available
- Automatic HTTPS
- Form handling (if needed)
- Edge functions (if needed later)

### GitHub Pages
```bash
npm run build
# Deploy dist/ folder to gh-pages branch
```
- Free
- Integrated with GitHub
- No custom domains on free tier

## Resume Presentation

### How to Describe on Resume
```
• Built full-stack Garmin fitness analysis platform with React frontend, FastAPI backend, and MCP protocol
• Implemented static showcase demo with mock data for public presentation (deployed on Vercel)
• Developed heart rate visualization and interval detection UI using Recharts and TailwindCSS
• Created AI chat interface demonstrating integration with ZeroClaw agent framework
```

### Demo Strategy
1. **Live Demo**: Share Vercel URL for immediate access
2. **Video Demo**: Record walkthrough of actual working system (with real backend)
3. **Code Tour**: Walk through backend code in interviews
4. **Architecture Discussion**: Explain MCP protocol and ZeroClaw integration

## Security Considerations

- **No API Keys**: Frontend uses only mock data
- **No Backend Calls**: Zero external HTTP requests
- **No Authentication**: Public access is safe
- **No Data Storage**: All data is client-side only
- **No Token Exposure**: AI agent remains private

## Future Enhancements (Optional)

If you want to add real connectivity later:
- [ ] Add environment variable for backend URL
- [ ] Implement real API calls with fallback to mock data
- [ ] Add authentication for real backend access
- [ ] Add settings page to configure backend connection
- [ ] Add demo mode toggle (mock vs real data)

## Related Documentation

- [Project README](../readme.md) - Overall project overview
- [MCP Server Implementation Plan](../mcp-server-implementation-plan.md) - Backend details
- [ZeroClaw Integration Guide](../zeroclaw-integration.md) - AI agent setup

## Success Criteria

- [ ] All 6 screens implemented with mock data
- [ ] Responsive design works on mobile/tablet/desktop
- [ ] Dark mode support
- [ ] Deployed to static hosting (Vercel/Netlify/GitHub Pages)
- [ ] Loading animations and transitions smooth
- [ ] Charts render correctly with mock data
- [ ] AI chat demonstrates pre-written conversations
- [ ] Architecture diagram clearly shows system components
- [ ] README with setup instructions
- [ ] GitHub repository organized and documented
