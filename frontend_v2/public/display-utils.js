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

export function formatTimestamp(value, locale) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(locale);
}

export function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

export function normalizedStatus(status) {
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

export function formatDiffHtml(diffText) {
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
