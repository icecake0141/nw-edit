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

// @ts-check

import { NwEditApiClient } from "./api-client.js";

const statusEl = document.getElementById("status");
const logEl = document.getElementById("log");
const detailMetaEl = document.getElementById("detailMeta");
const detailDataEl = document.getElementById("detailData");
const activeSummaryEl = document.getElementById("activeSummary");
const historyEl = document.getElementById("history");
const deviceCountEl = document.getElementById("deviceCount");
const useImportedEl = document.getElementById("useImported");
const runBtn = document.getElementById("runBtn");
const runAsyncBtn = document.getElementById("runAsyncBtn");
const pauseBtn = document.getElementById("pauseBtn");
const resumeBtn = document.getElementById("resumeBtn");
const cancelBtn = document.getElementById("cancelBtn");
const clearBtn = document.getElementById("clearBtn");
const importBtn = document.getElementById("importBtn");
const refreshDevicesBtn = document.getElementById("refreshDevicesBtn");
const listJobsBtn = document.getElementById("listJobsBtn");
const refreshActiveBtn = document.getElementById("refreshActiveBtn");

/** @type {WebSocket|null} */
let activeSocket = null;
/** @type {string|null} */
let selectedJobId = null;

pauseBtn.disabled = true;
resumeBtn.disabled = true;
cancelBtn.disabled = true;

function currentApiBase() {
  return document.getElementById("apiBase").value.trim();
}

function client() {
  return new NwEditApiClient(currentApiBase());
}

function toWsBase(apiBase) {
  return apiBase.replace("http://", "ws://").replace("https://", "wss://");
}

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
      return { host, port: Number(rawPort || "22") };
    });
}

function parseCommands(text) {
  return text
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
}

function openJobSocket(apiBase, jobId) {
  if (activeSocket) {
    activeSocket.close();
    activeSocket = null;
  }
  activeSocket = new WebSocket(`${toWsBase(apiBase)}/ws/v2/jobs/${jobId}`);
  activeSocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    appendLog(
      `${data.type} status=${data.status || "-"} device=${data.device || "-"} message=${data.message || "-"}`
    );
  };
  activeSocket.onerror = () => appendLog("websocket error");
}

function renderJobDetail(job, events, result) {
  const payload = {
    job,
    event_count: events.length,
    result,
  };
  detailMetaEl.textContent = `selected: ${job.job_id} (${job.status}) events=${events.length}`;
  detailDataEl.textContent = JSON.stringify(payload, null, 2);
}

function switchPage(pageName) {
  document.querySelectorAll(".page").forEach((el) => {
    el.classList.toggle("active", el.getAttribute("data-page") === pageName);
  });
  document.querySelectorAll(".nav-btn").forEach((el) => {
    const pressed = el.getAttribute("data-page") === pageName;
    el.setAttribute("aria-pressed", pressed ? "true" : "false");
  });
}

async function refreshImportedDevices() {
  const devices = await client().listDevices();
  deviceCountEl.textContent = `imported devices: ${devices.length}`;
  appendLog(`loaded imported devices: ${devices.length}`);
}

async function refreshJobs() {
  const jobs = await client().listJobs();
  historyEl.replaceChildren();

  if (jobs.length === 0) {
    const div = document.createElement("div");
    div.className = "history-item";
    div.textContent = "no jobs yet";
    historyEl.append(div);
    return;
  }

  jobs.forEach((job) => {
    const div = document.createElement("div");
    div.className = "history-item";
    div.innerHTML = `<div><strong>${job.job_name}</strong></div>
      <div class="muted">${job.job_id}</div>
      <div class="muted">status: ${job.status}</div>`;
    div.addEventListener("click", async () => {
      try {
        selectedJobId = job.job_id;
        const [detail, events, result] = await Promise.all([
          client().getJob(job.job_id),
          client().listJobEvents(job.job_id),
          client().getJobResult(job.job_id).catch(() => ({ job_id: job.job_id, status: "pending", device_results: {} })),
        ]);
        renderJobDetail(detail, events, result);
        appendLog(`history selected: ${job.job_id}`);
        switchPage("detail");
      } catch (error) {
        appendLog(String(error));
      }
    });
    historyEl.append(div);
  });

  appendLog(`loaded jobs: ${jobs.length}`);
}

async function refreshActive() {
  const active = await client().getActiveJob();
  if (!active.active || !active.job) {
    activeSummaryEl.textContent = "active job: none";
    pauseBtn.disabled = true;
    resumeBtn.disabled = true;
    cancelBtn.disabled = true;
    return;
  }

  activeSummaryEl.textContent = `active job: ${active.job.job_id} (${active.job.status})`;
  setStatus(`active:${active.job.status}`);
  pauseBtn.disabled = active.job.status !== "running";
  resumeBtn.disabled = active.job.status !== "paused";
  cancelBtn.disabled = !["running", "paused", "queued"].includes(active.job.status);
}

async function runSync() {
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

  runBtn.disabled = true;
  setStatus("creating");
  try {
    const job = await client().createJob(jobName, creator);
    appendLog(`job created: ${job.job_id}`);
    openJobSocket(currentApiBase(), job.job_id);

    const result = await client().runJob(job.job_id, commands, devices, useImported);
    appendLog(`run completed: ${result.status}`);
    Object.entries(result.device_results).forEach(([key, value]) => {
      appendLog(`${key} => status=${value.status} attempts=${value.attempts}`);
      if (value.error_code) {
        appendLog(`${key} error_code=${value.error_code}`);
      }
    });

    setStatus(result.status);
    await refreshJobs();
    await refreshActive();
  } catch (error) {
    setStatus("failed");
    appendLog(String(error));
  } finally {
    runBtn.disabled = false;
    if (activeSocket) {
      setTimeout(() => activeSocket && activeSocket.close(), 800);
    }
  }
}

async function runAsync() {
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

  runAsyncBtn.disabled = true;
  setStatus("creating-async");
  try {
    const job = await client().createJob(jobName, creator);
    appendLog(`job created: ${job.job_id}`);
    openJobSocket(currentApiBase(), job.job_id);
    const started = await client().runJobAsync(job.job_id, commands, devices, useImported);
    appendLog(`run async started: ${started.status}`);
    setStatus("running");
    await refreshJobs();
    await refreshActive();
    switchPage("monitor");
  } catch (error) {
    setStatus("failed");
    appendLog(String(error));
  } finally {
    runAsyncBtn.disabled = false;
  }
}

runBtn.addEventListener("click", runSync);
runAsyncBtn.addEventListener("click", runAsync);

importBtn.addEventListener("click", async () => {
  const csvInput = document.getElementById("csvInput").value;
  try {
    const result = await client().importDevices(csvInput);
    appendLog(`import success: valid=${result.devices.length} failed_rows=${result.failed_rows.length}`);
    if (result.failed_rows.length > 0) {
      appendLog(`first failure: ${result.failed_rows[0].error}`);
    }
    await refreshImportedDevices();
  } catch (error) {
    appendLog(String(error));
  }
});

refreshDevicesBtn.addEventListener("click", () => {
  refreshImportedDevices().catch((error) => appendLog(String(error)));
});

listJobsBtn.addEventListener("click", () => {
  refreshJobs().catch((error) => appendLog(String(error)));
});

refreshActiveBtn.addEventListener("click", () => {
  refreshActive().catch((error) => appendLog(String(error)));
});

pauseBtn.addEventListener("click", async () => {
  try {
    const result = await client().controlActiveJob("pause");
    appendLog(`paused ${result.job_id}`);
    setStatus("paused");
    await refreshActive();
  } catch (error) {
    appendLog(String(error));
  }
});

resumeBtn.addEventListener("click", async () => {
  try {
    const result = await client().controlActiveJob("resume");
    appendLog(`resumed ${result.job_id}`);
    setStatus("running");
    await refreshActive();
  } catch (error) {
    appendLog(String(error));
  }
});

cancelBtn.addEventListener("click", async () => {
  try {
    const result = await client().controlActiveJob("cancel");
    appendLog(`cancelled ${result.job_id}`);
    setStatus("cancelled");
    await refreshActive();
    if (selectedJobId) {
      const events = await client().listJobEvents(selectedJobId);
      appendLog(`selected job events: ${events.length}`);
    }
  } catch (error) {
    appendLog(String(error));
  }
});

clearBtn.addEventListener("click", () => {
  logEl.textContent = "";
});

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    switchPage(btn.getAttribute("data-page") || "import");
  });
});

setInterval(() => {
  refreshActive().catch((error) => appendLog(String(error)));
}, 4000);

refreshImportedDevices().catch(() => {});
refreshJobs().catch(() => {});
refreshActive().catch(() => {});
