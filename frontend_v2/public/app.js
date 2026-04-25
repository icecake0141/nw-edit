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
const localeSelectEl = document.getElementById("localeSelect");
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
const enablePresetModeEl = document.getElementById("enablePresetMode");
const presetPanelEl = document.getElementById("presetPanel");
const osModelSelectEl = document.getElementById("osModelSelect");
const presetSelectEl = document.getElementById("presetSelect");
const presetNameEl = document.getElementById("presetName");
const presetSaveNewBtn = document.getElementById("presetSaveNewBtn");
const presetUpdateBtn = document.getElementById("presetUpdateBtn");
const runBtn = document.getElementById("runBtn");
const pauseBtn = document.getElementById("pauseBtn");
const resumeBtn = document.getElementById("resumeBtn");
const cancelBtn = document.getElementById("cancelBtn");
const clearBtn = document.getElementById("clearBtn");
const importBtn = document.getElementById("importBtn");
const resetAppStateBtn = document.getElementById("resetAppStateBtn");
const refreshDevicesBtn = document.getElementById("refreshDevicesBtn");
const listJobsBtn = document.getElementById("listJobsBtn");
const refreshActiveBtn = document.getElementById("refreshActiveBtn");
const selectAllImportedBtn = document.getElementById("selectAllImportedBtn");
const clearImportedSelectionBtn = document.getElementById("clearImportedSelectionBtn");
const verifyCommandsEl = document.getElementById("verifyCommands");
const verifyModeHintEl = document.getElementById("verifyModeHint");
const verifyModeEls = Array.from(
  document.querySelectorAll('input[name="verifyMode"]')
);
const canaryDeviceEl = document.getElementById("canaryDevice");
const concurrencyLimitEl = document.getElementById("concurrencyLimit");
const staggerDelayEl = document.getElementById("staggerDelay");
const stopOnErrorEl = document.getElementById("stopOnError");
const enableRunConfirmationEl = document.getElementById("enableRunConfirmation");
const postCanaryStrategyEls = Array.from(
  document.querySelectorAll('input[name="postCanaryStrategy"]')
);
const statusDeviceSelectEl = document.getElementById("statusDeviceSelect");
const statusCommandsEl = document.getElementById("statusCommands");
const statusRunBtn = document.getElementById("statusRunBtn");
const statusOutputEl = document.getElementById("statusOutput");
const activeJobBannerEl = document.getElementById("activeJobBanner");
const activeJobBannerTextEl = document.getElementById("activeJobBannerText");
const viewActiveJobBtn = document.getElementById("viewActiveJobBtn");
const prodWarningOverlayEl = document.getElementById("prodWarningOverlay");
const prodWarningLabelsEl = document.getElementById("prodWarningLabels");
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
const helpContentEl = document.getElementById("helpContent");

const DEFAULT_LOCALE = "en";
const LOCALE_STORAGE_KEY = "nw-edit.locale";
const SUPPORTED_LOCALES = ["en"];
let currentLocale = resolveInitialLocale();

const translations = {
  en: {
    head: {
      title: "nw-edit v2 operations console",
    },
    locale: {
      label: "Language",
      option: {
        en: "English",
      },
    },
    form: {
      apiBase: "API Base",
      creator: "Creator",
      jobName: "Job Name",
      globalVars: "Global Vars (JSON)",
    },
    nav: {
      ariaLabel: "v2 pages",
      import: "Import",
      create: "Create",
      monitor: "Monitor",
      history: "History",
      statusCommand: "Status Command",
      detail: "Detail",
      help: "Help",
      title: {
        import: "Open the import page to register devices from CSV.",
        create: "Open the create page to define commands and start a job.",
        monitor: "Open the monitor page to control and inspect the active job.",
        history: "Open the history page to browse previously created jobs.",
        statusCommand: "Open the status command page for read-only checks on imported devices.",
        detail: "Open the detail page to inspect one selected job result.",
        help: "Open command variable usage examples for global and host vars.",
      },
    },
    labels: {
      prodWarning: "Production Environment",
      importedDevices: "imported devices: {count}",
      importedTargetCandidates: "Imported target candidates: {count}",
      selectDevice: "(select device)",
      selectCanary: "(select canary)",
      notSelected: "(not selected)",
      noJobsYet: "no jobs yet",
      noTargetDevicesYet: "No target devices yet",
      noActiveJobSelected: "No active job selected.",
      noActiveRunSelected: "No active run selected",
      noJobSelected: "No job selected",
      selectJobFromHistory: "Select a job from history",
      noOutputYet: "No output yet",
      emptyOutput: "(empty output)",
      none: "(none)",
    },
    status: {
      idle: "idle",
      creatingAsync: "creating-async",
      running: "running",
      paused: "paused",
      cancelled: "cancelled",
      failed: "failed",
      inputError: "input-error: {message}",
      active: "active:{status}",
      mode: "mode: worker={worker} / validator={validator}",
      modeUnknown: "mode: worker=- / validator=-",
      runningLabel: "Running",
      pausedLabel: "Paused",
      failedLabel: "Failed",
      cancelledLabel: "Cancelled",
      completedLabel: "Complete",
      queuedLabel: "Queue",
      activeNone: "active job: none",
      activeJob: "active job: {jobId} ({status})",
      selectedJob: "selected: {jobId} ({status}) events={events}",
    },
    messages: {
      verifyChoose: "Choose where verify commands run after the canary step.",
      verifyIgnored: "No verify commands configured. This setting will be ignored.",
      validatingDevices: "Validating devices... {processed}/{total}",
      csvImportFailed: "CSV import failed",
      globalVarsParseError: "global vars JSON parse error: {error}",
      globalVarsObject: "global vars must be a JSON object",
      presetModeDisabled: "Preset Mode is disabled",
      osModelRequired: "os_model is required",
      presetNameRequired: "preset name is required",
      commandsEmpty: "commands is empty",
      presetSaved: "preset saved: {name} ({osModel})",
      presetUpdated: "preset updated: {name} ({osModel})",
      presetSelectionRequired: "preset selection is required for update",
      websocketError: "websocket error",
      websocketClosed: "websocket closed for {jobId}",
      failedFetchResult: "failed to fetch result for {jobId}: {error}",
      loadedImportedDevices: "loaded imported devices: {count}",
      loadedJobs: "loaded jobs: {count}",
      historySelected: "history selected: {jobId}",
      importedDevicesEmpty: "imported devices are empty",
      selectAtLeastOneImportedDevice: "select at least one imported device",
      importedTargetDevicesEmpty: "imported target devices is empty",
      concurrencyLimitInvalid: "concurrency_limit must be >= 1",
      staggerDelayInvalid: "stagger_delay must be >= 0",
      postCanaryStrategyInvalid: "postCanaryStrategy must be parallel or sequential",
      canaryRequired: "canary device is required",
      canaryIncluded: "canary device must be included in target devices",
      executionModeAsync: "Execution mode: Async (/run/async)",
      canaryFlowSequential: "Canary -> Device-1 -> Device-2 -> ...",
      canaryFlowParallel: "Canary -> [Device-1, Device-2, ...] (parallel up to {limit})",
      settingCanary: "Canary: {value}",
      settingVerify: "Verify: {value}",
      settingStopOnError: "Stop on error: {value}",
      settingStaggerDelay: "Stagger delay: {value}s",
      settingPostCanary: "Post-canary strategy: {value}",
      settingConcurrencyInput: "Concurrency input: {value}",
      settingConcurrencyDisabled: "disabled (sequential mode)",
      settingEffectiveConcurrency: "Effective concurrency: {value}",
      settingTargetDevices: "Target devices: {count} (remaining after canary: {remaining})",
      settingTargetSource: "Target source: imported devices",
      runReviewOpened: "run review opened (async)",
      runReviewEmpty: "run review is empty",
      runReviewCancelled: "run review cancelled",
      cannotCreateWhileActive: "Cannot create a new job while active job {jobId} ({status}) is running",
      importStarted: "Import started",
      validationStarted: "Validation started (total={total})",
      progressOk: "{host}:{port} OK ({processed}/{total})",
      progressNg: "{host}:{port} NG ({processed}/{total})",
      importCompleted: "Import completed (valid={valid}, total={total})",
      importError: "Import error: {message}",
      importFailed: "Import failed: {message}",
      importSuccess: "import success: valid={count}",
      presetApplied: "preset applied: {name} ({osModel})",
      selectTargetDevice: "Please select a target device.",
      enterCommand: "Please enter at least one command.",
      runningEllipsis: "Running...",
      errorPrefix: "Error: {error}",
      statusCommandSucceeded: "status command succeeded for {host}:{port}",
      pausedJob: "paused {jobId}",
      resumedJob: "resumed {jobId}",
      cancelledJob: "cancelled {jobId}",
      selectedJobEvents: "selected job events: {count}",
      noActiveJob: "No active job",
      jobCreated: "job created: {jobId}",
      runAsyncStarted: "run async started: {status}",
      helpHtml: `<h3>Command Variables Help</h3>
        <p>Variables let you reuse command templates across devices. Use placeholders like <code>{{hostname}}</code> in command lines, then provide values from <code>global_vars</code> or CSV <code>host_vars</code>.</p>
        <h3>1) Placeholder Format</h3>
        <p>Use double braces in commands:</p>
        <pre>configure terminal
hostname {{hostname}}
clock timezone JST {{tz_offset}}</pre>
        <h3>2) Global Vars (job-level JSON)</h3>
        <p>Set in the top input field: <strong>Global Vars (JSON)</strong>.</p>
        <pre>{
  "hostname_prefix": "edge",
  "tz_offset": "9"
}</pre>
        <p>Equivalent API payload:</p>
        <pre>{
  "job_name": "nightly rollout",
  "creator": "local",
  "global_vars": {
    "hostname_prefix": "edge",
    "tz_offset": "9"
  }
}</pre>
        <h3>3) Host Vars (per-device CSV)</h3>
        <p>Use CSV column <code>host_vars</code> as a JSON object string:</p>
        <pre>host,port,device_type,username,password,name,verify_cmds,host_vars,prod
10.0.0.1,22,cisco_ios,admin,pass,edge-1,show run,"{""hostname"":""edge-1"",""tz_offset"":""9""}",true
10.0.0.2,22,cisco_ios,admin,pass,edge-2,show run,"{""hostname"":""edge-2""}",false</pre>
        <h3>4) Resolution Priority</h3>
        <p>If the same key exists in both places, device-level CSV value wins: <code>host_vars &gt; global_vars</code>.</p>
        <h3>5) Missing Variable Behavior</h3>
        <p>If any placeholder has no value, preflight fails with <code>HTTP 400</code>. Device commands are not executed.</p>
        <h3>6) Common Mistakes and Fixes</h3>
        <pre>- Invalid JSON in Global Vars:
  wrong: {"timezone":"Asia/Tokyo",}
  fix:   {"timezone":"Asia/Tokyo"}

- Global Vars must be an object:
  wrong: ["x", "y"]
  fix:   {"x":"1","y":"2"}

- CSV host_vars quoting:
  wrong: {"hostname":"edge-1"}   (not CSV-escaped)
  fix:   "{""hostname"":""edge-1""}"</pre>
        <h3>7) End-to-End Mini Example</h3>
        <p>Inputs:</p>
        <pre>global_vars:
{"tz_offset":"9","ntp_server":"192.0.2.10"}

command:
clock timezone JST {{tz_offset}}
ntp server {{ntp_server}}
hostname {{hostname}}

host_vars for 10.0.0.1:
{"hostname":"edge-1","ntp_server":"192.0.2.20"}</pre>
        <p>Resolved commands for 10.0.0.1:</p>
        <pre>clock timezone JST 9
ntp server 192.0.2.20
hostname edge-1</pre>
        <h3>8) Production Host Flag</h3>
        <p>Optional CSV column <code>prod</code> marks production hosts. <code>true</code> enables production warning UI in Create/Monitor/Detail pages when selected targets include that host.</p>
        <pre>host,port,device_type,username,password,name,verify_cmds,host_vars,prod
10.0.0.10,22,cisco_ios,admin,pass,core-prod,show run,"{""hostname"":""core-prod""}",true
10.0.0.20,22,cisco_ios,admin,pass,edge-dev,show run,"{""hostname"":""edge-dev""}",false</pre>`,
    },
  },
};

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
let runBusy = false;
let presetActionBusy = false;
let resetAppStateBusy = false;
/** @type {import("./api-client.js").JobDetail|null} */
let activeBlockingJob = null;
let reviewHostsCollapsed = false;
/** @type {{runInput: any}|null} */
let pendingRunReview = null;
/** @type {import("./api-client.js").JobSummary[]} */
let historyJobs = [];
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

function resolveInitialLocale() {
  const stored = window.localStorage.getItem(LOCALE_STORAGE_KEY);
  return SUPPORTED_LOCALES.includes(stored || "") ? stored : DEFAULT_LOCALE;
}

function translationValue(locale, key) {
  return key.split(".").reduce((value, part) => value?.[part], translations[locale]);
}

function interpolate(template, params = {}) {
  return String(template).replace(/\{(\w+)\}/g, (_, key) => String(params[key] ?? `{${key}}`));
}

function t(key, params) {
  const template =
    translationValue(currentLocale, key) ??
    translationValue(DEFAULT_LOCALE, key) ??
    key;
  return typeof template === "string" ? interpolate(template, params) : String(template);
}

function applyTranslations() {
  document.documentElement.lang = currentLocale;
  document.querySelectorAll("[data-i18n-text]").forEach((el) => {
    el.textContent = t(el.getAttribute("data-i18n-text") || "");
  });
  document.querySelectorAll("[data-i18n-title]").forEach((el) => {
    el.setAttribute("title", t(el.getAttribute("data-i18n-title") || ""));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.setAttribute("placeholder", t(el.getAttribute("data-i18n-placeholder") || ""));
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
    el.setAttribute("aria-label", t(el.getAttribute("data-i18n-aria-label") || ""));
  });
  document.title = t("head.title");
  if (localeSelectEl) {
    localeSelectEl.value = currentLocale;
  }
  renderHelpContent();
  renderProdWarningLabels();
}

function setLocale(locale) {
  currentLocale = SUPPORTED_LOCALES.includes(locale) ? locale : DEFAULT_LOCALE;
  window.localStorage.setItem(LOCALE_STORAGE_KEY, currentLocale);
  applyTranslations();
  rerenderLocalizedState();
}

function renderProdWarningLabels() {
  if (!prodWarningLabelsEl) {
    return;
  }
  const positions = [
    ["2%", "3%"], ["5%", "38%"], ["8%", "68%"], ["12%", "14%"], ["15%", "49%"],
    ["18%", "76%"], ["22%", "6%"], ["25%", "33%"], ["28%", "61%"], ["31%", "83%"],
    ["35%", "4%"], ["38%", "42%"], ["41%", "71%"], ["45%", "18%"], ["48%", "51%"],
    ["51%", "79%"], ["55%", "9%"], ["58%", "36%"], ["61%", "63%"], ["64%", "84%"],
    ["68%", "5%"], ["71%", "39%"], ["74%", "69%"], ["78%", "13%"], ["81%", "47%"],
    ["84%", "75%"], ["88%", "7%"], ["91%", "34%"], ["94%", "59%"], ["97%", "80%"],
  ];
  prodWarningLabelsEl.replaceChildren();
  positions.forEach(([top, left]) => {
    const span = document.createElement("span");
    span.style.top = top;
    span.style.left = left;
    span.textContent = t("labels.prodWarning");
    prodWarningLabelsEl.append(span);
  });
}

function renderHelpContent() {
  if (helpContentEl) {
    helpContentEl.innerHTML = t("messages.helpHtml");
  }
}

function rerenderLocalizedState() {
  setStatus(statusEl.dataset.statusKey || "idle", statusEl.dataset.statusParams ? JSON.parse(statusEl.dataset.statusParams) : undefined);
  if (modeStatusEl?.dataset.statusKey) {
    setModeStatus(modeStatusEl.dataset.statusKey, modeStatusEl.dataset.statusParams ? JSON.parse(modeStatusEl.dataset.statusParams) : undefined);
  }
  updateVerifyModeControls();
  renderImportedDeviceList();
  populateStatusDeviceSelect();
  refreshCanaryOptions();
  renderJobsList();
  renderMonitorState();
  renderReviewPanelIfVisible();
  refreshActiveSummaryTexts();
}

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

function setStatus(keyOrText, params) {
  const translated = keyOrText.includes(".") ? t(keyOrText, params) : keyOrText;
  statusEl.textContent = translated;
  statusEl.dataset.statusKey = keyOrText;
  statusEl.dataset.statusParams = params ? JSON.stringify(params) : "";
}

function setModeStatus(keyOrText, params) {
  if (modeStatusEl) {
    const translated = keyOrText.includes(".") ? t(keyOrText, params) : keyOrText;
    modeStatusEl.textContent = translated;
    modeStatusEl.dataset.statusKey = keyOrText;
    modeStatusEl.dataset.statusParams = params ? JSON.stringify(params) : "";
  }
}

function appendLog(message) {
  const line = `[${new Date().toLocaleTimeString(currentLocale)}] ${message}`;
  logEl.textContent += `${line}\n`;
  logEl.scrollTop = logEl.scrollHeight;
}

function appendImportStreamLog(message) {
  if (!importStreamLogEl) {
    return;
  }
  const line = `[${new Date().toLocaleTimeString(currentLocale)}] ${message}`;
  importStreamLogEl.textContent += `${line}\n`;
  importStreamLogEl.scrollTop = importStreamLogEl.scrollHeight;
}

function resetImportStreamLog() {
  if (!importStreamLogEl) {
    return;
  }
  importStreamLogEl.textContent = "";
}

function closeActiveSocket() {
  if (!activeSocket) {
    return;
  }
  activeSocket.close();
  activeSocket = null;
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
  runBtn.disabled = blocked || runBusy;
  if (resetAppStateBtn) {
    resetAppStateBtn.disabled = Boolean(runBusy || resetAppStateBusy);
  }
  setPresetActionState();
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

function selectedVerifyMode() {
  const selected = verifyModeEls.find((el) => el.checked);
  return selected ? selected.value : "all";
}

function describeVerifyMode(mode) {
  switch (mode) {
    case "canary":
      return "Canary device only";
    case "none":
      return "Skip verify commands";
    case "all":
    default:
      return "Canary first, then all devices";
  }
}

function describeVerifyPlan(verifyMode, verifyCommands) {
  if (!verifyCommands || verifyCommands.length === 0) {
    return "Skip verify commands";
  }
  return describeVerifyMode(verifyMode);
}

function updateVerifyModeControls() {
  const hasVerifyCommands = parseCommands(verifyCommandsEl.value).length > 0;
  verifyModeEls.forEach((el) => {
    el.disabled = !hasVerifyCommands;
  });
  if (verifyModeHintEl) {
    verifyModeHintEl.textContent = hasVerifyCommands
      ? t("messages.verifyChoose")
      : t("messages.verifyIgnored");
  }
}

function setImportInProgress(inProgress) {
  importBtn.disabled = inProgress;
  if (resetAppStateBtn) {
    resetAppStateBtn.disabled = Boolean(inProgress || runBusy || resetAppStateBusy);
  }
  setImportStreamVisible(inProgress);
  if (inProgress) {
    importProgressEl.classList.remove("hidden");
    importProgressTextEl.classList.remove("hidden");
    importProgressTextEl.textContent = t("messages.validatingDevices", { processed: 0, total: 0 });
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
    return t("messages.csvImportFailed");
  }
  if (typeof detail === "string") {
    return detail;
  }
  if (detail.failed_rows && Array.isArray(detail.failed_rows)) {
    const lines = detail.failed_rows.map(
      (item) => `- row ${item.row_number || "?"}: ${item.error}`
    );
    return `${detail.message || t("messages.csvImportFailed")} (${detail.failed_rows.length} rows)\n${lines.join("\n")}`;
  }
  return JSON.stringify(detail);
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
    throw new Error(t("messages.globalVarsParseError", { error: String(error) }));
  }
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error(t("messages.globalVarsObject"));
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
  return selectedImportedDeviceKeys();
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
  importedDeviceHintEl.textContent = t("labels.importedTargetCandidates", { count: candidates.length });
  refreshProdWarningOverlay();
}

function populateStatusDeviceSelect() {
  if (!statusDeviceSelectEl) {
    return;
  }
  statusDeviceSelectEl.innerHTML = `<option value="">${t("labels.selectDevice")}</option>`;
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
  const selectedKeys = selectedImportedDeviceKeys();
  const uniqueKeys = Array.from(new Set(selectedKeys));
  const candidates = uniqueKeys
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

  canaryDeviceEl.innerHTML = `<option value="">${t("labels.selectCanary")}</option>`;
  candidates.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.key;
    option.textContent = canaryOptionLabel(item);
    canaryDeviceEl.append(option);
  });
  if (previous && candidates.some((item) => item.key === previous)) {
    canaryDeviceEl.value = previous;
    return;
  }
  if (candidates.length > 0) {
    canaryDeviceEl.value = candidates[0].key;
  }
}

function populateOsModelSelect(models) {
  const previous = selectedOsModel();
  osModelSelectEl.innerHTML = `<option value="">${t("labels.notSelected")}</option>`;
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
  const preferredPresetId = presetSelectEl.value;
  if (!enablePresetModeEl.checked) {
    currentPresets = [];
    presetSelectEl.innerHTML = `<option value="">${t("labels.notSelected")}</option>`;
    setPresetActionState();
    return;
  }
  const model = selectedOsModel();
  presetSelectEl.innerHTML = `<option value="">${t("labels.notSelected")}</option>`;
  if (!model) {
    currentPresets = [];
    setPresetActionState();
    return;
  }
  currentPresets = await client().listPresets(model);
  currentPresets.forEach((preset) => {
    const option = document.createElement("option");
    option.value = preset.preset_id;
    option.textContent = preset.name;
    presetSelectEl.append(option);
  });
  if (preferredPresetId && currentPresets.some((preset) => preset.preset_id === preferredPresetId)) {
    presetSelectEl.value = preferredPresetId;
  }
  setPresetActionState();
}

function setPresetActionState() {
  if (!presetSaveNewBtn || !presetUpdateBtn || !presetNameEl) {
    return;
  }
  const modeEnabled = enablePresetModeEl.checked;
  const blocked = Boolean(activeBlockingJob) || presetActionBusy;
  presetNameEl.disabled = !modeEnabled || blocked;
  presetSaveNewBtn.disabled = !modeEnabled || blocked;
  presetUpdateBtn.disabled =
    !modeEnabled || blocked || !presetSelectEl.value || currentPresets.length === 0;
}

function buildPresetPayloadFromForm() {
  const osModel = selectedOsModel();
  if (!enablePresetModeEl.checked) {
    throw new Error(t("messages.presetModeDisabled"));
  }
  if (!osModel) {
    throw new Error(t("messages.osModelRequired"));
  }
  const name = presetNameEl.value.trim();
  if (!name) {
    throw new Error(t("messages.presetNameRequired"));
  }
  const commands = parseCommands(document.getElementById("commands").value);
  if (commands.length === 0) {
    throw new Error(t("messages.commandsEmpty"));
  }
  const verifyCommands = parseCommands(verifyCommandsEl.value);
  return {
    name,
    os_model: osModel,
    commands,
    verify_commands: verifyCommands,
  };
}

async function savePresetNew() {
  let payload;
  try {
    payload = buildPresetPayloadFromForm();
  } catch (error) {
    appendLog(String(error));
    return;
  }

  presetActionBusy = true;
  setPresetActionState();
  try {
    const created = await client().createPreset(payload);
    await refreshPresetOptions();
    if (currentPresets.some((preset) => preset.preset_id === created.preset_id)) {
      presetSelectEl.value = created.preset_id;
    }
    setPresetActionState();
    appendLog(t("messages.presetSaved", { name: created.name, osModel: created.os_model }));
  } catch (error) {
    appendLog(String(error));
  } finally {
    presetActionBusy = false;
    setPresetActionState();
  }
}

async function updateSelectedPreset() {
  const presetId = presetSelectEl.value.trim();
  if (!presetId) {
    appendLog(t("messages.presetSelectionRequired"));
    return;
  }

  let payload;
  try {
    payload = buildPresetPayloadFromForm();
  } catch (error) {
    appendLog(String(error));
    return;
  }

  presetActionBusy = true;
  setPresetActionState();
  try {
    const updated = await client().updatePreset(presetId, payload);
    await refreshPresetOptions();
    if (currentPresets.some((preset) => preset.preset_id === updated.preset_id)) {
      presetSelectEl.value = updated.preset_id;
    }
    setPresetActionState();
    appendLog(t("messages.presetUpdated", { name: updated.name, osModel: updated.os_model }));
  } catch (error) {
    appendLog(String(error));
  } finally {
    presetActionBusy = false;
    setPresetActionState();
  }
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
  activeSocket.onerror = () => appendLog(t("messages.websocketError"));
  activeSocket.onclose = () => appendLog(t("messages.websocketClosed", { jobId }));
}

function formatTimestamp(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(currentLocale);
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
      return t("status.runningLabel");
    case "paused":
      return t("status.pausedLabel");
    case "failed":
      return t("status.failedLabel");
    case "cancelled":
      return t("status.cancelledLabel");
    case "completed":
      return t("status.completedLabel");
    default:
      return t("status.queuedLabel");
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

function resetDetailState() {
  detailTargetDeviceKeys = [];
  detailMetaEl.textContent = "No job selected";
  detailSummaryEl.textContent = "Select a job from history";
  detailDevicesEl.innerHTML = "";
  detailDataEl.textContent = "";
}

function resetHistoryState() {
  historyEl.replaceChildren();
  const div = document.createElement("div");
  div.className = "history-item";
  div.textContent = "no jobs yet";
  historyEl.append(div);
}

function resetStatusCommandState() {
  if (statusDeviceSelectEl) {
    statusDeviceSelectEl.innerHTML = '<option value="">(select device)</option>';
  }
  if (statusCommandsEl) {
    statusCommandsEl.value = statusCommandsEl.defaultValue;
  }
  if (statusOutputEl) {
    statusOutputEl.textContent = statusOutputEl.defaultValue || "No output yet";
  }
}

function resetCreateFormState() {
  const jobNameEl = document.getElementById("jobName");
  const creatorEl = document.getElementById("creator");
  const globalVarsEl = document.getElementById("globalVars");
  const commandsEl = document.getElementById("commands");
  jobNameEl.value = jobNameEl.defaultValue;
  creatorEl.value = creatorEl.defaultValue;
  globalVarsEl.value = globalVarsEl.defaultValue;
  commandsEl.value = commandsEl.defaultValue;
  verifyCommandsEl.value = verifyCommandsEl.defaultValue;
  verifyModeEl.value = verifyModeEl.defaultValue;
  concurrencyLimitEl.value = concurrencyLimitEl.defaultValue;
  staggerDelayEl.value = staggerDelayEl.defaultValue;
  stopOnErrorEl.checked = stopOnErrorEl.defaultChecked;
  enableRunConfirmationEl.checked = enableRunConfirmationEl.defaultChecked;
  enablePresetModeEl.checked = enablePresetModeEl.defaultChecked;
  presetPanelEl.classList.toggle("hidden", !enablePresetModeEl.checked);
  osModelSelectEl.innerHTML = '<option value="">(not selected)</option>';
  presetSelectEl.innerHTML = '<option value="">(not selected)</option>';
  presetNameEl.value = presetNameEl.defaultValue;
  canaryDeviceEl.innerHTML = '<option value="">(select canary)</option>';
  postCanaryStrategyEls.forEach((el) => {
    el.checked = el.defaultChecked;
  });
  reviewHostsCollapsed = false;
  clearRunReview();
  updateReviewHostListVisibility();
  updatePostCanaryControls();
  setPresetActionState();
}

function resetImportSectionState() {
  const csvInputEl = document.getElementById("csvInput");
  csvInputEl.value = csvInputEl.defaultValue;
  clearImportError();
  resetImportStreamLog();
  setImportInProgress(false);
  deviceCountEl.textContent = "imported devices: 0";
}

function resetFrontendAppState() {
  closeActiveSocket();
  importedDevices = [];
  currentPresets = [];
  prodDeviceKeys = new Set();
  selectedJobId = null;
  activeBlockingJob = null;
  pendingRunReview = null;
  resetMonitorState();
  resetDetailState();
  resetHistoryState();
  resetStatusCommandState();
  resetImportSectionState();
  resetCreateFormState();
  logEl.textContent = "";
  activeSummaryEl.textContent = "active job: none";
  monitorSummaryEl.textContent = "No active run selected";
  monitorDevicesEl.innerHTML = "";
  pauseBtn.disabled = true;
  resumeBtn.disabled = true;
  cancelBtn.disabled = true;
  setStatus("ready");
  renderImportedDeviceList();
  populateStatusDeviceSelect();
  refreshCanaryOptions();
  refreshProdWarningOverlay();
  updateCreateActionState();
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
    return `<div class="muted">${escapeHtml(t("labels.noTargetDevicesYet"))}</div>`;
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
  if (!monitorState.job) {
    monitorSummaryEl.textContent = t("labels.noActiveRunSelected");
    monitorDevicesEl.innerHTML = "";
    return;
  }
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
    appendLog(t("messages.failedFetchResult", { jobId, error: String(error) }));
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
  detailMetaEl.textContent = t("status.selectedJob", {
    jobId: job.job_id,
    status: job.status,
    events: events.length,
  });
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

async function refreshImportedDevices(options = {}) {
  const { log = true } = options;
  importedDevices = await client().listDevices();
  prodDeviceKeys = new Set(
    importedDevices
      .filter((device) => Boolean(device.prod))
      .map((device) => importedDeviceKey(device))
  );
  deviceCountEl.textContent = t("labels.importedDevices", { count: importedDevices.length });
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
  if (log) {
    appendLog(t("messages.loadedImportedDevices", { count: importedDevices.length }));
  }
  refreshProdWarningOverlay();
}

function renderJobsList() {
  historyEl.replaceChildren();

  if (historyJobs.length === 0) {
    const div = document.createElement("div");
    div.className = "history-item";
    div.textContent = t("labels.noJobsYet");
    historyEl.append(div);
    return;
  }

  historyJobs.forEach((job) => {
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
      appendLog(t("messages.historySelected", { jobId: job.job_id }));
    });
    historyEl.append(div);
  });
}

async function refreshJobs() {
  historyJobs = await client().listJobs();
  renderJobsList();
  appendLog(t("messages.loadedJobs", { count: historyJobs.length }));
}

function refreshActiveSummaryTexts() {
  if (!monitorState.job && !activeBlockingJob) {
    activeSummaryEl.textContent = t("status.activeNone");
    if (!monitorDevicesEl.innerHTML) {
      monitorSummaryEl.textContent = t("labels.noActiveJobSelected");
    }
  }
  if (!selectedJobId && detailMetaEl) {
    detailMetaEl.textContent = t("labels.noJobSelected");
    if (!detailDevicesEl.innerHTML) {
      detailSummaryEl.textContent = t("labels.selectJobFromHistory");
    }
  }
}

async function refreshActive() {
  const active = await client().getActiveJob();
  if (!active.active || !active.job) {
    activeBlockingJob = null;
    updateCreateActionState();
    activeSummaryEl.textContent = t("status.activeNone");
    monitorSummaryEl.textContent = t("labels.noActiveJobSelected");
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

  activeSummaryEl.textContent = t("status.activeJob", { jobId: active.job.job_id, status: active.job.status });
  setStatus("status.active", { status: active.job.status });
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
    setModeStatus("status.mode", { worker: modes.worker_mode, validator: modes.validator_mode });
  } catch (error) {
    setModeStatus("status.modeUnknown");
    appendLog(`failed to load runtime modes: ${String(error)}`);
  }
}

function resolveRunTargets() {
  if (importedDevices.length === 0) {
    throw new Error(t("messages.importedDevicesEmpty"));
  }
  const chosen = selectedImportedDeviceKeys();
  if (chosen.length === 0) {
    throw new Error(t("messages.selectAtLeastOneImportedDevice"));
  }
  const importedDeviceKeys = chosen;
  const targetDevices = importedDeviceKeys
    .map((key) => {
      const [host, rawPort] = key.split(":");
      return { host, port: Number(rawPort || "22") };
    })
    .filter((device) => device.host && Number.isFinite(device.port));
  return {
    importedDeviceKeys,
    targetDevices,
  };
}

function selectedPostCanaryStrategy() {
  const selected = postCanaryStrategyEls.find((el) => el.checked)?.value || "parallel";
  return selected.trim();
}

function updatePostCanaryControls() {
  const strategy = selectedPostCanaryStrategy();
  const isParallel = strategy === "parallel";
  concurrencyLimitEl.disabled = !isParallel;
  concurrencyLimitEl.setAttribute("aria-disabled", String(!isParallel));
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
  const commands = parseCommands(document.getElementById("commands").value);
  const verifyCommands = parseCommands(verifyCommandsEl.value);
  const verifyMode = selectedVerifyMode();
  const concurrencyLimit = Number(concurrencyLimitEl.value || "5");
  const staggerDelay = Number(staggerDelayEl.value || "1.0");
  const stopOnError = stopOnErrorEl.checked;
  const postCanaryStrategy = selectedPostCanaryStrategy();

  if (commands.length === 0) {
    throw new Error(t("messages.commandsEmpty"));
  }
  if (!Number.isFinite(concurrencyLimit) || concurrencyLimit < 1) {
    throw new Error(t("messages.concurrencyLimitInvalid"));
  }
  if (!Number.isFinite(staggerDelay) || staggerDelay < 0) {
    throw new Error(t("messages.staggerDelayInvalid"));
  }
  if (!["parallel", "sequential"].includes(postCanaryStrategy)) {
    throw new Error(t("messages.postCanaryStrategyInvalid"));
  }

  const targets = resolveRunTargets();
  if (targets.targetDevices.length === 0) {
    throw new Error(t("messages.importedTargetDevicesEmpty"));
  }

  const canaryKey = canaryDeviceEl.value.trim();
  if (!canaryKey) {
    throw new Error(t("messages.canaryRequired"));
  }
  if (!targets.targetDevices.some((device) => `${device.host}:${device.port}` === canaryKey)) {
    throw new Error(t("messages.canaryIncluded"));
  }

  const [canaryHost, canaryRawPort] = canaryKey.split(":");
  const canary = { host: canaryHost, port: Number(canaryRawPort || "22") };
  const globalVars = parseGlobalVars(globalVarsText);
  const targetDeviceKeys = targets.importedDeviceKeys;
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

function buildReviewModel(runInput) {
  const remainingCount = Math.max(0, runInput.targetDeviceKeys.length - 1);
  const strategyText =
    runInput.postCanaryStrategy === "sequential"
      ? t("messages.canaryFlowSequential")
      : t("messages.canaryFlowParallel", { limit: runInput.effectiveConcurrencyLimit });
  return {
    modeText: t("messages.executionModeAsync"),
    hosts: runInput.targetDeviceKeys,
    commands: runInput.commands,
    verifyCommands: runInput.verifyCommands.length > 0 ? runInput.verifyCommands : [t("labels.none")],
    settings: [
      t("messages.settingCanary", { value: runInput.canaryKey }),
      t("messages.settingVerify", { value: describeVerifyPlan(runInput.verifyMode, runInput.verifyCommands) }),
      t("messages.settingStopOnError", { value: runInput.stopOnError }),
      t("messages.settingStaggerDelay", { value: runInput.staggerDelay }),
      t("messages.settingPostCanary", { value: runInput.postCanaryStrategy === "sequential" ? "Sequential" : "Parallel" }),
      t("messages.settingConcurrencyInput", {
        value: runInput.postCanaryStrategy === "sequential"
          ? t("messages.settingConcurrencyDisabled")
          : runInput.concurrencyLimit,
      }),
      t("messages.settingEffectiveConcurrency", { value: runInput.effectiveConcurrencyLimit }),
      t("messages.settingTargetDevices", { count: runInput.targetDeviceKeys.length, remaining: remainingCount }),
      t("messages.settingTargetSource"),
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

function renderRunReview(runInput) {
  const review = buildReviewModel(runInput);
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

function renderReviewPanelIfVisible() {
  if (pendingRunReview) {
    renderRunReview(pendingRunReview.runInput);
  }
}

async function executeRun(runInput) {
  runBusy = true;
  switchPage("monitor");
  updateCreateActionState();
  setStatus("status.creatingAsync");
  try {
    const job = await client().createJob(runInput.jobName, runInput.creator, runInput.globalVars);
    selectedJobId = job.job_id;
    beginMonitor(job, runInput.targetDeviceKeys, runInput.canaryKey);
    appendLog(t("messages.jobCreated", { jobId: job.job_id }));
    openJobSocket(currentApiBase(), job.job_id);

    const started = await client().runJobAsync(
      job.job_id,
      runInput.commands,
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
    appendLog(t("messages.runAsyncStarted", { status: started.status }));
    setStatus("status.running");
    await refreshJobs();
    await refreshActive();
  } catch (error) {
    setStatus("status.failed");
    appendLog(String(error));
  } finally {
    runBusy = false;
    updateCreateActionState();
  }
}

async function requestRun() {
  if (activeBlockingJob) {
    appendLog(
      t("messages.cannotCreateWhileActive", {
        jobId: activeBlockingJob.job_id,
        status: activeBlockingJob.status,
      })
    );
    switchPage("monitor");
    return;
  }
  try {
    const runInput = collectRunInput();
    if (!enableRunConfirmationEl.checked) {
      clearRunReview();
      await executeRun(runInput);
      return;
    }
    pendingRunReview = { runInput };
    renderRunReview(runInput);
    appendLog(t("messages.runReviewOpened"));
    switchPage("create");
  } catch (error) {
    const message = String(error);
    setStatus("status.inputError", { message });
    appendLog(message);
  }
}

runBtn.addEventListener("click", requestRun);
reviewExecuteBtn?.addEventListener("click", async () => {
  if (!pendingRunReview) {
    appendLog(t("messages.runReviewEmpty"));
    clearRunReview();
    return;
  }
  const review = pendingRunReview;
  clearRunReview();
  await executeRun(review.runInput);
});
reviewCancelBtn?.addEventListener("click", () => {
  appendLog(t("messages.runReviewCancelled"));
  clearRunReview();
});
reviewToggleHostsBtn?.addEventListener("click", () => {
  reviewHostsCollapsed = !reviewHostsCollapsed;
  updateReviewHostListVisibility();
});
verifyModeEls.forEach((el) => {
  el.addEventListener("change", updateVerifyModeControls);
});
postCanaryStrategyEls.forEach((el) => {
  el.addEventListener("change", updatePostCanaryControls);
});

importBtn.addEventListener("click", async () => {
  const csvInput = document.getElementById("csvInput").value;
  const importedCountBeforeImport = importedDevices.length;
  clearImportError();
  resetImportStreamLog();
  setImportInProgress(true);
  appendImportStreamLog(t("messages.importStarted"));
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
          importProgressTextEl.textContent = t("messages.validatingDevices", { processed: 0, total });
          appendImportStreamLog(t("messages.validationStarted", { total }));
        } else if (event.type === "progress") {
          const processed = Number(event.processed || 0);
          const total = Number(event.total || 0);
          const host = String(event.host || "?");
          const port = Number(event.port || 0);
          const result = event.connection_ok === true ? "OK" : "NG";
          importProgressEl.max = total > 0 ? total : 1;
          importProgressEl.value = processed;
          importProgressTextEl.textContent = t("messages.validatingDevices", { processed, total });
          appendImportStreamLog(
            t(event.connection_ok === true ? "messages.progressOk" : "messages.progressNg", {
              host,
              port: port || "?",
              processed,
              total,
            })
          );
          if (event.connection_ok === true) {
            successfulProgressCount += 1;
          }
          importedCount = successfulProgressCount;
          deviceCountEl.textContent = t("labels.importedDevices", { count: importedCount });
        } else if (event.type === "complete") {
          importedCount = (event.devices || []).length;
          const total = Number(event.total || importedCount);
          importProgressEl.max = total > 0 ? total : 1;
          importProgressEl.value = total;
          importProgressTextEl.textContent = t("messages.validatingDevices", { processed: total, total });
          deviceCountEl.textContent = t("labels.importedDevices", { count: importedCount });
          appendImportStreamLog(t("messages.importCompleted", { valid: importedCount, total }));
        } else if (event.type === "error") {
          const message = formatImportErrorDetail(event.detail);
          appendImportStreamLog(t("messages.importError", { message }));
          throw new Error(message);
        }
      }
    }
    appendLog(t("messages.importSuccess", { count: importedCount }));
    await refreshImportedDevices();
  } catch (error) {
    const message = String(error);
    deviceCountEl.textContent = t("labels.importedDevices", { count: importedCountBeforeImport });
    showImportError(message);
    appendImportStreamLog(t("messages.importFailed", { message }));
    appendLog(message);
  } finally {
    setImportInProgress(false);
  }
});

refreshDevicesBtn.addEventListener("click", () => {
  refreshImportedDevices().catch((error) => appendLog(String(error)));
});

resetAppStateBtn?.addEventListener("click", async () => {
  const confirmed = window.confirm(
    "Reset app state?\n\nImported devices, input values, job history, run results, and temporary UI state will be cleared. Saved presets will be kept."
  );
  if (!confirmed) {
    return;
  }
  resetAppStateBusy = true;
  updateCreateActionState();
  try {
    await client().resetAppState();
    resetFrontendAppState();
    switchPage("import");
    await refreshImportedDevices({ log: false });
    await refreshJobs();
    await refreshActive();
    await refreshRuntimeModes();
  } catch (error) {
    appendLog(String(error));
  } finally {
    resetAppStateBusy = false;
    updateCreateActionState();
  }
});

listJobsBtn.addEventListener("click", () => {
  refreshJobs().catch((error) => appendLog(String(error)));
});

refreshActiveBtn.addEventListener("click", () => {
  refreshActive().catch((error) => appendLog(String(error)));
});

enablePresetModeEl.addEventListener("change", async () => {
  presetPanelEl.classList.toggle("hidden", !enablePresetModeEl.checked);
  if (!enablePresetModeEl.checked) {
    osModelSelectEl.value = "";
    presetSelectEl.value = "";
    presetNameEl.value = "";
    await refreshPresetOptions().catch((error) => appendLog(String(error)));
    setPresetActionState();
    renderImportedDeviceList();
    refreshProdWarningOverlay();
    return;
  }
  await refreshPresetOptions().catch((error) => appendLog(String(error)));
  setPresetActionState();
  renderImportedDeviceList();
  refreshProdWarningOverlay();
});

osModelSelectEl.addEventListener("change", () => {
  renderImportedDeviceList();
  refreshCanaryOptions();
  presetNameEl.value = "";
  refreshPresetOptions().catch((error) => appendLog(String(error)));
  refreshProdWarningOverlay();
});

presetSelectEl.addEventListener("change", () => {
  const selected = currentPresets.find(
    (preset) => preset.preset_id === presetSelectEl.value
  );
  if (!selected) {
    setPresetActionState();
    return;
  }
  presetNameEl.value = selected.name;
  document.getElementById("commands").value = selected.commands.join("\n");
  verifyCommandsEl.value = selected.verify_commands.join("\n");
  updateVerifyModeControls();
  setPresetActionState();
  appendLog(t("messages.presetApplied", { name: selected.name, osModel: selected.os_model }));
});

presetSaveNewBtn?.addEventListener("click", () => {
  savePresetNew().catch((error) => appendLog(String(error)));
});

presetUpdateBtn?.addEventListener("click", () => {
  updateSelectedPreset().catch((error) => appendLog(String(error)));
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

verifyCommandsEl.addEventListener("input", updateVerifyModeControls);

statusRunBtn.addEventListener("click", async () => {
  const selected = statusDeviceSelectEl.value.trim();
  const commands = statusCommandsEl.value.trim();
  if (!selected) {
    statusOutputEl.textContent = t("messages.selectTargetDevice");
    return;
  }
  if (!commands) {
    statusOutputEl.textContent = t("messages.enterCommand");
    return;
  }
  const [host, rawPort] = selected.split(":");
  const port = Number(rawPort || "22");
  statusRunBtn.disabled = true;
  statusOutputEl.textContent = t("messages.runningEllipsis");
  try {
    const result = await client().execStatusCommands(host, port, commands);
    statusOutputEl.textContent = result.output || t("labels.emptyOutput");
    appendLog(t("messages.statusCommandSucceeded", { host, port }));
  } catch (error) {
    const text = String(error);
    statusOutputEl.textContent = t("messages.errorPrefix", { error: text });
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
    appendLog(t("messages.pausedJob", { jobId: result.job_id }));
    setStatus("status.paused");
    await refreshActive();
  } catch (error) {
    appendLog(String(error));
  }
});

resumeBtn.addEventListener("click", async () => {
  try {
    const result = await client().controlActiveJob("resume");
    appendLog(t("messages.resumedJob", { jobId: result.job_id }));
    setStatus("status.running");
    await refreshActive();
  } catch (error) {
    appendLog(String(error));
  }
});

cancelBtn.addEventListener("click", async () => {
  try {
    const result = await client().controlActiveJob("cancel");
    appendLog(t("messages.cancelledJob", { jobId: result.job_id }));
    setStatus("status.cancelled");
    await refreshActive();
    if (selectedJobId) {
      const events = await client().listJobEvents(selectedJobId);
      appendLog(t("messages.selectedJobEvents", { count: events.length }));
    }
  } catch (error) {
    appendLog(String(error));
  }
});

clearBtn.addEventListener("click", () => {
  logEl.textContent = "";
});

localeSelectEl?.addEventListener("change", () => {
  setLocale(localeSelectEl.value);
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
applyTranslations();
applyApiBaseVisibility();
setStatus("status.idle");
setModeStatus("status.modeUnknown");
updateCreateActionState();
updateVerifyModeControls();
updatePostCanaryControls();
setPresetActionState();
detailMetaEl.textContent = t("labels.noJobSelected");
detailSummaryEl.textContent = t("labels.selectJobFromHistory");
statusOutputEl.textContent = t("labels.noOutputYet");
deviceCountEl.textContent = t("labels.importedDevices", { count: 0 });
importedDeviceHintEl.textContent = t("labels.importedTargetCandidates", { count: 0 });
monitorSummaryEl.textContent = t("labels.noActiveRunSelected");
activeSummaryEl.textContent = t("status.activeNone");
renderMonitorState();
refreshProdWarningOverlay();
refreshImportedDevices().catch(() => {});
refreshJobs().catch(() => {});
refreshActive().catch(() => {});
refreshRuntimeModes().catch(() => {});
