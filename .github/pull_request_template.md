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
## Summary

- 

## Rationale

- 

## Related Issues

- Closes #

## LLM Involvement

- Files created/modified by LLM:
  - `git show --name-only --pretty="" HEAD`
- Human review performed:
  - 

## Validation Commands

```bash
python3 -m pip install -r backend/requirements-dev.txt
make check
./verify.sh
# Optional (docker-backed integration path)
make check-integration
```

## Backward Compatibility / Migration Notes

- 

## Documentation Updates

- [ ] README updated (usage/quick start)
- [ ] docs/ updated (behavior/implementation)
- [ ] Examples/snippets updated
- [ ] CHANGELOG/versioning updated (if user-facing behavior changed)

## PR Checklist

- [ ] License header added to new files and top-level LICENSE present
- [ ] LLM attribution added to modified/generated files
- [ ] Linting completed — score: 10/10 (command: `make check`)
- [ ] Tests passing locally (command: `make check`)
- [ ] Static analysis/type checks passing (command: `make check`)
- [ ] Formatting applied (command: `make check`)
- [ ] Pre-commit hooks passing (command: `make check`)
- [ ] CI green or expected to pass
- [ ] No merge conflicts with base branch
- [ ] Documentation updated (README, docs/, examples)
- [ ] Changelog/version updated if applicable
- [ ] PR description includes summary, rationale, LLM involvement note
- [ ] Validation commands listed in PR description
