"""Helpers for ci/native_qualification.sh (test-only). Standard library only."""
import hashlib, json, os, platform, re, subprocess, sys

EXPECTED_COUNTERS = {"steps": 101176981, "calls": 1092148, "peak_frames": 36}
ARCH = {"amd64": "x86_64", "x86_64": "x86_64", "x64": "x86_64", "arm64": "arm64", "aarch64": "arm64"}


def sh(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return (p.stdout + p.stderr).replace("\r", "").strip()
    except Exception as e:  # recorded, never fatal for information fields
        return "unavailable: %s" % e


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def binary_arch(path):
    b = open(path, "rb").read(4096)
    if b[:4] == b"\x7fELF":
        m = int.from_bytes(b[18:20], "little")
        return {0x3E: "x86_64", 0xB7: "arm64"}.get(m, "elf-0x%x" % m), "ELF"
    if b[:4] in (b"\xcf\xfa\xed\xfe",):
        cpu = int.from_bytes(b[4:8], "little")
        return {0x0100000C: "arm64", 0x01000007: "x86_64"}.get(cpu, "macho-0x%x" % cpu), "Mach-O"
    if b[:4] in (b"\xca\xfe\xba\xbe",):
        return "universal", "Mach-O fat"
    if b[:2] == b"MZ":
        off = int.from_bytes(b[0x3C:0x40], "little")
        m = int.from_bytes(b[off + 4:off + 6], "little")
        return {0x8664: "x86_64", 0xAA64: "arm64"}.get(m, "pe-0x%x" % m), "PE"
    return "unknown", "unknown"


def mem_total():
    try:
        if sys.platform.startswith("linux"):
            for line in open("/proc/meminfo"):
                if line.startswith("MemTotal"):
                    return int(line.split()[1]) * 1024
        if sys.platform == "darwin":
            return int(sh(["sysctl", "-n", "hw.memsize"]))
        if sys.platform == "win32":
            import ctypes
            class M(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong)] + [("x%d" % i, ctypes.c_ulonglong) for i in range(6)]
            m = M(); m.l = ctypes.sizeof(M); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.total
    except Exception:
        return None


def cmd_env(out, expect):
    rust = sh(["rustc", "-vV"])
    host = re.search(r"^host: (\S+)", rust, re.M)
    e = {
        "uname": " ".join(platform.uname()),
        "uname_m": sh(["uname", "-m"]),
        "machine": platform.machine(),
        "sys_platform": sys.platform,
        "python": sys.version.split()[0],
        "rustc_vV_default": rust,
        "rust_host": host.group(1) if host else None,
        "runner": {k: os.environ.get(k) for k in ("RUNNER_OS", "RUNNER_ARCH", "ImageOS", "ImageVersion", "RUNNER_NAME")},
        "cpu_count": os.cpu_count(),
        "mem_total_bytes": mem_total(),
    }
    if sys.platform == "darwin":
        e["sw_vers"] = sh(["sw_vers"])
        e["cpu_brand"] = sh(["sysctl", "-n", "machdep.cpu.brand_string"])
        e["hw_optional_arm64"] = sh(["sysctl", "-n", "hw.optional.arm64"])
        e["proc_translated"] = sh(["sysctl", "-n", "sysctl.proc_translated"])
    elif sys.platform.startswith("linux"):
        e["os_release"] = sh(["sh", "-c", ". /etc/os-release; echo $PRETTY_NAME"])
        e["cpu_model"] = sh(["sh", "-c", "grep -m1 'model name' /proc/cpuinfo || lscpu | grep -m1 'Model name'"])
    else:
        e["os"] = platform.platform()
    norm = ARCH.get(e["machine"].lower(), e["machine"])
    want = ARCH.get(expect, expect)
    checks = {
        "machine_is_expected": norm == want,
        "rust_host_is_expected": bool(e["rust_host"]) and ARCH.get(e["rust_host"].split("-")[0], "?") == want,
        "not_translated": e.get("proc_translated", "0") in ("0", "unavailable: ", "") or e.get("proc_translated", "").startswith("unavailable"),
    }
    e["checks"] = checks
    json.dump(e, open(out, "w"), indent=1)
    print(json.dumps(e, indent=1))
    return 0 if all(checks.values()) else 1


def cmd_binaries(out, expect, *pairs):
    want = ARCH.get(expect, expect)
    res, ok = {}, True
    for p in pairs:
        name, path = p.split("=", 1)
        if not os.path.isfile(path):
            res[name] = {"present": False}; ok = False; continue
        arch, fmt = binary_arch(path)
        r = {"present": True, "format": fmt, "arch": arch, "arch_ok": arch == want, "sha256": sha(path), "bytes": os.path.getsize(path)}
        if name.endswith("smc"):
            v = sh([path, "version", "--json"])
            try:
                r["source_fingerprint"] = json.loads(v).get("source_fingerprint")
            except Exception:
                r["version_raw"] = v[:400]
        ok &= r["arch_ok"]
        res[name] = r
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))
    return 0 if ok else 1


def read_metrics(*paths):
    for p in paths:
        if p and os.path.isfile(p):
            for line in open(p, encoding="utf-8", errors="replace"):
                if "semantic.run.metrics" in line:
                    return json.loads(line[line.index("{"):])
    return None


def cmd_hex(stdout, out_smc, metrics_out):
    text = open(stdout, encoding="utf-8", errors="replace").read().replace("\r", "")
    lines = [l for l in text.split("\n") if l.startswith("hex ")]
    if not lines:
        print("no hex line"); return 1
    h = re.match(r"[0-9a-f]*", lines[0][4:].strip()).group(0)
    open(out_smc, "wb").write(bytes.fromhex(h))
    m = read_metrics(stdout, stdout[:-len(".stdout")] + ".stderr" if stdout.endswith(".stdout") else None)
    json.dump(m, open(metrics_out, "w"), indent=1)
    print("wrote %s sha256=%s bytes=%d metrics=%s" % (out_smc, sha(out_smc), os.path.getsize(out_smc), json.dumps(m)))
    return 0


def cmd_expect(path, want_sha, want_bytes, metrics=None):
    got, size = sha(path), os.path.getsize(path)
    ok = got == want_sha and size == int(want_bytes)
    print("sha256=%s bytes=%d expected=%s/%s" % (got, size, want_sha, want_bytes))
    if metrics:
        m = json.load(open(metrics)) or {}
        c = m.get("counters", {})
        sub = {k: c.get(k) for k in EXPECTED_COUNTERS}
        print("outcome=%s counters=%s expected=%s" % (m.get("outcome"), sub, EXPECTED_COUNTERS))
        ok &= m.get("outcome") == "ok" and sub == EXPECTED_COUNTERS
    return 0 if ok else 1


def cmd_mutate(kind, src, dst):
    b = bytearray(open(src, "rb").read())
    if kind == "truncate":
        b = b[:-8]
    else:
        b[0] ^= 0xFF
    open(dst, "wb").write(bytes(b))
    return 0


def mem_from_log(path):
    if not os.path.isfile(path):
        return None
    t = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"Maximum resident set size \(kbytes\): (\d+)", t)
    if m:
        return {"max_rss_bytes": int(m.group(1)) * 1024, "method": "GNU time -v"}
    m = re.search(r"(\d+)\s+maximum resident set size", t)
    if m:
        return {"max_rss_bytes": int(m.group(1)), "method": "BSD time -l"}
    return None


def cmd_summary(out):
    j = lambda p: json.load(open(os.path.join(out, p))) if os.path.isfile(os.path.join(out, p)) else None
    steps = []
    for i, line in enumerate(open(os.path.join(out, "steps.tsv"))):
        if i:
            n, c, rc, s = line.rstrip("\n").split("\t")
            steps.append({"step": n, "class": c, "exit": int(rc), "seconds": int(s)})
    arts = {}
    for g in ("C1", "C2", "C3"):
        p = os.path.join(out, "artifacts", g + ".smc")
        if os.path.isfile(p):
            arts[g] = {"sha256": sha(p), "bytes": os.path.getsize(p)}
    logs = os.path.join(out, "logs")
    ws = ""
    wl = os.path.join(logs, "test_workspace.log")
    if os.path.isfile(wl):
        t = open(wl, encoding="utf-8", errors="replace").read()
        ws = {"test_result_lines": re.findall(r"test result: .*", t)[-200:],
              "failed_tests": re.findall(r"^---- (\S+) stdout ----", t, re.M)[:100],
              "errors": re.findall(r"^error(?:\[\w+\])?: .*", t, re.M)[:40]}
    rep = j("repro/report.json")
    pre = j("repro/preflight.json")
    s = {
        "env": j("env.json"), "binaries": j("binaries.json"), "steps": steps,
        "core_failures": [x["step"] for x in steps if x["class"] == "core" and x["exit"]],
        "info_failures": [x["step"] for x in steps if x["class"] == "info" and x["exit"]],
        "artifacts": arts,
        "metrics": {"C1_compiles_S": j("c2.metrics.json"), "C2_compiles_S": j("c3.metrics.json")},
        "memory": {"c0_compile_S": mem_from_log(os.path.join(logs, "c1_from_c0.log")),
                   "c1_compiles_S": mem_from_log(os.path.join(logs, "c2.stderr")),
                   "c2_compiles_S": mem_from_log(os.path.join(logs, "c3.stderr"))},
        "workspace_tests": ws,
        "repro": None if rep is None else {"verdict": rep.get("verdict"), "violations": rep.get("violations"),
                                           "bootstrap_record": rep.get("bootstrap_record"),
                                           "seal_reproduction": rep.get("facts", {}).get("seal_reproduction"),
                                           "counters": rep.get("facts", {}).get("counters")},
        "repro_preflight_tools": None if pre is None else pre.get("tools"),
    }
    json.dump(s, open(os.path.join(out, "summary.json"), "w"), indent=1)
    print(json.dumps({k: s[k] for k in ("core_failures", "info_failures", "artifacts")}, indent=1))
    return 0


MARKERS = ("UNSUPPORTED-FS-NON-UTF8", "SKIPPED-8DOT3-UNAVAILABLE")


def cmd_tests(log, out):
    """Per-test outcomes of a cargo test log (libtest output), by test binary."""
    text = open(log, encoding="utf-8", errors="replace").read().replace("\r", "")
    binaries, current = [], None
    for line in text.split("\n"):
        m = re.match(r"\s+Running (.+?)(?: \((.+)\))?$", line) or re.match(r"\s+Doc-tests (\S+)$", line)
        if m:
            current = {"target": m.group(1), "tests": {}}
            binaries.append(current)
            continue
        m = re.match(r"^test (.+?) \.\.\. (ok|FAILED|ignored)(?:, .*)?$", line)
        if m and current is not None:
            current["tests"][m.group(1)] = m.group(2)
    counts = {"ok": 0, "FAILED": 0, "ignored": 0}
    failed, ignored = [], []
    for b in binaries:
        for name, status in b["tests"].items():
            counts[status] += 1
            if status == "FAILED":
                failed.append(b["target"] + "::" + name)
            if status == "ignored":
                ignored.append(b["target"] + "::" + name)
    markers = {mk: len(re.findall(re.escape(mk), text)) for mk in MARKERS}
    totals = {"passed": 0, "failed": 0, "ignored": 0}
    for m in re.finditer(r"test result: \w+\. (\d+) passed; (\d+) failed; (\d+) ignored", text):
        totals["passed"] += int(m.group(1)); totals["failed"] += int(m.group(2)); totals["ignored"] += int(m.group(3))
    res = {"totals": totals, "counts": counts, "binaries": len(binaries), "failed": failed, "ignored": ignored,
           "markers": markers, "summary_lines": re.findall(r"test result: .*", text)}
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("totals", "counts", "binaries", "markers")}))
    print("FAILED: " + ", ".join(failed[:50]))
    return 0


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "sha":
        print(sha(args[0])); sys.exit(0)
    sys.exit({"env": cmd_env, "binaries": cmd_binaries, "hex": cmd_hex, "expect": cmd_expect,
              "mutate": cmd_mutate, "summary": cmd_summary, "tests": cmd_tests}[cmd](*args))