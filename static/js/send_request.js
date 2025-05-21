/**
 * API Request handling functions for ProbeFlex
 */

/**
 * Get query parameters from the UI
 * @returns {Object} Object containing parameter key-value pairs
 */
function getParams() {
    const params = {};
    document.querySelectorAll('.param-rows .row').forEach(row => {
        const key = row.querySelector('.param-key').value.trim();
        const value = row.querySelector('.param-value').value.trim();
        if (key) {
            params[key] = value;
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
    document.querySelectorAll('.header-rows .row').forEach(row => {
        const key = row.querySelector('.header-key').value.trim();
        const value = row.querySelector('.header-value').value.trim();
        if (key) {
            headers[key] = value;
        }
    });
    
    // Add auth headers if needed
    const authType = document.getElementById('auth-type').value;
    if (authType === 'bearer') {
        const token = document.getElementById('bearer-token').value;
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    } else if (authType === 'apikey') {
        const keyName = document.getElementById('apikey-name').value;
        const keyValue = document.getElementById('apikey-value').value;
        const location = document.getElementById('apikey-location').value;
        
        if (keyName && keyValue && location === 'header') {
            headers[keyName] = keyValue;
        }
    }
    
    return headers;
}

/**
 * Get request body data from the UI
 * @returns {Object|string} Body data as object or string depending on type
 */
function getBody() {
    const bodyType = document.getElementById('body-type').value;
    
    if (bodyType === 'json') {
        const jsonText = document.getElementById('json-editor').value.trim();
        try {
            return jsonText ? JSON.parse(jsonText) : {};
        } catch (e) {
            alert('Invalid JSON: ' + e.message);
            return {};
        }
    } else if (bodyType === 'form') {
        const formData = {};
        document.querySelectorAll('.form-rows .row').forEach(row => {
            const key = row.querySelector('.form-key').value.trim();
            const value = row.querySelector('.form-value').value.trim();
            if (key) {
                formData[key] = value;
            }
        });
        return formData;
    } else if (bodyType === 'raw') {
        return document.getElementById('raw-editor').value;
    }
    
    return {};
}

/**
 * Get authentication data from the UI
 * @returns {Object} Authentication configuration
 */
function getAuth() {
    const authType = document.getElementById('auth-type').value;
    const auth = { type: authType };
    
    if (authType === 'basic') {
        auth.username = document.getElementById('basic-username').value;
        auth.password = document.getElementById('basic-password').value;
    } else if (authType === 'bearer') {
        auth.token = document.getElementById('bearer-token').value;
    } else if (authType === 'apikey') {
        auth.key = document.getElementById('apikey-name').value;
        auth.value = document.getElementById('apikey-value').value;
        auth.location = document.getElementById('apikey-location').value;
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
    const method = document.getElementById('method-ajax').value;
    let url = document.getElementById('url-ajax').value.trim();
    
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
    const followRedirects = document.getElementById('follow-redirects').checked;
    const verifySSL = document.getElementById('verify-ssl').checked;
    
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
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
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
        document.getElementById('status-code').textContent = 'Error';
        document.getElementById('status-code').className = 'badge bg-danger';
        
        // Create proper error displays
        const errorBodyContainer = document.getElementById('response-body-content');
        errorBodyContainer.innerHTML = '';
        const errorBodyMessage = document.createElement('div');
        errorBodyMessage.className = 'alert alert-danger';
        errorBodyMessage.textContent = 'Error: ' + error.message;
        errorBodyContainer.appendChild(errorBodyMessage);
        
        const errorHeadersContainer = document.getElementById('response-headers-content');
        errorHeadersContainer.innerHTML = '';
        const errorHeadersMessage = document.createElement('div');
        errorHeadersMessage.className = 'alert alert-danger';
        errorHeadersMessage.textContent = 'Error: ' + error.message;
        errorHeadersContainer.appendChild(errorHeadersMessage);
    });
} 