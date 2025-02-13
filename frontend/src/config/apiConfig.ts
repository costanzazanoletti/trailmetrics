export const STRAVA_CLIENT_ID = import.meta.env.VITE_STRAVA_CLIENT_ID;
export const BASE_URL = import.meta.env.VITE_BASE_URL;
export const API_AUTH_BASE_URL = import.meta.env.VITE_API_AUTH__BASE_URL;
export const API_ACTIVITY_BASE_URL = import.meta.env.VITE_API_ACTIVITY_BASE_URL;
export const STRAVA_AUTH_URL = `https://www.strava.com/oauth/authorize?client_id=${STRAVA_CLIENT_ID}&response_type=code&redirect_uri=${API_AUTH_BASE_URL}&approval_prompt=force&scope=read,activity:read_all`;
