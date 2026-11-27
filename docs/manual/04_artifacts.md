# 4. Artifacts: compile, verify, hash, run

All commands run in PowerShell from `examples/qualification/ssf11` of the **Semantic source tag `v1.3.0-rc.2`** ([examples](https://github.com/skulmakov-oss/Semantic/tree/v1.3.0-rc.2/examples/qualification/ssf11)), with the **public rc.2 portable `smc.exe`** (fingerprint `4dfa17a48b77e39f`) on PATH. Outputs are the actual outputs. Absolute paths are shortened to `…`.

Compiling is **not** verification. A `.smc` artifact runs only after the verifier admits it.

```powershell
smc.exe compile f01_minimal/main.sm -o minimal.smc   # compiled 'f01_minimal/main.sm' -> 'minimal.smc' (127 bytes)
smc.exe verify minimal.smc                         # verified 'minimal.smc' (1 function(s), header=SEMCOD22, epoch=0.23)
smc.exe artifact hash minimal.smc                  # sha256:4ca8a7ec7ebf776cbec3b97c1896b783b933ff31f69dc077e0396dad1cdde075
smc.exe artifact inspect minimal.smc               # header, capabilities, functions, signing state
smc.exe disasm minimal.smc                         # bytecode listing
smc.exe run-smc minimal.smc                        # exit 0
```

Start of the actual `disasm` output:
```text
SEMCOD22 epoch=0.23 caps=0x0fffffff
fn main: code=54 bytes, strings=0, debug=0
  0000: LOAD_I32 r0, 1
  0007: LOAD_I32 r1, 1
  000e: ADD_I32 r2, r0, r1
```

## 4.1 Pinning the exact bytes
`run-smc --expect-sha256` refuses any artifact whose identity differs. It needs an explicit profile and root:
```powershell
$h = (smc.exe artifact hash minimal.smc)
smc.exe run-smc minimal.smc --expect-sha256 $h --profile pure --root .   # exit 0
```

## 4.2 Rejections
| Case | Command | Exit | Actual message |
|---|---|---|---|
| Wrong identity | `smc.exe run-smc minimal.smc --expect-sha256 sha256:0000…0000 --profile pure --root .` | 1 | `artifact identity mismatch: expected sha256:0000…, found sha256:4ca8a7ec…` |
| Unsupported header | `smc.exe verify f09_verifier_rejection/unsupported_header.smc` | 1 | `verify error [UnsupportedVersion] @0x0000: unsupported SemCode header 'NOTSEMCO'` |

Artifacts are **unsigned**; the SHA-256 is an identity, not a trust signature. Normative rules: `docs/spec/verifier.md`, `docs/spec/semcode.md` at the tag (see [docs/spec](https://github.com/skulmakov-oss/Semantic/tree/v1.3.0-rc.2/docs/spec)).
