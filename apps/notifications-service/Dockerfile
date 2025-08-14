# Stage 1: Build
FROM node:18-alpine AS build

WORKDIR /app

# Install dependencies first (better caching)
COPY package*.json ./
RUN npm install

# Copy all files and build
COPY . .
RUN npm run build

# Stage 2: Run (Production)
FROM node:18-alpine AS production

WORKDIR /app

# Copy only necessary files for running
COPY package*.json ./
RUN npm install --omit=dev

# Copy build output from the previous stage
COPY --from=build /app/dist ./dist

# The port the API Gateway listens on
EXPOSE 8040

CMD ["node", "dist/index.js"]
