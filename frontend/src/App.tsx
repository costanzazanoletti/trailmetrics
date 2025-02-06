import React, { useState } from 'react';
import { login } from './services/authService';
import { useUserStore } from './store/userStore';

const App = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const setUser = useUserStore((state) => state.setUser);
  const user = useUserStore((state) => state.user);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const userData = await login(username, password);
      setUser(userData);
      alert('Login Success');
    } catch (error) {
      alert('Login Error');
    }
  };

  const handleLogout = () => {
    setUser(null);
    alert('Logout success');
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center">
      {user ? (
        <div>
          <h1 className="text-4xl text-green-500">
            Benvenuto, {user.username}!
          </h1>
          <button
            onClick={handleLogout}
            className="mt-4 p-2 bg-red-500 text-white rounded"
          >
            Logout
          </button>
        </div>
      ) : (
        <form onSubmit={handleLogin} className="flex flex-col space-y-4">
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="p-2 border border-gray-300"
            placeholder="Username"
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="p-2 border border-gray-300"
            placeholder="Password"
            required
          />
          <button type="submit" className="p-2 bg-blue-500 text-white rounded">
            Login
          </button>
        </form>
      )}
    </div>
  );
};

export default App;
