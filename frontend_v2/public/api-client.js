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

/**
 * @typedef {{ host: string, port: number }} DeviceTarget
 * @typedef {{ job_id: string, job_name: string, creator: string, status: string, created_at: string }} JobSummary
 * @typedef {{ status: string, attempts: number, error?: string, error_code?: string, logs: string[], pre_output: string, apply_output: string, post_output: string, diff: string, diff_truncated: boolean, diff_original_size: number }} DeviceRunResponse
 * @typedef {{ job_id: string, status: string, device_results: Record<string, DeviceRunResponse> }} RunJobResponse
 * @typedef {{ devices: unknown[], failed_rows: { error: string }[] }} ImportDevicesResponse
 * @typedef {{ active: boolean, job?: JobSummary }} ActiveJobResponse
 */

/**
 * Thin typed client for nw-edit v2 API.
 */
export class NwEditApiClient {
  /** @param {string} baseUrl */
  constructor(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  /**
   * @template T
   * @param {string} path
   * @param {RequestInit=} init
   * @returns {Promise<T>}
   */
  async request(path, init) {
    const response = await fetch(`${this.baseUrl}${path}`, init);
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`${init?.method || "GET"} ${path} failed: ${response.status} ${text}`);
    }
    return /** @type {Promise<T>} */ (response.json());
  }

  /** @param {string} jobName @param {string} creator @returns {Promise<JobSummary>} */
  async createJob(jobName, creator) {
    return this.request("/api/v2/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_name: jobName, creator }),
    });
  }

  /** @returns {Promise<JobSummary[]>} */
  async listJobs() {
    return this.request("/api/v2/jobs");
  }

  /** @param {string} jobId @returns {Promise<JobSummary>} */
  async getJob(jobId) {
    return this.request(`/api/v2/jobs/${jobId}`);
  }

  /** @param {string} jobId @returns {Promise<unknown[]>} */
  async listJobEvents(jobId) {
    return this.request(`/api/v2/jobs/${jobId}/events`);
  }

  /** @param {string} jobId @returns {Promise<RunJobResponse>} */
  async getJobResult(jobId) {
    return this.request(`/api/v2/jobs/${jobId}/result`);
  }

  /** @returns {Promise<ActiveJobResponse>} */
  async getActiveJob() {
    return this.request("/api/v2/jobs/active");
  }

  /** @param {string} action @returns {Promise<JobSummary>} */
  async controlActiveJob(action) {
    const active = await this.getActiveJob();
    if (!active.active || !active.job) {
      throw new Error("No active job");
    }
    return this.request(`/api/v2/jobs/${active.job.job_id}/${action}`, {
      method: "POST",
    });
  }

  /** @returns {Promise<unknown[]>} */
  async listDevices() {
    return this.request("/api/v2/devices");
  }

  /** @param {string} csvText @returns {Promise<ImportDevicesResponse>} */
  async importDevices(csvText) {
    return this.request("/api/v2/devices/import", {
      method: "POST",
      headers: { "Content-Type": "text/plain" },
      body: csvText,
    });
  }

  /**
   * @param {string} jobId
   * @param {string[]} commands
   * @param {DeviceTarget[]} devices
   * @param {boolean} useImported
   * @returns {Promise<RunJobResponse>}
   */
  async runJob(jobId, commands, devices, useImported) {
    const payload = {
      commands,
      concurrency_limit: 2,
      stagger_delay: 0,
      stop_on_error: true,
      non_canary_retry_limit: 1,
      retry_backoff_seconds: 0,
    };
    if (!useImported) {
      payload.devices = devices;
      payload.canary = devices[0];
    }
    return this.request(`/api/v2/jobs/${jobId}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  /**
   * @param {string} jobId
   * @param {string[]} commands
   * @param {DeviceTarget[]} devices
   * @param {boolean} useImported
   * @returns {Promise<JobSummary>}
   */
  async runJobAsync(jobId, commands, devices, useImported) {
    const payload = {
      commands,
      concurrency_limit: 2,
      stagger_delay: 0,
      stop_on_error: true,
      non_canary_retry_limit: 1,
      retry_backoff_seconds: 0,
    };
    if (!useImported) {
      payload.devices = devices;
      payload.canary = devices[0];
    }
    return this.request(`/api/v2/jobs/${jobId}/run/async`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }
}
