# Contributing

PromptPro is maintained as a pragmatic CLI project. Contributions are welcome as long as they improve reliability, usability, or maintainability without diluting the core product idea.

## Development Setup

1. Fork the repository and clone your fork.
2. Create a virtual environment.
3. Install development dependencies.
4. Run the test suite before making changes.

```bash
git clone https://github.com/YOUR_USERNAME/PromptPro.git
cd PromptPro
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -e ".[dev]"
pre-commit install
python -m pytest -q -o addopts=
```

## Tooling

Use the same checks locally that CI uses for code quality:

```bash
black src tests
isort src tests
flake8 src tests
mypy src
python -m pytest -q -o addopts=
```

## Project Expectations

- Preserve existing behavior unless the change explicitly fixes a bug.
- Prefer small, reviewable pull requests over broad, unrelated edits.
- Add or update tests for any behavioral change.
- Keep user-facing text and documentation clear and consistent.
- Avoid introducing provider-specific assumptions into shared logic.

## Commit Style

Conventional Commits are preferred:

```text
feat(cli): add provider-aware model selection
fix(history): handle unreadable history file gracefully
docs(readme): clarify custom provider setup
```

Common types:

- `feat`
- `fix`
- `docs`
- `refactor`
- `test`
- `chore`

## Pull Requests

Each pull request should include:

- A concise summary of the change.
- The reason for the change.
- Notes on testing performed.
- Screenshots or terminal output when UI behavior changes.

Before opening a PR, verify:

- Tests pass locally.
- Formatting and linting checks pass.
- README or example files are updated if behavior changed.
- Secrets, local configs, and generated artifacts are not included.

## Reporting Issues

When filing an issue, include:

- What you expected to happen.
- What actually happened.
- Reproduction steps.
- Provider, model, and platform details when relevant.
- Logs or error output if available.

## Release Hygiene

If your change affects packaging, entrypoints, configuration, or public docs, check:

- `pyproject.toml`
- `.env.example`
- `README.md`
- `CHANGELOG.md`

## Questions

Use GitHub Issues for bugs and feature proposals. For implementation questions, open a discussion before starting large changes.
