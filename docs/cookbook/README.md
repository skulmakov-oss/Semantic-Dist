# Semantic Cookbook (v1.3.0-rc.2)

**Status:** non-normative how-to recipes.

**Identity:**
- Semantic-Dist release `v1.3.0-rc.2` (unsigned Windows x64 developer preview), with its portable `smc.exe` (source fingerprint `4dfa17a48b77e39f`).
- Frozen self-hosted compiler `semantic-selfhost-compiler-C1.smc` (sha256 `2bfd56e1…e939`).
- Upstream source pinned at Semantic `98f9db19`.

**How the outputs were produced:** every recipe was run with these binaries, each in a fresh empty directory, under PowerShell 7 (`pwsh`) with `smc.exe` on `PATH`. The outputs below are copied from those runs; directory prefixes are shortened to `…`. A run that matches is *observed* behaviour of these binaries; it is **not** a formal qualification.

**Running the steps:** each step was run as one script fragment, `pwsh -NoProfile -Command "<step>"`, so the exit code shown is that command's exit code. Some steps end with `exit`. Typed into an interactive PowerShell window, `exit` closes the window; run such steps as a script, or with `pwsh -NoProfile -Command`. Start each recipe in a new empty folder, so that no output from an earlier run is reused.

Normative sources stay authoritative:
- Semantic [`docs/spec/cli.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/cli.md) and [`controlled_application_boundary_v0.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/controlled_application_boundary_v0.md) at the tag;
- for C1, Semantic-Language [`compiler/driver.sm` @ `5b404e5`](https://github.com/skulmakov-oss/Semantic-Language/blob/5b404e5/compiler/driver.sm).

| # | Recipe | Capabilities used | Negative control |
|---|---|---|---|
| 01 | [Check a download against the release SHA256SUMS](#01-check-a-download-against-the-release-sha256sums) | none (PowerShell only) | yes |
| 02 | [Compile, verify and run a pinned artifact](#02-compile-verify-and-run-a-pinned-artifact) | `pure` (none) | yes |
| 03 | [Least-privilege file transform](#03-least-privilege-file-transform) | `cli-file-transform`: args.read, fs.read, fs.write, stdout.write | yes |
| 04 | [Branch on quad evidence explicitly](#04-branch-on-quad-evidence-explicitly) | none | yes |
| 05 | [Machine-readable diagnostics for CI](#05-machine-readable-diagnostics-for-ci) | none | yes |
| 06 | [Runtime failures and quotas fail with exit 1](#06-runtime-failures-and-quotas-fail-with-exit-1) | none | yes |
| 07 | [Compile with the frozen self-hosted compiler (C1) and accept fail-closed](#07-compile-with-the-frozen-self-hosted-compiler-c1-and-accept-fail-closed) | `cli-read-only` + `trusted-compiler` envelope for C1 | yes |

## 01. Check a download against the release SHA256SUMS

Confirms that the bytes you downloaded are the bytes the release lists. This shows integrity, not authenticity: rc.2 assets are unsigned.

**Also needed:** `semantic-selfhost-compiler-C1.smc`, `SHA256SUMS` (release assets).

**Step 1**: expected exit **0**, observed exit **0**.
```powershell
$want = (Select-String -Path SHA256SUMS -Pattern 'semantic-selfhost-compiler-C1.smc').Line.Split(' ')[0]; $got = (Get-FileHash semantic-selfhost-compiler-C1.smc -Algorithm SHA256).Hash.ToLower(); if ($got -eq $want) { "MATCH $got" } else { "MISMATCH $got"; exit 1 }
```
```text
MATCH 2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939
```

**Step 2 (negative control)**: expected exit **1**, observed exit **1**.
```powershell
Copy-Item semantic-selfhost-compiler-C1.smc tampered.smc; Add-Content tampered.smc 'x' -NoNewline; $want = (Select-String -Path SHA256SUMS -Pattern 'semantic-selfhost-compiler-C1.smc').Line.Split(' ')[0]; $got = (Get-FileHash tampered.smc -Algorithm SHA256).Hash.ToLower(); if ($got -eq $want) { "MATCH $got" } else { "MISMATCH $got"; exit 1 }
```
```text
MISMATCH 8d6d4ca6a6ff3e3188c2043fe4e6642d4385b8311d5b7abeabcf46e654f18cab
```

## 02. Compile, verify and run a pinned artifact

Separates the build from execution, and runs only the exact artifact you verified.

**Files:**

`hello.sm`
```
fn main() {
    let x: i32 = 40;
    assert(x + 2 == 42);
    return;
}
```

**Step 1**: expected exit **0**, observed exit **0**.
```powershell
smc.exe compile hello.sm -o hello.smc
```
```text
compiled 'hello.sm' -> 'hello.smc' (153 bytes)
```

**Step 2**: expected exit **0**, observed exit **0**.
```powershell
smc.exe verify hello.smc
```
```text
verified 'hello.smc' (1 function(s), header=SEMCOD22, epoch=0.23)
```

**Step 3**: expected exit **0**, observed exit **0**.
```powershell
smc.exe artifact hash hello.smc
```
```text
sha256:3b1113fedd90ff0e9c8c4ca99123e35c3fe80c41e18aedf5dd66de16eda7a264
```

**Step 4**: expected exit **0**, observed exit **0**.
```powershell
$id = (smc.exe artifact hash hello.smc).Trim(); smc.exe run-smc hello.smc --expect-sha256 $id --profile pure --root .
```
```text
(no output)
```

**Step 5 (negative control)**: expected exit **1**, observed exit **1**.
```powershell
smc.exe run-smc hello.smc --expect-sha256 sha256:0000000000000000000000000000000000000000000000000000000000000000 --profile pure --root .
```
```text
artifact identity mismatch: expected sha256:0000000000000000000000000000000000000000000000000000000000000000, found sha256:3b1113fedd90ff0e9c8c4ca99123e35c3fe80c41e18aedf5dd66de16eda7a264
```

## 03. Least-privilege file transform

Grants only the capabilities a program needs. Every path resolves inside `--root`.

**Files:**

`transform.sm`
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

`sandbox/input.txt`
```text
hello
```

**Step 1** in `sandbox`: expected exit **0**, observed exit **0**.
```powershell
smc.exe run ../transform.sm --profile cli-file-transform --root . -- input.txt output.txt
```
```text
(5 capability audit line(s) on stderr, e.g.)
schema=semantic.foundation.application.audit/0.1 seq=4 capability=stdout.write decision=allow bytes=18 path_hash=- payload_hash=4ea6eb36db8f953e
transform complete
```

**Step 2** in `sandbox`: expected exit **0**, observed exit **0**.
```powershell
Get-Content output.txt
```
```text
transformed:hello
```

**Step 3 (negative control)** in `sandbox`: expected exit **1**, observed exit **1**.
```powershell
smc.exe run ../transform.sm --profile cli-read-only --root . -- input.txt output2.txt
```
```text
(4 capability audit line(s) on stderr, e.g.)
schema=semantic.foundation.application.audit/0.1 seq=3 capability=fs.write decision=deny bytes=0 path_hash=- payload_hash=-
capability FsWrite denied for FsWrite [prom.cap.manifest v1 MissingCapability]: manifest does not grant this capability
```

**Step 4 (negative control)** in `sandbox`: expected exit **1**, observed exit **1**.
```powershell
smc.exe run ../transform.sm --profile cli-file-transform --root . -- input.txt ../escaped.txt
```
```text
(4 capability audit line(s) on stderr, e.g.)
schema=semantic.foundation.application.audit/0.1 seq=3 capability=fs.write decision=deny bytes=0 path_hash=- payload_hash=-
ABI FsWrite failure [InvalidInput]: path must be relative and must not contain parent traversal
```

**Step 5** in `sandbox`: expected exit **0**, observed exit **0**.
```powershell
Test-Path output2.txt, ../escaped.txt
```
```text
False
False
```

## 04. Branch on quad evidence explicitly

A `quad` is not a `bool`. Decide with `match`, `is` or comparisons, and handle `S` (conflict) and `N` (no evidence) on purpose.

**Files:**

`decide.sm`
```
fn decide(state: quad) -> i32 {
    return match state {
        N => { 0 }
        F => { 1 }
        T => { 2 }
        _ => { 3 }
    };
}

fn main() {
    let observed: quad = S;
    assert(decide(observed) == 3);
    assert(observed is S);
    assert(observed != N);
    if observed == T { assert(false); }
    return;
}
```

`bare.sm`
```
fn main() {
    let state: quad = T;
    if state { return; }
    return;
}
```

**Step 1**: expected exit **0**, observed exit **0**.
```powershell
smc.exe run decide.sm
```
```text
(no output)
```

**Step 2 (negative control)**: expected exit **1**, observed exit **1**.
```powershell
smc.exe check bare.sm
```
```text
Error [E0201]: if condition must be bool; explicit compare is required for quad (location unavailable)
help: Check type compatibility and explicit conversions.
```

## 05. Machine-readable diagnostics for CI

Decide on the exit code and the diagnostic `code`, not on message wording.

**Files:**

`bare.sm`
```
fn main() {
    let state: quad = T;
    if state { return; }
    return;
}
```

`hello.sm`
```
fn main() {
    let x: i32 = 40;
    assert(x + 2 == 42);
    return;
}
```

**Step 1**: expected exit **0**, observed exit **0**.
```powershell
(smc.exe check hello.sm --format json | ConvertFrom-Json).status
```
```text
passed
```

**Step 2 (negative control)**: expected exit **1**, observed exit **1**.
```powershell
$j = smc.exe check bare.sm --format json; $code = $LASTEXITCODE; "status=" + ($j | ConvertFrom-Json).status; if (($j -join ' ') -match '"code":\s*"(E\d+)"') { "code=" + $Matches[1] }; exit $code
```
```text
status=failed
code=E0201
```

## 06. Runtime failures and quotas fail with exit 1

Shows what a failed run looks like: one exit code and a distinguishable message.

**Files:**

`assert_fail.sm`
```
fn main() {
    assert(1 + 1 == 3);
    return;
}
```

`div_zero.sm`
```
fn main() {
    let divisor: i32 = 0;
    let quotient: i32 = 10 / divisor;
    assert(quotient == 0);
    return;
}
```

`spin.sm`
```
fn main() {
    let mut counter: i32 = 0;
    loop {
        counter = counter + 1;
    }
}
```

**Step 1 (negative control)**: expected exit **1**, observed exit **1**.
```powershell
smc.exe run assert_fail.sm
```
```text
assertion failed
```

**Step 2 (negative control)**: expected exit **1**, observed exit **1**.
```powershell
smc.exe run div_zero.sm
```
```text
runtime trap: DivisionByZero
```

**Step 3 (negative control)**: expected exit **1**, observed exit **1**.
```powershell
smc.exe run spin.sm
```
```text
quota exceeded: Steps limit=100000 used=100001
```

## 07. Compile with the frozen self-hosted compiler (C1) and accept fail-closed

`run-smc` exit 0 only means the VM finished. Accept C1 output only after validating its single result line and verifying the decoded artifact.

**Files:**

`prog.sm`
```
fn main() {
    let x: i32 = 40;
    assert(x + 2 == 42);
    return;
}
```

`bad.sm`
```
fn main() {
    let x: i32 = 40;
    fs_write_text("a", "b");
    return;
}
```

`c1_accept.py`: a reference checker, standard library only. Run it with `python -I`.
```python
"""Fail-closed acceptance check for one run of the frozen C1 compiler under 'smc run-smc'.
Usage: python -I c1_accept.py <run_smc_exit_code> <stdout_file> <out.smc>
Exit 0  ACCEPTED_CANDIDATE: artifact written to <out.smc>; the caller MUST still run 'smc verify <out.smc>'.
Exit 1  REJECTED: C1 printed a well-formed 'error <cat> @<offset>: <msg>' result.
Exit 2  FAILED: VM/run failure, or missing, ambiguous or malformed result. Never treat as acceptance."""
import re, sys
CATS = 'syntax|name|type|context|unsupported'
def done(code, msg): print(msg); sys.exit(code)
if len(sys.argv) != 4: done(2, 'FAILED usage')
try: rc = int(sys.argv[1])
except ValueError: done(2, 'FAILED bad exit code argument')
if rc != 0: done(2, 'FAILED run-smc exit %d (VM or envelope failure, no compiler result)' % rc)
try: raw = open(sys.argv[2], 'rb').read().decode('utf-8')
except (OSError, UnicodeDecodeError) as e: done(2, 'FAILED unreadable stdout: ' + type(e).__name__)
lines = [l for l in raw.replace('\r\n', '\n').split('\n') if l != '']
if len(lines) != 1: done(2, 'FAILED expected exactly one result line on stdout, got %d' % len(lines))
line = lines[0]
m = re.fullmatch(r'hex ((?:[0-9a-f]{2})+)', line)
if m:
    data = bytes.fromhex(m.group(1))
    if not data.startswith(b'SEMCOD'): done(2, 'FAILED decoded bytes lack the SemCode magic')
    open(sys.argv[3], 'wb').write(data)
    done(0, 'ACCEPTED_CANDIDATE %d bytes; run: smc verify %s' % (len(data), sys.argv[3]))
if re.fullmatch(r'error (%s) @\d+: .+' % CATS, line): done(1, 'REJECTED ' + line)
done(2, 'FAILED malformed result line')
```

**Also needed:** `C1.smc` (the release asset `semantic-selfhost-compiler-C1.smc`, saved as `C1.smc`).

**Step 1**: expected exit **0**, observed exit **0**.
```powershell
smc.exe run-smc C1.smc --expect-sha256 sha256:2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939 --profile cli-read-only --root . --envelope trusted-compiler --max-steps 150000000 --max-calls 2000000 --max-frames 256 -- prog.sm 2>$null > c1.out; $rc = $LASTEXITCODE; python -I c1_accept.py $rc c1.out prog.smc; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; smc.exe verify prog.smc
```
```text
ACCEPTED_CANDIDATE 153 bytes; run: smc verify prog.smc
verified 'prog.smc' (1 function(s), header=SEMCOD22, epoch=0.23)
```

**Step 2 (negative control)**: expected exit **1**, observed exit **1**.
```powershell
smc.exe run-smc C1.smc --expect-sha256 sha256:2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939 --profile cli-read-only --root . --envelope trusted-compiler --max-steps 150000000 --max-calls 2000000 --max-frames 256 -- bad.sm 2>$null > c1.out; "run-smc exit: $LASTEXITCODE"; python -I c1_accept.py $LASTEXITCODE c1.out bad.smc; exit $LASTEXITCODE
```
```text
run-smc exit: 0
REJECTED error name @37: unknown function 'fs_write_text'
```

**Step 3 (negative control)**: expected exit **2**, observed exit **2**.
```powershell
Set-Content -Path c1bad.out -Value 'hex 53454D' -NoNewline; python -I c1_accept.py 0 c1bad.out x.smc; exit $LASTEXITCODE
```
```text
FAILED malformed result line
```

## Notes

- **One failure code.** Every failure in these recipes exited with code **1**; the C1 checker's own codes are 0, 1 and 2. Branch on the message or diagnostic code, not on other exit values.
- **Use PowerShell 7 for recipe 07.** In Windows PowerShell 5.1, `>` writes UTF-16LE. The checker then refused the output with `FAILED unreadable stdout: UnicodeDecodeError` (observed). That is fail-closed, but it is not a usable result.
- **Hashes show integrity only.** `SHA256SUMS` and `--expect-sha256` prove that bytes match. They do not prove who produced them: rc.2 assets are unsigned.
- **Not covered:** non-Windows hosts, the installer, projects and packages (see the user manual, chapter 2), `watch`, `repl` and `lsp`.
