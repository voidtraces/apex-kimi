# Claude Code Native Systems — when to invoke them in an output prompt

An elite prompt for Claude Code doesn't just describe a task; it switches on the right native machinery. The **Approach** section of a generated prompt should name the relevant system below when it applies.

## Plan mode
Recommend when the task is **multi-step, irreversible, or high-stakes** (migrations, deletes, broad refactors). Phrase: "Enter plan mode first; present the plan before editing."
Skip for trivial, single-file, reversible edits.

## Explore / subagents
Recommend when the task touches **unfamiliar or large areas** of the codebase. Phrase: "Use the Explore agent to map X before changing it."
If a `graphify-out/` graph exists, prefer: "Query the graph for X."

## Skills
Point at the skill that matches the work:
- **test-driven-development** — for new features/bugfixes with testable behavior.
- **systematic-debugging** — for diagnosing a failure (before proposing fixes).
- **verification-before-completion** — always, for the done-proof.
Phrase: "Use the test-driven-development skill."

## Verification (always)
Every output prompt must require Claude to **prove** completion: run the tests, show the command output, confirm the success criteria. Phrase: "Before claiming done, run `<cmd>` and paste the output."

## Parallelism
Recommend dispatching parallel subagents only when there are **2+ genuinely independent** subtasks. Otherwise prefer sequential reasoning in one context.

## What NOT to inject
- Don't add "think step by step" — Claude plans natively.
- Don't pre-plan a task that should use plan mode; tell it to plan instead.
- Don't enumerate file traversal steps Explore would do better.
