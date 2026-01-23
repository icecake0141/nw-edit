/*
 * Copyright 2026 icecake0141
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * This file was created or modified with the assistance of an AI (Large Language Model).
 * Review required for correctness, security, and licensing.
 */

// API base URL
const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000';

// Global state
let devices = [];
let currentJobId = null;
let ws = null;
let currentJobStatus = null;

// Page navigation
function showPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
    
    document.getElementById(`page-${pageName}`).classList.add('active');
    document.getElementById(`nav-${pageName}`).classList.add('active');
    
    if (pageName === 'job-create') {
        loadDevicesForJobCreate();
    }
}

// Device Import
async function importDevices() {
    const csvContent = document.getElementById('csv-input').value.trim();
    
    if (!csvContent) {
        alert('Please enter CSV content');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/devices/import`, {
            method: 'POST',
            headers: {
                'Content-Type': 'text/plain',
            },
            body: csvContent
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to import devices');
        }
        
        const data = await response.json();
        devices = data.devices;
        
        displayDeviceResults(devices);
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

function displayDeviceResults(deviceList) {
    const container = document.getElementById('device-results');
    
    if (!deviceList || deviceList.length === 0) {
        container.innerHTML = '<p style="color: #999; padding: 20px;">No devices found</p>';
        return;
    }
    
    container.innerHTML = deviceList.map(device => {
        const statusClass = device.connection_ok ? 'success' : 'error';
        const statusText = device.connection_ok ? 'Connected' : 'Failed';
        const statusBadgeClass = device.connection_ok ? 'status-success' : 'status-error';
        
        return `
            <div class="device-item ${statusClass}">
                <div class="device-info">
                    <strong>${device.name || device.host}</strong> (${device.host}:${device.port})
                    <br>
                    <small>Type: ${device.device_type} | User: ${device.username}</small>
                    ${device.error_message ? `<br><span class="error-text">${device.error_message}</span>` : ''}
                </div>
                <div class="device-status ${statusBadgeClass}">${statusText}</div>
            </div>
        `;
    }).join('');
}

// Load devices for job creation
async function loadDevicesForJobCreate() {
    try {
        const response = await fetch(`${API_BASE}/api/devices`);
        const deviceList = await response.json();
        devices = deviceList;
        
        const selector = document.getElementById('device-selector');
        const canarySelector = document.getElementById('canary-selector');
        
        if (!deviceList || deviceList.length === 0) {
            selector.innerHTML = '<p style="color: #999; padding: 20px; text-align: center;">No devices imported yet</p>';
            canarySelector.innerHTML = '<option value="">No devices available</option>';
            return;
        }
        
        // Only show devices that passed connection test
        const validDevices = deviceList.filter(d => d.connection_ok);
        
        selector.innerHTML = validDevices.map(device => `
            <div class="checkbox-item">
                <input type="checkbox" id="device-${device.host}-${device.port}" value="${device.host}:${device.port}" checked>
                <label for="device-${device.host}-${device.port}">
                    ${device.name || device.host} (${device.host}:${device.port}) - ${device.device_type}
                </label>
            </div>
        `).join('');
        
        canarySelector.innerHTML = '<option value="">Select canary device...</option>' +
            validDevices.map(device => `
                <option value="${device.host}:${device.port}">
                    ${device.name || device.host} (${device.host}:${device.port})
                </option>
            `).join('');
    } catch (error) {
        console.error('Error loading devices:', error);
    }
}

// Create job
async function createJob() {
    const commands = document.getElementById('config-commands').value.trim();
    if (!commands) {
        alert('Configuration commands are required');
        return;
    }
    
    const canaryValue = document.getElementById('canary-selector').value;
    if (!canaryValue) {
        alert('Please select a canary device');
        return;
    }
    
    const [canaryHost, canaryPort] = canaryValue.split(':');
    
    // Get selected devices
    const selectedDevices = [];
    document.querySelectorAll('#device-selector input[type="checkbox"]:checked').forEach(checkbox => {
        const [host, port] = checkbox.value.split(':');
        selectedDevices.push({ host, port: parseInt(port) });
    });
    
    if (selectedDevices.length === 0) {
        alert('Please select at least one device');
        return;
    }
    
    // Check if canary is in selected devices
    const canaryInList = selectedDevices.some(d => 
        d.host === canaryHost && d.port === parseInt(canaryPort)
    );
    
    if (!canaryInList) {
        alert('Canary device must be in the selected devices list');
        return;
    }
    
    // Get verify commands
    const verifyCommandsText = document.getElementById('verify-commands').value.trim();
    const verifyCommands = verifyCommandsText 
        ? verifyCommandsText.split('\n').map(c => c.trim()).filter(c => c)
        : [];
    
    const jobData = {
        job_name: document.getElementById('job-name').value.trim() || null,
        creator: document.getElementById('job-creator').value.trim() || null,
        devices: selectedDevices,
        canary: {
            host: canaryHost,
            port: parseInt(canaryPort)
        },
        commands: commands,
        verify_only: document.getElementById('verify-mode').value,
        verify_cmds: verifyCommands,
        concurrency_limit: parseInt(document.getElementById('concurrency-limit').value),
        stagger_delay: parseFloat(document.getElementById('stagger-delay').value),
        stop_on_error: document.getElementById('stop-on-error').checked
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/jobs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(jobData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create job');
        }
        
        const result = await response.json();
        currentJobId = result.job_id;
        
        // Switch to monitor page
        showPage('job-monitor');
        startJobMonitoring(result.job_id);
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Job monitoring
async function startJobMonitoring(jobId) {
    // Fetch initial job state
    try {
        const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
        const job = await response.json();
        
        displayJobMonitor(job);
        
        // Connect WebSocket
        connectWebSocket(jobId);
    } catch (error) {
        console.error('Error fetching job:', error);
    }
}

function displayJobMonitor(job) {
    const container = document.getElementById('job-monitor-content');
    currentJobStatus = job.status;
    
    const deviceCards = Object.entries(job.device_results).map(([key, result]) => {
        const statusClass = result.status.toLowerCase();
        const isCanary = key === `${job.canary.host}:${job.canary.port}`;
        
        return `
            <div class="device-card ${statusClass}" id="device-${key}">
                <h3>${result.host}:${result.port} ${isCanary ? '(CANARY)' : ''}</h3>
                <p><strong>Status:</strong> <span class="status-badge status-${statusClass}">${result.status}</span></p>
                ${result.error ? `<p class="error-text">Error: ${result.error}</p>` : ''}
                ${result.log_trimmed ? '<p class="warning-text">⚠️ Log was trimmed due to size limit</p>' : ''}
                
                <div class="log-output" id="log-${key}">
                    ${result.logs.join('\n') || 'No logs yet...'}
                </div>
                
                ${result.pre_output ? `
                    <div class="verify-output verify-pre">
                        <h4>Pre-Verification Output</h4>
                        <pre class="verify-output-content">${escapeHtml(result.pre_output)}</pre>
                    </div>
                ` : ''}
                
                ${result.post_output ? `
                    <div class="verify-output verify-post">
                        <h4>Post-Verification Output</h4>
                        <pre class="verify-output-content">${escapeHtml(result.post_output)}</pre>
                    </div>
                ` : ''}
                
                ${result.diff ? `
                    <h4 style="margin-top: 15px;">Pre/Post Diff:</h4>
                    <div class="diff-output">${formatDiff(result.diff)}</div>
                ` : ''}
            </div>
        `;
    }).join('');
    
    container.innerHTML = `
        <div class="job-card">
            <h3>${job.job_name || 'Job'} (${job.job_id})</h3>
            <p><strong>Status:</strong> <span id="job-status-text" class="status-${job.status.toLowerCase()}">${job.status}</span></p>
            <p><strong>Creator:</strong> ${job.creator || 'N/A'}</p>
            <p><strong>Created:</strong> ${new Date(job.created_at).toLocaleString()}</p>
            ${job.completed_at ? `<p><strong>Completed:</strong> ${new Date(job.completed_at).toLocaleString()}</p>` : ''}
            <div class="job-actions">
                <button onclick="pauseJob()" id="pause-job-btn">Pause</button>
                <button onclick="resumeJob()" id="resume-job-btn">Resume</button>
                <button onclick="terminateJob()" id="terminate-job-btn" class="danger">Terminate</button>
            </div>
        </div>
        
        <h3>Device Results:</h3>
        ${deviceCards}
    `;

    updateJobControls(job.status);
}

function formatDiff(diffText) {
    if (!diffText) return '';
    
    return diffText.split('\n').map(line => {
        if (line.startsWith('+')) {
            return `<span class="diff-add">${escapeHtml(line)}</span>`;
        } else if (line.startsWith('-')) {
            return `<span class="diff-remove">${escapeHtml(line)}</span>`;
        } else {
            return escapeHtml(line);
        }
    }).join('\n');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function connectWebSocket(jobId) {
    if (ws) {
        ws.close();
    }
    
    ws = new WebSocket(`${WS_BASE}/ws/jobs/${jobId}`);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket closed');
    };
}

function handleWebSocketMessage(message) {
    console.log('WS message:', message);
    
    if (message.type === 'log') {
        const logElement = document.getElementById(`log-${message.device}`);
        if (logElement) {
            logElement.textContent += '\n' + message.data;
            logElement.scrollTop = logElement.scrollHeight;
        }
    } else if (message.type === 'device_status') {
        const deviceCard = document.getElementById(`device-${message.device}`);
        if (deviceCard) {
            deviceCard.className = `device-card ${message.status.toLowerCase()}`;
            const statusBadge = deviceCard.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.textContent = message.status;
                statusBadge.className = `status-badge status-${message.status.toLowerCase()}`;
            }
            if (message.error) {
                const existingError = deviceCard.querySelector('.error-text');
                if (!existingError) {
                    const errorP = document.createElement('p');
                    errorP.className = 'error-text';
                    errorP.textContent = `Error: ${message.error}`;
                    deviceCard.querySelector('h3').after(errorP);
                }
            }
        }
    } else if (message.type === 'job_complete') {
        console.log('Job completed with status:', message.status);
        // Refresh job details
        if (currentJobId) {
            fetchJobDetails(currentJobId);
        }
    } else if (message.type === 'job_status') {
        updateJobStatus(message.status);
    }
}

async function fetchJobDetails(jobId) {
    try {
        const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
        const job = await response.json();
        displayJobMonitor(job);
    } catch (error) {
        console.error('Error fetching job details:', error);
    }
}

function updateJobStatus(status) {
    currentJobStatus = status;
    const statusText = document.getElementById('job-status-text');
    if (statusText) {
        statusText.textContent = status;
        statusText.className = `status-${status.toLowerCase()}`;
    }
    updateJobControls(status);
}

function updateJobControls(status) {
    const pauseButton = document.getElementById('pause-job-btn');
    const resumeButton = document.getElementById('resume-job-btn');
    const terminateButton = document.getElementById('terminate-job-btn');
    if (!pauseButton || !resumeButton || !terminateButton) {
        return;
    }

    const isRunning = status === 'running';
    const isPaused = status === 'paused';
    const isTerminal = ['completed', 'failed', 'cancelled'].includes(status);

    pauseButton.disabled = !isRunning;
    resumeButton.disabled = !isPaused;
    terminateButton.disabled = isTerminal;
}

async function pauseJob() {
    if (!currentJobId) return;
    try {
        const response = await fetch(`${API_BASE}/api/jobs/${currentJobId}/pause`, {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to pause job');
        }
        const result = await response.json();
        updateJobStatus(result.status);
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function resumeJob() {
    if (!currentJobId) return;
    try {
        const response = await fetch(`${API_BASE}/api/jobs/${currentJobId}/resume`, {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to resume job');
        }
        const result = await response.json();
        updateJobStatus(result.status);
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function terminateJob() {
    if (!currentJobId) return;
    const confirmed = confirm('Terminate this job and cancel pending tasks?');
    if (!confirmed) return;

    try {
        const response = await fetch(`${API_BASE}/api/jobs/${currentJobId}/terminate`, {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to terminate job');
        }
        const result = await response.json();
        updateJobStatus(result.status);
        fetchJobDetails(currentJobId);
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('App initialized');
});
