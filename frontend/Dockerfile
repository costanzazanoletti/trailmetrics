# Use the official Node.js image
FROM node:18 AS build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json (if exists) first
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install --frozen-lockfile && npm install --save-dev @types/node

# Copy the rest of the application
COPY . .

# Pass environment variables at build time
ARG VITE_API_AUTH__BASE_URL
ARG VITE_API_ACTIVITY_BASE_URL
ARG VITE_STRAVA_CLIENT_ID

# Ensure they are available in the build
ENV VITE_API_AUTH__BASE_URL=$VITE_API_AUTH__BASE_URL
ENV VITE_API_ACTIVITY_BASE_URL=$VITE_API_ACTIVITY_BASE_URL
ENV VITE_STRAVA_CLIENT_ID=$VITE_STRAVA_CLIENT_ID

# Build the frontend (this will generate the production-ready files in dist/)
RUN npm run build

# --- Serve with Nginx ---
FROM nginx:alpine AS production

# Copy custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built frontend from build step
COPY --from=build /app/dist /usr/share/nginx/html

# Expose the port that Nginx serves on
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
