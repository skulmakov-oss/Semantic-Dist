#!/usr/bin/env bash
# Native runtime/compiler qualification (test-only, SEMANTIC-NATIVE-QUALIFICATION-GO-04).
# Builds the pinned upstream revisions natively on this runner, runs targeted and workspace tests,
# a CLI smoke, the self-hosting chain C0(S)=C1 -> C1(S)=C2 -> C2(S)=C3 on the corrected executor,
# and the Semantic-Language reproduction-mode workflow with the frozen executor.
# Engineering cross-platform evidence only: same operator, so never an independent Seal reproduction.
set -uo pipefail

OUT="${NQ_OUT:?}"; WORK="${NQ_WORK:?}"; EXPECT_ARCH="${NQ_EXPECT_ARCH:?}"
HERE="$(cd "$(dirname "$0")" && pwd)"
TOOLS="$HERE/nq_tools.py"

UP=fbb49594cc3554b90b0977f9b6a69fc584e11e79      # upstream RC candidate (corrected VM)
MAIN=30b45572780812b42603976a9520d7ece6acdea0    # upstream main (+#2089 test only)
C0=1d1e76c7509a03baa0133abaaa5819f5d32582b2      # historical C0 (frozen)
EXEC=825deca47f7e415e27b1e5f845a1c3030ea92300    # frozen normative executor
SLS=5b404e5fbf487f05106617576eddefdb1cea1a7a     # S (normative release commit)
SLT=e8dc34c15b9862ecf18ee9f4915b540837d9de37     # reproduction tooling (S identical)
C1_SHA=2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939
C1_BYTES=339746
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
must_fail() { "$@"; local rc=$?; echo "exit=$rc (expected non-zero)"; [ "$rc" -ne 0 ]; }
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
step clone_up   core clone "$SEM" "$UP"   "$WORK/up"
step clone_main core clone "$SEM" "$MAIN" "$WORK/main"
step clone_c0   core clone "$SEM" "$C0"   "$WORK/c0"
step clone_exec core clone "$SEM" "$EXEC" "$WORK/exec"
step clone_sl   core clone https://github.com/skulmakov-oss/Semantic-Language "$SLT" "$WORK/sl"
step s_identical_to_release core git -C "$WORK/sl" diff --quiet "$SLS" HEAD -- compiler bootstrap/source-set.toml

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
step test_2089_main core bash -c "cd '$WORK/main' && cargo test --release --locked -p sm-vm record_snapshot_read_after_call_without_destination"
step test_workspace info bash -c "cd '$WORK/up' && cargo test --locked --workspace --all-targets"

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
step smoke_assert_fails  core must_fail "$UPSMC" run "$SM/fail.sm"
step smoke_parse_fails   core must_fail "$UPSMC" compile "$SM/bad.sm" -o "$SM/bad.smc"
step smoke_truncated_rejected core bash -c "python '$TOOLS' mutate truncate '$SM/hello.smc' '$SM/trunc.smc' && ! '$UPSMC' verify '$SM/trunc.smc'"
step smoke_magic_rejected     core bash -c "python '$TOOLS' mutate magic '$SM/hello.smc' '$SM/magic.smc' && ! '$UPSMC' verify '$SM/magic.smc'"

# Self-hosting chain on the corrected executor (fbb49594).
A="$OUT/artifacts"
step c1_from_c0 core ${TIMEV[@]+"${TIMEV[@]}"} "$C0SMC" compile "$WORK/sl/compiler/main.sm" -o "$A/C1.smc"
step c1_identity core python "$TOOLS" expect "$A/C1.smc" "$C1_SHA" "$C1_BYTES"
step c1_verify_upstream core "$UPSMC" verify "$A/C1.smc"
step c1_wrong_hash_rejected core must_fail "$UPSMC" run-smc "$A/C1.smc" --expect-sha256 "sha256:0000000000000000000000000000000000000000000000000000000000000000" --profile cli-read-only --root "$SM" -- hello.sm
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
