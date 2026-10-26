# Stage 1: Build static bundle
FROM node:22-alpine AS builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# Stage 2: Serve with lean Nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
