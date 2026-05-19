# Frontend Overview

The frontend is a Vue 3 + Vite app for the DigiHuman assistant.

## Directory Guide

- `src/views`: page-level screens.
- `src/components`: reusable components such as navigation, status, and Live2D.
- `src/composables`: shared browser-side logic for auth, theme, audio, and
  health detail.
- `src/router`: route definitions and login guard.
- `src/lib/live2d`: Pixi/Live2D integration.
- `public`: static assets served by Vite, including Live2D models and vendor
  files.
- `dist`: generated build output.

## Development

Use the Vite dev server:

```powershell
cd frontend
npm run dev
```

The dev server proxies `/api`, `/health`, and `/ws` to the backend on port 8001.
