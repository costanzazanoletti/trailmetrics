import axios from 'axios';

const API_URL = 'https://your-backend-api.com/login';

export const login = async (username: string, password: string) => {
  try {
    const response = await axios.post(API_URL, { username, password });
    return response.data;
  } catch (error) {
    console.error('Login failed', error);
    throw new Error('Authentication Failed');
  }
};
