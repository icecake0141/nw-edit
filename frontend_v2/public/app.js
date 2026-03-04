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
const osModelSelectEl = document.getElementById("osModelSelect");
const presetSelectEl = document.getElementById("presetSelect");
const importedDeviceListEl = document.getElementById("importedDeviceList");
const importedDeviceHintEl = document.getElementById("importedDeviceHint");
const verifyCommandsEl = document.getElementById("verifyCommands");
const savePresetBtn = document.getElementById("savePresetBtn");
const savePresetFromDetailBtn = document.getElementById("savePresetFromDetailBtn");
const savePresetModalEl = document.getElementById("savePresetModal");
const savePresetNameEl = document.getElementById("savePresetName");
const savePresetOsModelEl = document.getElementById("savePresetOsModel");
const savePresetCommandsEl = document.getElementById("savePresetCommands");
const savePresetVerifyCommandsEl = document.getElementById("savePresetVerifyCommands");
const savePresetConfirmBtn = document.getElementById("savePresetConfirmBtn");
const savePresetCancelBtn = document.getElementById("savePresetCancelBtn");

/** @type {WebSocket|null} */
let activeSocket = null;
/** @type {string|null} */
let selectedJobId = null;
/** @type {import("./api-client.js").DeviceProfile[]} */
let importedDevices = [];
/** @type {import("./api-client.js").Preset[]} */
let currentPresets = [];
/** @type {{ source: "sync" | "detail", commands: string[], verifyCommands: string[], defaultOsModel: string }|null} */
let savePresetContext = null;

pauseBtn.disabled = true;
resumeBtn.disabled = true;
cancelBtn.disabled = true;
setSavePresetVisible(false);
setSavePresetFromDetailVisible(false);

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

function parseVerifyCommands(text) {
  return parseCommands(text);
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

function selectedImportedDeviceKeys() {
  return Array.from(
    document.querySelectorAll('input[name="importedDeviceKeys"]:checked')
  ).map((el) => el.value);
}

function selectedOsModel() {
  return osModelSelectEl.value.trim();
}

function setSavePresetVisible(visible) {
  savePresetBtn.classList.toggle("hidden", !visible);
}

function setSavePresetFromDetailVisible(visible) {
  savePresetFromDetailBtn.classList.toggle("hidden", !visible);
}

function openSavePresetModal(context) {
  savePresetContext = context;
  savePresetNameEl.value = "";
  savePresetOsModelEl.value = context.defaultOsModel || "";
  savePresetCommandsEl.value = context.commands.join("\n");
  savePresetVerifyCommandsEl.value = context.verifyCommands.join("\n");
  savePresetModalEl.classList.remove("hidden");
}

function closeSavePresetModal() {
  savePresetModalEl.classList.add("hidden");
}

function populateOsModelSelect(models) {
  const previous = selectedOsModel();
  osModelSelectEl.innerHTML = '<option value="">(未選択)</option>';
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

function renderImportedDeviceCandidates() {
  const model = selectedOsModel();
  importedDeviceListEl.replaceChildren();
  if (!model) {
    importedDeviceHintEl.textContent = "OSモデルを選択すると候補を表示します。";
    return;
  }
  const candidates = importedDevices.filter((device) => device.device_type === model);
  importedDeviceHintEl.textContent = `${model} の候補: ${candidates.length}台（初期未選択）`;
  if (candidates.length === 0) {
    return;
  }
  candidates.forEach((device) => {
    const label = document.createElement("label");
    label.className = "device-option";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = "importedDeviceKeys";
    input.value = `${device.host}:${device.port}`;
    const text = document.createElement("span");
    text.textContent = `${device.host}:${device.port} (${device.name || "-"} / ${device.device_type})`;
    label.append(input, text);
    importedDeviceListEl.append(label);
  });
}

async function refreshPresetOptions() {
  const model = selectedOsModel();
  presetSelectEl.innerHTML = '<option value="">(未選択)</option>';
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
  const deviceModels = Array.from(
    new Set(importedDevices.map((device) => device.device_type))
  ).sort();
  const presetModels = await client().listPresetOsModels();
  const allModels = Array.from(new Set([...deviceModels, ...presetModels])).sort();
  populateOsModelSelect(allModels);
  renderImportedDeviceCandidates();
  await refreshPresetOptions();
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
        const canSave =
          result.status === "completed" &&
          Object.values(result.device_results || {}).every(
            (value) => value.status === "success"
          ) &&
          Array.isArray(result.commands);
        if (canSave) {
          const targets = importedDevices.filter((device) =>
            (result.target_device_keys || []).includes(`${device.host}:${device.port}`)
          );
          const osModels = Array.from(
            new Set(targets.map((device) => device.device_type))
          );
          const defaultOsModel = osModels.length === 1 ? osModels[0] : "";
          savePresetContext = {
            source: "detail",
            commands: result.commands || [],
            verifyCommands: result.verify_commands || [],
            defaultOsModel,
          };
          setSavePresetFromDetailVisible(true);
        } else {
          setSavePresetFromDetailVisible(false);
        }
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
  const globalVarsText = document.getElementById("globalVars").value;
  const devices = parseDevices(document.getElementById("devices").value);
  const commands = parseCommands(document.getElementById("commands").value);
  const verifyCommands = parseVerifyCommands(verifyCommandsEl.value);
  const useImported = useImportedEl.checked;
  const importedDeviceKeys = selectedImportedDeviceKeys();

  if (commands.length === 0) {
    appendLog("commands is empty");
    return;
  }
  if (!useImported && devices.length === 0) {
    appendLog("ad-hoc devices is empty");
    return;
  }
  if (useImported) {
    if (!selectedOsModel()) {
      appendLog("対象OSモデルを選択してください");
      return;
    }
    if (importedDeviceKeys.length === 0) {
      appendLog("import済みデバイスの適用対象を選択してください");
      return;
    }
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
      devices,
      useImported,
      {
        verifyCommands,
        importedDeviceKeys,
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
    const canSave =
      result.status === "completed" &&
      Object.values(result.device_results).every((value) => value.status === "success");
    if (canSave) {
      const targets = importedDevices.filter((device) =>
        result.target_device_keys.includes(`${device.host}:${device.port}`)
      );
      const osModels = Array.from(new Set(targets.map((device) => device.device_type)));
      const defaultOsModel = osModels.length === 1 ? osModels[0] : selectedOsModel();
      savePresetContext = {
        source: "sync",
        commands: result.commands.length > 0 ? result.commands : commands,
        verifyCommands:
          result.verify_commands.length > 0
            ? result.verify_commands
            : verifyCommands,
        defaultOsModel,
      };
      setSavePresetVisible(true);
    } else {
      setSavePresetVisible(false);
      savePresetContext = null;
    }
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
  const verifyCommands = parseVerifyCommands(verifyCommandsEl.value);
  const useImported = useImportedEl.checked;
  const importedDeviceKeys = selectedImportedDeviceKeys();

  if (commands.length === 0) {
    appendLog("commands is empty");
    return;
  }
  if (!useImported && devices.length === 0) {
    appendLog("ad-hoc devices is empty");
    return;
  }
  if (useImported) {
    if (!selectedOsModel()) {
      appendLog("対象OSモデルを選択してください");
      return;
    }
    if (importedDeviceKeys.length === 0) {
      appendLog("import済みデバイスの適用対象を選択してください");
      return;
    }
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
      devices,
      useImported,
      {
        verifyCommands,
        importedDeviceKeys,
      }
    );
    appendLog(`run async started: ${started.status}`);
    setStatus("running");
    setSavePresetVisible(false);
    setSavePresetFromDetailVisible(false);
    savePresetContext = null;
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

osModelSelectEl.addEventListener("change", () => {
  renderImportedDeviceCandidates();
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
  appendLog(`実行プリセット適用: ${selected.name} (${selected.os_model})`);
});

savePresetBtn.addEventListener("click", () => {
  if (!savePresetContext) {
    return;
  }
  openSavePresetModal(savePresetContext);
});

savePresetFromDetailBtn.addEventListener("click", () => {
  if (!savePresetContext) {
    return;
  }
  openSavePresetModal(savePresetContext);
});

savePresetCancelBtn.addEventListener("click", () => {
  closeSavePresetModal();
});

savePresetConfirmBtn.addEventListener("click", async () => {
  const name = savePresetNameEl.value.trim();
  const osModel = savePresetOsModelEl.value.trim();
  const commands = parseCommands(savePresetCommandsEl.value);
  const verifyCommands = parseVerifyCommands(savePresetVerifyCommandsEl.value);
  if (!name) {
    appendLog("プリセット名を入力してください");
    return;
  }
  if (!osModel) {
    appendLog("OSモデルを入力してください");
    return;
  }
  if (commands.length === 0) {
    appendLog("プリセットのcommandsが空です");
    return;
  }
  const payload = {
    name,
    os_model: osModel,
    commands,
    verify_commands: verifyCommands,
  };
  try {
    await client().createPreset(payload);
    appendLog(`実行プリセット保存: ${name} (${osModel})`);
  } catch (error) {
    if (!String(error).includes("409")) {
      appendLog(String(error));
      return;
    }
    const sameModel = await client().listPresets(osModel);
    const existing = sameModel.find((preset) => preset.name === name);
    if (!existing) {
      appendLog(String(error));
      return;
    }
    const accepted = window.confirm(
      `同名プリセットが存在します。上書きしますか？\nname=${name} os_model=${osModel}`
    );
    if (!accepted) {
      appendLog("プリセット上書きをキャンセルしました");
      return;
    }
    await client().updatePreset(existing.preset_id, payload);
    appendLog(`実行プリセット上書き: ${name} (${osModel})`);
  }
  closeSavePresetModal();
  await refreshImportedDevices();
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
