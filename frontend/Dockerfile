FROM node:16.16-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --force
COPY bundles-src/ bundles-src/
RUN ./node_modules/.bin/parcel build bundles-src/index.js --dist-dir /app/bundles --public-url="./"
CMD ["echo", "Frontend build complete"]
