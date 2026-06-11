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

export function parseCommands(text) {
  return text
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
}

export function parseGlobalVars(text, translate) {
  const raw = text.trim();
  if (!raw) {
    return {};
  }
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    throw new Error(translate("messages.globalVarsParseError", { error: String(error) }));
  }
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error(translate("messages.globalVarsObject"));
  }
  return Object.fromEntries(
    Object.entries(parsed).map(([key, value]) => [String(key), String(value)])
  );
}

export function resolveEffectiveExecutionConfig(concurrencyLimit, strategy) {
  return {
    strategy,
    effectiveConcurrencyLimit: strategy === "sequential" ? 1 : concurrencyLimit,
  };
}

export function buildRunInput(rawInput, options) {
  const commands = parseCommands(rawInput.commandsText);
  const verifyCommands = parseCommands(rawInput.verifyCommandsText);
  const translate = options.translate;

  if (commands.length === 0) {
    throw new Error(translate("messages.commandsEmpty"));
  }
  if (!Number.isFinite(rawInput.concurrencyLimit) || rawInput.concurrencyLimit < 1) {
    throw new Error(translate("messages.concurrencyLimitInvalid"));
  }
  if (!Number.isFinite(rawInput.staggerDelay) || rawInput.staggerDelay < 0) {
    throw new Error(translate("messages.staggerDelayInvalid"));
  }
  if (!["parallel", "sequential"].includes(rawInput.postCanaryStrategy)) {
    throw new Error(translate("messages.postCanaryStrategyInvalid"));
  }
  if (!["all", "canary"].includes(rawInput.commandScope)) {
    throw new Error(translate("messages.commandScopeInvalid"));
  }
  if (rawInput.targets.targetDevices.length === 0) {
    throw new Error(translate("messages.importedTargetDevicesEmpty"));
  }
  if (!rawInput.canaryKey) {
    throw new Error(translate("messages.canaryRequired"));
  }
  if (
    !rawInput.targets.targetDevices.some(
      (device) => `${device.host}:${device.port}` === rawInput.canaryKey
    )
  ) {
    throw new Error(translate("messages.canaryIncluded"));
  }

  const [canaryHost, canaryRawPort] = rawInput.canaryKey.split(":");
  const canary = { host: canaryHost, port: Number(canaryRawPort || "22") };
  const globalVars = parseGlobalVars(rawInput.globalVarsText, translate);
  const targetDeviceKeys = rawInput.targets.importedDeviceKeys;
  const executionTargetDeviceKeys =
    rawInput.commandScope === "canary" ? [rawInput.canaryKey] : targetDeviceKeys;
  const effectiveConfig =
    rawInput.commandScope === "canary"
      ? { strategy: rawInput.postCanaryStrategy, effectiveConcurrencyLimit: 1 }
      : resolveEffectiveExecutionConfig(rawInput.concurrencyLimit, rawInput.postCanaryStrategy);

  return {
    jobName: rawInput.jobName,
    creator: rawInput.creator,
    globalVars,
    commands,
    commandScope: rawInput.commandScope,
    verifyCommands,
    verifyMode: rawInput.verifyMode,
    concurrencyLimit: rawInput.concurrencyLimit,
    staggerDelay: rawInput.staggerDelay,
    stopOnError: rawInput.stopOnError,
    canary,
    canaryKey: rawInput.canaryKey,
    targets: rawInput.targets,
    targetDeviceKeys,
    executionTargetDeviceKeys,
    postCanaryStrategy: rawInput.postCanaryStrategy,
    effectiveConcurrencyLimit: effectiveConfig.effectiveConcurrencyLimit,
  };
}
