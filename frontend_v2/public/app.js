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
 * This file was created or modified with the assistance of an AI (Large Language Model).
 * Review required for correctness, security, and licensing.
 */

const statusEl = document.getElementById("status");
const logEl = document.getElementById("log");
const runBtn = document.getElementById("runBtn");
const runAsyncBtn = document.getElementById("runAsyncBtn");
const pauseBtn = document.getElementById("pauseBtn");
const resumeBtn = document.getElementById("resumeBtn");
const cancelBtn = document.getElementById("cancelBtn");
const clearBtn = document.getElementById("clearBtn");
const importBtn = document.getElementById("importBtn");
const refreshDevicesBtn = document.getElementById("refreshDevicesBtn");
const listJobsBtn = document.getElementById("listJobsBtn");
const historyEl = document.getElementById("history");
const deviceCountEl = document.getElementById("deviceCount");
const useImportedEl = document.getElementById("useImported");

let activeSocket = null;
let latestActiveJobId = null;
pauseBtn.disabled = true;
resumeBtn.disabled = true;
cancelBtn.disabled = true;

function setStatus(text) {
  statusEl.textContent = text;
}

function appendLog(message) {
  const line = `[${new Date().toLocaleTimeString()}] ${message}`;
  logEl.textContent += `${line}\n`;
  logEl.scrollTop = logEl.scrollHeight;
}

function parseDevices(text) {
  return text
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean)
    .map((line) => {
      const [host, rawPort] = line.split(":");
      const port = Number(rawPort || "22");
      return { host, port };
    });
}

function parseCommands(text) {
  return text
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
}

function toWsBase(apiBase) {
  return apiBase.replace("http://", "ws://").replace("https://", "wss://");
}

async function createJob(apiBase, jobName, creator) {
  const response = await fetch(`${apiBase}/api/v2/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_name: jobName, creator }),
  });
  if (!response.ok) {
    throw new Error(`create job failed: ${response.status}`);
  }
  return response.json();
}

async function runJob(apiBase, jobId, devices, commands, useImported) {
  const payload = {
    commands,
    concurrency_limit: 2,
    stagger_delay: 0.0,
    stop_on_error: true,
    non_canary_retry_limit: 1,
    retry_backoff_seconds: 0.0,
  };
  if (!useImported) {
    payload.devices = devices;
    payload.canary = devices[0];
  }
  const response = await fetch(`${apiBase}/api/v2/jobs/${jobId}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`run job failed: ${response.status} ${text}`);
  }
  return response.json();
}

async function runJobAsync(apiBase, jobId, devices, commands, useImported) {
  const payload = {
    commands,
    concurrency_limit: 2,
    stagger_delay: 0.0,
    stop_on_error: true,
    non_canary_retry_limit: 1,
    retry_backoff_seconds: 0.0,
  };
  if (!useImported) {
    payload.devices = devices;
    payload.canary = devices[0];
  }
  const response = await fetch(`${apiBase}/api/v2/jobs/${jobId}/run/async`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`run async failed: ${response.status} ${text}`);
  }
  return response.json();
}

async function importCsv(apiBase, csvInput) {
  const response = await fetch(`${apiBase}/api/v2/devices/import`, {
    method: "POST",
    headers: { "Content-Type": "text/plain" },
    body: csvInput,
  });
  if (!response.ok) {
    throw new Error(`import failed: ${response.status}`);
  }
  return response.json();
}

async function fetchDevices(apiBase) {
  const response = await fetch(`${apiBase}/api/v2/devices`);
  if (!response.ok) {
    throw new Error(`device fetch failed: ${response.status}`);
  }
  return response.json();
}

async function fetchJobs(apiBase) {
  const response = await fetch(`${apiBase}/api/v2/jobs`);
  if (!response.ok) {
    throw new Error(`job list failed: ${response.status}`);
  }
  return response.json();
}

async function fetchActiveJob(apiBase) {
  const response = await fetch(`${apiBase}/api/v2/jobs/active`);
  if (!response.ok) {
    throw new Error(`active job failed: ${response.status}`);
  }
  return response.json();
}

async function controlActiveJob(apiBase, action) {
  const active = await fetchActiveJob(apiBase);
  if (!active.active || !active.job) {
    throw new Error("no active job");
  }
  const response = await fetch(`${apiBase}/api/v2/jobs/${active.job.job_id}/${action}`, {
    method: "POST",
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${action} failed: ${response.status} ${text}`);
  }
  return response.json();
}

async function fetchJob(apiBase, jobId) {
  const response = await fetch(`${apiBase}/api/v2/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error(`job detail failed: ${response.status}`);
  }
  return response.json();
}

async function fetchJobEvents(apiBase, jobId) {
  const response = await fetch(`${apiBase}/api/v2/jobs/${jobId}/events`);
  if (!response.ok) {
    throw new Error(`job events failed: ${response.status}`);
  }
  return response.json();
}

async function fetchJobResult(apiBase, jobId) {
  const response = await fetch(`${apiBase}/api/v2/jobs/${jobId}/result`);
  if (!response.ok) {
    throw new Error(`job result failed: ${response.status}`);
  }
  return response.json();
}

function renderHistory(items) {
  historyEl.replaceChildren();
  if (!items.length) {
    const div = document.createElement("div");
    div.className = "history-item";
    div.textContent = "no jobs yet";
    historyEl.append(div);
    return;
  }
  items.forEach((job) => {
    const div = document.createElement("div");
    div.className = "history-item";
    div.innerHTML = `
      <div><strong>${job.job_name}</strong></div>
      <div class="muted">${job.job_id}</div>
      <div class="muted">status: ${job.status}</div>
    `;
    div.addEventListener("click", async () => {
      const apiBase = document.getElementById("apiBase").value.trim();
      try {
        const detail = await fetchJob(apiBase, job.job_id);
        const events = await fetchJobEvents(apiBase, job.job_id);
        const result = await fetchJobResult(apiBase, job.job_id);
        appendLog(
          `history selected: ${detail.job_id} status=${detail.status} events=${events.length}`
        );
        Object.entries(result.device_results || {}).forEach(([key, value]) => {
          appendLog(`result ${key}: status=${value.status} attempts=${value.attempts}`);
        });
      } catch (error) {
        appendLog(String(error));
      }
    });
    historyEl.append(div);
  });
}

async function refreshImportedDevices() {
  const apiBase = document.getElementById("apiBase").value.trim();
  const devices = await fetchDevices(apiBase);
  deviceCountEl.textContent = `imported devices: ${devices.length}`;
  appendLog(`loaded imported devices: ${devices.length}`);
}

async function refreshJobs() {
  const apiBase = document.getElementById("apiBase").value.trim();
  const jobs = await fetchJobs(apiBase);
  renderHistory(jobs);
  appendLog(`loaded jobs: ${jobs.length}`);
}

function openJobSocket(apiBase, jobId) {
  if (activeSocket) {
    activeSocket.close();
    activeSocket = null;
  }
  const wsUrl = `${toWsBase(apiBase)}/ws/v2/jobs/${jobId}`;
  activeSocket = new WebSocket(wsUrl);
  activeSocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    appendLog(
      `${data.type} status=${data.status || "-"} device=${data.device || "-"} message=${data.message || "-"}`
    );
  };
  activeSocket.onerror = () => appendLog("websocket error");
}

async function run() {
  const apiBase = document.getElementById("apiBase").value.trim();
  const jobName = document.getElementById("jobName").value.trim();
  const creator = document.getElementById("creator").value.trim();
  const devices = parseDevices(document.getElementById("devices").value);
  const commands = parseCommands(document.getElementById("commands").value);
  const useImported = useImportedEl.checked;

  if (commands.length === 0) {
    appendLog("devices or commands is empty");
    return;
  }
  if (!useImported && devices.length === 0) {
    appendLog("ad-hoc devices is empty");
    return;
  }

  setStatus("creating");
  runBtn.disabled = true;
  try {
    const job = await createJob(apiBase, jobName, creator);
    appendLog(`job created: ${job.job_id}`);
    openJobSocket(apiBase, job.job_id);

    setStatus("running");
    const result = await runJob(apiBase, job.job_id, devices, commands, useImported);
    appendLog(`run completed: ${result.status}`);
    Object.entries(result.device_results).forEach(([key, value]) => {
      appendLog(`${key} => status=${value.status} attempts=${value.attempts}`);
      if (value.diff) {
        appendLog(`${key} diff:\n${value.diff}`);
      }
    });
    setStatus(result.status);
    await refreshJobs();
  } catch (error) {
    appendLog(String(error));
    setStatus("failed");
  } finally {
    runBtn.disabled = false;
    if (activeSocket) {
      setTimeout(() => activeSocket.close(), 800);
    }
  }
}

async function runAsync() {
  const apiBase = document.getElementById("apiBase").value.trim();
  const jobName = document.getElementById("jobName").value.trim();
  const creator = document.getElementById("creator").value.trim();
  const devices = parseDevices(document.getElementById("devices").value);
  const commands = parseCommands(document.getElementById("commands").value);
  const useImported = useImportedEl.checked;

  if (commands.length === 0) {
    appendLog("commands is empty");
    return;
  }
  if (!useImported && devices.length === 0) {
    appendLog("ad-hoc devices is empty");
    return;
  }

  setStatus("creating-async");
  runAsyncBtn.disabled = true;
  try {
    const job = await createJob(apiBase, jobName, creator);
    appendLog(`job created: ${job.job_id}`);
    openJobSocket(apiBase, job.job_id);
    const started = await runJobAsync(apiBase, job.job_id, devices, commands, useImported);
    appendLog(`run async started: ${started.status}`);
    setStatus("running");
    await refreshJobs();
  } catch (error) {
    appendLog(String(error));
    setStatus("failed");
  } finally {
    runAsyncBtn.disabled = false;
  }
}

runBtn.addEventListener("click", run);
runAsyncBtn.addEventListener("click", runAsync);
importBtn.addEventListener("click", async () => {
  const apiBase = document.getElementById("apiBase").value.trim();
  const csvInput = document.getElementById("csvInput").value;
  try {
    const result = await importCsv(apiBase, csvInput);
    appendLog(
      `import success: valid=${result.devices.length} failed_rows=${result.failed_rows.length}`
    );
    if (result.failed_rows.length) {
      appendLog(`first failure: ${result.failed_rows[0].error}`);
    }
    await refreshImportedDevices();
  } catch (error) {
    appendLog(String(error));
  }
});
refreshDevicesBtn.addEventListener("click", async () => {
  try {
    await refreshImportedDevices();
  } catch (error) {
    appendLog(String(error));
  }
});
listJobsBtn.addEventListener("click", async () => {
  try {
    await refreshJobs();
  } catch (error) {
    appendLog(String(error));
  }
});
clearBtn.addEventListener("click", () => {
  logEl.textContent = "";
});

refreshImportedDevices().catch(() => {});
refreshJobs().catch(() => {});

setInterval(async () => {
  const apiBase = document.getElementById("apiBase").value.trim();
  try {
    const active = await fetchActiveJob(apiBase);
    if (active.active && active.job) {
      latestActiveJobId = active.job.job_id;
      setStatus(`active:${active.job.status}`);
      pauseBtn.disabled = active.job.status !== "running";
      resumeBtn.disabled = active.job.status !== "paused";
      cancelBtn.disabled = !["running", "paused", "queued"].includes(active.job.status);
    } else {
      latestActiveJobId = null;
      pauseBtn.disabled = true;
      resumeBtn.disabled = true;
      cancelBtn.disabled = true;
    }
  } catch (error) {
    appendLog(String(error));
  }
}, 4000);

pauseBtn.addEventListener("click", async () => {
  const apiBase = document.getElementById("apiBase").value.trim();
  try {
    const result = await controlActiveJob(apiBase, "pause");
    appendLog(`paused ${result.job_id}`);
    setStatus("paused");
  } catch (error) {
    appendLog(String(error));
  }
});

resumeBtn.addEventListener("click", async () => {
  const apiBase = document.getElementById("apiBase").value.trim();
  try {
    const result = await controlActiveJob(apiBase, "resume");
    appendLog(`resumed ${result.job_id}`);
    setStatus("running");
  } catch (error) {
    appendLog(String(error));
  }
});

cancelBtn.addEventListener("click", async () => {
  const apiBase = document.getElementById("apiBase").value.trim();
  try {
    const result = await controlActiveJob(apiBase, "cancel");
    appendLog(`cancelled ${result.job_id}`);
    setStatus("cancelled");
    if (latestActiveJobId) {
      const events = await fetchJobEvents(apiBase, latestActiveJobId);
      appendLog(`events after cancel: ${events.length}`);
    }
  } catch (error) {
    appendLog(String(error));
  }
});
