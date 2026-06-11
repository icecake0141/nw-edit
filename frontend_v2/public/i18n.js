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

export const DEFAULT_LOCALE = "en";
export const LOCALE_STORAGE_KEY = "nw-edit.locale";
export const SUPPORTED_LOCALES = ["en"];

export const translations = {
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
    commandCards: {
      applyTitle: "Commands sent to devices",
      applyCopy: "These commands change target device configuration and run in order, one line at a time.",
      verifyTitle: "Verification commands",
      verifyCopy: "Use these commands to check state before and after changes. This field can be blank.",
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
      verifyChoose: "Choose where configured verify commands run.",
      verifyIgnored: "No verify commands configured. Execution command scope still applies.",
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
      commandScopeInvalid: "commandScope must be all or canary",
      canaryRequired: "canary device is required",
      canaryIncluded: "canary device must be included in target devices",
      executionModeAsync: "Execution mode: Async (/run/async)",
      canaryFlowSequential: "Canary -> Device-1 -> Device-2 -> ...",
      canaryFlowParallel: "Canary -> [Device-1, Device-2, ...] (parallel up to {limit})",
      canaryFlowOnly: "Canary only",
      settingCanary: "Canary: {value}",
      settingCommandScope: "Execution scope: {value}",
      settingVerify: "Verify: {value}",
      settingStopOnError: "Stop on error: {value}",
      settingStaggerDelay: "Stagger delay: {value}s",
      settingPostCanary: "Post-canary strategy: {value}",
      settingNotApplicable: "not applicable",
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
        <p>Variables let you reuse command templates across devices. Use placeholders like <code>{{hostname}}</code> in command lines, then provide values from <code>global_vars</code>, imported CSV columns, or CSV <code>host_vars</code>.</p>
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
        <h3>3) Default Host Vars from CSV Columns</h3>
        <p>Imported CSV columns are available automatically as per-host variables. You do not need to duplicate common fields in <code>host_vars</code>.</p>
        <p>Built-in defaults:</p>
        <pre>{{host}}        CSV host value
{{ip}}          same value as host
{{hostname}}    CSV name value, or host when name is empty
{{port}}        resolved SSH port
{{device_type}} normalized device type
{{name}}        CSV name value
{{username}}    CSV username value
{{prod}}        true or false</pre>
        <p>Additional CSV columns with valid variable names are also available. <code>password</code>, <code>host_vars</code>, and <code>verify_cmds</code> are excluded.</p>
        <pre>host,port,device_type,username,password,name,site,prod
10.0.0.1,22,cisco_ios,admin,pass,edge-1,tokyo,true

commands:
hostname {{hostname}}
snmp-server location {{site}}
logging host {{ip}}</pre>
        <h3>4) Explicit Host Vars (per-device CSV)</h3>
        <p>Use CSV column <code>host_vars</code> as a JSON object string:</p>
        <pre>host,port,device_type,username,password,name,verify_cmds,host_vars,prod
10.0.0.1,22,cisco_ios,admin,pass,edge-1,show run,"{""hostname"":""edge-1"",""tz_offset"":""9""}",true
10.0.0.2,22,cisco_ios,admin,pass,edge-2,show run,"{""hostname"":""edge-2""}",false</pre>
        <p>Use explicit <code>host_vars</code> when you need to add values that are not CSV columns, or override default host variables.</p>
        <h3>5) Resolution Priority</h3>
        <p>If the same key exists in multiple places, explicit device-level values win: <code>host_vars &gt; default CSV host vars &gt; global_vars</code>.</p>
        <h3>6) Missing Variable Behavior</h3>
        <p>If any placeholder has no value, preflight fails with <code>HTTP 400</code>. Device commands are not executed.</p>
        <h3>7) Common Mistakes and Fixes</h3>
        <pre>- Invalid JSON in Global Vars:
  wrong: {"timezone":"Asia/Tokyo",}
  fix:   {"timezone":"Asia/Tokyo"}

- Global Vars must be an object:
  wrong: ["x", "y"]
  fix:   {"x":"1","y":"2"}

- CSV host_vars quoting:
  wrong: {"hostname":"edge-1"}   (not CSV-escaped)
  fix:   "{""hostname"":""edge-1""}"</pre>
        <h3>8) End-to-End Mini Example</h3>
        <p>Inputs:</p>
        <pre>global_vars:
{"tz_offset":"9","ntp_server":"192.0.2.10"}

CSV row:
host,port,device_type,username,password,name,site
10.0.0.1,22,cisco_ios,admin,pass,edge-1,tokyo

command:
clock timezone JST {{tz_offset}}
ntp server {{ntp_server}}
hostname {{hostname}}
snmp-server location {{site}}

explicit host_vars for 10.0.0.1:
{"ntp_server":"192.0.2.20"}</pre>
        <p>Resolved commands for 10.0.0.1:</p>
        <pre>clock timezone JST 9
ntp server 192.0.2.20
hostname edge-1
snmp-server location tokyo</pre>
        <h3>9) Production Host Flag</h3>
        <p>Optional CSV column <code>prod</code> marks production hosts. <code>true</code> enables production warning UI in Create/Monitor/Detail pages when selected targets include that host.</p>
        <pre>host,port,device_type,username,password,name,verify_cmds,host_vars,prod
10.0.0.10,22,cisco_ios,admin,pass,core-prod,show run,"{""hostname"":""core-prod""}",true
10.0.0.20,22,cisco_ios,admin,pass,edge-dev,show run,"{""hostname"":""edge-dev""}",false</pre>`,
    },
  },
};

export function resolveInitialLocale(storage = window.localStorage) {
  const stored = storage.getItem(LOCALE_STORAGE_KEY);
  return SUPPORTED_LOCALES.includes(stored || "") ? stored : DEFAULT_LOCALE;
}

export function translationValue(locale, key) {
  return key.split(".").reduce((value, part) => value?.[part], translations[locale]);
}

export function interpolate(template, params = {}) {
  return String(template).replace(/\{(\w+)\}/g, (_, key) => String(params[key] ?? `{${key}}`));
}

export function translate(locale, key, params) {
  const template =
    translationValue(locale, key) ??
    translationValue(DEFAULT_LOCALE, key) ??
    key;
  return typeof template === "string" ? interpolate(template, params) : String(template);
}
