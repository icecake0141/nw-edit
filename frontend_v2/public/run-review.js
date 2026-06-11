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

export function buildReviewModel(runInput, options) {
  const executionDeviceKeys = runInput.executionTargetDeviceKeys || runInput.targetDeviceKeys;
  const remainingCount = Math.max(0, executionDeviceKeys.length - 1);
  const strategyText =
    runInput.commandScope === "canary"
      ? options.translate("messages.canaryFlowOnly")
      : runInput.postCanaryStrategy === "sequential"
      ? options.translate("messages.canaryFlowSequential")
      : options.translate("messages.canaryFlowParallel", { limit: runInput.effectiveConcurrencyLimit });
  return {
    modeText: options.translate("messages.executionModeAsync"),
    hosts: executionDeviceKeys,
    commands: runInput.commands,
    verifyCommands: runInput.verifyCommands.length > 0 ? runInput.verifyCommands : [options.translate("labels.none")],
    settings: [
      options.translate("messages.settingCanary", { value: runInput.canaryKey }),
      options.translate("messages.settingCommandScope", { value: options.describeCommandScope(runInput.commandScope) }),
      options.translate("messages.settingVerify", { value: options.describeVerifyPlan(runInput.verifyMode, runInput.verifyCommands) }),
      options.translate("messages.settingStopOnError", { value: runInput.stopOnError }),
      options.translate("messages.settingStaggerDelay", { value: runInput.staggerDelay }),
      options.translate("messages.settingPostCanary", {
        value:
          runInput.commandScope === "canary"
            ? options.translate("messages.settingNotApplicable")
            : runInput.postCanaryStrategy === "sequential"
            ? "Sequential"
            : "Parallel",
      }),
      options.translate("messages.settingConcurrencyInput", {
        value:
          runInput.commandScope === "canary" || runInput.postCanaryStrategy === "sequential"
            ? options.translate("messages.settingConcurrencyDisabled")
            : runInput.concurrencyLimit,
      }),
      options.translate("messages.settingEffectiveConcurrency", { value: runInput.effectiveConcurrencyLimit }),
      options.translate("messages.settingTargetDevices", { count: executionDeviceKeys.length, remaining: remainingCount }),
      options.translate("messages.settingTargetSource"),
    ],
    flowDiagram: strategyText,
  };
}
