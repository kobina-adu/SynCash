# Use official Node.js LTS image
FROM node:18-alpine AS base

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --production

# Copy the rest of the app
COPY . .

# Build the Next.js app
RUN npm run build

# Run Next.js in production mode
EXPOSE 3000
CMD ["npm", "start"]
