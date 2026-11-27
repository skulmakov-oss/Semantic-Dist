# Language reference (v1.3.0-rc.2)

Organised by topic. Each section names its **normative** source at the tag and its **observed** evidence: the first manual chapter ([docs/manual/01_first_programs.md](../manual/01_first_programs.md)) or the probe record [observations.md](observations.md). Status words follow the evidence levels in [README.md](README.md). Constructs without an observed example are marked *not verified here*.

## 1. Lexical structure
Normative: [`syntax.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/syntax.md), [`source_style.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/source_style.md).
- Observed: integer literals (`40`, `0u32`), `true`/`false`, the quad literals `N F T S`, text literals (`"transformed:"`).
- Declared status: `literal.ascii_byte` is current-main-experimental.
- Documented (in `docs/getting_started.md` at the tag; not a normative spec, *not verified here*): string literals have no escape processing in the current contract.

## 2. Declarations
Normative: [`source_semantics.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/source_semantics.md), [`types.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/types.md).
- Observed: `fn name(p: T) -> R { … }`; `let x: T = e;`; `let mut x: T = e;` with reassignment; `record Point { x: i32, y: i32, }` and its literal `Point { x: 3, y: 4 }`.
- Declared status: top-level `const` (`item.const.top_level`) is unsupported.
- *Not verified here:* enums/ADT declarations, schemas, closures, generic functions.

## 3. Types
Normative: [`types.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/types.md), [`foundation_stdlib_v0.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/foundation_stdlib_v0.md).
- Observed: `i32`, `u32` (literal `0u32`), `bool`, `quad`, `text`, `Option(i32)`, records.
- Normative: `Option(T)` and `Result(T, E)` are language-owned standard families. `Sequence(T)` and `Map(K, V)` exist with the helpers listed in foundation_stdlib_v0.md. `i32 / i32` is outside the first arithmetic wave (source_semantics.md).
- Declared status: checked `u32` arithmetic (`arithmetic.u32.checked`) is current-main-experimental.
- *Not verified here:* `f64`, tuples, `Result`, sequences, maps.

## 4. Expressions and operators
Normative: [`source_semantics.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/source_semantics.md).
- Observed: `+`, `==`, `!=`, `<`, `!` on `bool`; all quad operators ([quad_logic.md](quad_logic.md)).
- Normative: `&&` and `||` evaluate **both** operands, left to right, for `bool` and `quad` alike.
- Declared status: `?` (`operator.try`) and `??` (`operator.coalesce`) are unsupported.

## 5. Statements and control flow
Normative: [`source_semantics.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/source_semantics.md), [`branch_condition_quad_rule.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/branch_condition_quad_rule.md).
- Observed: `if`/`else` (condition must be `bool`), `while`, `match` with `_`, `assert(bool)`, `return;`, and `match` as an expression on `Option`.
- Normative: a `quad` `match` requires `_`; an enum `match` may omit `_` only when unguarded coverage is exhaustive; at most one `_` arm.
- Declared status: or-patterns, integer range patterns and `let … else` with ADT patterns are unsupported; `if let` is current-main-experimental.
- *Not verified here:* `loop`, `break`, `continue`, `for`, guards.

## 6. Functions
- Observed: a final `return;` in a unit function is optional (`fn main() {}` passes). A value-returning function uses `return expr;`: a bare tail expression `40 + 2` was rejected with `expected ';'`.
- Declared status: `control.function.return_completeness` is current-main-experimental.
- *Not verified here:* `requires`/`ensures` contracts.

## 7. Modules, projects and packages
Normative: [`modules.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/modules.md), [`project_model_v0.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/project_model_v0.md), [`package_baseline_v0.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/package_baseline_v0.md).
- Observed ([observations.md](observations.md#projects-and-packages)): `semantic.toml` with `[project] entry`; `Import "lib.sm" { double }`; `Semantic.package` with `dep <alias> <name> <path>` and `Import "m::main.sm"`; rejections for a missing dependency and for an entry that escapes the root.

## 8. Ownership and borrowing
Normative: [`runtime_ownership.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/runtime_ownership.md).
- Observed: statement and expression `match` with a `ref` capture both enforce `write path overlaps active borrow` (Semantic #2056 closed).
- Known open issue: E0201 false positive on tuple destructuring in a loop (Semantic #2045, reproduced on rc.2).

## 9. Capabilities and the host boundary
Normative: [`capabilities.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/capabilities.md), [`controlled_application_boundary_v0.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/controlled_application_boundary_v0.md), [`abi.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/abi.md).
- Observed ([observations.md](observations.md#capabilities-run-in-f08_file_transformsandbox)): `args_read`, `fs_read_text`, `fs_write_text` and `stdout_write` under the profiles `pure`, `cli-read-only` and `cli-file-transform`. Every denial exited 1 and wrote nothing.

## 10. Diagnostics
Normative: [`diagnostics.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/diagnostics.md), [`diagnostics_machine_schema_v1.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/diagnostics_machine_schema_v1.md), [`ERROR_CODES.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/ERROR_CODES.md).
- Observed ([observations.md](observations.md#artifacts-and-diagnostics)): `--format json` (schema `semantic.diagnostics` v1), `explain E0201`, E0005/E0201 messages. Every measured failure exited 1.

## 11. Artifacts, verifier, VM and quotas
Normative: [`semcode.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/semcode.md), [`verifier.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/verifier.md), [`vm.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/vm.md), [`quotas.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/quotas.md), [`ir.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/ir.md).
- Observed ([observations.md](observations.md#artifacts-and-diagnostics)): compile → verify → run; `artifact hash`/`inspect`; `disasm`; `--expect-sha256`; header `SEMCOD22` (epoch 0, rev 23).
- Declared status: SemCode floor `SEMCOD22`, promotions `SEMCOD23`–`SEMCOD25`.

## 12. Compiler subset (C1)
Normative (Semantic-Language): [`BOOTSTRAP_SUBSET.md`](https://github.com/skulmakov-oss/Semantic-Language/blob/main/docs/BOOTSTRAP_SUBSET.md).
- Observed ([observations.md](observations.md#frozen-c1-semantic-selfhost-compiler-c1smc-sha256-2bfd56e1)): C1 output is byte-identical to `smc compile` for 6 programs. C1 rejects `Import` and capability calls with an `error` line while `run-smc` exits 0 (findings F6).
