<!--
Copyright 2026 icecake0141
SPDX-License-Identifier: Apache-2.0

This file was created or modified with the assistance of an AI (Large Language Model).
Please review for correctness and security.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
-->
# Intent Compiler and Pre-Run Plan Implementation Plan

## Purpose

This feature addresses a practical gap in network automation abstraction. In many network environments, device modules remain vendor-specific and do not provide a strong meta-layer equivalent to common Linux/package abstractions. The goal here is not to build a full generic DSL, but to introduce an explicit compile step with guardrails:

- Operators describe a limited, common intent model.
- The system compiles intent into vendor/device-specific commands.
- Unsupported combinations fail early and explicitly.
- Execution remains transparent through a pre-run plan.

## Scope

### In Scope

- Limited Intent model:
  - NTP
  - SNMP RO
  - Management IP
  - Admin User
  - Management access restriction (MGMT ACL)
- Intent-to-command compilation per `device_type`
- Pre-run preview API (`/plan`) for explainability
- Backward compatibility with existing `run` and `run/async`

### Out of Scope

- Persistent audit trail storage
- Full generic DSL abstraction layer
- Advanced delete/replace reconciliation behavior

## Public API Changes

### `RunJobRequest` Extension

Add optional `intent` to the existing run payload.

Validation rules:

- Reject with `HTTP 400` when both `commands` and `intent` are provided.
- Reject with `HTTP 400` when both are absent.
- Reject with `HTTP 400` when any intent field is unsupported for a target `device_type`.

### New Endpoint

- `POST /api/v2/jobs/{job_id}/plan`

Returns:

- Per-device compiled command preview
- Warnings
- Compile summary

### Error Policy

- Unsupported intent/device combinations must return `HTTP 400`.
- No implicit fallback to vendor-default or raw commands.

## Interfaces and Types

### `IntentSpec`

- `ntp.servers`
- `snmp.community_ro`
- `management_ip.interface`
- `management_ip.address_cidr`
- `admin_user.username`
- `admin_user.password`
- `mgmt_acl.allowed_sources`

### Preview Response Model

- `mode` (`commands` or `intent`)
- `per_device_plan[]`
- `compile_summary`

Suggested per-device payload fields:

- `device_key`
- `device_type`
- `resolved_intent`
- `compiled_commands[]`
- `warnings[]`

Suggested summary fields:

- `supported_count`
- `unsupported_count`
- `errors[]`

### Compile Error Model

- `code`
- `message`
- `device_key`
- `intent_path`

## Implementation Design

### Compiler Module

Add:

- `backend_v2/app/application/intent_compiler.py`

Responsibilities:

- Normalize and validate `IntentSpec`
- Compile intent into device-specific command lists
- Return explicit compile failures for unsupported input

### Device Profile / Policy Module

Add:

- `backend_v2/app/domain/intent_profiles.py`

Responsibilities:

- Define supported intent capabilities per `device_type`
- Hold command template/policy rules per target platform
- Provide deterministic compile behavior across supported types

Target `device_type` list for this phase:

- `cisco_ios`
- `cisco_iosxr`
- `arista_eos`
- `juniper_junos`
- `fortinet`

### Run Preparation Integration

Integrate into current run preparation path:

- Keep existing `commands` flow unchanged.
- Add `intent` flow that compiles into `commands_by_device`.
- Reuse shared validation for both sync and async run paths.

### Plan Path (No Execution)

Add `/plan` path that:

- Resolves targets
- Performs compile and validation only
- Returns preview payload
- Does not execute any device operation

## Frontend Changes (Minimal)

- Add mode toggle: `commands` vs `intent`
- Enforce mutual exclusivity in UI
- Add `Plan` action/button
- Render preview result (`per_device_plan`, `compile_summary`)
- Keep existing commands-based run UX intact

## Testing Plan

### Unit Tests

- Compiler success paths across all 5 target device types
- Unsupported intent/device combination error paths
- Invalid input validation (format/value constraints)

### API Integration Tests

- `/plan` success and failure cases
- `run` and `run/async` with intent mode
- Backward compatibility for commands mode

### Frontend Tests

- Mode toggle behavior
- Preview rendering behavior
- Error display correctness

## Acceptance Criteria

- Existing commands-based workflows continue to pass unchanged.
- Intent preview works for all target device types:
  - `cisco_ios`
  - `cisco_iosxr`
  - `arista_eos`
  - `juniper_junos`
  - `fortinet`
- Unsupported cases fail before execution with explicit errors.
- No persisted audit/history capability is introduced in this phase.

## Assumptions and Defaults

- No persistent DB is introduced in this phase.
- No dedicated audit retention feature is added beyond normal runtime behavior.
- Explainability is provided by on-demand pre-run preview only.
