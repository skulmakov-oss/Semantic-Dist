# Proposed next manual sections (planning only)

| Section | Scope (tutorial) | Normative source at the tag | Notes |
|---|---|---|---|
| 7. Quad logic in depth | quad operators, comparisons, `match` patterns, decision tables | `docs/spec/types.md`, `docs/spec/quad_logic_frame_v1.md`, `docs/language/quad_language_design.md` | every operator must be run; only shipped operators |
| 8. Collections | sequences, maps, iteration, bounds | `docs/spec/source_semantics.md`, `foundation_stdlib_v0.md` | document quota interactions |
| 9. Types | records, enums/ADTs, `Option`/`Result`, tuples, generics boundary | `docs/spec/types.md` | generic **execution** is a documented boundary (F05) |
| 10. Memory and ownership | value semantics, borrows, move errors, ownership traps | `docs/spec/runtime_ownership.md` | explain, do not promise heap bounds (`quotas.md`) |

No implementation work is implied.
