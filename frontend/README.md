# Northstar dashboard frontend

React and TypeScript dashboard for the logistics API.

## Run locally

Start FastAPI from the repository root:

```bash
fastapi dev backend/app/main.py
```

Then start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies requests from `/api/*` to `http://127.0.0.1:8000/*` during local development.

## API configuration

All API URLs are defined in `src/api/endpoints.ts`. To point a deployed frontend at a different API base URL, set:

```bash
VITE_API_BASE_URL=https://api.example.com
```

The default base is `/api`, which works with the included development proxy and with a production reverse proxy using the same prefix.

## Checks

```bash
npm run lint
npm run build
```
