FROM node:22-alpine
WORKDIR /app
COPY . .
RUN npm install && npm run build
ENV PORT=3001
EXPOSE 3001
CMD ["npm", "start"]
