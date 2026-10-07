FROM node:24-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npx ng build

FROM caddy:2-alpine
COPY --from=build /app/dist/app/browser /srv
