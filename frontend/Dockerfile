FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Ensure proper permissions and ownership
RUN chown -R node:node /app
USER node

# Expose port
EXPOSE 3000

# Start development server with explicit host binding
CMD ["npm", "start", "--", "--host", "0.0.0.0"]
