# BharatVoice implementation update

## Scope of this update
This update preserves the existing FastAPI + SQLite backend and React + TypeScript + Vite frontend. It improves the dashboard and core order workflows without replacing the product architecture.

## Important backend defect fixed
The voice-order service called the asynchronous STT `transcribe()` method without awaiting it. This meant the voice-to-order endpoint could receive a coroutine instead of a transcription response. The service is now asynchronous and the route awaits it.

## Order lifecycle improvements
- Voice upload creates an order in `awaiting_confirmation` or `needs_clarification`; it never auto-confirms.
- Saving a non-empty corrected item list on a `needs_clarification` order moves it to `awaiting_confirmation`.
- The frontend only enables confirmation for `awaiting_confirmation` orders with at least one item.
- Added integration tests for voice-order creation, explicit confirmation, and resolving a clarification.

## Frontend improvements
- Rebuilt Dashboard to retain KPI cards and useful panels even when there are zero orders.
- Dashboard fetches paginated real order data (up to a bounded maximum) and clearly warns if that maximum is reached.
- Rebuilt Voice Orders with microphone recording, upload validation, playback preview, a 30-second recording cap, clear processing/error states, and an explicit review handoff.
- Rebuilt All Orders with server-side status filtering and pagination plus client-side search within the loaded page.
- Rebuilt Order Details with editable line items, add/remove controls, clarification resolution, explicit confirmation/cancellation, and spoken confirmation playback.
- Rebuilt Settings to match the actual `/api/health` response schema.
- Updated responsive application shell, sidebar, shared status/stat/action components, global styling, and toast notifications.

## Configuration fixes
- Added `GNANI_TTS_SPEED` and `GNANI_TTS_TIMEOUT_SECONDS`, which the TTS service already referenced.
- Mock mode now reflects the explicit `USE_MOCK_GNANI` setting. Explicit real mode without a key remains a configuration error; it does not silently switch to mock mode.

## Verification performed in this environment
- Backend: `python -m pytest -q` — **57 passed**.
- Backend: `python -m compileall -q app` — passed.
- Frontend: TypeScript transpile/JSX syntax parse — **18 TS/TSX files parsed successfully**.
- Full `npx tsc --noEmit` and `npm run build` could not be completed here because dependency installation (`npm ci`) timed out and Vite/type packages were unavailable in this environment. Run those two commands locally after extracting the archive.

## Known limitations / next checks
- Live Gnani STT/TTS has not been verified with real credentials.
- Mock STT returns a deterministic sample transcript; mock TTS returns silent WAV audio. The UI and Settings page explicitly identify mock mode.
- Audio duration is capped in the browser recorder; the backend validates file size and WAV duration. Non-WAV upload duration should be tested/strengthened before production.
- Authentication, per-shop tenancy, deployment hardening, and production observability are outside this update.
