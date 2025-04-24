import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from './layouts/ProtectedRoute';
import { AppLayout } from './layouts/AppLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Planning from './pages/Planning';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Protected routes with layout */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/planning" element={<Planning />} />
        </Route>

        {/* Public routes (login) */}
        <Route path="/" element={<Login />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;