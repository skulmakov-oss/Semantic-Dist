# 3. Capabilities and the host boundary

All commands run in PowerShell from `examples/qualification/ssf11` of the **Semantic source tag `v1.3.0-rc.2`** ([examples](https://github.com/skulmakov-oss/Semantic/tree/v1.3.0-rc.2/examples/qualification/ssf11)), with the **public rc.2 portable `smc.exe`** (fingerprint `4dfa17a48b77e39f`) on PATH. Outputs are the actual outputs. Absolute paths are shortened to `…`.

A program can touch the host only through capabilities that the selected **profile** grants. Every file path is resolved **inside `--root`**. Profiles used here: `pure` (no capabilities), `cli-read-only`, `cli-file-transform`.

`f08_file_transform/main.sm`:
```
fn main() {
    let input_path: text = args_read(0u32);
    let output_path: text = args_read(1u32);
    let input: text = fs_read_text(input_path);
    fs_write_text(output_path, "transformed:" + input);
    stdout_write("transform complete");
    return;
}
```

## 3.1 Allowed: read, transform, write
From `f08_file_transform/sandbox`, which contains `input.txt` with the text `hello`:
```powershell
smc.exe run ../main.sm --profile cli-file-transform --root . -- input.txt output.txt   # exit 0
Get-Content output.txt                                                                  # transformed:hello
```
stderr carries one audit line per capability decision. For example:
```text
schema=semantic.foundation.application.audit/0.1 seq=0 capability=args.read decision=allow bytes=9 path_hash=- payload_hash=aec75445d976fadd
schema=semantic.foundation.application.audit/0.1 seq=1 capability=args.read decision=allow bytes=10 path_hash=- payload_hash=64e66ea068934e52
```

## 3.2 Denied operations (each exits 1 and writes nothing)
| Case | Command | Actual denial |
|---|---|---|
| Write under a read-only profile | `smc.exe run ../main.sm --profile cli-read-only --root . -- input.txt output2.txt` | `capability FsWrite denied for FsWrite [prom.cap.manifest v1 MissingCapability]: manifest does not grant this capability` |
| Path escapes the root | `smc.exe run ../main.sm --profile cli-file-transform --root . -- input.txt ../escaped.txt` | `ABI FsWrite failure [InvalidInput]: path must be relative and must not contain parent traversal` |
| `pure` profile reading arguments | `smc.exe run ../main.sm --profile pure --root . -- input.txt output3.txt` | `capability ArgsRead denied for ArgsRead [prom.cap.manifest v1 MissingCapability]: manifest does not grant this capability` |

Afterwards the directory holds only `main.sm`, `sandbox/input.txt` and `sandbox/output.txt`. `output2.txt`, `output3.txt` and `../escaped.txt` were not created.

Normative rules: `docs/spec/controlled_application_boundary_v0.md` at the tag.
