# TrailMetrics Frontend

This is the web interface for **TrailMetrics**, built with **React**, **TypeScript**, and **Vite**. The application allows athletes to authenticate via Strava, explore activity data, visualize metrics such as cadence and efficiency, and plan training strategies.

## Overview

Features include:

- OAuth2 login via Strava
- Dynamic map and elevation chart visualization
- Segment list with gradient, terrain, weather, and efficiency data
- Interactive dashboard for activity metrics
- Panel to explore similar segments and comparative stats

## Setup

### Prerequisites

- Node.js (>= 18)
- npm or yarn

### Install Dependencies

```bash
npm install
# or
yarn install
```

## Running the App Locally

Start the development server:

```bash
npm run dev
# or
yarn dev
```

The app will be available at `http://localhost:3000`.

## Environment Configuration

All runtime variables are defined in `.env` and documented in `.env.example`. These include:

```env
VITE_API_AUTH__BASE_URL=http://localhost:8080
VITE_API_ACTIVITY_BASE_URL=http://localhost:8081
VITE_STRAVA_CLIENT_ID=your_client_id
```

These variables configure the backend endpoints and Strava OAuth client.

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── assets/          # Icons and images
│   ├── components/      # Shared UI components
│   ├── config/          # Environment setup
│   ├── hooks/           # Custom React hooks
│   ├── layouts/         # Page layouts
│   ├── mappers/         # Mapping API responses to frontend models
│   ├── pages/           # Route views (Dashboard, Planning)
│   ├── services/        # API functions
│   ├── store/           # Zustand state management
│   ├── styles/          # Tailwind + custom styles
│   ├── types/           # TypeScript interfaces
│   └── utils/           # Utility functions
```

## Linting and Formatting

The project uses ESLint and Prettier. Run:

```bash
npm run lint
npm run format
```

## Testing

Tests are not currently implemented in the frontend.

## More Information

For overall architecture and backend integration, see the [Developer Guide](../../docs/developer-guide.md).
