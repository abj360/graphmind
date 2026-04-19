FROM node:22-alpine

WORKDIR /app

COPY api/package.json api/package-lock.json ./
RUN npm ci --omit=dev

COPY api/src ./src

EXPOSE 4000
CMD ["node", "src/index.js"]
