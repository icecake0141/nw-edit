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
const apiBaseFieldEl = document.getElementById("apiBaseField");
const modeStatusEl = document.getElementById("modeStatus");
const logEl = document.getElementById("log");
const detailMetaEl = document.getElementById("detailMeta");
const detailDataEl = document.getElementById("detailData");
const detailSummaryEl = document.getElementById("detailSummary");
const detailDevicesEl = document.getElementById("detailDevices");
const activeSummaryEl = document.getElementById("activeSummary");
const monitorSummaryEl = document.getElementById("monitorSummary");
const monitorDevicesEl = document.getElementById("monitorDevices");
const historyEl = document.getElementById("history");
const deviceCountEl = document.getElementById("deviceCount");
const importProgressEl = document.getElementById("importProgress");
const importProgressTextEl = document.getElementById("importProgressText");
const importLoadingEl = document.getElementById("importLoading");
const importStreamLogEl = document.getElementById("importStreamLog");
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
const verifyModeEl = document.getElementById("verifyMode");
const canaryDeviceEl = document.getElementById("canaryDevice");
const concurrencyLimitEl = document.getElementById("concurrencyLimit");
const staggerDelayEl = document.getElementById("staggerDelay");
const stopOnErrorEl = document.getElementById("stopOnError");
const enableRunConfirmationEl = document.getElementById("enableRunConfirmation");
const postCanaryStrategyEl = document.getElementById("postCanaryStrategy");
const statusDeviceSelectEl = document.getElementById("statusDeviceSelect");
const statusCommandsEl = document.getElementById("statusCommands");
const statusRunBtn = document.getElementById("statusRunBtn");
const statusOutputEl = document.getElementById("statusOutput");
const activeJobBannerEl = document.getElementById("activeJobBanner");
const activeJobBannerTextEl = document.getElementById("activeJobBannerText");
const viewActiveJobBtn = document.getElementById("viewActiveJobBtn");
const prodWarningOverlayEl = document.getElementById("prodWarningOverlay");
const runReviewPanelEl = document.getElementById("runReviewPanel");
const reviewModeTextEl = document.getElementById("reviewModeText");
const reviewTargetHostsEl = document.getElementById("reviewTargetHosts");
const reviewCommandsEl = document.getElementById("reviewCommands");
const reviewVerifyCommandsEl = document.getElementById("reviewVerifyCommands");
const reviewSettingsEl = document.getElementById("reviewSettings");
const reviewFlowDiagramEl = document.getElementById("reviewFlowDiagram");
const reviewExecuteBtn = document.getElementById("reviewExecuteBtn");
const reviewCancelBtn = document.getElementById("reviewCancelBtn");
const reviewToggleHostsBtn = document.getElementById("reviewToggleHostsBtn");

/** @type {WebSocket|null} */
let activeSocket = null;
/** @type {string|null} */
let selectedJobId = null;
/** @type {import("./api-client.js").DeviceProfile[]} */
let importedDevices = [];
/** @type {import("./api-client.js").Preset[]} */
let currentPresets = [];
/** @type {Set<string>} */
let prodDeviceKeys = new Set();
/** @type {string[]} */
let detailTargetDeviceKeys = [];
let monitorResultLoading = false;
let runSyncBusy = false;
let runAsyncBusy = false;
/** @type {import("./api-client.js").JobDetail|null} */
let activeBlockingJob = null;
let reviewHostsCollapsed = false;
/** @type {{mode: string, runInput: any}|null} */
let pendingRunReview = null;
const monitorState = {
  job: null,
  targetDeviceKeys: [],
  canaryKey: null,
  deviceStatuses: {},
  streamLogs: {},
  result: null,
  eventCount: 0,
};

pauseBtn.disabled = true;
resumeBtn.disabled = true;
cancelBtn.disabled = true;

function currentApiBase() {
  return document.getElementById("apiBase").value.trim();
}

function isPrivilegedModeEnabled() {
  const params = new URLSearchParams(window.location.search);
  const mode = (params.get("mode") || "").toLowerCase();
  const role = (params.get("role") || "").toLowerCase();
  if (mode === "developer" || mode === "admin") {
    return true;
  }
  if (role === "developer" || role === "admin") {
    return true;
  }
  const boolLike = ["1", "true", "yes", "on"];
  const developerEnabled = boolLike.includes(
    (params.get("developer") || "").toLowerCase()
  );
  const adminEnabled = boolLike.includes(
    (params.get("admin") || "").toLowerCase()
  );
  return developerEnabled || adminEnabled;
}

function applyApiBaseVisibility() {
  if (!apiBaseFieldEl) {
    return;
  }
  apiBaseFieldEl.classList.toggle("hidden", !isPrivilegedModeEnabled());
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

function setModeStatus(text) {
  if (modeStatusEl) {
    modeStatusEl.textContent = text;
  }
}

function appendLog(message) {
  const line = `[${new Date().toLocaleTimeString()}] ${message}`;
  logEl.textContent += `${line}\n`;
  logEl.scrollTop = logEl.scrollHeight;
}

function appendImportStreamLog(message) {
  if (!importStreamLogEl) {
    return;
  }
  const line = `[${new Date().toLocaleTimeString()}] ${message}`;
  importStreamLogEl.textContent += `${line}\n`;
  importStreamLogEl.scrollTop = importStreamLogEl.scrollHeight;
}

function resetImportStreamLog() {
  if (!importStreamLogEl) {
    return;
  }
  importStreamLogEl.textContent = "";
}

function setImportStreamVisible(visible) {
  if (!importLoadingEl || !importStreamLogEl) {
    return;
  }
  importLoadingEl.classList.toggle("hidden", !visible);
  importStreamLogEl.classList.toggle("hidden", !visible);
}

function isActiveRunBlocking(status) {
  return ["queued", "running", "paused"].includes(String(status || "").toLowerCase());
}

function updateCreateActionState() {
  const blocked = Boolean(activeBlockingJob);
  runBtn.disabled = blocked || runSyncBusy;
  runAsyncBtn.disabled = blocked || runAsyncBusy;
  if (!activeJobBannerEl || !activeJobBannerTextEl) {
    return;
  }
  if (!blocked) {
    activeJobBannerEl.classList.add("hidden");
    return;
  }
  activeJobBannerTextEl.textContent =
    `Active job ${activeBlockingJob.job_id} (${activeBlockingJob.status}) is running. ` +
    "New job creation is disabled.";
  activeJobBannerEl.classList.remove("hidden");
}

function setImportInProgress(inProgress) {
  importBtn.disabled = inProgress;
  setImportStreamVisible(inProgress);
  if (inProgress) {
    importProgressEl.classList.remove("hidden");
    importProgressTextEl.classList.remove("hidden");
    importProgressTextEl.textContent = "Validating devices... 0/0";
  }
  if (inProgress) {
    importProgressEl.removeAttribute("value");
    importProgressEl.removeAttribute("max");
  } else {
    importProgressEl.max = 100;
    importProgressEl.value = 100;
    importProgressTextEl.classList.add("hidden");
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

function formatImportErrorDetail(detail) {
  if (!detail) {
    return "CSV import failed";
  }
  if (typeof detail === "string") {
    return detail;
  }
  if (detail.failed_rows && Array.isArray(detail.failed_rows)) {
    const lines = detail.failed_rows.map(
      (item) => `- row ${item.row_number || "?"}: ${item.error}`
    );
    return `${detail.message || "CSV import failed"} (${detail.failed_rows.length} rows)\n${lines.join("\n")}`;
  }
  return JSON.stringify(detail);
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

function resolveHostname(device) {
  const name = String(device?.name || "").trim();
  if (name) {
    return name;
  }
  const hostVarsHostname = String(device?.host_vars?.hostname || "").trim();
  if (hostVarsHostname) {
    return hostVarsHostname;
  }
  return String(device?.host || "");
}

function buildDeviceDisplayMap(devices) {
  return Object.fromEntries(
    devices.map((device) => [importedDeviceKey(device), resolveHostname(device)])
  );
}

function hostFromDeviceKey(deviceKey) {
  const delimiter = String(deviceKey || "").lastIndexOf(":");
  if (delimiter <= 0) {
    return String(deviceKey || "");
  }
  return deviceKey.slice(0, delimiter);
}

function canaryOptionLabel(item) {
  const hostname = item.hostname || item.host;
  return `${item.key} (${hostname})`;
}

function setProdWarningVisible(visible) {
  if (!prodWarningOverlayEl) {
    return;
  }
  prodWarningOverlayEl.classList.toggle("active", visible);
}

function currentPageName() {
  const activePage = document.querySelector(".page.active");
  return activePage?.getAttribute("data-page") || "import";
}

function hasProdDevice(keys) {
  return keys.some((key) => prodDeviceKeys.has(key));
}

function createPageTargetKeysForWarning() {
  if (!useImportedEl.checked) {
    return [];
  }
  const selectedKeys = selectedImportedDeviceKeys();
  if (selectedKeys.length > 0) {
    return selectedKeys;
  }
  return importedDevices.map((device) => importedDeviceKey(device));
}

function refreshProdWarningOverlay() {
  const page = currentPageName();
  let visible = false;
  if (page === "create") {
    visible = hasProdDevice(createPageTargetKeysForWarning());
  } else if (page === "monitor") {
    visible = hasProdDevice(monitorState.targetDeviceKeys || []);
  } else if (page === "detail") {
    visible = hasProdDevice(detailTargetDeviceKeys || []);
  }
  setProdWarningVisible(visible);
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
    text.textContent = `${importedDeviceKey(device)} (${device.name || "-"} / ${device.device_type}${device.prod ? " / PROD" : ""})`;
    label.append(input, text);
    importedDeviceListEl.append(label);
  });
  importedDeviceHintEl.textContent = `Imported target candidates: ${candidates.length}`;
  refreshProdWarningOverlay();
}

function populateStatusDeviceSelect() {
  if (!statusDeviceSelectEl) {
    return;
  }
  statusDeviceSelectEl.innerHTML = '<option value="">(select device)</option>';
  importedDevices.forEach((device) => {
    const option = document.createElement("option");
    option.value = importedDeviceKey(device);
    option.textContent = `${importedDeviceKey(device)} (${device.name || "-"} / ${device.device_type}${device.prod ? " / PROD" : ""})`;
    statusDeviceSelectEl.append(option);
  });
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

function refreshCanaryOptions() {
  if (!canaryDeviceEl) {
    return;
  }
  const previous = canaryDeviceEl.value;
  let candidates = [];
  if (useImportedEl.checked) {
    const selectedKeys = selectedImportedDeviceKeys();
    const keys =
      selectedKeys.length > 0
        ? selectedKeys
        : importedDevices.map((device) => importedDeviceKey(device));
    const uniqueKeys = Array.from(new Set(keys));
    candidates = uniqueKeys
      .map((key) => {
        const matched = importedDevices.find((device) => importedDeviceKey(device) === key);
        const [host, rawPort] = key.split(":");
        return {
          key,
          host,
          port: Number(rawPort || "22"),
          hostname: matched?.name || host,
        };
      })
      .filter((item) => item.host && Number.isFinite(item.port));
  } else {
    const adHocDevices = parseDevices(document.getElementById("devices").value);
    const unique = new Map();
    adHocDevices.forEach((device) => {
      unique.set(`${device.host}:${device.port}`, device);
    });
    candidates = Array.from(unique.values()).map((device) => ({
      key: `${device.host}:${device.port}`,
      host: device.host,
      port: device.port,
      hostname: device.host,
    }));
  }

  canaryDeviceEl.innerHTML = '<option value="">(select canary)</option>';
  candidates.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.key;
    option.textContent = canaryOptionLabel(item);
    canaryDeviceEl.append(option);
  });
  if (previous && candidates.some((item) => item.key === previous)) {
    canaryDeviceEl.value = previous;
  }
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
    handleJobSocketMessage(data).catch((error) => appendLog(String(error)));
  };
  activeSocket.onerror = () => appendLog("websocket error");
  activeSocket.onclose = () => appendLog(`websocket closed for ${jobId}`);
}

function formatTimestamp(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function normalizedStatus(status) {
  switch (String(status || "").toLowerCase()) {
    case "running":
      return "running";
    case "paused":
      return "paused";
    case "failed":
      return "failed";
    case "cancelled":
      return "cancelled";
    case "success":
    case "completed":
      return "completed";
    default:
      return "queued";
  }
}

function statusLabel(status) {
  switch (normalizedStatus(status)) {
    case "running":
      return "Running";
    case "paused":
      return "Paused";
    case "failed":
      return "Failed";
    case "cancelled":
      return "Cancelled";
    case "completed":
      return "Complete";
    default:
      return "Queue";
  }
}

function ensureMonitorDevice(deviceKey) {
  if (!monitorState.deviceStatuses[deviceKey]) {
    monitorState.deviceStatuses[deviceKey] = "queued";
  }
  if (!monitorState.streamLogs[deviceKey]) {
    monitorState.streamLogs[deviceKey] = [];
  }
}

function pushDeviceStream(deviceKey, line) {
  ensureMonitorDevice(deviceKey);
  monitorState.streamLogs[deviceKey].push(line);
  if (monitorState.streamLogs[deviceKey].length > 500) {
    monitorState.streamLogs[deviceKey] = monitorState.streamLogs[deviceKey].slice(-500);
  }
}

function resetMonitorState() {
  monitorState.job = null;
  monitorState.targetDeviceKeys = [];
  monitorState.canaryKey = null;
  monitorState.deviceStatuses = {};
  monitorState.streamLogs = {};
  monitorState.result = null;
  monitorState.eventCount = 0;
}

function beginMonitor(job, targetDeviceKeys, canaryKey) {
  resetMonitorState();
  monitorState.job = { ...job };
  monitorState.targetDeviceKeys = [...targetDeviceKeys];
  monitorState.canaryKey = canaryKey || targetDeviceKeys[0] || null;
  monitorState.targetDeviceKeys.forEach((key) => ensureMonitorDevice(key));
  renderMonitorState();
  refreshProdWarningOverlay();
}

function combineDeviceKeys(source) {
  const ordered = [];
  const seen = new Set();
  const push = (key) => {
    if (!key || seen.has(key)) {
      return;
    }
    seen.add(key);
    ordered.push(key);
  };
  (source.targetDeviceKeys || []).forEach(push);
  Object.keys(source.deviceStatuses || {}).forEach(push);
  Object.keys(source.streamLogs || {}).forEach(push);
  Object.keys(source.result?.device_results || {}).forEach(push);
  return ordered;
}

function formatDiffHtml(diffText) {
  if (!diffText) {
    return "";
  }
  return diffText
    .split("\n")
    .map((line) => {
      if (line.startsWith("+")) {
        return `<span class="diff-add">${escapeHtml(line)}</span>`;
      }
      if (line.startsWith("-")) {
        return `<span class="diff-remove">${escapeHtml(line)}</span>`;
      }
      return escapeHtml(line);
    })
    .join("\n");
}

function buildExecutionSummaryHtml(source, eventCount) {
  const keys = combineDeviceKeys(source);
  let queue = 0;
  let running = 0;
  let complete = 0;
  let failed = 0;
  keys.forEach((key) => {
    const resultStatus = source.result?.device_results?.[key]?.status;
    const streamStatus = source.deviceStatuses?.[key];
    const status = normalizedStatus(resultStatus || streamStatus || "queued");
    if (status === "running") {
      running += 1;
    } else if (status === "completed") {
      complete += 1;
    } else if (status === "failed" || status === "cancelled") {
      failed += 1;
    } else {
      queue += 1;
    }
  });
  const status = source.job?.status || source.result?.status || "queued";
  return `
    <div><strong>${escapeHtml(source.job?.job_name || "job")} (${escapeHtml(source.job?.job_id || "-")})</strong></div>
    <div class="muted">Status:
      <span class="status-badge status-${normalizedStatus(status)}">${statusLabel(status)}</span>
      / Created: ${escapeHtml(formatTimestamp(source.job?.created_at || ""))}
      / Devices: ${keys.length}
      / Events: ${eventCount}
    </div>
    <div class="muted">Queue: ${queue} / Running: ${running} / Complete: ${complete} / Failed: ${failed}</div>
  `;
}

function buildDeviceCardsHtml(source, deviceNameMap = {}) {
  const keys = combineDeviceKeys(source);
  if (keys.length === 0) {
    return '<div class="muted">No target devices yet</div>';
  }
  return keys
    .map((key) => {
      const result = source.result?.device_results?.[key];
      const streamStatus = source.deviceStatuses?.[key];
      const status = normalizedStatus(result?.status || streamStatus || "queued");
      const attempts = result?.attempts || 0;
      const error = result?.error || "";
      const streamLines = source.streamLogs?.[key] || [];
      const fallbackResultLines = (result?.logs || []).map((line) => `[result] ${line}`);
      const mergedLines = streamLines.length > 0 ? streamLines : fallbackResultLines;
      const streamText = mergedLines.length > 0 ? mergedLines.join("\n") : "No logs yet...";
      const isCanary = source.canaryKey === key;
      const hostname = String(deviceNameMap[key] || "").trim() || hostFromDeviceKey(key);
      return `
        <div class="device-card status-${status}" id="device-card-${key.replace(":", "-")}">
          <h4>${escapeHtml(`${key} (${hostname})`)} ${isCanary ? '<span class="status-badge status-paused">CANARY</span>' : ""} <span class="status-badge status-${status}">${statusLabel(status)}</span></h4>
          <div class="meta">Attempts: ${attempts || "-"} ${error ? `/ Error: ${escapeHtml(error)}` : ""}</div>
          <div class="output-label">Command Stream</div>
          <pre class="stream-output">${escapeHtml(streamText)}</pre>
          ${result?.pre_output ? `<div class="output-label">Verify Pre</div><pre class="verify-output">${escapeHtml(result.pre_output)}</pre>` : ""}
          ${result?.apply_output ? `<div class="output-label">Apply Output</div><pre class="verify-output">${escapeHtml(result.apply_output)}</pre>` : ""}
          ${result?.post_output ? `<div class="output-label">Verify Post</div><pre class="verify-output">${escapeHtml(result.post_output)}</pre>` : ""}
          ${result?.diff ? `<div class="output-label">Pre/Post Diff</div><div class="diff-output">${formatDiffHtml(result.diff)}</div>` : ""}
          ${result?.diff_truncated ? `<div class="muted">diff truncated (original: ${result.diff_original_size} bytes)</div>` : ""}
        </div>
      `;
    })
    .join("");
}

function renderExecutionPanel(summaryEl, devicesEl, source, eventCount = 0, deviceNameMap = {}) {
  summaryEl.innerHTML = buildExecutionSummaryHtml(source, eventCount);
  devicesEl.innerHTML = buildDeviceCardsHtml(source, deviceNameMap);
}

function renderMonitorState() {
  renderExecutionPanel(
    monitorSummaryEl,
    monitorDevicesEl,
    monitorState,
    monitorState.eventCount,
    buildDeviceDisplayMap(importedDevices)
  );
}

async function handleJobSocketMessage(data) {
  appendLog(
    `${data.type} status=${data.status || "-"} device=${data.device || "-"} message=${data.message || "-"}`
  );
  if (!monitorState.job || data.job_id !== monitorState.job.job_id) {
    return;
  }
  monitorState.eventCount += 1;
  if (data.device) {
    ensureMonitorDevice(data.device);
    if (data.status) {
      monitorState.deviceStatuses[data.device] = data.status;
    }
    if (data.message) {
      pushDeviceStream(data.device, `[${data.type}] ${data.message}`);
    } else if (data.status) {
      pushDeviceStream(data.device, `[${data.type}] ${data.status}`);
    }
  } else if (data.status && monitorState.job) {
    monitorState.job.status = data.status;
  }
  renderMonitorState();
  if (data.type === "job_complete") {
    await fetchRunResultForMonitor(data.job_id);
  }
}

async function fetchRunResultForMonitor(jobId) {
  if (monitorResultLoading) {
    return;
  }
  monitorResultLoading = true;
  try {
    const [job, result] = await Promise.all([
      client().getJob(jobId),
      client().getJobResult(jobId),
    ]);
    if (!monitorState.job || monitorState.job.job_id !== jobId) {
      return;
    }
    monitorState.job = { ...job };
    monitorState.result = result;
    monitorState.targetDeviceKeys = result.target_device_keys || monitorState.targetDeviceKeys;
    Object.entries(result.device_results || {}).forEach(([deviceKey, value]) => {
      ensureMonitorDevice(deviceKey);
      monitorState.deviceStatuses[deviceKey] = value.status || monitorState.deviceStatuses[deviceKey];
    });
    renderMonitorState();
  } catch (error) {
    appendLog(`failed to fetch result for ${jobId}: ${String(error)}`);
  } finally {
    monitorResultLoading = false;
  }
}

function formatJobDetailText(job, events, result) {
  const lines = [];
  const deviceResults = result?.device_results || {};
  const successCount = Object.values(deviceResults).filter((item) => item.status === "success").length;
  const failedCount = Object.values(deviceResults).filter((item) => item.status !== "success").length;

  lines.push("=== Job Overview ===");
  lines.push(`Job ID: ${job.job_id}`);
  lines.push(`Name: ${job.job_name}`);
  lines.push(`Creator: ${job.creator}`);
  lines.push(`Status: ${job.status}`);
  lines.push(`Created: ${formatTimestamp(job.created_at)}`);
  lines.push(`Started: ${formatTimestamp(job.started_at || "")}`);
  lines.push(`Completed: ${formatTimestamp(job.completed_at || "")}`);
  lines.push("");
  lines.push("=== Summary ===");
  lines.push(`Events: ${events.length}`);
  lines.push(`Target devices: ${Object.keys(deviceResults).length}`);
  lines.push(`Success: ${successCount}`);
  lines.push(`Failed: ${failedCount}`);
  lines.push("");
  lines.push("=== Device Results ===");
  Object.entries(deviceResults).forEach(([key, value]) => {
    lines.push(`- ${key}`);
    lines.push(`  status=${value.status} attempts=${value.attempts}`);
    if (value.error_code || value.error) {
      lines.push(`  error_code=${value.error_code || "-"} error=${value.error || "-"}`);
    }
    if (value.logs && value.logs.length > 0) {
      lines.push("  logs:");
      value.logs.forEach((entry) => lines.push(`    ${entry}`));
    }
    if (value.pre_output) {
      lines.push("  pre_output:");
      String(value.pre_output).split("\n").forEach((entry) => lines.push(`    ${entry}`));
    }
    if (value.apply_output) {
      lines.push("  apply_output:");
      String(value.apply_output).split("\n").forEach((entry) => lines.push(`    ${entry}`));
    }
    if (value.post_output) {
      lines.push("  post_output:");
      String(value.post_output).split("\n").forEach((entry) => lines.push(`    ${entry}`));
    }
    if (value.diff) {
      lines.push("  diff:");
      String(value.diff).split("\n").forEach((entry) => lines.push(`    ${entry}`));
    }
  });
  if (Object.keys(deviceResults).length === 0) {
    lines.push("(result is not ready yet)");
  }
  return lines.join("\n");
}

function renderJobDetail(job, events, result) {
  detailTargetDeviceKeys = result?.target_device_keys || Object.keys(result?.device_results || {});
  detailMetaEl.textContent = `selected: ${job.job_id} (${job.status}) events=${events.length}`;
  detailDataEl.textContent = formatJobDetailText(job, events, result);
  const detailSource = {
    job,
    result,
    targetDeviceKeys: detailTargetDeviceKeys,
    canaryKey: null,
    deviceStatuses: {},
    streamLogs: {},
  };
  renderExecutionPanel(
    detailSummaryEl,
    detailDevicesEl,
    detailSource,
    events.length,
    buildDeviceDisplayMap(importedDevices)
  );
  refreshProdWarningOverlay();
}

async function loadAndRenderJob(jobId, targetPage = "detail") {
  try {
    const [detail, events, result] = await Promise.all([
      client().getJob(jobId),
      client().listJobEvents(jobId),
      client().getJobResult(jobId).catch(() => ({ job_id: jobId, status: "pending", device_results: {} })),
    ]);
    renderJobDetail(detail, events, result);
    if (monitorState.job && monitorState.job.job_id === jobId) {
      monitorState.job = { ...monitorState.job, ...detail, status: result.status || detail.status };
      monitorState.result = result;
      monitorState.targetDeviceKeys = result.target_device_keys || monitorState.targetDeviceKeys;
      Object.entries(result.device_results || {}).forEach(([deviceKey, value]) => {
        ensureMonitorDevice(deviceKey);
        monitorState.deviceStatuses[deviceKey] = value.status || monitorState.deviceStatuses[deviceKey];
      });
      renderMonitorState();
    }
    if (targetPage) {
      switchPage(targetPage);
    }
  } catch (error) {
    appendLog(String(error));
  }
}

function switchPage(pageName) {
  document.querySelectorAll(".page").forEach((el) => {
    el.classList.toggle("active", el.getAttribute("data-page") === pageName);
  });
  document.querySelectorAll(".nav-btn").forEach((el) => {
    const pressed = el.getAttribute("data-page") === pageName;
    el.setAttribute("aria-pressed", pressed ? "true" : "false");
  });
  refreshProdWarningOverlay();
}

async function refreshImportedDevices() {
  importedDevices = await client().listDevices();
  prodDeviceKeys = new Set(
    importedDevices
      .filter((device) => Boolean(device.prod))
      .map((device) => importedDeviceKey(device))
  );
  deviceCountEl.textContent = `imported devices: ${importedDevices.length}`;
  const importedModels = Array.from(
    new Set(importedDevices.map((device) => device.device_type))
  ).sort();
  const presetModels = await client().listPresetOsModels().catch(() => []);
  const allModels = Array.from(new Set([...importedModels, ...presetModels])).sort();
  populateOsModelSelect(allModels);
  renderImportedDeviceList();
  populateStatusDeviceSelect();
  refreshCanaryOptions();
  await refreshPresetOptions().catch((error) => appendLog(String(error)));
  appendLog(`loaded imported devices: ${importedDevices.length}`);
  refreshProdWarningOverlay();
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
    status.textContent = `status: ${job.status} / creator: ${job.creator}`;
    const timestamps = document.createElement("div");
    timestamps.className = "muted";
    timestamps.textContent = `created: ${formatTimestamp(job.created_at)}`;

    div.append(titleWrap, id, status, timestamps);
    div.addEventListener("click", async () => {
      selectedJobId = job.job_id;
      await loadAndRenderJob(job.job_id, "detail");
      appendLog(`history selected: ${job.job_id}`);
    });
    historyEl.append(div);
  });

  appendLog(`loaded jobs: ${jobs.length}`);
}

async function refreshActive() {
  const active = await client().getActiveJob();
  if (!active.active || !active.job) {
    activeBlockingJob = null;
    updateCreateActionState();
    activeSummaryEl.textContent = "active job: none";
    monitorSummaryEl.textContent = "No active job selected.";
    monitorDevicesEl.innerHTML = "";
    pauseBtn.disabled = true;
    resumeBtn.disabled = true;
    cancelBtn.disabled = true;
    if (monitorState.job && ["running", "queued", "paused"].includes(monitorState.job.status)) {
      fetchRunResultForMonitor(monitorState.job.job_id).catch(() => {});
    }
    refreshProdWarningOverlay();
    return;
  }

  activeSummaryEl.textContent = `active job: ${active.job.job_id} (${active.job.status})`;
  setStatus(`active:${active.job.status}`);
  activeBlockingJob = isActiveRunBlocking(active.job.status) ? active.job : null;
  updateCreateActionState();
  pauseBtn.disabled = active.job.status !== "running";
  resumeBtn.disabled = active.job.status !== "paused";
  cancelBtn.disabled = !["running", "paused", "queued"].includes(active.job.status);
  if (monitorState.job && monitorState.job.job_id === active.job.job_id) {
    monitorState.job = { ...monitorState.job, ...active.job };
    renderMonitorState();
  }
  refreshProdWarningOverlay();
}

async function refreshRuntimeModes() {
  try {
    const modes = await client().getRuntimeModes();
    setModeStatus(`mode: worker=${modes.worker_mode} / validator=${modes.validator_mode}`);
  } catch (error) {
    setModeStatus("mode: worker=- / validator=-");
    appendLog(`failed to load runtime modes: ${String(error)}`);
  }
}

function resolveRunTargets(useImported, adHocDevices) {
  if (!useImported) {
    return {
      importedDeviceKeys: [],
      adHocDevices,
      targetDevices: adHocDevices,
    };
  }
  if (importedDevices.length === 0) {
    throw new Error("imported devices are empty");
  }
  const chosen = selectedImportedDeviceKeys();
  const importedDeviceKeys =
    chosen.length > 0 ? chosen : importedDevices.map((device) => importedDeviceKey(device));
  const targetDevices = importedDeviceKeys
    .map((key) => {
      const [host, rawPort] = key.split(":");
      return { host, port: Number(rawPort || "22") };
    })
    .filter((device) => device.host && Number.isFinite(device.port));
  return {
    importedDeviceKeys,
    adHocDevices: [],
    targetDevices,
  };
}

function resolveTargetDeviceKeys(useImported, targets) {
  if (useImported) {
    return targets.importedDeviceKeys;
  }
  return targets.adHocDevices.map((device) => `${device.host}:${device.port}`);
}

function resolveEffectiveExecutionConfig(concurrencyLimit, strategy) {
  return {
    strategy,
    effectiveConcurrencyLimit: strategy === "sequential" ? 1 : concurrencyLimit,
  };
}

function collectRunInput() {
  const jobName = document.getElementById("jobName").value.trim();
  const creator = document.getElementById("creator").value.trim();
  const globalVarsText = document.getElementById("globalVars").value;
  const devices = parseDevices(document.getElementById("devices").value);
  const commands = parseCommands(document.getElementById("commands").value);
  const verifyCommands = parseCommands(verifyCommandsEl.value);
  const verifyMode = verifyModeEl.value;
  const concurrencyLimit = Number(concurrencyLimitEl.value || "5");
  const staggerDelay = Number(staggerDelayEl.value || "1.0");
  const stopOnError = stopOnErrorEl.checked;
  const useImported = useImportedEl.checked;
  const postCanaryStrategy = (postCanaryStrategyEl.value || "parallel").trim();

  if (commands.length === 0) {
    throw new Error("commands is empty");
  }
  if (!Number.isFinite(concurrencyLimit) || concurrencyLimit < 1) {
    throw new Error("concurrency_limit must be >= 1");
  }
  if (!Number.isFinite(staggerDelay) || staggerDelay < 0) {
    throw new Error("stagger_delay must be >= 0");
  }
  if (!["parallel", "sequential"].includes(postCanaryStrategy)) {
    throw new Error("postCanaryStrategy must be parallel or sequential");
  }

  const targets = resolveRunTargets(useImported, devices);
  if (!useImported && targets.adHocDevices.length === 0) {
    throw new Error("ad-hoc devices is empty");
  }
  if (targets.targetDevices.length === 0) {
    throw new Error("target devices is empty");
  }

  const canaryKey = canaryDeviceEl.value.trim();
  if (!canaryKey) {
    throw new Error("canary device is required");
  }
  if (!targets.targetDevices.some((device) => `${device.host}:${device.port}` === canaryKey)) {
    throw new Error("canary device must be included in target devices");
  }

  const [canaryHost, canaryRawPort] = canaryKey.split(":");
  const canary = { host: canaryHost, port: Number(canaryRawPort || "22") };
  const globalVars = parseGlobalVars(globalVarsText);
  const targetDeviceKeys = resolveTargetDeviceKeys(useImported, targets);
  const effectiveConfig = resolveEffectiveExecutionConfig(concurrencyLimit, postCanaryStrategy);

  return {
    jobName,
    creator,
    globalVars,
    commands,
    verifyCommands,
    verifyMode,
    concurrencyLimit,
    staggerDelay,
    stopOnError,
    useImported,
    canary,
    canaryKey,
    targets,
    targetDeviceKeys,
    postCanaryStrategy,
    effectiveConcurrencyLimit: effectiveConfig.effectiveConcurrencyLimit,
  };
}

function clearElementChildren(el) {
  el.replaceChildren();
}

function appendListItems(el, values) {
  clearElementChildren(el);
  values.forEach((value) => {
    const li = document.createElement("li");
    li.textContent = value;
    el.append(li);
  });
}

function buildReviewModel(mode, runInput) {
  const remainingCount = Math.max(0, runInput.targetDeviceKeys.length - 1);
  const strategyText =
    runInput.postCanaryStrategy === "sequential"
      ? "Canary -> Device-1 -> Device-2 -> ..."
      : `Canary -> [Device-1, Device-2, ...] (parallel up to ${runInput.effectiveConcurrencyLimit})`;
  return {
    modeText: mode === "sync" ? "Execution mode: Sync (/run)" : "Execution mode: Async (/run/async)",
    hosts: runInput.targetDeviceKeys,
    commands: runInput.commands,
    verifyCommands: runInput.verifyCommands.length > 0 ? runInput.verifyCommands : ["(none)"],
    settings: [
      `Canary: ${runInput.canaryKey}`,
      `Verify mode: ${runInput.verifyMode}`,
      `Stop on error: ${runInput.stopOnError}`,
      `Stagger delay: ${runInput.staggerDelay}s`,
      `Post-canary strategy: ${runInput.postCanaryStrategy}`,
      `Concurrency input: ${runInput.concurrencyLimit}`,
      `Effective concurrency: ${runInput.effectiveConcurrencyLimit}`,
      `Target devices: ${runInput.targetDeviceKeys.length} (remaining after canary: ${remainingCount})`,
      `Target source: ${runInput.useImported ? "imported devices" : "ad-hoc devices"}`,
    ],
    flowDiagram: strategyText,
  };
}

function setRunReviewVisible(visible) {
  runReviewPanelEl.classList.toggle("hidden", !visible);
}

function updateReviewHostListVisibility() {
  reviewTargetHostsEl.classList.toggle("hidden", reviewHostsCollapsed);
  reviewToggleHostsBtn.textContent = reviewHostsCollapsed ? "Expand" : "Collapse";
}

function renderRunReview(mode, runInput) {
  const review = buildReviewModel(mode, runInput);
  reviewModeTextEl.textContent = review.modeText;
  appendListItems(reviewTargetHostsEl, review.hosts);
  appendListItems(reviewCommandsEl, review.commands);
  appendListItems(reviewVerifyCommandsEl, review.verifyCommands);
  appendListItems(reviewSettingsEl, review.settings);
  reviewFlowDiagramEl.textContent = review.flowDiagram;
  updateReviewHostListVisibility();
  setRunReviewVisible(true);
}

function clearRunReview() {
  pendingRunReview = null;
  setRunReviewVisible(false);
}

async function executeRun(mode, runInput) {
  if (mode === "sync") {
    runSyncBusy = true;
  } else {
    runAsyncBusy = true;
  }
  switchPage("monitor");
  updateCreateActionState();
  setStatus(mode === "sync" ? "creating" : "creating-async");
  try {
    const job = await client().createJob(runInput.jobName, runInput.creator, runInput.globalVars);
    selectedJobId = job.job_id;
    beginMonitor(job, runInput.targetDeviceKeys, runInput.canaryKey);
    appendLog(`job created: ${job.job_id}`);
    openJobSocket(currentApiBase(), job.job_id);

    if (mode === "sync") {
      const result = await client().runJob(
        job.job_id,
        runInput.commands,
        runInput.targets.adHocDevices,
        runInput.useImported,
        {
          verifyCommands: runInput.verifyCommands,
          verifyMode: runInput.verifyMode,
          importedDeviceKeys: runInput.targets.importedDeviceKeys,
          canary: runInput.canary,
          concurrencyLimit: runInput.effectiveConcurrencyLimit,
          staggerDelay: runInput.staggerDelay,
          stopOnError: runInput.stopOnError,
        }
      );
      monitorState.result = result;
      monitorState.job = { ...job, status: result.status };
      monitorState.targetDeviceKeys = result.target_device_keys || monitorState.targetDeviceKeys;
      Object.entries(result.device_results || {}).forEach(([deviceKey, value]) => {
        ensureMonitorDevice(deviceKey);
        monitorState.deviceStatuses[deviceKey] = value.status;
      });
      renderMonitorState();
      appendLog(`run completed: ${result.status}`);
      Object.entries(result.device_results).forEach(([key, value]) => {
        appendLog(`${key} => status=${value.status} attempts=${value.attempts}`);
        if (value.error_code) {
          appendLog(`${key} error_code=${value.error_code}`);
        }
      });
      setStatus(result.status);
      const events = await client().listJobEvents(job.job_id).catch(() => []);
      renderJobDetail({ ...job, status: result.status }, events, result);
      await refreshJobs();
      await refreshActive();
      return;
    }

    const started = await client().runJobAsync(
      job.job_id,
      runInput.commands,
      runInput.targets.adHocDevices,
      runInput.useImported,
      {
        verifyCommands: runInput.verifyCommands,
        verifyMode: runInput.verifyMode,
        importedDeviceKeys: runInput.targets.importedDeviceKeys,
        canary: runInput.canary,
        concurrencyLimit: runInput.effectiveConcurrencyLimit,
        staggerDelay: runInput.staggerDelay,
        stopOnError: runInput.stopOnError,
      }
    );
    appendLog(`run async started: ${started.status}`);
    setStatus("running");
    await refreshJobs();
    await refreshActive();
  } catch (error) {
    setStatus("failed");
    appendLog(String(error));
  } finally {
    if (mode === "sync") {
      runSyncBusy = false;
      if (activeSocket) {
        setTimeout(() => activeSocket && activeSocket.close(), 800);
      }
    } else {
      runAsyncBusy = false;
    }
    updateCreateActionState();
  }
}

async function requestRun(mode) {
  if (activeBlockingJob) {
    appendLog(
      `Cannot create a new job while active job ${activeBlockingJob.job_id} (${activeBlockingJob.status}) is running`
    );
    switchPage("monitor");
    return;
  }
  try {
    const runInput = collectRunInput();
    if (!enableRunConfirmationEl.checked) {
      clearRunReview();
      await executeRun(mode, runInput);
      return;
    }
    pendingRunReview = { mode, runInput };
    renderRunReview(mode, runInput);
    appendLog(`run review opened (${mode})`);
    switchPage("create");
  } catch (error) {
    appendLog(String(error));
  }
}

async function runSync() {
  await requestRun("sync");
}

async function runAsync() {
  await requestRun("async");
}

runBtn.addEventListener("click", runSync);
runAsyncBtn.addEventListener("click", runAsync);
reviewExecuteBtn?.addEventListener("click", async () => {
  if (!pendingRunReview) {
    appendLog("run review is empty");
    clearRunReview();
    return;
  }
  const review = pendingRunReview;
  clearRunReview();
  await executeRun(review.mode, review.runInput);
});
reviewCancelBtn?.addEventListener("click", () => {
  appendLog("run review cancelled");
  clearRunReview();
});
reviewToggleHostsBtn?.addEventListener("click", () => {
  reviewHostsCollapsed = !reviewHostsCollapsed;
  updateReviewHostListVisibility();
});

importBtn.addEventListener("click", async () => {
  const csvInput = document.getElementById("csvInput").value;
  const importedCountBeforeImport = importedDevices.length;
  clearImportError();
  resetImportStreamLog();
  setImportInProgress(true);
  appendImportStreamLog("Import started");
  try {
    const response = await fetch(`${currentApiBase()}/api/v2/devices/import/progress`, {
      method: "POST",
      headers: { "Content-Type": "text/plain" },
      body: csvInput,
    });
    if (!response.ok || !response.body) {
      throw new Error(`POST /api/v2/devices/import/progress failed: ${response.status}`);
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let importedCount = importedCountBeforeImport;
    let successfulProgressCount = 0;
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.trim()) {
          continue;
        }
        const event = JSON.parse(line);
        if (event.type === "start") {
          const total = Number(event.total || 0);
          importProgressEl.max = total > 0 ? total : 1;
          importProgressEl.value = 0;
          importProgressTextEl.textContent = `Validating devices... 0/${total}`;
          appendImportStreamLog(`Validation started (total=${total})`);
        } else if (event.type === "progress") {
          const processed = Number(event.processed || 0);
          const total = Number(event.total || 0);
          const host = String(event.host || "?");
          const port = Number(event.port || 0);
          const result = event.connection_ok === true ? "OK" : "NG";
          importProgressEl.max = total > 0 ? total : 1;
          importProgressEl.value = processed;
          importProgressTextEl.textContent = `Validating devices... ${processed}/${total}`;
          appendImportStreamLog(`${host}:${port || "?"} ${result} (${processed}/${total})`);
          if (event.connection_ok === true) {
            successfulProgressCount += 1;
          }
          importedCount = successfulProgressCount;
          deviceCountEl.textContent = `imported devices: ${importedCount}`;
        } else if (event.type === "complete") {
          importedCount = (event.devices || []).length;
          const total = Number(event.total || importedCount);
          importProgressEl.max = total > 0 ? total : 1;
          importProgressEl.value = total;
          importProgressTextEl.textContent = `Validating devices... ${total}/${total}`;
          deviceCountEl.textContent = `imported devices: ${importedCount}`;
          appendImportStreamLog(`Import completed (valid=${importedCount}, total=${total})`);
        } else if (event.type === "error") {
          const message = formatImportErrorDetail(event.detail);
          appendImportStreamLog(`Import error: ${message}`);
          throw new Error(message);
        }
      }
    }
    appendLog(`import success: valid=${importedCount}`);
    await refreshImportedDevices();
  } catch (error) {
    const message = String(error);
    deviceCountEl.textContent = `imported devices: ${importedCountBeforeImport}`;
    showImportError(message);
    appendImportStreamLog(`Import failed: ${message}`);
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
  refreshCanaryOptions();
  refreshProdWarningOverlay();
});

enablePresetModeEl.addEventListener("change", async () => {
  presetPanelEl.classList.toggle("hidden", !enablePresetModeEl.checked);
  if (!enablePresetModeEl.checked) {
    osModelSelectEl.value = "";
    presetSelectEl.value = "";
    await refreshPresetOptions().catch((error) => appendLog(String(error)));
    renderImportedDeviceList();
    refreshProdWarningOverlay();
    return;
  }
  await refreshPresetOptions().catch((error) => appendLog(String(error)));
  renderImportedDeviceList();
  refreshProdWarningOverlay();
});

osModelSelectEl.addEventListener("change", () => {
  renderImportedDeviceList();
  refreshCanaryOptions();
  refreshPresetOptions().catch((error) => appendLog(String(error)));
  refreshProdWarningOverlay();
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
  refreshCanaryOptions();
  refreshProdWarningOverlay();
});

clearImportedSelectionBtn.addEventListener("click", () => {
  clearImportedSelection();
  refreshCanaryOptions();
  refreshProdWarningOverlay();
});

importedDeviceListEl.addEventListener("change", () => {
  refreshCanaryOptions();
  refreshProdWarningOverlay();
});

document.getElementById("devices").addEventListener("input", () => {
  if (!useImportedEl.checked) {
    refreshCanaryOptions();
  }
  refreshProdWarningOverlay();
});

statusRunBtn.addEventListener("click", async () => {
  const selected = statusDeviceSelectEl.value.trim();
  const commands = statusCommandsEl.value.trim();
  if (!selected) {
    statusOutputEl.textContent = "Please select a target device.";
    return;
  }
  if (!commands) {
    statusOutputEl.textContent = "Please enter at least one command.";
    return;
  }
  const [host, rawPort] = selected.split(":");
  const port = Number(rawPort || "22");
  statusRunBtn.disabled = true;
  statusOutputEl.textContent = "Running...";
  try {
    const result = await client().execStatusCommands(host, port, commands);
    statusOutputEl.textContent = result.output || "(empty output)";
    appendLog(`status command succeeded for ${host}:${port}`);
  } catch (error) {
    const text = String(error);
    statusOutputEl.textContent = `Error: ${text}`;
    appendLog(text);
  } finally {
    statusRunBtn.disabled = false;
  }
});

viewActiveJobBtn?.addEventListener("click", async () => {
  switchPage("monitor");
  await refreshActive().catch((error) => appendLog(String(error)));
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
  btn.addEventListener("click", async () => {
    const page = btn.getAttribute("data-page") || "import";
    switchPage(page);
    if (page === "status-command") {
      refreshImportedDevices().catch((error) => appendLog(String(error)));
    } else if (page === "monitor") {
      await refreshActive().catch((error) => appendLog(String(error)));
    } else if (page === "detail" && selectedJobId) {
      await loadAndRenderJob(selectedJobId, null);
    }
  });
});

document.getElementById("apiBase").addEventListener("change", () => {
  refreshRuntimeModes().catch((error) => appendLog(String(error)));
});

setInterval(() => {
  refreshActive().catch((error) => appendLog(String(error)));
}, 4000);

presetPanelEl.classList.add("hidden");
applyApiBaseVisibility();
updateCreateActionState();
renderMonitorState();
refreshProdWarningOverlay();
refreshImportedDevices().catch(() => {});
refreshJobs().catch(() => {});
refreshActive().catch(() => {});
refreshRuntimeModes().catch(() => {});
