import axios from 'axios';
import { API_ACTIVITY_BASE_URL } from '../config/apiConfig';

// Create an axios instance with default settings
const apiClient = axios.create({
  baseURL: API_ACTIVITY_BASE_URL,
  withCredentials: true, // Ensures cookies (JWT) are sent with requests
});

export const fetchActivities = async () => {
  try {
    const res = await apiClient.get('/api/activities');
    return res.data;
  } catch (error) {
    console.error('Unable to fetch activities');
    return [];
  }
};
