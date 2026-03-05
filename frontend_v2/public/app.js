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
const importProgressEl = document.getElementById("importProgress");
const importErrorsEl = document.getElementById("importErrors");
const importedDeviceListEl = document.getElementById("importedDeviceList");
const importedDeviceHintEl = document.getElementById("importedDeviceHint");
const useImportedEl = document.getElementById("useImported");
const enablePresetModeEl = document.getElementById("enablePresetMode");
const presetPanelEl = document.getElementById("presetPanel");
const osModelSelectEl = document.getElementById("osModelSelect");
const presetSelectEl = document.getElementById("presetSelect");
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
const selectAllImportedBtn = document.getElementById("selectAllImportedBtn");
const clearImportedSelectionBtn = document.getElementById("clearImportedSelectionBtn");
const verifyCommandsEl = document.getElementById("verifyCommands");

/** @type {WebSocket|null} */
let activeSocket = null;
/** @type {string|null} */
let selectedJobId = null;
/** @type {import("./api-client.js").DeviceProfile[]} */
let importedDevices = [];
/** @type {import("./api-client.js").Preset[]} */
let currentPresets = [];

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

function setImportInProgress(inProgress) {
  importProgressEl.classList.toggle("hidden", !inProgress);
  importBtn.disabled = inProgress;
  if (inProgress) {
    importProgressEl.removeAttribute("value");
  }
}

function showImportError(text) {
  importErrorsEl.textContent = text;
  importErrorsEl.classList.remove("hidden");
}

function clearImportError() {
  importErrorsEl.textContent = "";
  importErrorsEl.classList.add("hidden");
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

function parseGlobalVars(text) {
  const raw = text.trim();
  if (!raw) {
    return {};
  }
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    throw new Error(`global vars JSON parse error: ${String(error)}`);
  }
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("global vars must be a JSON object");
  }
  return Object.fromEntries(
    Object.entries(parsed).map(([key, value]) => [String(key), String(value)])
  );
}

function importedDeviceKey(device) {
  return `${device.host}:${device.port}`;
}

function selectedImportedDeviceKeys() {
  return Array.from(
    document.querySelectorAll('input[name="importedDeviceKeys"]:checked')
  ).map((el) => el.value);
}

function selectedOsModel() {
  return osModelSelectEl.value.trim();
}

function renderImportedDeviceList() {
  const osModel = enablePresetModeEl.checked ? selectedOsModel() : "";
  const candidates = osModel
    ? importedDevices.filter((device) => device.device_type === osModel)
    : importedDevices;
  importedDeviceListEl.replaceChildren();
  candidates.forEach((device) => {
    const label = document.createElement("label");
    label.className = "device-option";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = "importedDeviceKeys";
    input.value = importedDeviceKey(device);
    const text = document.createElement("span");
    text.textContent = `${importedDeviceKey(device)} (${device.name || "-"} / ${device.device_type})`;
    label.append(input, text);
    importedDeviceListEl.append(label);
  });
  importedDeviceHintEl.textContent = `Imported target candidates: ${candidates.length}`;
}

function selectAllImported() {
  document.querySelectorAll('input[name="importedDeviceKeys"]').forEach((input) => {
    input.checked = true;
  });
}

function clearImportedSelection() {
  document.querySelectorAll('input[name="importedDeviceKeys"]').forEach((input) => {
    input.checked = false;
  });
}

function populateOsModelSelect(models) {
  const previous = selectedOsModel();
  osModelSelectEl.innerHTML = '<option value="">(not selected)</option>';
  models.forEach((model) => {
    const option = document.createElement("option");
    option.value = model;
    option.textContent = model;
    osModelSelectEl.append(option);
  });
  if (previous && models.includes(previous)) {
    osModelSelectEl.value = previous;
  }
}

async function refreshPresetOptions() {
  if (!enablePresetModeEl.checked) {
    currentPresets = [];
    presetSelectEl.innerHTML = '<option value="">(not selected)</option>';
    return;
  }
  const model = selectedOsModel();
  presetSelectEl.innerHTML = '<option value="">(not selected)</option>';
  if (!model) {
    currentPresets = [];
    return;
  }
  currentPresets = await client().listPresets(model);
  currentPresets.forEach((preset) => {
    const option = document.createElement("option");
    option.value = preset.preset_id;
    option.textContent = preset.name;
    presetSelectEl.append(option);
  });
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
  importedDevices = await client().listDevices();
  deviceCountEl.textContent = `imported devices: ${importedDevices.length}`;
  const importedModels = Array.from(
    new Set(importedDevices.map((device) => device.device_type))
  ).sort();
  const presetModels = await client().listPresetOsModels().catch(() => []);
  const allModels = Array.from(new Set([...importedModels, ...presetModels])).sort();
  populateOsModelSelect(allModels);
  renderImportedDeviceList();
  await refreshPresetOptions().catch((error) => appendLog(String(error)));
  appendLog(`loaded imported devices: ${importedDevices.length}`);
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
    const titleWrap = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = job.job_name;
    titleWrap.append(title);

    const id = document.createElement("div");
    id.className = "muted";
    id.textContent = job.job_id;

    const status = document.createElement("div");
    status.className = "muted";
    status.textContent = `status: ${job.status}`;

    div.append(titleWrap, id, status);
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

function resolveRunTargets(useImported, adHocDevices) {
  if (!useImported) {
    return {
      importedDeviceKeys: [],
      adHocDevices,
    };
  }
  if (importedDevices.length === 0) {
    throw new Error("imported devices are empty");
  }
  const chosen = selectedImportedDeviceKeys();
  return {
    importedDeviceKeys:
      chosen.length > 0 ? chosen : importedDevices.map((device) => importedDeviceKey(device)),
    adHocDevices: [],
  };
}

async function runSync() {
  const jobName = document.getElementById("jobName").value.trim();
  const creator = document.getElementById("creator").value.trim();
  const globalVarsText = document.getElementById("globalVars").value;
  const devices = parseDevices(document.getElementById("devices").value);
  const commands = parseCommands(document.getElementById("commands").value);
  const verifyCommands = parseCommands(verifyCommandsEl.value);
  const useImported = useImportedEl.checked;

  if (commands.length === 0) {
    appendLog("commands is empty");
    return;
  }

  let targets;
  try {
    targets = resolveRunTargets(useImported, devices);
    if (!useImported && targets.adHocDevices.length === 0) {
      appendLog("ad-hoc devices is empty");
      return;
    }
  } catch (error) {
    appendLog(String(error));
    return;
  }

  let globalVars;
  try {
    globalVars = parseGlobalVars(globalVarsText);
  } catch (error) {
    appendLog(String(error));
    return;
  }

  runBtn.disabled = true;
  setStatus("creating");
  try {
    const job = await client().createJob(jobName, creator, globalVars);
    appendLog(`job created: ${job.job_id}`);
    openJobSocket(currentApiBase(), job.job_id);

    const result = await client().runJob(
      job.job_id,
      commands,
      targets.adHocDevices,
      useImported,
      {
        verifyCommands,
        importedDeviceKeys: targets.importedDeviceKeys,
      }
    );
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
  const globalVarsText = document.getElementById("globalVars").value;
  const devices = parseDevices(document.getElementById("devices").value);
  const commands = parseCommands(document.getElementById("commands").value);
  const verifyCommands = parseCommands(verifyCommandsEl.value);
  const useImported = useImportedEl.checked;

  if (commands.length === 0) {
    appendLog("commands is empty");
    return;
  }

  let targets;
  try {
    targets = resolveRunTargets(useImported, devices);
    if (!useImported && targets.adHocDevices.length === 0) {
      appendLog("ad-hoc devices is empty");
      return;
    }
  } catch (error) {
    appendLog(String(error));
    return;
  }

  let globalVars;
  try {
    globalVars = parseGlobalVars(globalVarsText);
  } catch (error) {
    appendLog(String(error));
    return;
  }

  runAsyncBtn.disabled = true;
  setStatus("creating-async");
  try {
    const job = await client().createJob(jobName, creator, globalVars);
    appendLog(`job created: ${job.job_id}`);
    openJobSocket(currentApiBase(), job.job_id);
    const started = await client().runJobAsync(
      job.job_id,
      commands,
      targets.adHocDevices,
      useImported,
      {
        verifyCommands,
        importedDeviceKeys: targets.importedDeviceKeys,
      }
    );
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
  clearImportError();
  setImportInProgress(true);
  try {
    const result = await client().importDevices(csvInput);
    appendLog(`import success: valid=${result.devices.length} failed_rows=${result.failed_rows.length}`);
    if (result.failed_rows.length > 0) {
      const top = result.failed_rows
        .slice(0, 5)
        .map((item) => `row ${item.row_number}: ${item.error}`)
        .join(" | ");
      showImportError(`Import completed with ${result.failed_rows.length} failed row(s). ${top}`);
      appendLog(`first failure: ${result.failed_rows[0].error}`);
    }
    await refreshImportedDevices();
  } catch (error) {
    const message = String(error);
    showImportError(`CSV import failed. ${message}`);
    appendLog(message);
  } finally {
    setImportInProgress(false);
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

useImportedEl.addEventListener("change", () => {
  importedDeviceListEl.parentElement.classList.toggle("hidden", !useImportedEl.checked);
});

enablePresetModeEl.addEventListener("change", async () => {
  presetPanelEl.classList.toggle("hidden", !enablePresetModeEl.checked);
  if (!enablePresetModeEl.checked) {
    osModelSelectEl.value = "";
    presetSelectEl.value = "";
    await refreshPresetOptions().catch((error) => appendLog(String(error)));
    renderImportedDeviceList();
    return;
  }
  await refreshPresetOptions().catch((error) => appendLog(String(error)));
  renderImportedDeviceList();
});

osModelSelectEl.addEventListener("change", () => {
  renderImportedDeviceList();
  refreshPresetOptions().catch((error) => appendLog(String(error)));
});

presetSelectEl.addEventListener("change", () => {
  const selected = currentPresets.find(
    (preset) => preset.preset_id === presetSelectEl.value
  );
  if (!selected) {
    return;
  }
  document.getElementById("commands").value = selected.commands.join("\n");
  verifyCommandsEl.value = selected.verify_commands.join("\n");
  appendLog(`preset applied: ${selected.name} (${selected.os_model})`);
});

selectAllImportedBtn.addEventListener("click", () => {
  selectAllImported();
});

clearImportedSelectionBtn.addEventListener("click", () => {
  clearImportedSelection();
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

presetPanelEl.classList.add("hidden");
refreshImportedDevices().catch(() => {});
refreshJobs().catch(() => {});
refreshActive().catch(() => {});
