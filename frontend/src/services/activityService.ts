import axios from 'axios';
import { API_ACTIVITY_BASE_URL } from '../config/apiConfig';

// Create an axios instance with default settings
const apiClient = axios.create({
  baseURL: API_ACTIVITY_BASE_URL,
  withCredentials: true, // Ensures cookies (JWT) are sent with requests
});

export interface PaginatedActivitiesResponse {
  content: any[]; 
  totalPages: number;
  totalElements: number;
  size: number;
  number: number; // current page
}

export const fetchActivities = async (
  page = 0,
  size = 10
): Promise<PaginatedActivitiesResponse> => {
  try {
    const res = await apiClient.get("/api/activities", {
      params: { page, size },
    });
    return res.data.data;
  } catch (error) {
    console.error("Unable to fetch activities", error);
    throw error;
  }
};

export const fetchActivityById = async (id: string) => {
  const res = await apiClient.get(`/api/activities/${id}`);
  return res.data.data; 
};

