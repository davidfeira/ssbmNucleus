const port = window.electron?.backendPort || 5000;
export const BACKEND_URL = `http://127.0.0.1:${port}`;
export const API_URL = `${BACKEND_URL}/api/mex`;
