// Dev override: open http://localhost:3000/?backendPort=NNNNN to point a
// browser preview at a test backend instead of the app's port-5000 instance.
const port = window.electron?.backendPort
  || new URLSearchParams(window.location.search).get('backendPort')
  || 5000;
export const BACKEND_URL = `http://127.0.0.1:${port}`;
export const API_URL = `${BACKEND_URL}/api/mex`;
