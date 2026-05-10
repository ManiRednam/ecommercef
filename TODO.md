# TODO - Backend refactor + Frontend/Backend integration

## Plan (approved)
1. Create backend structure: `backend/functions/` and `backend/routes/` packages.
2. Extract shared helpers from `backend/app.py` into:
   - `backend/functions/auth.py` (token_required, getUserByToken)
   - `backend/functions/http.py` (json_success, json_error, getDataFromToken if needed)
3. Extract `/api/admin/*` endpoints into:
   - `backend/routes/api_admin.py` using a Flask Blueprint.
4. Refactor `backend/app.py` to:
   - define `create_app()`
   - register `api_admin` blueprint
   - keep existing non-API routes unchanged for now
5. Integrate frontend by serving `frontend/build` from Flask:
   - serve `index.html` for non-`/api/*` routes (SPA fallback)
6. Validate:
   - `GET /api/admin/dashboard`, `GET/POST /api/admin/products`, `GET /api/admin/orders` work
   - React loads served pages after running `npm run build`.

## Progress
- [ ] Step 1: Create backend folders/files
- [ ] Step 2: Move auth/json helper code
- [ ] Step 3: Move /api/admin routes into blueprint
- [ ] Step 4: Refactor app.py with create_app + blueprint registration
- [ ] Step 5: Serve frontend/build + SPA fallback
- [ ] Step 6: Test endpoints and SPA loading

