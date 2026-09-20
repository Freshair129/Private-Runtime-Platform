# Git & Workflow Standards

## Branching Strategy

- `main`: Production-ready code.
- `develop`: Integration branch for sprints.
- `feat/PRP-XXX-description`: Feature branches.
- `fix/PRP-XXX-description`: Bug fix branches.

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `domain(scope): ...`
- `feat(scope): ...`
- `fix(scope): ...`
- `docs(scope): ...`
- `refactor(scope): ...`
- `chore(scope): ...`

*Include Task ID (e.g., `PRP-P1S101`) in the footer or body of the commit.*

## Pull Requests (PRs)

- **One Task per PR**: Do not bundle multiple tasks into one PR.
- **Evidence Required**: Screenshots or videos for UI changes; test logs for logic.
- **Checklist**: Must include the DoD checklist in the PR description.

## DDD Workflow Hook

Before any PR:

1. Ensure `AGENTS.md` is updated if architectural changes occurred.
2. Ensure `RCA` or `Spec` docs are committed alongside the code.
