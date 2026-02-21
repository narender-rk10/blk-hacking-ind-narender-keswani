# Build: docker build -t blk-hacking-ind-narender-frontend .
# Using node:20-alpine for build (minimal size)
# Using nginx:alpine for serving (production-grade, ~23MB)
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
