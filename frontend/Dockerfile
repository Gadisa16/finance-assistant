FROM node:20-alpine
WORKDIR /app
COPY frontend/package.json frontend/vite.config.js /app/
RUN npm install
COPY frontend/src /app/src
EXPOSE 5173
CMD ["npm", "run", "dev"]
