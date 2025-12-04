# Semantic Commit Convention for Aurora Forester

## Commit Types

| Type | Description |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Formatting, no code change |
| `refactor` | Code refactoring |
| `perf` | Performance improvement |
| `test` | Adding/updating tests |
| `chore` | Maintenance tasks |
| `ci` | CI/CD changes |
| `build` | Build system changes |
| `revert` | Revert previous commit |
| `aurora` | Aurora-specific persona/behavior updates |
| `learn` | Learning system updates |
| `tune` | Model tuning/fine-tuning |

## Scopes

| Scope | Description |
|-------|-------------|
| `core` | Core Aurora system |
| `bot` | Discord bot |
| `learning` | Pattern learning/recursion |
| `agents` | Meta-agent spawning |
| `think-tank` | Idea capture system |
| `security` | Security model |
| `persona` | Persona/character updates |
| `workflows` | Workflow definitions |
| `models` | HuggingFace models |
| `context` | Context library |

## Examples

```bash
# Feature
git commit -m "feat(learning): add recursive pattern recognition"

# Aurora persona update
git commit -m "aurora(persona): refine remembering from the ether concept"

# Learning system
git commit -m "learn(patterns): implement observation-based adaptation"

# Model tuning
git commit -m "tune(models): integrate HuggingFace sentiment model"
```

## Commit Message Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

- **Subject**: Imperative mood, no period, max 72 chars
- **Body**: Explain the "why" not the "what"
- **Footer**: Breaking changes, issue references
