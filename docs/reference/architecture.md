# Architecture reference

**Status:** non-normative reference.

**Pinned sources:**
- Semantic tag `v1.3.0-rc.2` (`98f9db19`) `docs/spec/`;
- Semantic-Language `26cc93f5` `docs/`;
- this repository's `upstream_anchor.json` and `manifests/selfhost_pin.json`.

If this page and a normative source differ, the normative source wins.

**Labels used on this page:**
- **Design:** stated by a normative source.
- **Observed:** seen with the public rc.2 binaries while writing these docs; not a formal qualification.
- **Derived:** concluded from the cited sources.

Packaging and installers are described separately in [../architecture.md](../architecture.md). That document is not repeated here.

## 1. Repositories and ownership
| Repository | Owns | Source |
|---|---|---|
| `skulmakov-oss/Semantic` | Language authority, the Rust reference compiler (C0), the SemCode format, `sm-verify`, `sm-vm` and the PROMETHEUS capability/ABI layer | [ARCHITECTURE.md](https://github.com/skulmakov-oss/Semantic-Language/blob/26cc93f59a3375a428c43ac4ab04eb9364cbec97/docs/ARCHITECTURE.md) §2; [index.md](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/index.md) |
| `skulmakov-oss/Semantic-Language` | The self-hosted compiler source `S`, written in Semantic, plus its harnesses and C1/C2 evidence | [OWNERSHIP.md](https://github.com/skulmakov-oss/Semantic-Language/blob/26cc93f59a3375a428c43ac4ab04eb9364cbec97/docs/OWNERSHIP.md) rule 3 |
| `skulmakov-oss/Semantic-Dist` | Distribution: the upstream anchor, provenance, packaging and these docs | [../architecture.md](../architecture.md) §1 |

**Design:**
- One public concept has one owner.
- A capability that `S` needs is implemented and qualified upstream first.
- Ownership transfers only through a recorded decision ([OWNERSHIP.md](https://github.com/skulmakov-oss/Semantic-Language/blob/26cc93f59a3375a428c43ac4ab04eb9364cbec97/docs/OWNERSHIP.md) rules 1, 2 and 4).

## 2. From source to execution
```text
source (.sm)
  -> frontend: parse, resolve, typecheck            [sm-front]
  -> IR + lowering                                  [ir.md]
  -> SemCode artifact (.smc): versioned header       [semcode.md]
  -> verifier admission (structural, fail-closed)   [verifier.md]
  -> VM execution (deterministic, quota-bounded)    [vm.md]
  -> host effects only via capability check + ABI   [capabilities.md]
```

**Design:**
- **IR.** The IR is "the explicit lowered execution-contract boundary". The downstream binary contract is owned by SemCode, not by the IR ([ir.md](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/ir.md)).
- **SemCode.**
  - A producer emits exactly one supported header variant.
  - A verifier rejects unknown or unsupported headers.
  - A VM never reinterprets an unsupported header.
  - Incompatible changes need a version bump ([semcode.md](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/semcode.md), "Version Policy").
- **Verifier.**
  - It is a public admission layer. It is not a parser, runtime, executor or optimizer.
  - It rejects only malformed or contract-inconsistent bytecode ([verifier.md](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/verifier.md), "Purpose" and "Separation Rule").
- **VM.**
  - It executes verified SemCode deterministically, manages frames and enforces quotas.
  - It does not own the binary contract or the capability policy ([vm.md](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/vm.md), "Purpose").
  - On a route without a host, a host-effect opcode fails with an ABI `Unavailable` error. The VM never fabricates host values ("No-Host Execution").
- **Host boundary.**
  - Host effects pass only through the ABI host trait and the capability check.
  - A missing capability rejects the effect **before** the host call ([capabilities.md](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/capabilities.md), "Enforcement Rule").
  - Semantic-Language states the same rule as "the host performs mechanics; Semantic performs compiler meaning" ([HOST_BOUNDARY.md](https://github.com/skulmakov-oss/Semantic-Language/blob/26cc93f59a3375a428c43ac4ab04eb9364cbec97/docs/HOST_BOUNDARY.md) §1).

**Observed:**
- `smc verify` rejected an artifact with an unsupported header: exit 1, `verify error [UnsupportedVersion] @0x0000: unsupported SemCode header 'NOTSEMCO'` (upstream example `examples/qualification/ssf11/f09_verifier_rejection`).
- A capability not granted by the selected profile is denied with `MissingCapability`, and nothing is written.
- A path outside `--root` is refused. See the user manual, chapters 3 and 4.

## 3. Artifact identity
**Design:**
- An artifact is identified by its exact bytes.
- `run-smc --expect-sha256` refuses to run an artifact whose SHA-256 differs ([cli.md](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/cli.md)).

**Observed:**
- `smc artifact hash` printed `sha256:<hex>` equal to the file's SHA-256 for a test artifact.
- A wrong `--expect-sha256` produced `artifact identity mismatch` with exit 1.

**Derived:**
- Identity is integrity, not authorship. rc.2 artifacts and binaries are unsigned (see the [status glossary](../status_glossary.md)).
- Package fingerprints from `smc package inspect` use `fnv1a64-non-cryptographic`. They are content identities, not security hashes.

## 4. Quotas: counts, not cost
**Design:**
- **Quota kinds:** `Steps`, `Calls`, `StackDepth`, `Frames`, `Registers`, `SymbolTable` and `EffectCalls`.
- **Who enforces:** `sm-vm` enforces them at run time. The exception is `SymbolTable`, which `sm-verify` enforces at admission.
- **Envelopes:** an integration layer may choose another envelope only if the divergence is recorded in provenance.

  (All from [quotas.md](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/quotas.md), "Purpose" and "Quota Taxonomy".)
- **Non-claims:**
  - `Steps` counts decoded opcodes. One step can copy a value of unbounded size.
  - No quota bounds bytes, aggregate heap or wall-clock time.
  - Raising `max_steps` or `max_frames` is not a memory or time safety measure (same file, "Non-claims").

**Observed:** an infinite loop under default `smc run` stopped with `quota exceeded: Steps limit=100000 used=100001` (exit 1).

## 5. Bootstrap: C0, S, C1, C2 and the Seal
**Design** ([BOOTSTRAP_CONTRACT.md](https://github.com/skulmakov-oss/Semantic-Language/blob/26cc93f59a3375a428c43ac4ab04eb9364cbec97/docs/BOOTSTRAP_CONTRACT.md) §1 and §7; [ARCHITECTURE.md](https://github.com/skulmakov-oss/Semantic-Language/blob/26cc93f59a3375a428c43ac4ab04eb9364cbec97/docs/ARCHITECTURE.md) §8):

**Terms:**
- **C0:** the Rust reference compiler at a pinned Semantic SHA.
- **S:** the compiler source set, written in Semantic.
- **C1** = `C0(S)`.
- **C2** = `C1(S)`, produced by running the admitted C1 in the VM.

**Steps:**
1. C0 compiles `S` to C1.
2. C1 is admitted and executed to compile `S` to C2.
3. C2 is admitted but not executed.
4. A fixed point means `Canonical(C1) == Canonical(C2)`.
5. If the fixed point passes with zero unexplained deltas, a **Bootstrap Seal** records:
   - the C0 SHA;
   - the source-set identity;
   - the C1 and C2 identities;
   - the comparison rule;
   - the contract identities;
   - the platforms;
   - the remaining Rust responsibilities.

**Pinned for rc.2** (this repository's `manifests/selfhost_pin.json`):

| Item | Value |
|---|---|
| `S` | Semantic-Language `5b404e5f` (source-set identity `sha256:c9e0cb33…`) |
| C0 | Semantic `1d1e76c7` (historical reference compiler of Bootstrap Contract v4) |
| C1 | sha256 `2bfd56e1…e939`, 339,746 bytes |
| Runtime envelope | `max_steps` 150,000,000, `max_calls` 2,000,000, `max_frames` 256 |

**Status** (statuses only as recorded in the [status glossary](../status_glossary.md)):
- The self-hosting fixed point is **qualified** under Bootstrap Contract v4. Four-target CI runs are **repeatability evidence**.
- The Bootstrap Seal is **validated**; **not reproduced**; **not accepted**.

**Observed:**
- C1, run with the public `smc run-smc` and the envelope above, compiled small programs to bytes identical to `smc compile`.
- C1 exits 0 also when it rejects a program. Accept its output only by a fail-closed criterion: exit 0, exactly one valid `hex` result line, and the decoded artifact passing `smc verify`. A CLI reference and a Cookbook with this criterion are pending review in separate pull requests.
- Tracked as skulmakov-oss/Semantic#2105.

## 6. Distribution, anchor and provenance
**Design** (this repository's `upstream_anchor.json`):
- The release builds from Semantic at a pinned commit, `98f9db199b28d6b126873f8f445aaff49b83d674` for rc.2, with:
  - an immutable checkout;
  - a clean tree;
  - a lockfile hash match;
  - no automatic tracking of upstream `main`.
- **SemCode policy:**
  - default emitted header `SEMCOD22` (rev 23);
  - supported revisions 1–26;
  - verifier rule `strict-fail-closed`.

**Derived:**
- The workflow "Verify Upstream Provenance & Anchor Schema" runs on pull requests and on pushes to `main`. A release artifact can therefore be traced to one upstream commit and one lockfile.
- That traceability is provenance, not a signature.

## 7. Known open questions (not resolved here)
- **skulmakov-oss/Semantic#2103:** "known" means F or T in `semantic-core-quad` but any non-N state in the spec. Not fixed.
- **skulmakov-oss/Semantic#2104:** the readable quad predicates `known`, `unknown` and `conflict` are documented but not available in rc.2. Not fixed.
