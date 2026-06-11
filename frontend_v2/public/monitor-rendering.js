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

import {
  escapeHtml,
  formatDiffHtml,
  formatTimestamp,
  normalizedStatus,
} from "./display-utils.js";

export function combineDeviceKeys(source) {
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

export function buildExecutionSummaryHtml(source, eventCount, options) {
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
      <span class="status-badge status-${normalizedStatus(status)}">${options.statusLabel(status)}</span>
      / Created: ${escapeHtml(formatTimestamp(source.job?.created_at || "", options.locale))}
      / Devices: ${keys.length}
      / Events: ${eventCount}
    </div>
    <div class="muted">Queue: ${queue} / Running: ${running} / Complete: ${complete} / Failed: ${failed}</div>
  `;
}

export function buildDeviceCardsHtml(source, deviceNameMap = {}, options) {
  const keys = combineDeviceKeys(source);
  if (keys.length === 0) {
    return `<div class="muted">${escapeHtml(options.translate("labels.noTargetDevicesYet"))}</div>`;
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
      const hostname = String(deviceNameMap[key] || "").trim() || options.hostFromDeviceKey(key);
      return `
        <div class="device-card status-${status}" id="device-card-${key.replace(":", "-")}">
          <h4>${escapeHtml(`${key} (${hostname})`)} ${isCanary ? '<span class="status-badge status-paused">CANARY</span>' : ""} <span class="status-badge status-${status}">${options.statusLabel(status)}</span></h4>
          <div class="meta">Attempts: ${attempts || "-"} ${error ? `/ Error: ${escapeHtml(error)}` : ""}</div>
          <div class="output-label">Command Stream</div>
          <pre class="stream-output" data-device-key="${escapeHtml(key)}">${escapeHtml(streamText)}</pre>
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
