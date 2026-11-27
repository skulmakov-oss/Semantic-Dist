# 1. First programs

Every example here was saved to a file and run with the **public rc.2 portable `smc.exe`** (source fingerprint `4dfa17a48b77e39f`), as `.\smc.exe check <file>` and `.\smc.exe run <file>`. Exit code `0` means success. A failed `assert` or any error gives exit code `1`.

Language rules are defined normatively in [docs/spec @ v1.3.0-rc.2](https://github.com/skulmakov-oss/Semantic/tree/v1.3.0-rc.2/docs/spec). This chapter only shows the common forms.

## 1.1 The smallest program
Every program has `fn main()`, which ends with `return;`. `assert(condition)` stops the program with exit code 1 when the condition is false.
```
fn main() {
    assert(1 + 1 == 2);
    return;
}
```
*Run:* `check` passes, `run` exits 0.

## 1.2 Variables
`let` declares a variable with an explicit type. Add `mut` if you want to assign to it again.
```
fn main() {
    let x: i32 = 40;
    let mut y: i32 = 1;
    y = y + 1;
    assert(x + y == 42);
    return;
}
```
*Run:* exits 0.

## 1.3 Functions
Parameters and return values have explicit types.
```
fn add(a: i32, b: i32) -> i32 {
    return a + b;
}

fn main() {
    assert(add(40, 2) == 42);
    return;
}
```
*Run:* exits 0. As a full artifact pipeline:
```powershell
.\smc.exe compile 03_fn.sm -o 03_fn.smc   # compiled '03_fn.sm' -> '03_fn.smc' (225 bytes)
.\smc.exe verify 03_fn.smc               # verified '03_fn.smc' (2 function(s), header=SEMCOD22, epoch=0.23)
.\svm.exe run 03_fn.smc                  # exit code 0
```

## 1.4 Conditions and loops
`if`/`else` and `while` take a `bool` condition.
```
fn main() {
    let mut i: i32 = 0;
    let mut sum: i32 = 0;
    while i < 5 {
        sum = sum + i;
        i = i + 1;
    }
    if sum == 10 {
        assert(true);
    } else {
        assert(false);
    }
    return;
}
```
*Run:* exits 0.
```
fn main() {
    let ok: bool = true;
    assert(ok);
    assert(!false);
    return;
}
```
*Run:* exits 0.

## 1.5 Four-state values: `quad`
`quad` has four states: `N` (null/unknown), `F` (false), `T` (true) and `S` (conflict). It is **not** a `bool`. To branch on a `quad`, compare it explicitly or use `match`.
```
fn main() {
    let signal: quad = T;
    if signal == T {
        assert(true);
    }
    let unknown: quad = N;
    assert(unknown != T);
    return;
}
```
*Run:* exits 0.

Using a `quad` directly as a condition is rejected:
```
fn main() {
    let q: quad = T;
    if q {
        assert(true);
    }
    return;
}
```
*Run:* `check` fails with `Error [E0201]: if condition must be bool; explicit compare is required for quad`.

`match` on a `quad`:
```
fn describe(q: quad) -> i32 {
    match q {
        N => { return 0; }
        F => { return 1; }
        T => { return 2; }
        _ => { return 3; }
    }
}

fn main() {
    assert(describe(T) == 2);
    assert(describe(S) == 3);
    return;
}
```
*Run:* exits 0.

> **Observed in rc.2:** a `match` on `quad` needs a `_` arm. Listing `N`, `F`, `T` and `S` explicitly, without `_`, is rejected with `match requires default arm '_'`.

## 1.6 Optional values: `Option`
```
fn main() {
    let v: Option(i32) = Option::Some(7);
    let n: i32 = match v {
        Option::Some(x) => { x }
        _ => { 0 }
    };
    assert(n == 7);
    return;
}
```
*Run:* exits 0.

## 1.7 Records
```
record Point {
    x: i32,
    y: i32,
}

fn main() {
    let p: Point = Point { x: 3, y: 4 };
    assert(p.x + p.y == 7);
    return;
}
```
*Run:* exits 0.

## 1.8 When things go wrong
A failed assertion. `check` passes, but `run` exits 1 and prints `assertion failed`:
```
fn main() {
    assert(1 + 1 == 3);
    return;
}
```

A syntax error. `check` exits 1:
```
fn main() {
    let x: i32 = ;
}
```
```text
Error [E0005]: expected primary expression at line 2:18
```

A type error. `check` exits 1:
```
fn main() {
    let x: i32 = true;
    return;
}
```
```text
Error [E0201]: type mismatch in let 'x': I32 vs Bool at line 2:9
```

## Not covered here (not run for this chapter)
Imports and projects, capabilities (file and stdout effects), generics, traits, sequences and maps, and text handling are left to later chapters. Until then, see the specification.
