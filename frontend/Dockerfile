FROM node:20-alpine
WORKDIR /app
COPY frontend/package.json frontend/vite.config.js frontend/tsconfig.json frontend/tailwind.config.cjs frontend/postcss.config.cjs /app/
RUN npm install
COPY frontend/index.html /app/index.html
COPY frontend/src /app/src
EXPOSE 5173
CMD ["npm", "run", "dev"]
