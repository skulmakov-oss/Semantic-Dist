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

`run-smc` exit 0 only means the VM finished. C1 exits 0 also when it **rejects** a program. The checker below runs C1 itself and classifies its single result line. It verifies the decoded artifact with `smc verify`, and only then publishes it to a **new** file. It never overwrites an existing file.

**Run it** in a new empty folder created for this recipe; the checker refuses an output path that already exists. Python 3 is required (`python -I`). The checker captures the compiler's output itself, so no shell redirection is involved.

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

`c1_accept3.py`: reference checker, standard library only, embedded exactly as tested.
```python
"""Fail-closed acceptance of one frozen-C1 compilation (RFC-01 F6, checker v3).

Runs 'smc run-smc' with the pinned C1, classifies its single result line, verifies the
decoded artifact with 'smc verify', and publishes it without ever replacing an existing
file. The exit code is the outcome; one JSON line on stdout explains it.

  python -I c1_accept3.py --smc SMC --c1 C1.smc --c1-sha256 HEX --root DIR --input FILE
                          --out NEW.smc [--expect-sha256 HEX] [limits]

Outcomes: 0 ACCEPTED, 1 REJECTED (well-formed compiler rejection), 2 VM_FAILURE (run-smc
non-zero, or timeout), 3 PROTOCOL_FAILURE (missing/ambiguous/malformed/oversized output),
4 VERIFY_FAILURE (header, verifier, hash), 5 TOOL_FAILURE (usage, I/O, collision, alias,
incomplete or failed output capture).

Threat model: a caller-controlled scratch directory without hostile same-user activity.
Concurrent creation of --out is detected and never overwritten; this is not a defence
against a hostile process of the same user. If printing the JSON line fails (also after
publication), the process exits immediately with the outcome code; the verified artifact stays.
--root, --c1 and a --smc containing a path separator are resolved against the caller's
directory; --input is relative to --root.
"""
import argparse, hashlib, json, os, re, subprocess, sys, tempfile, threading

OUTCOMES = {0: 'ACCEPTED', 1: 'REJECTED', 2: 'VM_FAILURE', 3: 'PROTOCOL_FAILURE', 4: 'VERIFY_FAILURE', 5: 'TOOL_FAILURE'}
HEX_LINE = re.compile(r'hex ((?:[0-9a-f]{2})+)')
ERR_LINE = re.compile(r'error (syntax|name|type|context|unsupported) @(0|[1-9][0-9]{0,9}): ([\x20-\x7e]+)')
TEMP_PREFIX = '.c1accept3-'
MAGIC = b'SEMCOD'


class Outcome(Exception):
    def __init__(self, code, reason, **extra):
        super().__init__(reason)
        self.code, self.reason, self.extra = code, reason, extra


class Parser(argparse.ArgumentParser):
    def error(self, message):  # never let argparse exit with 2 (that code means VM_FAILURE)
        raise Outcome(5, 'usage: ' + message)


def bounded_int(lo, hi):
    def conv(text):
        try:
            v = int(text, 10)
        except ValueError:
            raise argparse.ArgumentTypeError('not an integer')
        if not lo <= v <= hi:
            raise argparse.ArgumentTypeError('must be in [%d, %d]' % (lo, hi))
        return v
    return conv


def parse_args(argv):
    p = Parser(add_help=False, allow_abbrev=False)
    for name in ('--smc', '--c1', '--c1-sha256', '--root', '--input', '--out'):
        p.add_argument(name, required=True)
    p.add_argument('--expect-sha256')
    p.add_argument('--max-stdout-bytes', type=bounded_int(1, 1 << 30), default=1 << 28)
    p.add_argument('--max-stderr-bytes', type=bounded_int(1, 1 << 30), default=1 << 24)
    p.add_argument('--run-timeout', type=bounded_int(1, 86400), default=3600)
    p.add_argument('--verify-timeout', type=bounded_int(1, 86400), default=600)
    a = p.parse_args(argv)
    # Resolve filesystem paths against the caller's directory before any child changes cwd.
    a.root = os.path.abspath(a.root)
    a.c1 = os.path.abspath(a.c1)
    if os.sep in a.smc or (os.altsep and os.altsep in a.smc):
        a.smc = os.path.abspath(a.smc)  # a bare name keeps PATH lookup
    for name in ('c1_sha256', 'expect_sha256'):
        v = getattr(a, name)
        if v is not None:
            v = v.lower().removeprefix('sha256:')
            if not re.fullmatch(r'[0-9a-f]{64}', v):
                raise Outcome(5, 'usage: --%s must be 64 hex digits' % name.replace('_', '-'))
            setattr(a, name, v)
    return a


def key(path):
    return os.path.normcase(os.path.realpath(path))


def check_paths(a):
    if not os.path.isdir(a.root):
        raise Outcome(5, 'root is not a directory')
    out = os.path.abspath(a.out)
    parent = os.path.dirname(out)
    if not os.path.isdir(parent):
        raise Outcome(5, 'output directory does not exist')
    if os.path.lexists(out):
        raise Outcome(5, 'output already exists; refusing to reuse or overwrite it')
    out_key = os.path.normcase(os.path.join(os.path.realpath(parent), os.path.basename(out)))
    inp = a.input if os.path.isabs(a.input) else os.path.join(a.root, a.input)
    for label, other in (('input', inp), ('c1', a.c1), ('smc', a.smc)):
        if out_key == key(other):
            raise Outcome(5, 'output path aliases the %s path' % label)
    if os.path.basename(out).startswith(TEMP_PREFIX):
        raise Outcome(5, 'output name uses the reserved temporary prefix')
    return out, parent


def build_run_cmd(a):
    return [a.smc, 'run-smc', a.c1, '--expect-sha256', 'sha256:' + a.c1_sha256, '--profile', 'cli-read-only',
            '--root', '.', '--envelope', 'trusted-compiler', '--max-steps', '150000000', '--max-calls', '2000000',
            '--max-frames', '256', '--', a.input]


READER_JOIN_TIMEOUT = 30  # seconds to wait for each reader thread after the child ends
KILL_WAIT_TIMEOUT = 30    # seconds to wait for the child to exit after kill()


def run_bounded(cmd, cwd, timeout, max_out, max_err):
    """Run cmd capturing both streams with byte limits enforced while reading.

    Fail closed: a reader error, a reader that does not finish (EOF or limit) in time,
    or a child that does not exit after kill() raises Outcome(5). Partial streams are
    never returned. Only the direct child is managed; descendants it spawns are not.
    """
    try:
        proc = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as e:
        raise Outcome(5, 'cannot start %s: %s' % (os.path.basename(str(cmd[0])), type(e).__name__))
    bufs = {'out': bytearray(), 'err': bytearray()}
    over = {'out': False, 'err': False}
    done = {'out': False, 'err': False}  # True only after EOF or a deliberate stop at the limit
    errors = {}

    def stop_child():
        try:
            proc.kill()
        except OSError:
            pass

    def pump(stream, name, limit):
        try:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    done[name] = True
                    return
                if len(bufs[name]) + len(chunk) > limit:
                    over[name] = True
                    done[name] = True
                    stop_child()
                    return
                bufs[name] += chunk
        except BaseException as e:  # recorded and re-raised as a fail-closed outcome below
            errors[name] = type(e).__name__
            stop_child()
        finally:
            try:
                stream.close()
            except OSError:
                pass

    threads = [threading.Thread(target=pump, args=(proc.stdout, 'out', max_out), daemon=True),
               threading.Thread(target=pump, args=(proc.stderr, 'err', max_err), daemon=True)]
    for t in threads:
        t.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        stop_child()
        try:
            proc.wait(timeout=KILL_WAIT_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise Outcome(5, 'child did not exit after kill; capture state unknown')
    for t in threads:
        t.join(timeout=READER_JOIN_TIMEOUT)
    if any(t.is_alive() for t in threads):
        stop_child()
        raise Outcome(5, 'output capture did not complete')
    if errors:
        raise Outcome(5, 'output capture failed: ' + ', '.join('%s=%s' % kv for kv in sorted(errors.items())))
    if not timed_out and not (done['out'] and done['err']):
        raise Outcome(5, 'output capture ended without end-of-stream')
    return proc.returncode, bytes(bufs['out']), bytes(bufs['err']), over['out'], over['err'], timed_out


def classify(stdout):
    if not stdout.isascii():
        raise Outcome(3, 'result is not ASCII')
    s = stdout.decode('ascii')
    if s.endswith('\r\n'):
        s = s[:-2]
    elif s.endswith('\n'):
        s = s[:-1]
    if s == '' or '\n' in s or '\r' in s:
        raise Outcome(3, 'stdout must be exactly one non-empty line (one optional trailing LF or CRLF)')
    m = HEX_LINE.fullmatch(s)
    if m:
        return bytes.fromhex(m.group(1))
    e = ERR_LINE.fullmatch(s)
    if e:
        if int(e.group(2)) > 0xFFFFFFFF:
            raise Outcome(3, 'error offset out of range')
        raise Outcome(1, 'compiler rejected the input', category=e.group(1), offset=int(e.group(2)), message=e.group(3))
    raise Outcome(3, 'result line is neither a valid hex line nor a valid error line')


def write_temp(parent, data):
    fd, tmp = tempfile.mkstemp(prefix=TEMP_PREFIX, suffix='.tmp', dir=parent)
    try:
        with os.fdopen(fd, 'wb') as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return tmp


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(a, path):
    rc, out, err, o_over, e_over, t_out = run_bounded([a.smc, 'verify', path], os.path.dirname(path), a.verify_timeout, 1 << 20, 1 << 20)
    if t_out:
        raise Outcome(5, 'verifier timed out')
    if o_over or e_over:
        raise Outcome(4, 'verifier output exceeded the capture limit; artifact not accepted')
    if rc != 0:
        raise Outcome(4, 'smc verify rejected the artifact', verify_exit=rc)


def publish_noclobber(src, dst):
    """Move src to dst only if dst does not exist; never replaces an existing file."""
    if os.name == 'nt':
        os.rename(src, dst)  # MoveFileExW without MOVEFILE_REPLACE_EXISTING: fails if dst exists
    else:
        os.link(src, dst)  # fails with EEXIST if dst exists
        os.unlink(src)


def accept(a):
    out, parent = check_paths(a)
    rc, so, se, o_over, e_over, t_out = run_bounded(build_run_cmd(a), a.root, a.run_timeout, a.max_stdout_bytes, a.max_stderr_bytes)
    info = {'run_exit': rc, 'stdout_bytes': len(so), 'stderr_bytes': len(se),
            'stderr_non_audit_lines': sum(1 for line in se.splitlines() if line and not line.startswith(b'schema=semantic.foundation.application.audit/'))}
    if t_out:
        raise Outcome(2, 'run-smc exceeded the timeout; child killed', **info)
    if o_over:
        raise Outcome(3, 'stdout exceeded the limit; child killed', **info)
    if e_over:
        raise Outcome(3, 'stderr exceeded the limit; child killed', **info)
    if rc != 0:
        raise Outcome(2, 'run-smc exited %d; no compiler result is admissible' % rc, **info)
    data = classify(so)
    if not data.startswith(MAGIC):
        raise Outcome(4, 'decoded bytes lack the SemCode magic', **info)
    want = hashlib.sha256(data).hexdigest()
    if a.expect_sha256 and want != a.expect_sha256:
        raise Outcome(4, 'artifact sha256 differs from --expect-sha256', **info)
    tmp = None
    try:
        try:
            tmp = write_temp(parent, data)
        except OSError as e:
            raise Outcome(5, 'cannot write the temporary artifact: ' + type(e).__name__, **info)
        verify(a, tmp)
        if sha256_file(tmp) != want:
            raise Outcome(4, 'verified file differs from the decoded result', **info)
        try:
            publish_noclobber(tmp, out)
        except FileExistsError:
            raise Outcome(5, 'output appeared concurrently; left untouched', **info)
        except OSError as e:
            raise Outcome(5, 'publication failed: ' + type(e).__name__, **info)
        tmp = None
        if sha256_file(out) != want:
            raise Outcome(5, 'published file differs from the verified bytes; left in place for inspection', **info)
        return {'outcome': 'ACCEPTED', 'code': 0, 'artifact_sha256': want, 'bytes': len(data), 'out': os.path.basename(out), **info}
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass


REPORT_FAILED = False


def main(argv=None):
    global REPORT_FAILED
    try:
        result = accept(parse_args(sys.argv[1:] if argv is None else argv))
    except Outcome as o:
        result = {'outcome': OUTCOMES[o.code], 'code': o.code, 'reason': o.reason, **o.extra}
    except Exception as e:  # unexpected: fail closed
        result = {'outcome': 'TOOL_FAILURE', 'code': 5, 'reason': 'internal error: ' + type(e).__name__}
    try:
        sys.stdout.write(json.dumps(result, sort_keys=True) + '\n')
        sys.stdout.flush()
    except Exception:
        REPORT_FAILED = True  # the exit code remains authoritative
    return result['code']


if __name__ == '__main__':
    code = main()
    if REPORT_FAILED:
        os._exit(code)  # skip interpreter-exit flushing of the failed stream (it would turn the code into 120)
    sys.exit(code)
```

**Also needed:** the release asset `semantic-selfhost-compiler-C1.smc`, saved as `C1.smc`.

**Outcome codes**

| Exit | Outcome | Meaning |
| --- | --- | --- |
| 0 | `ACCEPTED` | one valid `hex` line; `SEMCOD` magic; `smc verify` passed; published to a new file |
| 1 | `REJECTED` | one well-formed `error <category> @<offset>: <message>` line; nothing written |
| 2 | `VM_FAILURE` | `run-smc` exited non-zero or timed out; no result is admissible |
| 3 | `PROTOCOL_FAILURE` | output missing, repeated, mixed, malformed, non-ASCII or over the size limit |
| 4 | `VERIFY_FAILURE` | missing magic, `smc verify` failed, or the hash differs from `--expect-sha256` |
| 5 | `TOOL_FAILURE` | bad arguments; output already exists or aliases an input; an I/O or publication error; or output capture that failed or did not complete |

Each step below is one fragment run with `pwsh -NoProfile -Command`. Checker steps end with `exit $LASTEXITCODE`, so the exit code shown is the checker's own; `-Command` alone would report every non-zero code as 1. The other steps are assertions that exit 1 if they fail.

**Step 1**: expected exit **0**, observed exit **0**.
```powershell
New-Item -ItemType Directory out | Out-Null; python -I c1_accept3.py --smc (Get-Command smc.exe).Source --c1 C1.smc --c1-sha256 2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939 --root . --input prog.sm --out out\prog.smc; exit $LASTEXITCODE
```
```text
{"artifact_sha256": "3b1113fedd90ff0e9c8c4ca99123e35c3fe80c41e18aedf5dd66de16eda7a264", "bytes": 153, "code": 0, "out": "prog.smc", "outcome": "ACCEPTED", "run_exit": 0, "stderr_bytes": 597, "stderr_non_audit_lines": 0, "stdout_bytes": 310}
```

**Step 2**: expected exit **0**, observed exit **0**.
```powershell
smc.exe compile prog.sm -o c0.smc | Out-Null; if ((Get-FileHash out\prog.smc).Hash -eq (Get-FileHash c0.smc).Hash) { 'identical to smc compile' } else { 'DIFFERENT'; exit 1 }
```
```text
identical to smc compile
```

**Step 3 (negative control)**: expected exit **1**, observed exit **1**.
```powershell
python -I c1_accept3.py --smc (Get-Command smc.exe).Source --c1 C1.smc --c1-sha256 2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939 --root . --input bad.sm --out out\bad.smc; exit $LASTEXITCODE
```
```text
{"category": "name", "code": 1, "message": "unknown function 'fs_write_text'", "offset": 37, "outcome": "REJECTED", "reason": "compiler rejected the input"}
```

**Step 4**: expected exit **0**, observed exit **0**.
```powershell
if (Test-Path out\bad.smc) { 'UNEXPECTED FILE'; exit 1 } else { 'no file written' }
```
```text
no file written
```

**Step 5 (negative control)**: expected exit **5**, observed exit **5**.
```powershell
python -I c1_accept3.py --smc (Get-Command smc.exe).Source --c1 C1.smc --c1-sha256 2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939 --root . --input prog.sm --out out\prog.smc; exit $LASTEXITCODE
```
```text
{"code": 5, "outcome": "TOOL_FAILURE", "reason": "output already exists; refusing to reuse or overwrite it"}
```

**Step 6**: expected exit **0**, observed exit **0**.
```powershell
if ((Get-FileHash out\prog.smc).Hash -eq (Get-FileHash c0.smc).Hash) { 'existing file unchanged' } else { 'CHANGED'; exit 1 }
```
```text
existing file unchanged
```

**Limits**
- The checker assumes a folder you control. It detects an output file that appears concurrently and leaves it untouched; it is not a defence against a hostile process of the same user.
- Output capture is fail-closed. A read error on either stream, a reader that does not reach end-of-stream, or a child that does not exit after being killed ends in outcome 5, and nothing is classified or published. Only the direct child process is managed; processes it starts itself are not tracked.
- If printing the JSON line fails (also after publication), the checker exits immediately with the outcome code.
- `--root`, `--c1` and an `--smc` path containing a separator are resolved against the folder you run the command from; `--input` is relative to `--root`. A bare `--smc` name is looked up on `PATH`.
- The deterministic test suite used to qualify this exact file is not part of this page. This is observed behaviour, not formal qualification.

## Notes

- **One failure code.** Every `smc` failure in these recipes exited with code **1**. Branch on the message or diagnostic code, not on other exit values. The recipe 07 checker has its own codes 0–5 (table above).
- **Recipe 07 needs Python 3.** The checker captures the compiler's output itself, so shell redirection and its encoding are not involved.
- **Hashes show integrity only.** `SHA256SUMS` and `--expect-sha256` prove that bytes match. They do not prove who produced them: rc.2 assets are unsigned.
- **Not covered:** non-Windows hosts, the installer, projects and packages (see the user manual, chapter 2), `watch`, `repl` and `lsp`.
