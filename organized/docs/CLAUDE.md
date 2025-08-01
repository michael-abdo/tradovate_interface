# Expanded Prompt-Handling Checklist

## 1. Read the prompt

* **Action:** Read all new user text, attachments, and prior-turn context.
* **Goal:** Capture exact request, constraints, and deliverables.
* **Tip:** Reopen earlier messages if referenced.

## 2. Pause to understand intent & scope

* Restate the problem privately in your own words.
* Identify the **why** (business value, bug root cause, user pain).
* Consult `README.md`, `claude.md`, architecture docs, and code.
* **Exit criterion:** You can state the root issue + success definition in two sentences.

## 3. Draft a step-by-step plan

* Use an ordered list of atomic steps (code edits, tests, docs).
* Ensure alignment with

  * project vision & Claude rules 1-10
  * existing module boundaries & naming
  * the root cause from step 2
* **No-go:** speculative or “maybe useful later” code.

## 4. Verify the plan

* **Checklist:**

  * Matches prompt requirements exactly.
  * Adds no redundant code.
  * Preserves architecture, style, dependency policy.
* Revise if any mismatch.

## 5. Devil’s-advocate pass

* Ask: *Can this be solved with less code or config only?*
* Either simplify or justify current minimality.

## 6. Implement minimal changes

* Touch only necessary files.
* Prefer editing existing modules.
* If a new file is unavoidable, place it per README directory guidelines.
* Keep code clear: small functions, obvious names, minimal comments.

## 7. Generate detailed logs

* Create `logs/YYYY-MM-DD_HH-MM-SS/`.
* One log per core function (e.g., `start_services.log`).
* Each log:

  * Timestamps (`[%Y-%m-%d %H:%M:%S]`)
  * Section headers (`=== Starting Order Placement ===`)
  * Capture stdout & stderr; mark failures with `!!! ERROR !!!`.

## 8. Write unit tests

* One test file per touched module.
* Cover happy path **and** at least one failure case.
* Store in `tests/` mirroring source tree.
* Use mocks—no flaky IO or network.

## 9. Run tests

* Use project’s test runner (e.g., `pytest`).
* CI must fail on any test failure.

## 10. Inspect log output

* Look for uncaught exceptions, missing sections, unexpected warnings.
* If issues arise, jump back to **step 2** to reassess.

## 11. Loop until clean

* Proceed only when:

  * All tests green.
  * Logs show expected flow without errors.

## 12. Update documentation

* **README.md:** Add new behavior, config flags, endpoints.
* **Docstrings:** Update for any signature change.

## 13. Commit changes

```text
fix: <concise summary>

Rationale:
- Aligns with vision: <guideline # / long-term goal>
- Root cause: <brief>
- Changes: <files edited/added>
- Tests: <files> (all passing)
```

* Reference issue ID or prompt date for traceability.

---

Follow this checklist **verbatim** for every prompt to guarantee stability, clarity, and strategic alignment.
