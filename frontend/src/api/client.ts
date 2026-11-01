const API_BASE_URL = '/api/v1';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('flowguard_token');
  const headers = new Headers(options.headers || {});

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // If not FormData, default content-type to application/json
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    localStorage.removeItem('flowguard_token');
    localStorage.removeItem('flowguard_user');
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    throw new Error('Session expired. Please log in again.');
  }

  if (!response.ok) {
    let errorDetail = 'An error occurred';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail);
  }

  // Check if response is JSON or blob (like CSV)
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }
  return response as any;
}

export async function downloadFile(
  endpoint: string,
  defaultFilename?: string
): Promise<void> {
  const token = localStorage.getItem('flowguard_token');
  const headers = new Headers();

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Normalize endpoint URL
  let url = endpoint;
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    if (url.startsWith('/api/v1/')) {
      // URL already has full prefix
    } else if (url.startsWith('/api/v1')) {
      url = url.replace('/api/v1', API_BASE_URL);
    } else {
      url = `${API_BASE_URL}${url.startsWith('/') ? url : `/${url}`}`;
    }
  }

  const response = await fetch(url, {
    method: 'GET',
    headers
  });

  if (response.status === 401) {
    localStorage.removeItem('flowguard_token');
    localStorage.removeItem('flowguard_user');
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    throw new Error('Session expired. Please log in again.');
  }

  if (!response.ok) {
    let errorDetail = 'Download failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = (await response.text()) || `HTTP ${response.status} ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  // Extract filename from Content-Disposition header if available
  let filename = defaultFilename;
  const disposition = response.headers.get('content-disposition');
  if (disposition) {
    const filenameMatch = disposition.match(/filename\*?=(?:UTF-8'')?["']?([^"';\n\r]+)["']?/i);
    if (filenameMatch && filenameMatch[1]) {
      filename = decodeURIComponent(filenameMatch[1].trim());
    }
  }

  if (!filename) {
    const cleanPath = url.split('?')[0];
    const segments = cleanPath.split('/');
    filename = segments[segments.length - 1] || 'downloaded_file';
  }

  const blob = await response.blob();
  const objectUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);

  setTimeout(() => {
    window.URL.revokeObjectURL(objectUrl);
  }, 100);
}
