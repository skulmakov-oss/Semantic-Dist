# Findings (v1.3.0-rc.2)
Recorded only. **No specification or source change is made or implied, and no issue was opened.**

## F1 (unresolved discrepancy): what counts as "known"
| Source | Definition of "known" | Includes `S`? |
|---|---|---|
| [`quad_logic_frame_v1.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/quad_logic_frame_v1.md) (frozen spec draft) | "Known / Non-null (any state other than `N`)" | **yes** |
| `docs/language/quad_predicate_vocabulary.md` and `quad_language_design.md` (design notes) | `known(x)` = `x != N` | **yes** |
| `docs/research/quad_logic_execution_model_v0_1.md` (research) | `is_known(q)` = `F ∨ T ∨ S` ("treats conflict as known") | **yes** |
| crate `semantic-core-quad` `QuadState::is_known()` | `F` or `T` | **no** |
| crate `QuadMasks32::known()` / `QuadroReg32::mask_known()` | lanes in state `T` or `F` | **no** |

Callers of `is_known` / `mask_known` at the tag (read-only `git grep`):
- `semantic-core-exec` `Instr::QIsKnown`, used by the `core-lab`, `semantic-core-bench` and `semantic-core-capsule` crates;
- the delta functions in `semantic-core-quad` (`became_known` / `became_unknown` and the plane / exact-state delta paths).

`sm-vm`, `sm-ir`, `sm-front` and `sm-format` have no `QIsKnown` and no caller. **Source programs on rc.2 are not affected**: no source predicate reaches them (see F2).

Two readings are possible. *Non-null evidence* (`≠ N`, includes `S`) differs from *determinate, non-conflicting truth* (`F` or `T`, excludes `S`). Under the crate reading, a lane moving `N → S` is not counted as "became known", and `QIsKnown(S)` is `false`.

Alternatives (owner decision; none applied):
- A: rename the crate predicate to `is_determinate` and keep `known` = `≠ N`;
- B: amend the spec draft to the crate meaning;
- C: provide both, with explicit names.

## F2 (unresolved discrepancy): readable predicates documented but unavailable
- `types.md` (normative) lists `known(a)`, `unknown(a)`, `conflict(a)` and `a is S` as "readable quad predicate, surface alias for an existing bool predicate".
- Design notes define the aliases: `known(x)`→`x != N`, `unknown(x)`→`x == N`, `conflict(x)`→`x == S`, `x is S`→`x == S`. `semantic_sugar_track.md` has **Status: proposal**.
- Tag source (read-only): the parser and typechecker contain `is` (`q is S`). `known`, `unknown` and `conflict` are not built-ins in `sm-front`.
- Observed: `q is S` is admitted; `known(q)`, `unknown(q)` and `conflict(q)` fail with `unknown function` under `smc run`.
- **Probe scope:** `smc run` on single-file programs with the rc.2 binary; one probe per predicate, plus `known(S)`. Projects, `check --format json` and `language describe` entries were not probed for these names.

Regression matrix proposed for whichever option is chosen:
| Case | Expected if aliases are added | Expected if docs are narrowed |
|---|---|---|
| `known(N/F/T/S)` | `false/true/true/true` | rejected, `unknown function` |
| `unknown(N/F/T/S)` | `true/false/false/false` | rejected |
| `conflict(N/F/T/S)` | `false/false/false/true` | rejected |
| `q is N/F/T/S` | `== N/F/T/S` | unchanged |
| `if known(q)` | admitted (bool) | rejected |

Alternatives: (a) add the three aliases in a future source change; (b) mark them "proposal, not available" in `types.md`. Either is an owner decision through the normal governance path.

## F3–F7 (observations)
| ID | Observation |
|---|---|
| F3 | `a -> b` and `qtruth_impl` have identical tables but distinct opcodes. Both differ from conventional material implication ([quad_logic.md §4](quad_logic.md)). |
| F4 | Quad `&&`/`||` are declared **current-main-experimental**; bool `&&`/`||` are foundation-included. |
| F5 | `semantic_stable_foundation_matrix.md` at the tag is an SSF-00 snapshot; its release facts predate the published v1.2.0. |
| F6 | `run-smc` with the frozen C1 exits 0 when C1 rejects a program; the rejection is an `error …` line. |
| F7 | `_` is required in a `quad` `match` (normative), unlike an exhaustive enum `match`. |
