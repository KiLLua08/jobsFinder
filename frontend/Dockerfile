FROM node:22-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Set the API URL before copying source so next.config.ts picks it up
ARG NEXT_PUBLIC_API_URL=http://web:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Copy source (excludes .env.local via .dockerignore)
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
