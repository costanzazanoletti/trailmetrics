import { Navbar } from "../components/Navbar";
import { NavLink, Outlet } from "react-router-dom";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Top Navbar */}
      <Navbar />

      {/* Horizontal menu with sections */}
      <div className="flex gap-6 px-6 py-4 bg-white shadow-sm border-b">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `text-sm font-medium ${
              isActive ? "text-blue-600" : "text-gray-600"
            } hover:underline`
          }
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/planning"
          className={({ isActive }) =>
            `text-sm font-medium ${
              isActive ? "text-blue-600" : "text-gray-600"
            } hover:underline`
          }
        >
          Planning
        </NavLink>
      </div>

      {/* Dynamic content */}
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  );
}
