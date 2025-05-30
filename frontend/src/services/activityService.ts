import axios from 'axios';
import { PlannedActivityInput } from '../types/activity';
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
    const res = await apiClient.get('/api/activities', {
      params: { page, size },
    });
    return res.data.data;
  } catch (error) {
    console.error('Unable to fetch activities', error);
    throw error;
  }
};

export const fetchActivityById = async (id: string) => {
  try {
    const res = await apiClient.get(`/api/activities/${id}`);
    return res.data.data;
  } catch (error) {
    console.error('Unable to fetch activity details', error);
    throw error;
  }
};

export const fetchActivityStreams = async (id: string) => {
  try {
    const res = await apiClient.get(`/api/activities/${id}/streams`);
    return res.data.data;
  } catch (error) {
    console.error('Unable to fetch activity streams', error);
    throw error;
  }
};

export const fetchActivitySegments = async (id: string) => {
  try {
    const res = await apiClient.get(`/api/activities/${id}/segments`);
    return res.data.data;
  } catch (error) {
    console.error('Unable to fetch activity segments', error);
    throw error;
  }
};

export const fetchSimilarSegments = async (segmentId: string) => {
  try {
    const res = await apiClient.get(`/api/segments/${segmentId}/similar`);
    return res.data.data;
  } catch (error) {
    console.error('Unable to fetch similar segments', error);
    throw error;
  }
};

export const fetchTopSegmentsByGrade = async (segmentId: string) => {
  try {
    const res = await apiClient.get(`/api/segments/${segmentId}/top-grade`);
    return res.data.data;
  } catch (error) {
    console.error('Unable to fetch top segments by grade', error);
    throw error;
  }
};

export const syncActivities = async () => {
  try {
    const res = await apiClient.get(`/api/activities/sync`);
    return res.data.data;
  } catch (error) {
    console.error('Unable to sync activities', error);
    throw error;
  }
};

export const fetchPlannedActivities = async (
  page = 0,
  size = 10
): Promise<PaginatedActivitiesResponse> => {
  try {
    const res = await apiClient.get('/api/activities/planned', {
      params: { page, size },
    });
    return res.data.data;
  } catch (error) {
    console.error('Unable to fetch planned activities', error);
    throw error;
  }
};

export const createPlannedActivity = async (
  data: PlannedActivityInput,
  file: File
): Promise<void> => {
  try {
    const formData = new FormData();
    formData.append('data', JSON.stringify(data));
    formData.append('file', file);

    await apiClient.post('/api/activities/planned', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      withCredentials: true,
    });
  } catch (error) {
    console.error('Failed to create planned activity', error);
    throw error;
  }
};
