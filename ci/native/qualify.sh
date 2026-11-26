#!/usr/bin/env bash
# Native release-candidate qualification of the pinned upstream (Semantic-Dist).
# The upstream commit comes from upstream_anchor.json; the self-hosted compiler
# identities (C0, frozen executor, S, tooling, C1) come from manifests/selfhost_pin.json
# and the constants below. Workspace tests, the self-hosting chain and the
# reproduction-mode workflow are all core gates.
# Builds the pinned upstream revisions natively on this runner, runs targeted and workspace tests,
# a CLI smoke, the self-hosting chain C0(S)=C1 -> C1(S)=C2 -> C2(S)=C3 on the corrected executor,
# and the Semantic-Language reproduction-mode workflow with the frozen executor.
# Engineering cross-platform evidence only: same operator, so never an independent Seal reproduction.
set -uo pipefail

OUT="${NQ_OUT:?}"; WORK="${NQ_WORK:?}"; EXPECT_ARCH="${NQ_EXPECT_ARCH:?}"
CAND="$(python -c 'import json;print(json.load(open("upstream_anchor.json"))["canonical_upstream"]["pinned_commit_sha"])' | tr -d '\r')"
[[ "$CAND" =~ ^[0-9a-f]{40}$ ]] || { echo "invalid anchor commit"; exit 1; }
HERE="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$HERE/nq_tools.py"

UP="$CAND"                                       # pinned upstream (upstream_anchor.json)

# Self-hosted compiler identities come from manifests/selfhost_pin.json (the
# distribution's single source of truth), so a manifest change is qualified
# against what it declares. The frozen executor, the reproduction tooling and
# the counters are contract constants of Bootstrap Contract v4 and stay here.
manifest() { python -c 'import json,sys;d=json.load(open("manifests/selfhost_pin.json"))
for k in sys.argv[1].split("."): d=d[k]
print(d)' "$1" | tr -d '\r'; }
C0="$(manifest c0_reference.commit)"
SLS="$(manifest self_hosted_compiler.commit)"
C1_SHA="$(manifest self_hosted_compiler.c1_sha256)"
C1_BYTES="$(manifest self_hosted_compiler.c1_bytes)"
for v in "$C0" "$SLS"; do [[ "$v" =~ ^[0-9a-f]{40}$ ]] || { echo "invalid manifest commit: $v"; exit 1; }; done
[[ "$C1_SHA" =~ ^[0-9a-f]{64}$ && "$C1_BYTES" =~ ^[0-9]+$ ]] || { echo "invalid manifest C1 identity"; exit 1; }
LOCK_SHA="$(python -c 'import json;print(json.load(open("upstream_anchor.json"))["canonical_upstream"]["cargo_lock_blob_sha256"])' | tr -d '\r')"
[[ "$LOCK_SHA" =~ ^[0-9a-f]{64}$ ]] || { echo "invalid anchor Cargo.lock digest"; exit 1; }
EXEC=825deca47f7e415e27b1e5f845a1c3030ea92300    # frozen normative executor
SLT=e8dc34c15b9862ecf18ee9f4915b540837d9de37     # reproduction tooling (S identical)
HELLO_SHA=3b1113fedd90ff0e9c8c4ca99123e35c3fe80c41e18aedf5dd66de16eda7a264   # Windows reference SemCode of hello.sm
LIM=(--envelope trusted-compiler --max-steps 150000000 --max-calls 2000000 --max-frames 256)

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) EXE=.exe; TIMEV=() ;;
  Darwin) EXE=; TIMEV=(/usr/bin/time -l) ;;
  *) EXE=; if [ -x /usr/bin/time ]; then TIMEV=(/usr/bin/time -v); else TIMEV=(); fi ;;
esac

mkdir -p "$OUT/logs" "$OUT/artifacts" "$WORK"
STEPS="$OUT/steps.tsv"; printf 'step\tclass\texit\tseconds\n' > "$STEPS"
# step <name> <core|info> <command...>: core failures fail the job; info results are reported only.
step() {
  local name=$1 class=$2; shift 2
  local t0; t0=$(date +%s)
  "$@" > "$OUT/logs/$name.log" 2>&1
  local rc=$?
  printf '%s\t%s\t%s\t%s\n' "$name" "$class" "$rc" "$(( $(date +%s) - t0 ))" >> "$STEPS"
  echo "[$name] class=$class exit=$rc"
  return $rc
}
# Identity gates stop the run: nothing is built or tested from unverified sources.
abort() { echo "IDENTITY GATE FAILED: $1"; python "$TOOLS" summary "$OUT" || true; exit 1; }
# reject <exit-code> <ERE> <command...>: a negative check passes only on the exact controlled exit code AND the
# expected diagnostic; a crash, signal or any other code fails it (no false PASS from abnormal termination).
reject() {
  local want=$1 pat=$2; shift 2
  local out rc; out=$("$@" 2>&1); rc=$?
  printf '%s\n' "$out"; echo "exit=$rc (expected $want, diagnostic /$pat/)"
  [ "$rc" -eq "$want" ] && printf '%s' "$out" | grep -Eq "$pat"
}
py() { python "$@" | tr -d '\r'; }

step env core python "$TOOLS" env "$OUT/env.json" "$EXPECT_ARCH"

clone() {  # clone <url> <sha> <dir>: LF checkout at an exact commit
  git -c core.autocrlf=false -c core.eol=lf clone -q --filter=blob:none --no-checkout "$1" "$3" &&
  git -C "$3" config core.autocrlf false && git -C "$3" config core.eol lf &&
  git -C "$3" checkout -q "$2" &&
  [ "$(git -C "$3" rev-parse HEAD)" = "$2" ] &&
  echo "$3 head=$(git -C "$3" rev-parse HEAD) tree=$(git -C "$3" rev-parse 'HEAD^{tree}')"
}
SEM=https://github.com/skulmakov-oss/Semantic
step clone_up   core clone "$SEM" "$UP"   "$WORK/up" || abort "clone_up"
step anchor_cargo_lock core bash -c "got=\$(python '$TOOLS' sha '$WORK/up/Cargo.lock' | tr -d '\r'); echo \"Cargo.lock sha256=\$got anchor=$LOCK_SHA\"; [ \"\$got\" = '$LOCK_SHA' ]" || abort anchor_cargo_lock
step clone_c0   core clone "$SEM" "$C0"   "$WORK/c0" || abort "clone_c0"
step clone_exec core clone "$SEM" "$EXEC" "$WORK/exec" || abort "clone_exec"
step clone_sl   core clone https://github.com/skulmakov-oss/Semantic-Language "$SLT" "$WORK/sl" || abort "clone_sl"
step s_identical_to_release core git -C "$WORK/sl" diff --quiet "$SLS" HEAD -- compiler bootstrap/source-set.toml || abort "s_identical_to_release"

build() { local d=$1; shift; (cd "$d" && rustc -vV && cargo -V && cargo build --release --locked "$@"); }
step build_up   core build "$WORK/up"   --bin smc --bin svm
step build_c0   core build "$WORK/c0"   --bin smc
step build_exec core build "$WORK/exec" --bin smc
UPSMC="$WORK/up/target/release/smc$EXE"; UPSVM="$WORK/up/target/release/svm$EXE"
C0SMC="$WORK/c0/target/release/smc$EXE"; EXSMC="$WORK/exec/target/release/smc$EXE"
step binaries core python "$TOOLS" binaries "$OUT/binaries.json" "$EXPECT_ARCH" "up_smc=$UPSMC" "up_svm=$UPSVM" "c0_smc=$C0SMC" "exec_smc=$EXSMC"

# Targeted native tests on the RC candidate, then the #2089 test on main, then the whole workspace (info).
step test_sm_vm     core bash -c "cd '$WORK/up' && cargo test --release --locked -p sm-vm"
step test_sm_verify core bash -c "cd '$WORK/up' && cargo test --release --locked -p sm-verify"
step test_quad      core bash -c "cd '$WORK/up' && cargo test --release --locked -p semantic-core-quad"
# A filter that selects no test must not count as a pass.
step test_2089_record_snapshot core bash -c "cd '$WORK/up' && cargo test --release --locked -p sm-vm record_snapshot_read_after_call_without_destination > '$OUT/logs/test_2089.cargo.log' 2>&1; rc=\$?; cat '$OUT/logs/test_2089.cargo.log'; [ \$rc -eq 0 ] && grep -Eq 'test result: ok\. [1-9][0-9]* passed' '$OUT/logs/test_2089.cargo.log'"
step test_paths_lsp core bash -c "cd '$WORK/up' && cargo test --release --locked -p smc-cli --lib -- lsp:: platform_paths hub:: package_manifest:: --show-output"
step test_hub_cli core bash -c "cd '$WORK/up' && cargo test --release --locked --test hub_cli -- --show-output"
step test_workspace core bash -c "cd '$WORK/up' && cargo test --locked --workspace --all-targets --no-fail-fast -- --show-output"
step test_doctests core bash -c "cd '$WORK/up' && cargo test --locked --workspace --doc"
python "$TOOLS" tests "$OUT/logs/test_workspace.log" "$OUT/workspace_tests.json"

# CLI smoke with the native corrected toolchain.
SM="$WORK/smoke"; mkdir -p "$SM"
printf 'fn main() { let x: i32 = 40; assert(x + 2 == 42); return; }\n' > "$SM/hello.sm"
printf 'fn main() { assert(1 + 1 == 3); return; }\n' > "$SM/fail.sm"
printf 'fn main() { let x: i32 = ; }\n' > "$SM/bad.sm"
step smoke_compile   core "$UPSMC" compile "$SM/hello.sm" -o "$SM/hello.smc"
step smoke_verify    core "$UPSMC" verify "$SM/hello.smc"
step smoke_hash_equals_windows_reference core bash -c "h=\$('$UPSMC' artifact hash '$SM/hello.smc' | tr -d '\r'); echo \"\$h\"; [ \"\$h\" = 'sha256:$HELLO_SHA' ]"
step smoke_run       core "$UPSMC" run "$SM/hello.sm"
step smoke_run_smc   core "$UPSMC" run-smc "$SM/hello.smc"
step smoke_svm_run   core "$UPSVM" run "$SM/hello.smc"
step smoke_deterministic core bash -c "'$UPSMC' compile '$SM/hello.sm' -o '$SM/hello2.smc' && cmp '$SM/hello.smc' '$SM/hello2.smc'"
step smoke_assert_fails  core reject 1 '^assertion failed' "$UPSMC" run "$SM/fail.sm"
step smoke_parse_fails   core reject 1 'expected primary expression' "$UPSMC" compile "$SM/bad.sm" -o "$SM/bad.smc"
step smoke_mutants core bash -c "python '$TOOLS' mutate truncate '$SM/hello.smc' '$SM/trunc.smc' && python '$TOOLS' mutate magic '$SM/hello.smc' '$SM/magic.smc'"
step smoke_truncated_rejected core reject 1 '^verify error \[TruncatedFunction\]' "$UPSMC" verify "$SM/trunc.smc"
step smoke_magic_rejected     core reject 1 '^verify error \[UnsupportedVersion\]' "$UPSMC" verify "$SM/magic.smc"

# Self-hosting chain on the corrected executor (fbb49594).
A="$OUT/artifacts"
step c1_from_c0 core ${TIMEV[@]+"${TIMEV[@]}"} "$C0SMC" compile "$WORK/sl/compiler/main.sm" -o "$A/C1.smc"
step c1_identity core python "$TOOLS" expect "$A/C1.smc" "$C1_SHA" "$C1_BYTES"
step c1_verify_upstream core "$UPSMC" verify "$A/C1.smc"
step c1_wrong_hash_rejected core reject 1 '^artifact identity mismatch: expected sha256:0{64}, found sha256:'"$C1_SHA" "$UPSMC" run-smc "$A/C1.smc" --expect-sha256 "sha256:0000000000000000000000000000000000000000000000000000000000000000" --profile cli-read-only --root "$SM" -- hello.sm
gen() {  # gen <executor> <in.smc> <out.smc> <tag>
  local h; h=$(py "$TOOLS" sha "$2")
  ${TIMEV[@]+"${TIMEV[@]}"} "$1" run-smc "$2" --expect-sha256 "sha256:$h" --profile cli-read-only --root "$WORK/sl/compiler" "${LIM[@]}" --metrics json -- main.sm > "$OUT/logs/$4.stdout" 2> "$OUT/logs/$4.stderr"
  local rc=$?; cat "$OUT/logs/$4.stderr"; [ $rc -eq 0 ] || return $rc
  python "$TOOLS" hex "$OUT/logs/$4.stdout" "$3" "$OUT/$4.metrics.json"
}
step c2_from_c1 core gen "$UPSMC" "$A/C1.smc" "$A/C2.smc" c2
step c2_identity core python "$TOOLS" expect "$A/C2.smc" "$C1_SHA" "$C1_BYTES" "$OUT/c2.metrics.json"
step c3_from_c2 core gen "$UPSMC" "$A/C2.smc" "$A/C3.smc" c3
step c3_identity core python "$TOOLS" expect "$A/C3.smc" "$C1_SHA" "$C1_BYTES" "$OUT/c3.metrics.json"
step c1_output_equals_c0 core bash -c "h=\$(python '$TOOLS' sha '$A/C1.smc' | tr -d '\r'); '$UPSMC' run-smc '$A/C1.smc' --expect-sha256 sha256:\$h --profile cli-read-only --root '$SM' ${LIM[*]} -- hello.sm > '$SM/c1_hello.stdout' && python '$TOOLS' hex '$SM/c1_hello.stdout' '$SM/hello_by_c1.smc' '$SM/c1_hello.metrics.json' && cmp '$SM/hello_by_c1.smc' '$SM/hello.smc' && '$UPSMC' verify '$SM/hello_by_c1.smc' && '$UPSMC' run-smc '$SM/hello_by_c1.smc'"

# Reproduction-mode workflow (Semantic-Language tooling e8dc34c1): native C0 + native frozen executor 825deca4,
# admitted by source fingerprint; full scope incl. the 140-fixture differential. Never yields a v4 record.
step repro_mode core bash -c "cd '$WORK/sl' && python -I tests/selfhost/selfhost.py all --out '$OUT/repro' --smc '$C0SMC' --executor '$EXSMC' --reproduction-build --c0-checkout '$WORK/c0' --require-clean"

for b in "$UPSMC" "$UPSVM" "$C0SMC" "$EXSMC"; do [ -f "$b" ] && cp "$b" "$OUT/artifacts/$(basename "$(dirname "$(dirname "$(dirname "$b")")")")_$(basename "$b")"; done
python "$TOOLS" summary "$OUT"
awk -F'\t' 'NR>1 && $2=="core" && $3!="0" {bad=1; print "CORE FAILURE: " $1} END {exit bad}' "$STEPS"