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
const IMPORT_PROGRESS_HIDE_DELAY_MS = 1500;

// Global state
let devices = [];
let currentJobId = null;
let ws = null;
let currentJobStatus = null;
let taskHistory = [];
let activeJob = null;
let selectedHistoryId = null;

// Page navigation
function showPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
    
    document.getElementById(`page-${pageName}`).classList.add('active');
    document.getElementById(`nav-${pageName}`).classList.add('active');
    
    // Clean up WebSocket when navigating away from job monitor
    if (ws && pageName !== 'job-monitor') {
        ws.close();
        ws = null;
        currentJobId = null;
    }
    
    if (pageName === 'job-create') {
        loadDevicesForJobCreate();
        refreshActiveJobState();
    } else if (pageName === 'status-command') {
        loadDevicesForStatusCommand();
    } else if (pageName === 'job-history') {
        loadTaskHistory();
    }
}

async function refreshActiveJobState() {
    try {
        const response = await fetch(`${API_BASE}/api/jobs/active`);
        if (!response.ok) {
            throw new Error('Failed to fetch active job');
        }
        const result = await response.json();
        activeJob = result.active ? result.job : null;
    } catch (error) {
        console.error('Error fetching active job:', error);
        activeJob = null;
    }
    updateActiveJobBanner();
}

function updateActiveJobBanner() {
    const banner = document.getElementById('active-job-banner');
    const bannerText = document.getElementById('active-job-banner-text');
    const createButton = document.getElementById('create-job-button');
    if (!banner || !bannerText || !createButton) {
        return;
    }

    const isActive = activeJob && ['running', 'queued', 'paused'].includes(activeJob.status);
    if (!isActive) {
        banner.classList.add('hidden');
        createButton.disabled = false;
        return;
    }

    banner.classList.remove('hidden');
    const label = activeJob.job_name || activeJob.job_id;
    bannerText.textContent = `Job "${label}" is ${activeJob.status}. Starting another job is blocked until it finishes or is cancelled.`;
    createButton.disabled = true;
}

function viewActiveJob() {
    if (!activeJob) {
        return;
    }
    showPage('job-monitor');
    startJobMonitoring(activeJob.job_id);
}

function formatDuration(durationSeconds) {
    if (durationSeconds === null || durationSeconds === undefined) {
        return '—';
    }
    if (durationSeconds < 60) {
        return `${durationSeconds.toFixed(1)}s`;
    }
    const minutes = Math.floor(durationSeconds / 60);
    const seconds = durationSeconds % 60;
    return `${minutes}m ${seconds.toFixed(0)}s`;
}

async function loadTaskHistory() {
    try {
        const response = await fetch(`${API_BASE}/api/jobs`);
        if (!response.ok) {
            throw new Error('Failed to fetch task history');
        }
        taskHistory = await response.json();
        if (taskHistory.length > 0) {
            const hasSelection = taskHistory.some(entry => entry.job_id === selectedHistoryId);
            if (!hasSelection) {
                selectedHistoryId = taskHistory[0].job_id;
                await selectHistoryEntry(selectedHistoryId);
                return;
            }
        }
        renderTaskHistory();
    } catch (error) {
        console.error('Error loading task history:', error);
    }
}

function renderTaskHistory() {
    const listContainer = document.getElementById('task-history-list');
    if (!listContainer) {
        return;
    }

    if (!taskHistory || taskHistory.length === 0) {
        const empty = document.createElement('p');
        empty.style.color = '#999';
        empty.style.padding = '20px';
        empty.style.textAlign = 'center';
        empty.textContent = 'No task history yet';
        listContainer.replaceChildren(empty);
        return;
    }

    listContainer.textContent = '';
    taskHistory.forEach(entry => {
        const isActive = entry.job_id === selectedHistoryId;
        const createdLabel = entry.created_at ? new Date(entry.created_at).toLocaleString() : 'Unknown';
        const durationLabel = formatDuration(entry.duration_seconds);
        const exitCode = entry.exit_code === null || entry.exit_code === undefined ? '—' : entry.exit_code;

        const item = document.createElement('div');
        item.className = `history-entry${isActive ? ' active' : ''}`;
        item.addEventListener('click', () => selectHistoryEntry(entry.job_id));

        const title = document.createElement('h4');
        title.append(document.createTextNode(`${entry.job_name || 'Job'} `));
        const statusBadge = document.createElement('span');
        statusBadge.className = `status-badge status-${sanitizeClassToken(entry.status)}`;
        statusBadge.textContent = String(entry.status || 'unknown');
        title.append(statusBadge);

        const createdMeta = document.createElement('div');
        createdMeta.className = 'history-meta';
        createdMeta.textContent = `Created: ${createdLabel}`;

        const durationMeta = document.createElement('div');
        durationMeta.className = 'history-meta';
        durationMeta.textContent = `Duration: ${durationLabel} | Exit code: ${exitCode}`;

        item.append(title, createdMeta, durationMeta);
        listContainer.appendChild(item);
    });
}

async function selectHistoryEntry(jobId) {
    selectedHistoryId = jobId;
    renderTaskHistory();
    try {
        const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch job details');
        }
        const job = await response.json();
        const summary = (taskHistory || []).find(entry => entry.job_id === jobId) || null;
        renderHistoryDetail(job, summary);
    } catch (error) {
        console.error('Error loading job detail:', error);
    }
}

function renderHistoryDetail(job, summary) {
    const detailContainer = document.getElementById('task-history-detail');
    if (!detailContainer) {
        return;
    }

    const durationLabel = summary ? formatDuration(summary.duration_seconds) : '—';
    const exitCode = summary && summary.exit_code !== null && summary.exit_code !== undefined ? summary.exit_code : '—';
    const deviceCards = buildDeviceCards(job);
    const statusClass = sanitizeClassToken(job.status);
    const statusText = escapeHtml(job.status || 'unknown');
    const createdAt = job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A';
    const startedAt = job.started_at ? new Date(job.started_at).toLocaleString() : null;
    const completedAt = job.completed_at ? new Date(job.completed_at).toLocaleString() : null;
    const verifyCommands = job.verify_cmds && job.verify_cmds.length ? job.verify_cmds.join(', ') : 'None';

    detailContainer.innerHTML = `
        <div class="job-card">
            <h3>${escapeHtml(job.job_name || 'Job')} (${escapeHtml(job.job_id)})</h3>
            <p><strong>Status:</strong> <span class="status-badge status-${statusClass}">${statusText}</span></p>
            <p><strong>Creator:</strong> ${escapeHtml(job.creator || 'N/A')}</p>
            <p><strong>Created:</strong> ${escapeHtml(createdAt)}</p>
            ${startedAt ? `<p><strong>Started:</strong> ${escapeHtml(startedAt)}</p>` : ''}
            ${completedAt ? `<p><strong>Completed:</strong> ${escapeHtml(completedAt)}</p>` : ''}
            <p><strong>Duration:</strong> ${escapeHtml(durationLabel)}</p>
            <p><strong>Exit Code:</strong> ${escapeHtml(exitCode)}</p>
            <p><strong>Verify Mode:</strong> ${escapeHtml(job.verify_only)}</p>
            <p><strong>Verify Commands:</strong> ${escapeHtml(verifyCommands)}</p>
            <p><strong>Concurrency Limit:</strong> ${escapeHtml(job.concurrency_limit)}</p>
            <p><strong>Stagger Delay:</strong> ${escapeHtml(job.stagger_delay)}s</p>
            <p><strong>Stop on Error:</strong> ${job.stop_on_error ? 'Yes' : 'No'}</p>
            <h4 style="margin-top: 15px;">Commands</h4>
            <div class="log-output">${escapeHtml(job.commands || '')}</div>
        </div>
        <h3>Device Results:</h3>
        ${deviceCards}
    `;
}

// Device Import
function updateImportProgress(processed, total) {
    const progressContainer = document.getElementById('import-progress');
    const progressText = document.getElementById('import-progress-text');
    const progressFill = document.getElementById('import-progress-fill');
    const safeTotal = total || 0;
    const percent = safeTotal > 0 ? (processed / safeTotal) * 100 : 0;
    progressContainer.style.display = 'block';
    progressText.textContent = `Validating devices... ${processed}/${safeTotal}`;
    progressFill.style.width = `${percent}%`;
}

async function importDevices() {
    const csvContent = document.getElementById('csv-input').value.trim();
    const importButton = document.getElementById('import-button');
    const progressContainer = document.getElementById('import-progress');
    
    if (!csvContent) {
        alert('Please enter CSV content');
        return;
    }
    
    try {
        importButton.disabled = true;
        updateImportProgress(0, 0);

        const response = await fetch(`${API_BASE}/api/devices/import/progress`, {
            method: 'POST',
            headers: {
                'Content-Type': 'text/plain',
            },
            body: csvContent
        });
        
        if (!response.ok) {
            let detail = 'Failed to import devices';
            try {
                const error = await response.json();
                detail = error.detail || detail;
            } catch (_) {
                const errorText = await response.text();
                if (errorText) {
                    detail = errorText;
                }
            }
            throw new Error(detail);
        }

        let total = 0;
        let processed = 0;
        let finalDevices = null;
        if (!response.body) {
            throw new Error('Failed to read import progress stream');
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) {
                break;
            }
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.trim()) {
                    continue;
                }
                const event = JSON.parse(line);
                if (event.type === 'start') {
                    total = event.total || 0;
                    updateImportProgress(0, total);
                } else if (event.type === 'progress') {
                    processed = event.processed || processed;
                    total = event.total || total;
                    updateImportProgress(processed, total);
                } else if (event.type === 'complete') {
                    finalDevices = event.devices || [];
                    updateImportProgress(event.processed || processed, event.total || total);
                } else if (event.type === 'error') {
                    throw new Error(event.detail || 'Failed to import devices');
                }
            }
        }

        if (buffer.trim()) {
            const event = JSON.parse(buffer);
            if (event.type === 'complete') {
                finalDevices = event.devices || [];
                updateImportProgress(event.processed || processed, event.total || total);
            } else if (event.type === 'error') {
                throw new Error(event.detail || 'Failed to import devices');
            }
        }

        devices = finalDevices || [];
        displayDeviceResults(devices);
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        importButton.disabled = false;
        if (progressContainer) {
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, IMPORT_PROGRESS_HIDE_DELAY_MS);
        }
    }
}

function displayDeviceResults(deviceList) {
    const container = document.getElementById('device-results');
    
    if (!deviceList || deviceList.length === 0) {
        const empty = document.createElement('p');
        empty.style.color = '#999';
        empty.style.padding = '20px';
        empty.textContent = 'No devices found';
        container.replaceChildren(empty);
        return;
    }
    
    container.textContent = '';
    deviceList.forEach(device => {
        const statusClass = device.connection_ok ? 'success' : 'error';
        const statusText = device.connection_ok ? 'Connected' : 'Failed';
        const statusBadgeClass = device.connection_ok ? 'status-success' : 'status-error';

        const item = document.createElement('div');
        item.className = `device-item ${statusClass}`;

        const info = document.createElement('div');
        info.className = 'device-info';
        const name = document.createElement('strong');
        name.textContent = String(device.name || device.host || '');
        info.append(name, document.createTextNode(` (${device.host}:${device.port})`));
        info.append(document.createElement('br'));
        const small = document.createElement('small');
        small.textContent = `Type: ${device.device_type} | User: ${device.username}`;
        info.append(small);

        if (device.error_message) {
            info.append(document.createElement('br'));
            const error = document.createElement('span');
            error.className = 'error-text';
            error.textContent = String(device.error_message);
            info.append(error);
        }

        const status = document.createElement('div');
        status.className = `device-status ${statusBadgeClass}`;
        status.textContent = statusText;

        item.append(info, status);
        container.appendChild(item);
    });
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
            const empty = document.createElement('p');
            empty.style.color = '#999';
            empty.style.padding = '20px';
            empty.style.textAlign = 'center';
            empty.textContent = 'No devices imported yet';
            selector.replaceChildren(empty);

            const noOption = document.createElement('option');
            noOption.value = '';
            noOption.textContent = 'No devices available';
            canarySelector.replaceChildren(noOption);
            return;
        }
        
        // Only show devices that passed connection test
        const validDevices = deviceList.filter(d => d.connection_ok);

        selector.textContent = '';
        const selectAllItem = document.createElement('div');
        selectAllItem.className = 'checkbox-item';
        const selectAllInput = document.createElement('input');
        selectAllInput.type = 'checkbox';
        selectAllInput.id = 'select-all-devices';
        selectAllInput.setAttribute('aria-label', 'Select all devices');
        const selectAllLabel = document.createElement('label');
        selectAllLabel.setAttribute('for', 'select-all-devices');
        const strong = document.createElement('strong');
        strong.textContent = 'Select All';
        selectAllLabel.append(strong);
        selectAllItem.append(selectAllInput, selectAllLabel);
        selector.appendChild(selectAllItem);

        validDevices.forEach((device, index) => {
            const item = document.createElement('div');
            item.className = 'checkbox-item';
            const checkboxId = `device-option-${index}`;
            const value = `${device.host}:${device.port}`;

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = checkboxId;
            checkbox.value = value;

            const label = document.createElement('label');
            label.setAttribute('for', checkboxId);
            label.textContent = `${device.name || device.host} (${device.host}:${device.port}) - ${device.device_type}`;

            item.append(checkbox, label);
            selector.appendChild(item);
        });

        const selectAllCheckbox = document.getElementById('select-all-devices');
        const deviceCheckboxes = selector.querySelectorAll('input[type="checkbox"]:not(#select-all-devices)');
        const updateSelectAllState = () => {
            const checkedCount = Array.from(deviceCheckboxes).filter(cb => cb.checked).length;
            selectAllCheckbox.checked = checkedCount === deviceCheckboxes.length && deviceCheckboxes.length > 0;
            selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < deviceCheckboxes.length;
        };

        selector.onchange = (event) => {
            if (event.target.id === 'select-all-devices') {
                deviceCheckboxes.forEach(checkbox => {
                    checkbox.checked = selectAllCheckbox.checked;
                });
                selectAllCheckbox.indeterminate = false;
                return;
            }

            if (event.target.matches('input[type="checkbox"]:not(#select-all-devices)')) {
                updateSelectAllState();
            }
        };

        updateSelectAllState();

        canarySelector.textContent = '';
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select canary device...';
        canarySelector.appendChild(defaultOption);

        validDevices.forEach(device => {
            const option = document.createElement('option');
            option.value = `${device.host}:${device.port}`;
            option.textContent = `${device.name || device.host} (${device.host}:${device.port})`;
            canarySelector.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading devices:', error);
    }
}

async function loadDevicesForStatusCommand() {
    const selector = document.getElementById('status-device-selector');
    if (!selector) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/devices`);
        const deviceList = await response.json();
        const validDevices = (deviceList || []).filter(d => d.connection_ok);

        selector.textContent = '';
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select a managed device...';
        selector.appendChild(defaultOption);

        validDevices.forEach(device => {
            const option = document.createElement('option');
            option.value = `${device.host}:${device.port}`;
            option.textContent = `${device.name || device.host} (${device.host}:${device.port})`;
            selector.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading devices for status command:', error);
    }
}

async function runStatusCommand() {
    const selectedDevice = document.getElementById('status-device-selector').value;
    const commands = document.getElementById('status-commands').value.trim();
    const runButton = document.getElementById('status-command-button');
    const output = document.getElementById('status-command-output');

    if (!selectedDevice) {
        alert('Please select a target device');
        return;
    }
    if (!commands) {
        alert('Please enter at least one command');
        return;
    }

    const [host, port] = selectedDevice.split(':');
    runButton.disabled = true;
    output.textContent = 'Running status command...';

    try {
        const response = await fetch(`${API_BASE}/api/commands/exec`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                host,
                port: parseInt(port),
                commands,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to execute status command');
        }

        const result = await response.json();
        output.textContent = result.output || 'No output returned';
    } catch (error) {
        output.textContent = `Error: ${error.message}`;
        alert(`Error: ${error.message}`);
    } finally {
        runButton.disabled = false;
    }
}

// Create job
async function createJob() {
    await refreshActiveJobState();
    if (activeJob && ['running', 'queued', 'paused'].includes(activeJob.status)) {
        const label = activeJob.job_name || activeJob.job_id;
        alert(`Job "${label}" is currently ${activeJob.status}. Please wait for it to finish or cancel it before starting another job.`);
        return;
    }

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
    document.querySelectorAll('#device-selector input[type="checkbox"]:not(#select-all-devices):checked').forEach(checkbox => {
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
        
        // Reset form after successful job creation to prevent data contamination
        resetJobForm();
        
        // Switch to monitor page
        showPage('job-monitor');
        startJobMonitoring(result.job_id);
        refreshActiveJobState();
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

function resetJobForm() {
    // Reset all form fields to default values
    document.getElementById('job-name').value = '';
    document.getElementById('job-creator').value = '';
    document.getElementById('config-commands').value = '';
    document.getElementById('verify-commands').value = '';
    document.getElementById('verify-mode').value = 'canary';
    document.getElementById('concurrency-limit').value = '5';
    document.getElementById('stagger-delay').value = '1.0';
    document.getElementById('stop-on-error').checked = true;
    document.getElementById('canary-selector').selectedIndex = 0;
    
    // Uncheck all device checkboxes
    document.querySelectorAll('#device-selector input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });
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

function buildDeviceCards(job) {
    return Object.entries(job.device_results).map(([key, result]) => {
        const statusClass = sanitizeClassToken(result.status);
        const isCanary = key === `${job.canary.host}:${job.canary.port}`;
        const resultTitle = `${result.host}:${result.port} ${isCanary ? '(CANARY)' : ''}`.trim();
        const deviceId = `device-${domIdFromDeviceKey(key)}`;
        const logId = `log-${domIdFromDeviceKey(key)}`;
        const logs = Array.isArray(result.logs) ? result.logs.join('\n') : String(result.logs || '');

        return `
            <div class="device-card ${statusClass}" id="${deviceId}">
                <h3>${escapeHtml(resultTitle)}</h3>
                <p><strong>Status:</strong> <span class="status-badge status-${statusClass}">${escapeHtml(result.status || 'unknown')}</span></p>
                ${result.error ? `<p class="error-text">Error: ${escapeHtml(result.error)}</p>` : ''}
                ${result.log_trimmed ? '<p class="warning-text">⚠️ Log was trimmed due to size limit</p>' : ''}
                
                <div class="log-output" id="${logId}">
                    ${escapeHtml(logs || 'No logs yet...')}
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
}

function displayJobMonitor(job) {
    const container = document.getElementById('job-monitor-content');
    currentJobStatus = job.status;
    
    const deviceCards = buildDeviceCards(job);
    const statusClass = sanitizeClassToken(job.status);
    
    container.innerHTML = `
        <div class="job-card">
            <h3>${escapeHtml(job.job_name || 'Job')} (${escapeHtml(job.job_id)})</h3>
            <p><strong>Status:</strong> <span id="job-status-text" class="status-${statusClass}">${escapeHtml(job.status || 'unknown')}</span></p>
            <p><strong>Creator:</strong> ${escapeHtml(job.creator || 'N/A')}</p>
            <p><strong>Created:</strong> ${escapeHtml(new Date(job.created_at).toLocaleString())}</p>
            ${job.completed_at ? `<p><strong>Completed:</strong> ${escapeHtml(new Date(job.completed_at).toLocaleString())}</p>` : ''}
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
    div.textContent = text === null || text === undefined ? '' : String(text);
    return div.innerHTML;
}

function sanitizeClassToken(value) {
    const token = String(value || 'unknown').toLowerCase();
    return /^[a-z0-9_-]+$/.test(token) ? token : 'unknown';
}

function domIdFromDeviceKey(key) {
    return encodeURIComponent(String(key || ''));
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
        const logElement = document.getElementById(`log-${domIdFromDeviceKey(message.device)}`);
        if (logElement) {
            logElement.textContent += '\n' + message.data;
            logElement.scrollTop = logElement.scrollHeight;
        }
    } else if (message.type === 'device_status') {
        const deviceCard = document.getElementById(`device-${domIdFromDeviceKey(message.device)}`);
        if (deviceCard) {
            const safeStatusClass = sanitizeClassToken(message.status);
            deviceCard.className = `device-card ${safeStatusClass}`;
            const statusBadge = deviceCard.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.textContent = message.status;
                statusBadge.className = `status-badge status-${safeStatusClass}`;
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
        refreshActiveJobState();
        loadTaskHistory();
    } else if (message.type === 'job_status') {
        updateJobStatus(message.status);
        refreshActiveJobState();
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
        statusText.className = `status-${sanitizeClassToken(status)}`;
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
    refreshActiveJobState();
});
