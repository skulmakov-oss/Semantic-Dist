# 5. Diagnostics and exit codes

All commands run in PowerShell from `examples/qualification/ssf11` of the **Semantic source tag `v1.3.0-rc.2`** ([examples](https://github.com/skulmakov-oss/Semantic/tree/v1.3.0-rc.2/examples/qualification/ssf11)), with the **public rc.2 portable `smc.exe`** (fingerprint `4dfa17a48b77e39f`) on PATH. Outputs are the actual outputs. Absolute paths are shortened to `…`.

## 5.1 Machine-readable diagnostics
`f02_quad_bare_condition/main.sm` uses a `quad` directly as an `if` condition:
```
fn main() {
    let state: quad = T;
    if state { return; }
    return;
}
```
```powershell
smc.exe check f02_quad_bare_condition/main.sm --format json   # exit 1
smc.exe explain E0201                                         # exit 0
```
Start of the JSON (schema `semantic.diagnostics`, version 1):
```json
{
  "schema": "semantic.diagnostics",
  "schema_version": 1,
  "status": "failed",
  "sources": [
    {
  …
```
`explain` prints:
```text
E0201: Type mismatch. Example: expected QVec/Bool, found other type.
```
Compare diagnostics by `code`, not by message wording.

## 5.2 Measured exit codes
| Situation | Example | Exit | Message |
|---|---|---|---|
| Success | `smc.exe run f06_project` | 0 | (none) |
| Compile-time error | `smc.exe check f02_quad_bare_condition/main.sm` | 1 | `Error [E0201]: …` |
| Failed assertion | `smc.exe run f10_runtime_failure/assertion_failure.sm` | 1 | `assertion failed` |
| Runtime trap | `smc.exe run f10_runtime_failure/division_by_zero.sm` | 1 | `runtime trap: DivisionByZero` |
| Quota exhausted | `smc.exe run f10_runtime_failure/step_quota.sm` | 1 | `quota exceeded: Steps limit=100000 used=100001` |
| Capability denied | chapter 3 | 1 | `… MissingCapability …` |
| Verifier rejection | chapter 4 | 1 | `verify error [UnsupportedVersion] …` |

Every failure measured for this manual exited with code 1. Other non-zero codes were not observed, and this manual does not claim them. The error-code list is `docs/ERROR_CODES.md` at the tag.
