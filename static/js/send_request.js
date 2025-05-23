/**
 * API Request handling functions for ProbeFlex
 */

/**
 * Get query parameters from the UI
 * @returns {Object} Object containing parameter key-value pairs
 */
function getParams() {
    const params = {};
    const paramRows = document.querySelectorAll('.param-rows .row');
    if (paramRows.length === 0) {
        console.warn('No param rows found');
        return {};
    }
    
    paramRows.forEach(row => {
        const keyElement = row.querySelector('.param-key');
        const valueElement = row.querySelector('.param-value');
        
        if (keyElement && valueElement) {
            const key = keyElement.value.trim();
            const value = valueElement.value.trim();
            if (key) {
                params[key] = value;
            }
        }
    });
    return params;
}

/**
 * Get request headers from the UI
 * @returns {Object} Object containing header key-value pairs
 */
function getHeaders() {
    const headers = {};
    const headerRows = document.querySelectorAll('.header-rows .row');
    if (headerRows.length === 0) {
        console.warn('No header rows found');
    } else {
        headerRows.forEach(row => {
            const keyElement = row.querySelector('.header-key');
            const valueElement = row.querySelector('.header-value');
            
            if (keyElement && valueElement) {
                const key = keyElement.value.trim();
                const value = valueElement.value.trim();
                if (key) {
                    headers[key] = value;
                }
            }
        });
    }
    
    // Add auth headers if needed
    const authTypeElement = document.getElementById('auth-type');
    if (!authTypeElement) {
        console.warn('auth-type element not found');
        return headers;
    }
    
    const authType = authTypeElement.value;
    if (authType === 'bearer') {
        const tokenElement = document.getElementById('bearer-token');
        if (tokenElement) {
            const token = tokenElement.value;
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }
    } else if (authType === 'apikey') {
        const keyNameElement = document.getElementById('apikey-name');
        const keyValueElement = document.getElementById('apikey-value');
        const locationElement = document.getElementById('apikey-location');
        
        if (keyNameElement && keyValueElement && locationElement) {
            const keyName = keyNameElement.value;
            const keyValue = keyValueElement.value;
            const location = locationElement.value;
            
            if (keyName && keyValue && location === 'header') {
                headers[keyName] = keyValue;
            }
        }
    }
    
    return headers;
}

/**
 * Get request body data from the UI
 * @returns {Object|string} Body data as object or string depending on type
 */
function getBody() {
    const bodyTypeElement = document.getElementById('body-type');
    if (!bodyTypeElement) {
        console.warn('body-type element not found, returning empty object');
        return {};
    }
    
    const bodyType = bodyTypeElement.value;
    
    if (bodyType === 'json') {
        const jsonEditorElement = document.getElementById('json-editor');
        if (!jsonEditorElement) {
            console.warn('json-editor element not found, returning empty object');
            return {};
        }
        
        const jsonText = jsonEditorElement.value.trim();
        if (!jsonText) {
            return {};
        }
        
        try {
            return JSON.parse(jsonText);
        } catch (e) {
            alert('Invalid JSON: ' + e.message);
            return {};
        }
    } else if (bodyType === 'form') {
        const formData = {};
        const formRows = document.querySelectorAll('.form-rows .row');
        if (formRows.length === 0) {
            console.warn('No form rows found');
            return {};
        }
        
        formRows.forEach(row => {
            const keyElement = row.querySelector('.form-key');
            const valueElement = row.querySelector('.form-value');
            
            if (keyElement && valueElement) {
                const key = keyElement.value.trim();
                const value = valueElement.value.trim();
                if (key) {
                    formData[key] = value;
                }
            }
        });
        return formData;
    } else if (bodyType === 'raw') {
        const rawEditorElement = document.getElementById('raw-editor');
        if (!rawEditorElement) {
            console.warn('raw-editor element not found, returning empty string');
            return '';
        }
        return rawEditorElement.value;
    }
    
    return {};
}

/**
 * Get authentication data from the UI
 * @returns {Object} Authentication configuration
 */
function getAuth() {
    const authTypeElement = document.getElementById('auth-type');
    if (!authTypeElement) {
        console.warn('auth-type element not found');
        return { type: 'none' };
    }
    
    const authType = authTypeElement.value;
    const auth = { type: authType };
    
    if (authType === 'basic') {
        const usernameElement = document.getElementById('basic-username');
        const passwordElement = document.getElementById('basic-password');
        
        if (usernameElement && passwordElement) {
            auth.username = usernameElement.value;
            auth.password = passwordElement.value;
        } else {
            console.warn('Basic auth elements not found');
        }
    } else if (authType === 'bearer') {
        const tokenElement = document.getElementById('bearer-token');
        if (tokenElement) {
            auth.token = tokenElement.value;
        } else {
            console.warn('Bearer token element not found');
        }
    } else if (authType === 'apikey') {
        const keyElement = document.getElementById('apikey-name');
        const valueElement = document.getElementById('apikey-value');
        const locationElement = document.getElementById('apikey-location');
        
        if (keyElement && valueElement && locationElement) {
            auth.key = keyElement.value;
            auth.value = valueElement.value;
            auth.location = locationElement.value;
        } else {
            console.warn('API key auth elements not found');
        }
    }
    
    return auth;
}

/**
 * Update URL with query parameters
 * @param {string} url - The base URL
 * @param {Object} params - Query parameters
 * @returns {string} Updated URL with query parameters
 */
function updateQueryParams(url, params) {
    try {
        const urlObj = new URL(url);
        for (const [key, value] of Object.entries(params)) {
            urlObj.searchParams.set(key, value);
        }
        return urlObj.toString();
    } catch (e) {
        console.error("Error updating URL parameters:", e);
        return url;
    }
}

/**
 * Update the response UI with a status message
 * @param {string} message - Message to display
 */
function updateResponse(message) {
    document.getElementById('status-code').textContent = 'Processing...';
    document.getElementById('status-code').className = 'badge bg-secondary';
    document.getElementById('response-time').textContent = '0 ms';
    document.getElementById('response-body-content').innerHTML = `<p class="text-muted">${message}</p>`;
    document.getElementById('response-headers-content').innerHTML = '<p class="text-muted">Waiting for response...</p>';
}

/**
 * Display the API response in the UI
 * @param {Object} data - Response data from the API
 */
function displayResponse(data) {
    // Update status code
    const statusCode = data.status_code;
    document.getElementById('status-code').textContent = statusCode;
    
    let statusClass = 'bg-secondary';
    if (statusCode >= 200 && statusCode < 300) {
        statusClass = 'bg-success';
    } else if (statusCode >= 300 && statusCode < 400) {
        statusClass = 'bg-info';
    } else if (statusCode >= 400 && statusCode < 500) {
        statusClass = 'bg-warning';
    } else if (statusCode >= 500) {
        statusClass = 'bg-danger';
    }
    document.getElementById('status-code').className = `badge ${statusClass}`;
    
    // Update response time
    document.getElementById('response-time').textContent = `${Math.round(data.time || 0)} ms`;
    
    // Update response body
    const responseBodyContainer = document.getElementById('response-body-content');
    responseBodyContainer.innerHTML = '';
    
    if (typeof data.body === 'object') {
        // Check if JSONFormatter is available
        if (typeof JSONFormatter === 'function') {
            try {
                const formatter = new JSONFormatter(data.body, 2, {
                    hoverPreviewEnabled: true,
                    hoverPreviewArrayCount: 100,
                    hoverPreviewFieldCount: 5,
                    theme: 'dark',
                    animateOpen: true,
                    animateClose: true
                });
                responseBodyContainer.appendChild(formatter.render());
            } catch (e) {
                const pre = document.createElement('pre');
                pre.textContent = JSON.stringify(data.body, null, 2);
                responseBodyContainer.appendChild(pre);
            }
        } else {
            const pre = document.createElement('pre');
            pre.textContent = JSON.stringify(data.body, null, 2);
            responseBodyContainer.appendChild(pre);
        }
    } else {
        const pre = document.createElement('pre');
        pre.textContent = data.body;
        responseBodyContainer.appendChild(pre);
    }
    
    // Update response headers
    const responseHeadersContainer = document.getElementById('response-headers-content');
    responseHeadersContainer.innerHTML = '';
    
    // Check if JSONFormatter is available
    if (typeof JSONFormatter === 'function') {
        try {
            const formatter = new JSONFormatter(data.headers, 2);
            responseHeadersContainer.appendChild(formatter.render());
        } catch (e) {
            const pre = document.createElement('pre');
            pre.textContent = JSON.stringify(data.headers, null, 2);
            responseHeadersContainer.appendChild(pre);
        }
    } else {
        const pre = document.createElement('pre');
        pre.textContent = JSON.stringify(data.headers, null, 2);
        responseHeadersContainer.appendChild(pre);
    }
}

/**
 * Send the API request with data from the UI
 */
function sendRequest() {
    const methodElement = document.getElementById('method-ajax');
    const urlElement = document.getElementById('url-ajax');
    
    if (!methodElement) {
        alert('Method selector not found');
        return;
    }
    
    if (!urlElement) {
        alert('URL input not found');
        return;
    }
    
    const method = methodElement.value;
    let url = urlElement.value.trim();
    
    if (!url) {
        alert('Please enter a URL');
        return;
    }
    
    // Add protocol if missing
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
    }
    
    const params = getParams();
    const headers = getHeaders();
    const body = getBody();
    const auth = getAuth();
    
    // Get follow redirects and verify SSL options with fallbacks
    const followRedirectsElement = document.getElementById('follow-redirects');
    const verifySSLElement = document.getElementById('verify-ssl');
    
    const followRedirects = followRedirectsElement ? followRedirectsElement.checked : true;
    const verifySSL = verifySSLElement ? verifySSLElement.checked : true;
    
    // Update URL with query params for GET, HEAD, DELETE, OPTIONS
    if (method === 'GET' || method === 'HEAD' || method === 'DELETE' || method === 'OPTIONS') {
        try {
            url = updateQueryParams(url, params);
        } catch (e) {
            alert('Invalid URL: ' + e.message);
            return;
        }
    }
    
    // Update status indicator
    updateResponse('Sending request...');
    
    console.log('Sending request to:', url);
    console.log('Method:', method);
    console.log('Headers:', headers);
    console.log('Body:', body);
    console.log('Auth:', auth);
    console.log('Verify SSL:', verifySSL);
    
    // Get CSRF token
    const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfTokenElement) {
        alert('CSRF token not found. Please refresh the page.');
        return;
    }
    const csrfToken = csrfTokenElement.value;
    
    // Send the request
    fetch('/api/send/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            url: url,
            method: method,
            params: params,
            headers: headers,
            body: body,
            auth: auth,
            follow_redirects: followRedirects,
            verify_ssl: verifySSL
        })
    })
    .then(response => {
        console.log('Response received:', response);
        if (!response.ok) {
            throw new Error('Server returned ' + response.status + ' ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        console.log('Data received:', data);
        displayResponse(data);
    })
    .catch(error => {
        console.error('Error:', error);
        
        const statusCodeElement = document.getElementById('status-code');
        if (statusCodeElement) {
            statusCodeElement.textContent = 'Error';
            statusCodeElement.className = 'badge bg-danger';
        }
        
        // Create proper error displays
        const errorBodyContainer = document.getElementById('response-body-content');
        if (errorBodyContainer) {
            errorBodyContainer.innerHTML = '';
            const errorBodyMessage = document.createElement('div');
            errorBodyMessage.className = 'alert alert-danger';
            errorBodyMessage.textContent = 'Error: ' + error.message;
            errorBodyContainer.appendChild(errorBodyMessage);
        }
        
        const errorHeadersContainer = document.getElementById('response-headers-content');
        if (errorHeadersContainer) {
            errorHeadersContainer.innerHTML = '';
            const errorHeadersMessage = document.createElement('div');
            errorHeadersMessage.className = 'alert alert-danger';
            errorHeadersMessage.textContent = 'Error: ' + error.message;
            errorHeadersContainer.appendChild(errorHeadersMessage);
        }
    });
} 