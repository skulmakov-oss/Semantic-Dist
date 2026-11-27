# 2. Projects, imports and packages

All commands run in PowerShell from `examples/qualification/ssf11` of the **Semantic source tag `v1.3.0-rc.2`** ([examples](https://github.com/skulmakov-oss/Semantic/tree/v1.3.0-rc.2/examples/qualification/ssf11)), with the **public rc.2 portable `smc.exe`** (fingerprint `4dfa17a48b77e39f`) on PATH. Outputs are the actual outputs. Absolute paths are shortened to `…`.

## 2.1 A project root
A project root is a directory with `semantic.toml`. Its `[project] entry` names the main module.

`f06_project/semantic.toml`:
```toml
[package]
name = "ssf11_project"

[project]
entry = "src/main.sm"
```
`f06_project/src/main.sm` imports a function from `lib.sm` in the same module root:
```
Import "lib.sm" { double }

fn main() {
    assert(double(21) == 42);
    return;
}
```
`f06_project/src/lib.sm`:
```
fn double(value: i32) -> i32 {
    return value + value;
}
```
```powershell
smc.exe check f06_project   # exit 0
smc.exe run f06_project     # exit 0
smc.exe test f06_project    # exit 0
```
Actual output of `test`:
```text
ok tests/double.sm
test result: ok. 1 passed
```

## 2.2 Local packages
A package has a `Semantic.package` manifest. Dependencies are explicit relative paths. There is no registry, no network fetch and no implicit search.

`f06_packages/app/Semantic.package` and `app/src/main.sm`:
```text
format 1
package app
manifest_dir .
module_root src
dep m mathlib ../mathlib
```
```
Import "m::main.sm"

fn main() {
    assert(triple(14) == 42);
    return;
}
```
```powershell
smc.exe run f06_packages/app               # exit 0
smc.exe package inspect f06_packages/app   # exit 0, prints a provenance JSON record
```
The record starts with `"fingerprint_algorithm": "fnv1a64-non-cryptographic"`. Its fingerprints are content identities, not security hashes.

## 2.3 What is rejected
| Case | Command | Exit | Actual message |
|---|---|---|---|
| Missing dependency (`dep missing missing ../does_not_exist`) | `smc.exe run f06_package_missing_dep` | 1 | `package module admission error: dependency alias 'missing' expected Semantic.package at '…\does_not_exist\Semantic.package'` |
| Entry escapes the root (`entry = "../main.sm"`) | `smc.exe check f06_project_entry_escape` | 1 | `failed to parse '…semantic.toml': project entry '../main.sm' must not escape the project root` |

**Not covered (not run):** top-level alias imports are a documented current limit (`examples/canonical/boundary_alias_import`, not a supported workflow). Normative rules: `docs/spec/project_model_v0.md` and `docs/spec/package_baseline_v0.md` at the tag.
