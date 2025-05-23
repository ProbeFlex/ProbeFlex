/**
 * Common UI functionality for API request forms
 * Used across home.html, request_form.html, and request_detail.html
 */

/**
 * Initialize all event listeners and UI components
 */
function initializeRequestUI() {
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Auth type toggle
    const authTypeElement = document.getElementById('auth-type');
    if (authTypeElement) {
        authTypeElement.addEventListener('change', function() {
            const authType = this.value;
            document.querySelectorAll('.auth-details').forEach(el => el.style.display = 'none');
            if (authType !== 'none') {
                const authDetailsElement = document.getElementById(`${authType}-auth-details`);
                if (authDetailsElement) {
                    authDetailsElement.style.display = 'block';
                }
            }
        });
    }

    // Body type toggle
    const bodyTypeElement = document.getElementById('body-type');
    if (bodyTypeElement) {
        bodyTypeElement.addEventListener('change', function() {
            const bodyType = this.value;
            document.querySelectorAll('.body-inputs').forEach(el => el.style.display = 'none');
            if (bodyType !== 'none') {
                const bodyInputElement = document.getElementById(`${bodyType}-body`);
                if (bodyInputElement) {
                    bodyInputElement.style.display = 'block';
                }
            }
        });
    }
    
    // Add keyboard event handling for URL field - press Enter to send
    const urlElement = document.getElementById('url-ajax');
    if (urlElement) {
        urlElement.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                sendRequest();
            }
        });
    }

    // Add param button
    const addParamBtn = document.getElementById('add-param');
    if (addParamBtn) {
        addParamBtn.addEventListener('click', addParameterRow);
    }

    // Add header button
    const addHeaderBtn = document.getElementById('add-header');
    if (addHeaderBtn) {
        addHeaderBtn.addEventListener('click', addHeaderRow);
    }

    // Add form item button
    const addFormItemBtn = document.getElementById('add-form-item');
    if (addFormItemBtn) {
        addFormItemBtn.addEventListener('click', addFormItemRow);
    }

    // Add remove button event listeners for initial rows
    document.querySelectorAll('.remove-param, .remove-header, .remove-form-item').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.row').remove();
        });
    });

    // Send button event listener
    const sendBtn = document.getElementById('send-btn-ajax');
    if (sendBtn) {
        sendBtn.addEventListener('click', function() {
            sendRequest();
        });
    }
}

/**
 * Add a new parameter row
 */
function addParameterRow() {
    const paramRow = document.createElement('div');
    paramRow.className = 'row mb-2';
    paramRow.innerHTML = `
        <div class="col-5">
            <input type="text" class="form-control param-key" placeholder="Key">
        </div>
        <div class="col-5">
            <input type="text" class="form-control param-value" placeholder="Value">
        </div>
        <div class="col-2">
            <button class="btn btn-sm btn-outline-danger remove-param">Remove</button>
        </div>
    `;
    
    const paramRows = document.querySelector('.param-rows');
    if (paramRows) {
        paramRows.appendChild(paramRow);
        
        // Add event listener to the newly created remove button
        paramRow.querySelector('.remove-param').addEventListener('click', function() {
            paramRow.remove();
        });
    }
}

/**
 * Add a new header row
 */
function addHeaderRow() {
    const headerRow = document.createElement('div');
    headerRow.className = 'row mb-2';
    headerRow.innerHTML = `
        <div class="col-5">
            <input type="text" class="form-control header-key" placeholder="Key">
        </div>
        <div class="col-5">
            <input type="text" class="form-control header-value" placeholder="Value">
        </div>
        <div class="col-2">
            <button class="btn btn-sm btn-outline-danger remove-header">Remove</button>
        </div>
    `;
    
    const headerRows = document.querySelector('.header-rows');
    if (headerRows) {
        headerRows.appendChild(headerRow);
        
        // Add event listener to the newly created remove button
        headerRow.querySelector('.remove-header').addEventListener('click', function() {
            headerRow.remove();
        });
    }
}

/**
 * Add a new form item row
 */
function addFormItemRow() {
    const formRow = document.createElement('div');
    formRow.className = 'row mb-2';
    formRow.innerHTML = `
        <div class="col-5">
            <input type="text" class="form-control form-key" placeholder="Key">
        </div>
        <div class="col-5">
            <input type="text" class="form-control form-value" placeholder="Value">
        </div>
        <div class="col-2">
            <button class="btn btn-sm btn-outline-danger remove-form-item">Remove</button>
        </div>
    `;
    
    const formRows = document.querySelector('.form-rows');
    if (formRows) {
        formRows.appendChild(formRow);
        
        // Add event listener to the newly created remove button
        formRow.querySelector('.remove-form-item').addEventListener('click', function() {
            formRow.remove();
        });
    }
}

/**
 * Safe JSON parsing for Django json_script filter output
 * @param {string} elementId - ID of the element containing JSON data
 * @param {*} defaultValue - Default value if parsing fails
 * @returns {*} Parsed JSON data or default value
 */
function safeJsonParse(elementId, defaultValue = {}) {
    try {
        const element = document.getElementById(elementId);
        if (!element) {
            console.warn(`Element ${elementId} not found`);
            return defaultValue;
        }
        
        // Django json_script filter uses textContent directly
        const data = JSON.parse(element.textContent);
        return data;
    } catch (e) {
        console.error(`JSON parse error for ${elementId}:`, e);
        const element = document.getElementById(elementId);
        console.error('Raw text:', element ? element.textContent : 'Element not found');
        return defaultValue;
    }
}

/**
 * Safe element getter with warning logging
 * @param {string} id - Element ID
 * @returns {Element|null} Element or null if not found
 */
function safeGetElement(id) {
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Element ${id} not found`);
    }
    return element;
}

/**
 * Populate form fields from saved request data (for editing)
 * @param {Object} requestData - Request data to populate
 */
function populateFormFromRequestData(requestData) {
    if (!requestData) return;
    
    // Set method and URL
    const methodElement = document.getElementById('method-ajax');
    const urlElement = document.getElementById('url-ajax');
    
    if (methodElement && requestData.method) {
        methodElement.value = requestData.method;
    }
    if (urlElement && requestData.url) {
        urlElement.value = requestData.url;
    }
    
    // Set timeout and checkbox settings
    const timeoutElement = document.getElementById('timeout');
    const followRedirectsElement = document.getElementById('follow-redirects');
    const verifySSLElement = document.getElementById('verify-ssl');
    
    if (timeoutElement && requestData.timeout) {
        timeoutElement.value = requestData.timeout;
    }
    if (followRedirectsElement && typeof requestData.follow_redirects === 'boolean') {
        followRedirectsElement.checked = requestData.follow_redirects;
    }
    if (verifySSLElement && typeof requestData.verify_ssl === 'boolean') {
        verifySSLElement.checked = requestData.verify_ssl;
    }
    
    // Set auth type and data
    if (requestData.auth) {
        const authTypeElement = document.getElementById('auth-type');
        if (authTypeElement) {
            const authType = requestData.auth.type || 'none';
            authTypeElement.value = authType;
            
            // Show the appropriate auth details section
            document.querySelectorAll('.auth-details').forEach(el => el.style.display = 'none');
            if (authType !== 'none') {
                const authDetailsElement = document.getElementById(`${authType}-auth-details`);
                if (authDetailsElement) {
                    authDetailsElement.style.display = 'block';
                }
                
                // Populate auth fields
                if (authType === 'basic') {
                    const usernameElement = document.getElementById('basic-username');
                    const passwordElement = document.getElementById('basic-password');
                    if (usernameElement) usernameElement.value = requestData.auth.username || '';
                    if (passwordElement) passwordElement.value = requestData.auth.password || '';
                } else if (authType === 'bearer') {
                    const tokenElement = document.getElementById('bearer-token');
                    if (tokenElement) tokenElement.value = requestData.auth.token || '';
                } else if (authType === 'apikey') {
                    const keyNameElement = document.getElementById('apikey-name');
                    const keyValueElement = document.getElementById('apikey-value');
                    const keyLocationElement = document.getElementById('apikey-location');
                    if (keyNameElement) keyNameElement.value = requestData.auth.key || '';
                    if (keyValueElement) keyValueElement.value = requestData.auth.value || '';
                    if (keyLocationElement) keyLocationElement.value = requestData.auth.location || 'header';
                }
            }
        }
    }
    
    // Set body type and content
    if (requestData.body && typeof requestData.body === 'object' && Object.keys(requestData.body).length > 0) {
        const bodyTypeElement = document.getElementById('body-type');
        const jsonEditorElement = document.getElementById('json-editor');
        
        if (bodyTypeElement) {
            bodyTypeElement.value = 'json';
            // Show JSON body section
            document.querySelectorAll('.body-inputs').forEach(el => el.style.display = 'none');
            const jsonBodyElement = document.getElementById('json-body');
            if (jsonBodyElement) {
                jsonBodyElement.style.display = 'block';
            }
        }
        
        if (jsonEditorElement) {
            jsonEditorElement.value = JSON.stringify(requestData.body, null, 2);
        }
    }
    
    // Populate headers
    if (requestData.headers && typeof requestData.headers === 'object') {
        populateKeyValueRows('.header-rows', '.header-key', '.header-value', requestData.headers, addHeaderRow);
    }
    
    // Populate parameters
    if (requestData.params && typeof requestData.params === 'object') {
        populateKeyValueRows('.param-rows', '.param-key', '.param-value', requestData.params, addParameterRow);
    }
}

/**
 * Populate key-value rows (headers or params)
 * @param {string} containerSelector - Container selector
 * @param {string} keySelector - Key input selector
 * @param {string} valueSelector - Value input selector  
 * @param {Object} data - Data object with key-value pairs
 * @param {Function} addRowFunction - Function to add new rows
 */
function populateKeyValueRows(containerSelector, keySelector, valueSelector, data, addRowFunction) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    
    const entries = Object.entries(data);
    if (entries.length === 0) return;
    
    // Check if there's already a first row
    const firstRow = container.querySelector('.row');
    let firstEntry = true;
    
    entries.forEach(([key, value]) => {
        if (firstEntry && firstRow) {
            // Use the existing first row
            const keyElement = firstRow.querySelector(keySelector);
            const valueElement = firstRow.querySelector(valueSelector);
            if (keyElement) keyElement.value = key;
            if (valueElement) valueElement.value = value;
            firstEntry = false;
        } else {
            // Add new row
            addRowFunction();
            
            // Get the last added row
            const rows = container.querySelectorAll('.row');
            const lastRow = rows[rows.length - 1];
            if (lastRow) {
                const keyElement = lastRow.querySelector(keySelector);
                const valueElement = lastRow.querySelector(valueSelector);
                if (keyElement) keyElement.value = key;
                if (valueElement) valueElement.value = value;
            }
        }
    });
}

/**
 * Setup save request modal functionality (for home.html)
 * @param {Array} projects - Array of project data for collections dropdown
 */
function setupSaveRequestModal(projects) {
    const saveBtn = document.getElementById('save-btn');
    const saveRequestBtn = document.getElementById('save-request-btn');
    
    if (!saveBtn || !saveRequestBtn) return;
    
    // Save button opens modal
    saveBtn.addEventListener('click', function() {
        const modal = new bootstrap.Modal(document.getElementById('saveRequestModal'));
        modal.show();
    });

    // Save request to collection
    saveRequestBtn.addEventListener('click', function() {
        const name = document.getElementById('request-name').value.trim();
        const description = document.getElementById('request-description').value.trim();
        const collectionId = document.getElementById('collection-select').value;
        
        if (!name) {
            alert('Please enter a name for this request');
            return;
        }
        
        if (!collectionId) {
            alert('Please select a collection');
            return;
        }
        
        const method = document.getElementById('method-ajax').value;
        const url = document.getElementById('url-ajax').value.trim();
        
        if (!url) {
            alert('Please enter a URL');
            return;
        }
        
        const requestData = {
            name: name,
            description: description,
            url: url,
            method: method,
            headers: getHeaders(),
            params: getParams(),
            body: getBody(),
            auth: getAuth()
        };
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        fetch(`/collections/${collectionId}/requests/new/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error saving request');
            }
            return response.json();
        })
        .then(data => {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('saveRequestModal'));
            modal.hide();
            
            // Show success message
            alert('Request saved successfully!');
            
            // Optionally redirect to the new request
            if (data && data.id) {
                window.location.href = `/requests/${data.id}/`;
            }
        })
        .catch(error => {
            alert('Error saving request: ' + error.message);
        });
    });
}

/**
 * Setup form submission for request_form.html
 */
function setupFormSubmission() {
    const saveBtn = document.getElementById('save-btn-submit');
    if (!saveBtn) return;
    
    saveBtn.addEventListener('click', function(e) {
        // Transfer request data to hidden form fields
        const savedUrlElement = document.getElementById('saved-url');
        const savedMethodElement = document.getElementById('saved-method');
        const savedHeadersElement = document.getElementById('saved-headers');
        const savedParamsElement = document.getElementById('saved-params');
        const savedBodyElement = document.getElementById('saved-body');
        const savedAuthElement = document.getElementById('saved-auth');
        const savedTimeoutElement = document.getElementById('saved-timeout');
        const savedFollowRedirectsElement = document.getElementById('saved-follow-redirects');
        const savedVerifySSLElement = document.getElementById('saved-verify-ssl');
        
        if (savedUrlElement) savedUrlElement.value = document.getElementById('url-ajax').value;
        if (savedMethodElement) savedMethodElement.value = document.getElementById('method-ajax').value;
        if (savedHeadersElement) savedHeadersElement.value = JSON.stringify(getHeaders());
        if (savedParamsElement) savedParamsElement.value = JSON.stringify(getParams());
        if (savedBodyElement) savedBodyElement.value = JSON.stringify(getBody());
        if (savedAuthElement) savedAuthElement.value = JSON.stringify(getAuth());
        if (savedTimeoutElement) savedTimeoutElement.value = document.getElementById('timeout').value;
        if (savedFollowRedirectsElement) savedFollowRedirectsElement.value = document.getElementById('follow-redirects').checked;
        if (savedVerifySSLElement) savedVerifySSLElement.value = document.getElementById('verify-ssl').checked;
    });
} 