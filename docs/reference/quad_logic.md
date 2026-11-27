# Quad logic reference (v1.3.0-rc.2)

Normative sources (tag): [`quad_logic_frame_v1.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/quad_logic_frame_v1.md), [`types.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/types.md), [`source_semantics.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/source_semantics.md), [`foundation_stdlib_v0.md`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/foundation_stdlib_v0.md).

**Measurement scope:**
- Every table cell below is **observed** with the public rc.2 `smc.exe` (fingerprint `4dfa17a48b77e39f`), one `smc run` per candidate value: 544 runs in total.
- The lattice and truth-map results match all **104** rows of the tag's golden table [`quad_4x4_static.csv`](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/tests/golden_snapshots/s2043/quad_4x4_static.csv): 16 rows each for implies, lattice and/or, truth and/or/impl; 4 rows each for not and truth not.
- Equality predicates are not in that golden file; they were measured separately (32 cells).

## 1. Values
| Value | (t,f) planes | Bits | Meaning (normative, types.md) |
|---|---|---|---|
| `N` | (0,0) | `00` | unknown |
| `F` | (0,1) | `01` | false |
| `T` | (1,0) | `10` | true |
| `S` | (1,1) | `11` | conflict |

`N` is a value meaning *no evidence*. It is not a null reference and not `Option::None`. `S` means *conflicting evidence*: it is the fourth value, not a `bool`.

## 2. Operator families (normative: source_semantics.md, foundation_stdlib_v0.md)
| Family | Source form | Result | Plane formula | Declared status (`smc language describe`) |
|---|---|---|---|---|
| Identity predicate | `a == b`, `a != b` | `bool` | same / different value | — |
| Knowledge lattice (legacy operators) | `a && b`, `a \|\| b`, `!a`, `a -> b` | `quad` | meet `(a.t&b.t, a.f&b.f)`; join `(a.t\|b.t, a.f\|b.f)`; `!a=(a.f,a.t)`; `a->b=(a.f\|b.t, a.t\|b.f)` | `logic.quad.and_or`: **current-main-experimental** |
| Truth map (Belnap) | `qtruth_and`, `qtruth_or`, `qtruth_not`, `qtruth_impl` | `quad` | `(a.t&b.t, a.f\|b.f)`; `(a.t\|b.t, a.f&b.f)`; `(a.f,a.t)`; `(a.f\|b.t, a.t\|b.f)` | `std.quad`: **Selected** in foundation_stdlib_v0.md |

The specification states that the families "never alias each other". Implementation note (observed in the tag source): the lattice operators use the `QAnd`/`QOr`/`QNot`/`QImpl` opcodes; the truth map uses `QTruthAnd`/`QTruthOr`/`QTruthNot`/`QTruthImpl`.

## 3. Observed tables (rows `a`, columns `b`)
| a && b | N | F | T | S |
|---|---|---|---|---|
| **N** | N | N | N | N |
| **F** | N | F | N | F |
| **T** | N | N | T | T |
| **S** | N | F | T | S |

| `a \|\| b` | N | F | T | S |
|---|---|---|---|---|
| **N** | N | F | T | S |
| **F** | F | F | S | S |
| **T** | T | S | T | S |
| **S** | S | S | S | S |

| a -> b (legacy implication) | N | F | T | S |
|---|---|---|---|---|
| **N** | N | F | T | S |
| **F** | T | S | T | S |
| **T** | F | F | S | S |
| **S** | S | S | S | S |

| `!a` | N | F | T | S |
|---|---|---|---|---|
| | N | T | F | S |

| qtruth_and(a, b) | N | F | T | S |
|---|---|---|---|---|
| **N** | N | F | N | F |
| **F** | F | F | F | F |
| **T** | N | F | T | S |
| **S** | F | F | S | S |

| qtruth_or(a, b) | N | F | T | S |
|---|---|---|---|---|
| **N** | N | N | T | T |
| **F** | N | F | T | S |
| **T** | T | T | T | T |
| **S** | T | S | T | S |

| qtruth_impl(a, b) | N | F | T | S |
|---|---|---|---|---|
| **N** | N | F | T | S |
| **F** | T | S | T | S |
| **T** | F | F | S | S |
| **S** | S | S | S | S |

| `qtruth_not(a)` | N | F | T | S |
|---|---|---|---|---|
| | N | T | F | S |

### Equality predicates (observed, 32 cells)
`a == b` is `true` exactly when `a` and `b` are the same value, and `a != b` is its negation. `S == S` is `true : bool`; `S && S` is `S : quad`.

## 4. Two implications
| | Definition | Observed table (rows N,F,T,S) |
|---|---|---|
| **Legacy implication** `a -> b` and `qtruth_impl(a, b)` | `NOT(a) join b` = `(a.f\|b.t, a.t\|b.f)` (normative, frozen; `qtruth_impl(T,T) = S`) | N F T S / T S T S / F F S S / S S S S |
| **Conventional material implication** in the truth map, written `qtruth_or(qtruth_not(a), b)` | `(a.f\|b.t, a.t&b.f)` | N N T T / T T T T / N F T S / T S T S |

- The legacy rule is **not** conventional material implication. For example, `T -> T` is `S`, not `T`.
- `a -> b` and `qtruth_impl` give the same table, but they are separate operations with different opcodes. Identical output does not mean identical implementation.

## 5. Orders (derived, not separately normative)
Both orders are **mathematically derived** from the normative plane formulas. The specification does not state either order as its own contract.

| Order | Definition | Covering edges | Consistency check |
|---|---|---|---|
| Knowledge order ≤k | `a ≤k b` iff `a.t ≤ b.t` and `a.f ≤ b.f` | N < F, N < T, F < S, T < S | `&&` = greatest lower bound and `\|\|` = least upper bound in 16/16 cells |
| Truth order ≤t | `a ≤t b` iff `a.t ≤ b.t` and `a.f ≥ b.f` | N < T, F < N, F < S, S < T | `qtruth_and` = glb and `qtruth_or` = lub in 16/16 cells |

Bottom/top: knowledge `N`/`S`; truth `F`/`T`.

## 6. Boolean boundary (observed; normative where cited)
| Form | Result |
|---|---|
| `if q {}` | rejected, `if condition must be bool; explicit compare is required for quad` (types.md) |
| `if q == T {}` | admitted |
| `let b: bool = q;` | rejected, `type mismatch … Bool vs Quad` |
| `q && true` | rejected, `operator type mismatch: Quad vs Bool` |
| `match q {…}` without `_` | rejected, `match requires default arm '_'` (source_semantics.md) |
| `q is S` | admitted, `bool` |
| `known(q)`, `unknown(q)`, `conflict(q)` | **rejected**, `unknown function`; see findings F2 |

No implicit `quad` → `bool` conversion exists. The explicit routes are a comparison or a `match`.

## 7. Representations
- **Scalar:** one 2-bit lane (`QuadState`, crate `semantic-core-quad`).
- **Packed:** `QuadroReg32` in the crate (32 lanes in a `u64`). **No source-level packed type is available**; `qvec(N)` is reserved at parser level (types.md). Packed forms are implementation detail.
