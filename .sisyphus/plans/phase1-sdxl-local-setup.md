# Phase 1 SDXL Local Setup

## TL;DR

> **Quick Summary**: Stabilize the already-working local SDXL single-image baseline into a reproducible, testable, workflow-aligned Phase 1 foundation.
>
> **Deliverables**:
> - Reproducible local setup instructions and dependency manifest
> - Verified single-image SDXL GPU/CPU generation baseline
> - Test and verification workflow suitable for iterative execution
> - OpenCode + Superpowers workflow alignment for Phase 1 execution
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Task 1 -> Task 3 -> Task 6 -> Final Verification

---

## Context

### Original Request
Support custom prompt/resolution and batch generation for local SDXL/LoRA over time, but start small. The user asked to complete the entire first phase only, with the environment already working, tests/verification included, and the process aligned to the `obra/superpowers` standard workflow.

### Interview Summary
**Key Discussions**:
- The repo was intentionally reset to a minimal baseline.
- A single-image SDXL script already exists and has been manually run successfully on GPU.
- Strict editor diagnostics were important, so the starter script was adjusted to behave better under strict checking.
- Testing and verification must be built into the workflow, not left until the end.
- The user wants a practical iterative workflow, not a premature large project structure.

**Research Findings**:
- Current repo contains `scripts/generate_sdxl.py`, `tests/test_generate_sdxl.py`, `outputs/`, and a minimal `README.md`.
- There is no dependency manifest or CI/workflow automation yet.
- Superpowers upstream workflow is: brainstorming -> writing-plans -> subagent-driven-development / executing-plans -> test-driven-development -> requesting-code-review -> finishing-a-development-branch.
- OpenCode usage requires Superpowers to be installed via `opencode.json` plugin config and verified after restart.

### Metis Review
**Identified Gaps** (addressed):
- Formal Metis output was unavailable due repeated tool timeout; equivalent gap coverage was resolved conservatively in this plan by locking Phase 1 scope to reproducibility, verification, and workflow setup only.
- Potential scope creep into batch generation, LoRA, API work, and larger architecture was explicitly excluded.

---

## Work Objectives

### Core Objective
Turn the current one-off working SDXL script into a reliable Phase 1 baseline that can be reproduced, tested, verified, and executed through the intended Superpowers-style workflow.

### Concrete Deliverables
- A dependency/install manifest for the current local SDXL baseline
- A verified README/setup flow covering environment, test, and generation commands
- Expanded automated verification for the existing CLI baseline
- Minimal workflow wiring/instructions for OpenCode + Superpowers usage in this repo

### Definition of Done
- [ ] `python -m unittest discover -v` passes in the project environment
- [ ] `python scripts/generate_sdxl.py --help` succeeds
- [ ] A documented end-to-end generation command succeeds on the configured machine
- [ ] Superpowers installation/usage steps are documented and verifiable for this repo

### Must Have
- Preserve the current single-image SDXL baseline
- Keep Phase 1 small and reproducible
- Include automated verification plus manual QA
- Include workflow guidance for iterative execution

### Must NOT Have (Guardrails)
- No batch generation implementation in Phase 1
- No LoRA loading implementation in Phase 1
- No API/server layer in Phase 1
- No speculative large-scale folder architecture beyond what Phase 1 needs

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** for acceptance checks wherever possible; manual QA is limited to command execution and output inspection by the executing agent.

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: Tests-after (baseline exists; expand from current tests)
- **Framework**: `unittest`
- **Agent-Executed QA**: ALWAYS

### QA Policy
Every task must include agent-executed QA scenarios. Evidence paths may use terminal output and generated files in `outputs/` and `.sisyphus/evidence/` where relevant.

- **CLI**: Use Bash to run help/test/generation commands and inspect outputs
- **Config/Docs**: Use Bash + Read to validate commands exist and documentation matches actual behavior
- **Workflow Setup**: Use Read/Bash to confirm plugin config, restart instructions, and verification steps are present

---

## Execution Strategy

### Parallel Execution Waves

> Maximize throughput while keeping the current repo minimal.

```
Wave 1 (Start Immediately - reproducibility + verification baseline):
├── Task 1: Lock dependency manifest and version guidance [quick]
├── Task 2: Expand README into reproducible Phase 1 runbook [writing]
├── Task 3: Strengthen automated tests for current CLI behavior [quick]
└── Task 4: Add basic editor/workspace guidance for strict Python checking [quick]

Wave 2 (After Wave 1 - workflow alignment):
├── Task 5: Add OpenCode/Superpowers project setup instructions [writing]
├── Task 6: Add executable verification commands and evidence expectations [quick]
└── Task 7: Add lightweight automation entrypoint for repeatable Phase 1 checks [quick]

Wave 3 (After Wave 2 - integration hardening):
├── Task 8: Validate CPU fallback and GPU happy-path documentation against current script [quick]
├── Task 9: Tighten README/task flow to match Superpowers iterative execution sequence [writing]
└── Task 10: Final Phase 1 repo hygiene pass (ignore rules, outputs policy, command clarity) [quick]

Wave FINAL (After ALL tasks — 4 parallel reviews, then user okay):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)
-> Present results -> Get explicit user okay

Critical Path: Task 1 -> Task 3 -> Task 6 -> Task 9 -> F1-F4 -> user okay
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 4
```

### Dependency Matrix

- **1**: - - 6, 9, 10, 1
- **2**: - - 9, 10, 1
- **3**: 1 - 6, 8, 2
- **4**: - - 10, 1
- **5**: - - 9, 2
- **6**: 1, 3 - 9, FINAL, 2
- **7**: 3 - 10, FINAL, 2
- **8**: 3 - FINAL, 3
- **9**: 2, 5, 6 - FINAL, 3
- **10**: 1, 2, 4, 7 - FINAL, 3

### Agent Dispatch Summary

- **1**: **4** - T1 → `quick`, T2 → `writing`, T3 → `quick`, T4 → `quick`
- **2**: **3** - T5 → `writing`, T6 → `quick`, T7 → `quick`
- **3**: **3** - T8 → `quick`, T9 → `writing`, T10 → `quick`
- **FINAL**: **4** - F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [x] 1. Lock dependency manifest and version guidance

  **What to do**:
  - Add a minimal dependency manifest for the currently working Phase 1 baseline.
  - Record the known-good PyTorch/CUDA combination that was manually verified on the current GPU.
  - Make the install path reproducible without requiring users to rediscover compatibility issues.

  **Must NOT do**:
  - Do not add optional Phase 2/3 dependencies for LoRA, API servers, or batch orchestration.
  - Do not claim universal GPU compatibility beyond the documented verified environment.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Small, concrete setup hardening task with limited files.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: No UI work involved.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4)
  - **Blocks**: 6, 9, 10
  - **Blocked By**: None

  **References**:
  - `scripts/generate_sdxl.py` - Current runtime dependencies and CLI behavior to mirror in manifest instructions.
  - `README.md` - Current minimal project statement that will need reproducible setup detail.

  **Acceptance Criteria**:
  - [ ] A dependency manifest exists in the repo root.
  - [ ] The manifest/install guidance matches the currently verified torch CUDA build.
  - [ ] Running install instructions does not require hidden assumptions outside the documented environment.

  **QA Scenarios**:
  ```
  Scenario: Dependency manifest matches current baseline
    Tool: Bash
    Preconditions: Repo root, active project environment
    Steps:
      1. Read the manifest and compare listed packages to the imports used by scripts/generate_sdxl.py.
      2. Run the documented verification command(s) from the manifest or README.
      3. Confirm no undocumented required package remains missing.
    Expected Result: The documented Phase 1 dependency set is sufficient for tests/help execution.
    Failure Indicators: Missing import at runtime, undocumented dependency, or mismatched torch guidance.
    Evidence: .sisyphus/evidence/task-1-dependency-baseline.txt

  Scenario: Unsupported scope packages are absent
    Tool: Read
    Preconditions: Manifest exists
    Steps:
      1. Inspect the dependency manifest.
      2. Confirm there are no Phase 2/3-only packages such as API server frameworks or LoRA-specific extras unless already required by current baseline.
    Expected Result: Manifest remains tightly scoped to Phase 1.
    Evidence: .sisyphus/evidence/task-1-scope-check.txt
  ```

  **Commit**: YES
  - Message: `chore(phase1): lock dependency baseline`
  - Files: `requirements.txt`, `README.md`
  - Pre-commit: `python -m unittest discover -v`

- [x] 2. Expand README into reproducible Phase 1 runbook

  **What to do**:
  - Turn the minimal README into a clear Phase 1 runbook.
  - Document environment activation, install, test, help, CPU run, and GPU run commands.
  - Keep the document intentionally small and focused on current baseline usage.

  **Must NOT do**:
  - Do not document unimplemented Phase 2/3 features.
  - Do not overload the README with architecture speculation.

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Primary output is concise technical documentation.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `dev-browser`: Not needed for local markdown docs.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4)
  - **Blocks**: 9, 10
  - **Blocked By**: None

  **References**:
  - `README.md` - Existing starting point to expand.
  - `scripts/generate_sdxl.py` - Source of actual supported CLI arguments.
  - `tests/test_generate_sdxl.py` - Existing verification command baseline.

  **Acceptance Criteria**:
  - [ ] README includes exact commands for install, test, help, CPU generation, and GPU generation.
  - [ ] README reflects only implemented behavior.
  - [ ] A new user can follow the Phase 1 runbook without needing unstated project context.

  **QA Scenarios**:
  ```
  Scenario: README commands match real CLI behavior
    Tool: Bash
    Preconditions: Updated README present
    Steps:
      1. Copy the documented help command from README.
      2. Run it exactly as written.
      3. Confirm the script prints CLI help successfully.
    Expected Result: The documented command executes without modification.
    Failure Indicators: README command mismatch, wrong paths, or unsupported flags.
    Evidence: .sisyphus/evidence/task-2-readme-help.txt

  Scenario: README does not claim missing features
    Tool: Read
    Preconditions: Updated README present
    Steps:
      1. Inspect README sections describing scope.
      2. Confirm batch generation, LoRA, or API features are not described as available.
    Expected Result: README stays Phase 1-only.
    Evidence: .sisyphus/evidence/task-2-scope-check.txt
  ```

  **Commit**: YES
  - Message: `docs(phase1): add reproducible runbook`
  - Files: `README.md`
  - Pre-commit: `python scripts/generate_sdxl.py --help`

- [x] 3. Strengthen automated tests for current CLI behavior

  **What to do**:
  - Extend current unit coverage for the existing CLI baseline.
  - Add tests for device resolution and other critical current behaviors.
  - Preserve mocked execution so tests remain lightweight.

  **Must NOT do**:
  - Do not introduce tests that require actual model downloads.
  - Do not add speculative tests for future batch/LoRA/API features.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Focused Python test expansion in a small existing test suite.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `playwright`: Not relevant to CLI unit tests.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4)
  - **Blocks**: 6, 7, 8
  - **Blocked By**: 1

  **References**:
  - `tests/test_generate_sdxl.py` - Current test suite to extend.
  - `scripts/generate_sdxl.py` - Source of current CLI behavior.

  **Acceptance Criteria**:
  - [ ] Tests cover argument parsing baseline plus device resolution behavior.
  - [ ] `python -m unittest discover -v` passes.
  - [ ] Tests remain fast and do not hit external model downloads.

  **QA Scenarios**:
  ```
  Scenario: Unit suite passes locally
    Tool: Bash
    Preconditions: Test updates complete
    Steps:
      1. Run `python -m unittest discover -v` from repo root.
      2. Inspect the output for failures or errors.
    Expected Result: All tests pass.
    Failure Indicators: Any failing test, import error, or hidden runtime dependency.
    Evidence: .sisyphus/evidence/task-3-unittest.txt

  Scenario: Tests remain isolated from model downloads
    Tool: Read
    Preconditions: Test file updated
    Steps:
      1. Inspect test code for direct pipeline/model download calls.
      2. Confirm build_pipeline or runtime-heavy paths remain mocked.
    Expected Result: Tests stay lightweight.
    Evidence: .sisyphus/evidence/task-3-isolation.txt
  ```

  **Commit**: YES
  - Message: `test(phase1): harden cli baseline coverage`
  - Files: `tests/test_generate_sdxl.py`
  - Pre-commit: `python -m unittest discover -v`

- [x] 4. Add basic editor/workspace guidance for strict Python checking

  **What to do**:
  - Provide minimal repo-level guidance or configuration so strict-checking expectations are explicit.
  - Keep the approach as narrow as possible: interpreter clarity and any justified diagnostic guidance.

  **Must NOT do**:
  - Do not suppress unrelated diagnostics broadly.
  - Do not create large editor-specific config beyond current need.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Small configuration/documentation task.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: Not relevant.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3)
  - **Blocks**: 10
  - **Blocked By**: None

  **References**:
  - `scripts/generate_sdxl.py` - Current strict-checking-sensitive file.
  - Upstream context from user reports about strict Pylance mode.

  **Acceptance Criteria**:
  - [ ] The repo clearly states how to select the intended Python interpreter or workspace behavior.
  - [ ] Any added config is narrowly scoped and justified by the current strict-checking issues.

  **QA Scenarios**:
  ```
  Scenario: Interpreter/workspace guidance is actionable
    Tool: Read
    Preconditions: Config or docs added
    Steps:
      1. Inspect the added guidance/config.
      2. Confirm it explicitly points to the intended environment and does not over-configure unrelated settings.
    Expected Result: A developer can align VSCode/editor behavior with the project environment.
    Evidence: .sisyphus/evidence/task-4-editor-guidance.txt

  Scenario: Strict-checking guidance is limited in scope
    Tool: Read
    Preconditions: Config or docs added
    Steps:
      1. Inspect any added workspace settings or pyright/pylance config.
      2. Confirm only current Phase 1 issues are addressed.
    Expected Result: No blanket suppression beyond justified cases.
    Evidence: .sisyphus/evidence/task-4-scope.txt
  ```

  **Commit**: YES
  - Message: `chore(editor): clarify strict python setup`
  - Files: `.vscode/settings.json` or `README.md`
  - Pre-commit: `python -m py_compile scripts/generate_sdxl.py tests/test_generate_sdxl.py`

- [x] 5. Add OpenCode/Superpowers project setup instructions

  **What to do**:
  - Document the exact project-level OpenCode plugin setup required for Superpowers.
  - Include verification instructions so missing skill discovery can be diagnosed early.

  **Must NOT do**:
  - Do not assume globally installed plugin state.
  - Do not document unavailable skills as guaranteed unless verification steps are provided.

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: This is workflow/process documentation.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not a git operation task.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7)
  - **Blocks**: 9
  - **Blocked By**: None

  **References**:
  - `https://raw.githubusercontent.com/obra/superpowers/main/.opencode/INSTALL.md` - OpenCode installation instructions.
  - `https://raw.githubusercontent.com/obra/superpowers/main/README.md` - Standard workflow sequence.

  **Acceptance Criteria**:
  - [ ] Repo docs explain how to configure `opencode.json` for Superpowers.
  - [ ] Repo docs include a concrete verification step for skill discovery.
  - [ ] Repo docs explain the intended Phase 1 execution flow in OpenCode terms.

  **QA Scenarios**:
  ```
  Scenario: OpenCode plugin instructions are complete
    Tool: Read
    Preconditions: Workflow docs updated
    Steps:
      1. Inspect the documented OpenCode setup steps.
      2. Confirm they include plugin config, restart, and verification guidance.
    Expected Result: Setup instructions are sufficient to diagnose missing skill discovery.
    Evidence: .sisyphus/evidence/task-5-superpowers-setup.txt

  Scenario: Workflow docs avoid unsupported guarantees
    Tool: Read
    Preconditions: Workflow docs updated
    Steps:
      1. Inspect wording around available skills and loops.
      2. Confirm instructions describe verification, not blind assumptions.
    Expected Result: Documentation is accurate to real OpenCode behavior.
    Evidence: .sisyphus/evidence/task-5-scope.txt
  ```

  **Commit**: YES
  - Message: `docs(workflow): add opencode superpowers setup`
  - Files: `README.md`, `opencode.json`
  - Pre-commit: `python scripts/generate_sdxl.py --help`

- [x] 6. Add executable verification commands and evidence expectations

  **What to do**:
  - Make verification explicit and repeatable.
  - Define which commands must be run for Phase 1 and what outputs count as success.
  - Ensure tests and manual CLI validation are both captured.

  **Must NOT do**:
  - Do not rely on vague “works on my machine” statements.
  - Do not include verification for unimplemented features.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Small task focused on command-level verification.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `review-work`: Final review is a separate phase.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 7)
  - **Blocks**: 9, FINAL
  - **Blocked By**: 1, 3

  **References**:
  - `tests/test_generate_sdxl.py` - Automated verification baseline.
  - `scripts/generate_sdxl.py` - Manual QA command target.
  - `README.md` - Documentation surface for executable commands.

  **Acceptance Criteria**:
  - [ ] The repo defines a small set of canonical Phase 1 verification commands.
  - [ ] Each command has an expected success signal.
  - [ ] Manual GPU/CPU verification paths are clearly separated.

  **QA Scenarios**:
  ```
  Scenario: Canonical verification commands execute
    Tool: Bash
    Preconditions: Verification docs updated
    Steps:
      1. Run the documented unit-test command.
      2. Run the documented CLI help command.
      3. Confirm both succeed exactly as documented.
    Expected Result: Core verification commands are executable and stable.
    Failure Indicators: Command mismatch, missing dependencies, wrong paths.
    Evidence: .sisyphus/evidence/task-6-commands.txt

  Scenario: Success criteria are concrete
    Tool: Read
    Preconditions: Verification docs updated
    Steps:
      1. Inspect the success expectations for each command.
      2. Confirm they use observable outputs rather than vague language.
    Expected Result: Verification language is binary and executable.
    Evidence: .sisyphus/evidence/task-6-criteria.txt
  ```

  **Commit**: YES
  - Message: `docs(phase1): define verification flow`
  - Files: `README.md`
  - Pre-commit: `python -m unittest discover -v`

- [x] 7. Add lightweight automation entrypoint for repeatable Phase 1 checks

  **What to do**:
  - Add one small repeatable command entrypoint for Phase 1 verification.
  - Keep it minimal: it should orchestrate the current baseline checks, not build a full task runner ecosystem.

  **Must NOT do**:
  - Do not add a large automation framework.
  - Do not include long-running image generation by default if it makes the baseline cumbersome.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Focused automation helper.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `playwright`: Not needed.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6)
  - **Blocks**: 10, FINAL
  - **Blocked By**: 3

  **References**:
  - `tests/test_generate_sdxl.py` - Existing test command.
  - `README.md` - Surface where the repeatable entrypoint should be documented.

  **Acceptance Criteria**:
  - [ ] A single documented command or script runs the canonical lightweight Phase 1 checks.
  - [ ] The command finishes quickly and does not require model download/generation by default.

  **QA Scenarios**:
  ```
  Scenario: Repeatable Phase 1 check command works
    Tool: Bash
    Preconditions: Automation entrypoint added
    Steps:
      1. Run the documented Phase 1 check command exactly as written.
      2. Observe command output and exit status.
    Expected Result: The check command completes successfully and covers the intended lightweight baseline.
    Failure Indicators: Missing script, failing command, or unexpected heavyweight behavior.
    Evidence: .sisyphus/evidence/task-7-check-command.txt

  Scenario: Automation remains lightweight
    Tool: Read
    Preconditions: Automation entrypoint added
    Steps:
      1. Inspect the command/script implementation.
      2. Confirm it runs tests/help checks rather than forcing full model generation.
    Expected Result: Baseline automation stays fast and Phase 1-sized.
    Evidence: .sisyphus/evidence/task-7-scope.txt
  ```

  **Commit**: YES
  - Message: `chore(phase1): add lightweight verification entrypoint`
  - Files: `scripts/` or repo root helper file
  - Pre-commit: run the new verification entrypoint

- [x] 8. Validate CPU fallback and GPU happy-path documentation against current script

  **What to do**:
  - Ensure the documented CPU and GPU usage paths match the actual current script behavior.
  - Capture the known limitations clearly, especially around environment-specific GPU support.

  **Must NOT do**:
  - Do not add runtime fallback behavior if it is not already implemented unless separately specified.
  - Do not overgeneralize hardware compatibility claims.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Focused consistency check between code and docs.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `oracle`: Overkill for this bounded task.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 9, 10)
  - **Blocks**: FINAL
  - **Blocked By**: 3

  **References**:
  - `scripts/generate_sdxl.py` - Actual device behavior source.
  - `README.md` - Documentation target.

  **Acceptance Criteria**:
  - [ ] Docs accurately distinguish CPU fallback usage and GPU happy-path usage.
  - [ ] Docs do not promise automatic GPU recovery behavior that the script does not implement.

  **QA Scenarios**:
  ```
  Scenario: CPU and GPU commands are both documented correctly
    Tool: Read
    Preconditions: README updated
    Steps:
      1. Inspect documented CPU and GPU examples.
      2. Compare them against the current CLI arguments and known runtime behavior.
    Expected Result: Documentation matches implemented behavior.
    Evidence: .sisyphus/evidence/task-8-device-docs.txt

  Scenario: GPU path still works on configured machine
    Tool: Bash
    Preconditions: Verified GPU environment
    Steps:
      1. Run the documented GPU generation command.
      2. Confirm an image is written to outputs/.
    Expected Result: GPU happy-path succeeds on the documented environment.
    Evidence: .sisyphus/evidence/task-8-gpu-run.txt
  ```

  **Commit**: YES
  - Message: `docs(device): align cpu gpu usage`
  - Files: `README.md`
  - Pre-commit: documented CPU/GPU commands

- [x] 9. Tighten README/task flow to match Superpowers iterative execution sequence

  **What to do**:
  - Align the repo’s workflow documentation to the practical subset of the Superpowers sequence relevant to this project.
  - Make it obvious how Phase 1 moves from planning to execution to verification.

  **Must NOT do**:
  - Do not pretend unavailable skills are active unless setup/verification says so.
  - Do not document phases beyond current Phase 1 baseline.

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Workflow documentation alignment task.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 8, 10)
  - **Blocks**: FINAL
  - **Blocked By**: 2, 5, 6

  **References**:
  - `https://raw.githubusercontent.com/obra/superpowers/main/README.md` - Upstream workflow sequence.
  - `README.md` - Local workflow documentation surface.
  - `.sisyphus/plans/phase1-sdxl-local-setup.md` - Execution source of truth.

  **Acceptance Criteria**:
  - [ ] Local docs explain the intended order of planning, execution, testing, review, and completion for Phase 1.
  - [ ] Local docs remain honest about current environment/plugin limitations.

  **QA Scenarios**:
  ```
  Scenario: Workflow sequence is understandable from docs alone
    Tool: Read
    Preconditions: Workflow docs updated
    Steps:
      1. Read the workflow section in README.
      2. Confirm the sequence from setup to verification is explicit and coherent.
    Expected Result: A user can follow the intended Phase 1 workflow without extra explanation.
    Evidence: .sisyphus/evidence/task-9-workflow.txt

  Scenario: Workflow docs stay Phase 1-scoped
    Tool: Read
    Preconditions: Workflow docs updated
    Steps:
      1. Inspect workflow docs for references to later-phase features.
      2. Confirm later-phase work is not presented as current baseline.
    Expected Result: Workflow remains strictly Phase 1.
    Evidence: .sisyphus/evidence/task-9-scope.txt
  ```

  **Commit**: YES
  - Message: `docs(workflow): align phase1 execution sequence`
  - Files: `README.md`
  - Pre-commit: manual read-through + command spot checks

- [x] 10. Final Phase 1 repo hygiene pass

  **What to do**:
  - Clean up ignore rules, generated output policy, and command clarity so the repo is usable as a stable baseline.
  - Keep this limited to obvious Phase 1 hygiene.

  **Must NOT do**:
  - Do not restructure the repo into a large architecture.
  - Do not remove useful sample output or evidence without a clear policy replacement.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Small repo hygiene and consistency pass.
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `ai-slop-remover`: Not needed if changes are already tightly scoped.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 8, 9)
  - **Blocks**: FINAL
  - **Blocked By**: 1, 2, 4, 7

  **References**:
  - Repo root layout - Current minimal structure to preserve.
  - `outputs/` - Existing generated artifacts and policy target.
  - `.gitignore` if present or to be added - Ignore policy target.

  **Acceptance Criteria**:
  - [ ] Repo distinguishes source, generated outputs, and planning artifacts cleanly.
  - [ ] Output handling policy is clear and consistent.
  - [ ] No unnecessary directories/files are introduced.

  **QA Scenarios**:
  ```
  Scenario: Repo hygiene is coherent
    Tool: Read
    Preconditions: Hygiene changes complete
    Steps:
      1. Inspect repo root files and updated docs/config.
      2. Confirm generated outputs and baseline source files are handled consistently.
    Expected Result: Repo remains minimal and understandable.
    Evidence: .sisyphus/evidence/task-10-hygiene.txt

  Scenario: No premature structure was introduced
    Tool: Read
    Preconditions: Hygiene changes complete
    Steps:
      1. Compare repo structure before and after changes.
      2. Confirm no large Phase 2/3 scaffolding was added.
    Expected Result: Repo stays intentionally small.
    Evidence: .sisyphus/evidence/task-10-scope.txt
  ```

  **Commit**: YES
  - Message: `chore(phase1): finalize repo hygiene`
  - Files: repo root minimal set
  - Pre-commit: `python -m unittest discover -v`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. Verify each Phase 1 deliverable exists, and verify no batch generation, LoRA, or API work was added. Confirm documented commands match the actual repo state.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run test and command checks, inspect changed files for unnecessary abstraction, dead instructions, stale commands, and strict-checking regressions.
  Output: `Build [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high`
  Execute documented Phase 1 commands from a clean shell: tests, help output, and one generation command on the configured environment. Verify outputs and evidence paths.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  Verify the repo changes only harden Phase 1 baseline setup/workflow. Reject any premature batch, LoRA, or API work.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **1**: `chore(phase1): lock local SDXL setup baseline` - manifest/docs/test files, `python -m unittest discover -v`
- **2**: `docs(workflow): add superpowers phase1 execution flow` - workflow docs/config, verification commands

---

## Success Criteria

### Verification Commands
```bash
python -m unittest discover -v
python scripts/generate_sdxl.py --help
python scripts/generate_sdxl.py --device cpu --prompt "phase1 smoke test"
# On configured GPU machine:
python scripts/generate_sdxl.py --device cuda --prompt "phase1 smoke test"
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] Automated tests pass
- [ ] Manual generation command succeeds on documented environment
- [ ] Superpowers/OpenCode Phase 1 workflow is documented and verifiable
