#!/usr/bin/env bash
# Targeted RED/GREEN check of one exact Semantic commit (test-only, GO-05).
# HQ_EXPECT=fail requires a real libtest failure ("test result: FAILED") whose
# output matches HQ_PATTERN; a build error or any other failure does not count.
# HQ_EXPECT=pass requires every command to succeed, HQ_REQUIRE (if set) to
# match and HQ_FORBID (if set) not to match.
set -uo pipefail
OUT="${HQ_OUT:?}"; WORK="${HQ_WORK:?}"; SHA="${HQ_SHA:?}"; EXPECT="${HQ_EXPECT:?}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"; TOOLS="$HERE/nq_tools.py"
mkdir -p "$OUT" "$WORK"
python "$TOOLS" env "$OUT/env.json" "${HQ_ARCH:?}" > "$OUT/env.log" 2>&1 || { echo "architecture check failed"; cat "$OUT/env.log"; exit 1; }
git -c core.autocrlf=false -c core.eol=lf clone -q --filter=blob:none --no-checkout https://github.com/skulmakov-oss/Semantic "$WORK/sem"
git -C "$WORK/sem" checkout -q "$SHA"
[ "$(git -C "$WORK/sem" rev-parse HEAD)" = "$SHA" ] || { echo "head mismatch"; exit 1; }
echo "sha=$SHA tree=$(git -C "$WORK/sem" rev-parse 'HEAD^{tree}')" > "$OUT/source.txt"
: > "$OUT/all.log"; rcs=""
while IFS= read -r cmd; do
  [ -n "$cmd" ] || continue
  echo "### cargo test --locked $cmd -- --show-output" | tee -a "$OUT/all.log"
  (cd "$WORK/sem" && eval "cargo test --locked $cmd -- --show-output") >> "$OUT/all.log" 2>&1
  rc=$?; rcs="$rcs $rc"; echo "### exit=$rc" | tee -a "$OUT/all.log"
done < <(python -c 'import json,os;[print(c) for c in json.loads(os.environ["HQ_CMDS"])]' | tr -d '\r')
python "$TOOLS" tests "$OUT/all.log" "$OUT/tests.json"
verdict=FAIL
if [ "$EXPECT" = fail ]; then
  if grep -q "test result: FAILED" "$OUT/all.log" && grep -Eq "${HQ_PATTERN:?}" "$OUT/all.log"; then verdict="RED-CONFIRMED"; fi
else
  ok=1; for r in $rcs; do [ "$r" = 0 ] || ok=0; done
  [ -z "${HQ_REQUIRE:-}" ] || grep -Eq "${HQ_REQUIRE}" "$OUT/all.log" || ok=0
  [ -z "${HQ_FORBID:-}" ] || ! grep -Eq "${HQ_FORBID}" "$OUT/all.log" || ok=0
  [ $ok = 1 ] && verdict="GREEN"
fi
echo "expect=$EXPECT exits=[$rcs ] verdict=$verdict" | tee "$OUT/verdict.txt"
[ "$verdict" != FAIL ]
