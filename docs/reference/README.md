# Semantic reference (v1.3.0-rc.2)

A user-facing **reference**, kept separate from the normative contracts. It never overrides them: the normative specifications at tag [`v1.3.0-rc.2`](https://github.com/skulmakov-oss/Semantic/tree/v1.3.0-rc.2/docs/spec) win on any difference. Differences found while writing are listed in [findings.md](findings.md) and are **not** silently corrected.

- [language.md](language.md): language reference, by topic.
- [quad_logic.md](quad_logic.md): four-valued logic reference; every operator cell is observed.
- [findings.md](findings.md): unresolved discrepancies and observations.
- [observations.md](observations.md): the exact probe commands and results behind the "observed" statements.

Pinned identities: Semantic tag `v1.3.0-rc.2` = `98f9db199b28d6b126873f8f445aaff49b83d674`; tool = public rc.2 portable `smc.exe`, source fingerprint `4dfa17a48b77e39f`.

## Evidence levels used on every page
| Level | Meaning | Not the same as |
|---|---|---|
| **Normative** | Stated in a normative specification at tag `v1.3.0-rc.2` (`docs/spec/*.md`). | a design note, a research note, or this reference |
| **Declared status** | The release state the shipped tool reports (`smc language describe`) or a status inventory at the tag. | formal qualification of a feature you rely on |
| **Observed** | Measured here with the public rc.2 `smc.exe` (fingerprint `4dfa17a48b77e39f`). A passing example shows the observed behaviour of that binary. | **qualification**: a formal status granted by the project's qualification process |
| **Derived** | Follows mathematically from normative formulas; not a separate contract. | normative |
| **Not verified** | Cited but not executed or cross-checked here. | false |

## Coverage
| Area | Normative source | Observed here | Not verified here |
|---|---|---|---|
| Quad values, operators, Boolean boundary | yes | all 4×4 / 4×1 cells (544 runs) | packed source types (none exist in source) |
| Declarations, types, control flow | yes | the forms in manual chapter 1 | loops (`loop`/`break`/`continue`/`for`), tuples, enums, closures, generics |
| Modules, projects, packages | yes | observations.md | alias imports (documented limit) |
| Capabilities | yes | observations.md | profiles other than `pure` / `cli-read-only` / `cli-file-transform` |
| Diagnostics, artifacts | yes | observations.md | every error code |
