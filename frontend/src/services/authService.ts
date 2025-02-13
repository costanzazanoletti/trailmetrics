import axios from 'axios';
import { API_AUTH_BASE_URL } from '../config/apiConfig';

// Create an axios instance with default settings
const apiClient = axios.create({
  baseURL: API_AUTH_BASE_URL,
  withCredentials: true, // Ensures cookies (JWT) are sent with requests
});

// Function to check if the user is authenticated
export const checkAuth = async () => {
  try {
    const res = await apiClient.get('/api/auth/user');
    return res.data;
  } catch (error) {
    console.error('Authentication check failed:', error);
    return { authenticated: false };
  }
};

// Function to start Strava authentication
export const loginWithStrava = () => {
  window.location.href = `${API_AUTH_BASE_URL}/oauth2/authorization/strava`;
};

// Function to log out
export const logout = async () => {
  try {
    await apiClient.post('/api/auth/logout'); // Calls backend to clear session
  } catch (error) {
    console.error('Logout failed:', error);
  } finally {
    localStorage.removeItem('auth-storage'); // Clears persisted auth state
    window.location.href = '/'; // Redirect to home
  }
};
