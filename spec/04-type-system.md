# STOKED Language Specification

## Chapter 4 — Type System

---

This chapter defines the type system of STOKED: the kind system, type universe, subtyping relation, and typing judgments for expressions, processes, stations, and distributions.

## 4.1 Kinds

Every type in STOKED is classified by a *kind*. Kinds prevent ill-formed type expressions.

```
K ::= Type                    -- the kind of value types
    | Dist                    -- the kind of distribution types
    | Proc                    -- the kind of process types
    | Chan                    -- the kind of channel types
    | Res                     -- the kind of resource types
    | K -> K                  -- type-level functions (parameterized types)
```

**Kind assignment rules:**

```
─────────────────── [K-Base]
⊢ Bool : Type       ⊢ Int : Type       ⊢ Float : Type
⊢ String : Type     ⊢ Unit : Type      ⊢ Duration : Type
⊢ Rate : Type

    ⊢ T : Type
─────────────────── [K-Chan]
⊢ Chan<T> : Chan

    ⊢ T : Type
─────────────────── [K-Dist]
⊢ Dist<T> : Dist

    n ∈ ℕ⁺
─────────────────── [K-Res]
⊢ Resource<n> : Res

─────────────────── [K-Proc]
⊢ proc : Proc

    ⊢ T₁ : Type    ⊢ T₂ : Type
─────────────────────────────────── [K-Record]
⊢ { f₁: T₁, ..., fₙ: Tₙ } : Type

    ⊢ T : Type
─────────────────── [K-List]
⊢ List<T> : Type

    ⊢ T : Type
─────────────────── [K-Option]
⊢ Option<T> : Type

    ⊢ T : Type
─────────────────── [K-Set]
⊢ Set<T> : Type

    ⊢ T₁ : Type  ...  ⊢ Tₙ : Type
──────────────────────────────────── [K-Tuple]
⊢ (T₁, ..., Tₙ) : Type

    ⊢ T₁ : Type  ...  ⊢ Tₙ : Type
──────────────────────────────────── [K-Variant]
⊢ C₁(T₁) | ... | Cₙ(Tₙ) : Type

    ⊢ Tₖ : Type    ⊢ Tᵥ : Type
─────────────────────────────────── [K-Map]
⊢ Map<Tₖ, Tᵥ> : Type
```

## 4.2 Type Universe

The complete type universe of STOKED is organized in four layers:

### 4.2.1 Base Types

```
τ_base ::= Bool | Int | Float | String | Unit | Duration | Rate
```

**Duration** and **Rate** are dimensioned types. Duration values carry time units; Rate values carry inverse-time units. The type system enforces dimensional consistency:

```
    Γ ⊢ e₁ : Duration    Γ ⊢ e₂ : Duration
    ────────────────────────────────────────── [T-DurAdd]
    Γ ⊢ e₁ + e₂ : Duration

    Γ ⊢ e₁ : Float    Γ ⊢ e₂ : Duration
    ────────────────────────────────────────── [T-DurScale]
    Γ ⊢ e₁ * e₂ : Duration

    Γ ⊢ e₁ : Rate    Γ ⊢ e₂ : Duration
    ────────────────────────────────────────── [T-LittlesWIP]
    Γ ⊢ e₁ * e₂ : Float

    Γ ⊢ e : Duration    e > 0
    ────────────────────────────── [T-DurToRate]
    Γ ⊢ 1/e : Rate
```

### 4.2.2 Composite Types

```
τ_comp ::= { f₁: T₁, ..., fₙ: Tₙ }           -- records
         | C₁(T̄₁) | ... | Cₖ(T̄ₖ)              -- variants
         | List<T>                               -- lists
         | Set<T>                                -- sets
         | Map<K, V>                             -- maps
         | (T₁, T₂, ..., Tₙ)                    -- tuples
         | Option<T>                             -- optionals
```

### 4.2.3 Domain-Specific Types

```
τ_domain ::= Chan<T>                            -- typed channel
           | Dist<T>                             -- distribution over T
           | Resource<n>                         -- resource with capacity n
```

### 4.2.4 Process Types

```
τ_proc ::= proc                                 -- the type of processes
```

All well-typed process expressions have type `proc`. The process type does not carry additional information in this version of STOKED; behavioral properties are verified by the well-formedness conditions (§8) rather than encoded in the type.

## 4.3 Type Environments

A *type environment* Γ is a finite ordered sequence of bindings:

```
Γ ::= ∅                                         -- empty environment
    | Γ, x : T                                  -- value binding
    | Γ, a : Chan<T>                             -- channel binding
    | Γ, s : Station(T_in, T_out)                -- station binding
    | Γ, r : Resource<n>                         -- resource binding
    | Γ, X : proc                                -- process variable binding
```

**Well-formedness of environments:**

```
────────── [Env-Empty]
⊢ ∅ ok

    ⊢ Γ ok    x ∉ dom(Γ)    ⊢ T : Type
    ───────────────────────────────────── [Env-Var]
    ⊢ (Γ, x : T) ok
```

## 4.4 Subtyping

STOKED has structural subtyping for records (width and depth) and nominal subtyping for variants.

```
─────────── [Sub-Refl]
T <: T

    T₁ <: T₂    T₂ <: T₃
    ─────────────────────── [Sub-Trans]
    T₁ <: T₃

    ∀i. Tᵢ <: Uᵢ    m ≥ n
    ──────────────────────────────────────────────────────────── [Sub-Record]
    { f₁: T₁, ..., fₘ: Tₘ } <: { f₁: U₁, ..., fₙ: Uₙ }

    ∀i ∈ 1..m. ∃j ∈ 1..n. Cᵢ = Dⱼ ∧ T̄ᵢ <: Ūⱼ     m ≤ n
    ──────────────────────────────────────────────────────────── [Sub-Variant]
    C₁(T̄₁) | ... | Cₘ(T̄ₘ)  <:  D₁(Ū₁) | ... | Dₙ(Ūₙ)

    T <: U
    ──────────────────── [Sub-List]
    List<T> <: List<U>

Lists in STOKED are immutable value types, making covariance sound.

    T <: U
    ────────────────────────── [Sub-Option]
    Option<T> <: Option<U>

    T <: U
    ────────────────────────── [Sub-Dist]
    Dist<T> <: Dist<U>
```

**Channel subtyping** is *invariant* — `Chan<T> <: Chan<U>` if and only if `T = U`. This prevents type errors in concurrent communication.

```
    T = U
    ──────────────────── [Sub-Chan]
    Chan<T> <: Chan<U>
```

### 4.4.1 Numeric Coercions

```
──────────────── [Sub-IntFloat]
Int <: Float
```

Integer values may be used where Float is expected. This is the only implicit coercion in STOKED.

## 4.5 Typing Judgments for Expressions

```
    x : T ∈ Γ
    ─────────────── [T-Var]
    Γ ⊢ x : T

    ──────────────────── [T-Int]
    Γ ⊢ n : Int          (where n is an integer literal)

    ──────────────────── [T-Float]
    Γ ⊢ r : Float        (where r is a float literal)

    ──────────────────── [T-Bool]
    Γ ⊢ b : Bool         (where b ∈ {true, false})

    ──────────────────── [T-String]
    Γ ⊢ s : String       (where s is a string literal)

    ──────────────────── [T-Unit]
    Γ ⊢ () : Unit

    ──────────────────── [T-Time]
    Γ ⊢ t : Duration     (where t is a time literal)

    ──────────────────── [T-Rate]
    Γ ⊢ r : Rate         (where r is a rate literal)

    Γ ⊢ e : T    T <: U
    ───────────────────── [T-Sub]
    Γ ⊢ e : U

    Γ ⊢ e₁ : Int    Γ ⊢ e₂ : Int    ⊕ ∈ {+,-,*,/,%}
    ──────────────────────────────────────────────────── [T-ArithInt]
    Γ ⊢ e₁ ⊕ e₂ : Int

    Γ ⊢ e₁ : Float    Γ ⊢ e₂ : Float    ⊕ ∈ {+,-,*,/}
    ──────────────────────────────────────────────────────── [T-ArithFloat]
    Γ ⊢ e₁ ⊕ e₂ : Float

    Γ ⊢ e₁ : T    Γ ⊢ e₂ : T    T ∈ {Int, Float, Duration}
    ──────────────────────────────────────────────────────────── [T-Compare]
    Γ ⊢ e₁ < e₂ : Bool          (likewise for <=, >, >=, ==, !=)

    Γ ⊢ e₁ : Bool    Γ ⊢ e₂ : Bool
    ──────────────────────────────── [T-Logic]
    Γ ⊢ e₁ and e₂ : Bool         (likewise for or)

    Γ ⊢ e : Bool
    ──────────────── [T-Not]
    Γ ⊢ not e : Bool

    Γ ⊢ e : { ..., f : T, ... }
    ───────────────────────────── [T-Field]
    Γ ⊢ e.f : T

    Γ ⊢ eᵢ : Tᵢ   for all i
    ─────────────────────────────────── [T-Record]
    Γ ⊢ { f₁: e₁, ..., fₙ: eₙ } : { f₁: T₁, ..., fₙ: Tₙ }

    Γ, x : T ⊢ e : U
    ──────────────────────────── [T-Fn]
    Γ ⊢ fn(x: T) -> e : T -> U

    Γ ⊢ e₁ : T -> U    Γ ⊢ e₂ : T
    ─────────────────────────────── [T-App]
    Γ ⊢ e₁(e₂) : U

    Γ ⊢ e₁ : T    Γ, x : T ⊢ e₂ : U
    ──────────────────────────────────── [T-Let]
    Γ ⊢ let x = e₁ in e₂ : U

    Γ ⊢ e₁ : Bool    Γ ⊢ e₂ : T    Γ ⊢ e₃ : T
    ─────────────────────────────────────────────── [T-If]
    Γ ⊢ if e₁ then e₂ else e₃ : T

    Γ ⊢ e : T    ∀i. (Γ ⊢ patᵢ : T ⇒ Γᵢ) ∧ (Γ, Γᵢ ⊢ eᵢ : U)
    ─────────────────────────────────────────────────────────────── [T-Match]
    Γ ⊢ match e { pat₁ => e₁, ..., patₙ => eₙ } : U
```

### 4.5.1 Stochastic Binding

```
    Γ ⊢ D : Dist<T>    Γ, x : T ⊢ e : U
    ────────────────────────────────────── [T-StochLet]
    Γ ⊢ let stochastic x ~ D in e : U
```

The stochastic let-binding `let stochastic x ~ D in e` draws a sample from distribution D and binds it to x. The type of x is T (the base type of the distribution), not Dist<T>.

## 4.6 Typing Judgments for Distributions

```
    Γ ⊢ v : Duration
    ──────────────────────────────────── [T-Deterministic]
    Γ ⊢ Deterministic(v) : Dist<Duration>

    Γ ⊢ λ : Rate    λ > 0
    ──────────────────────────────────── [T-Exponential]
    Γ ⊢ Exponential(λ) : Dist<Duration>

    Γ ⊢ μ : Float    Γ ⊢ σ : Float    σ > 0
    ────────────────────────────────────────── [T-LogNormal]
    Γ ⊢ LogNormal(μ, σ) : Dist<Duration>

    Γ ⊢ μ : Float    Γ ⊢ σ : Float    σ > 0
    ────────────────────────────────────────── [T-Normal]
    Γ ⊢ Normal(μ, σ) : Dist<Duration>

    Γ ⊢ lo : Float    Γ ⊢ hi : Float    lo < hi
    ─────────────────────────────────────────────── [T-Uniform]
    Γ ⊢ Uniform(lo, hi) : Dist<Duration>

    Γ ⊢ p : Float    0 ≤ p ≤ 1
    ─────────────────────────────────── [T-Bernoulli]
    Γ ⊢ Bernoulli(p) : Dist<Bool>

    Γ ⊢ λ : Rate    λ > 0
    ─────────────────────────────── [T-Poisson]
    Γ ⊢ Poisson(λ) : Dist<Int>

    ∀i. Γ ⊢ wᵢ : Float ∧ wᵢ > 0    ∀i. Γ ⊢ Dᵢ : Dist<T>
    ─────────────────────────────────────────────────────────── [T-Mix]
    Γ ⊢ mix(w₁: D₁, ..., wₙ: Dₙ) : Dist<T>

    Γ ⊢ D : Dist<Duration>    Γ ⊢ lo : Float    Γ ⊢ hi : Float
    ─────────────────────────────────────────────────────────────── [T-Truncate]
    Γ ⊢ truncate(D, lo, hi) : Dist<Duration>

    Γ ⊢ D₁ : Dist<Duration>    Γ ⊢ D₂ : Dist<Duration>
    ──────────────────────────────────────────────────────── [T-Convolve]
    Γ ⊢ convolve(D₁, D₂) : Dist<Duration>
```

**Remaining Continuous Distributions.** The following distributions are typed analogously:

```
[T-Erlang]
    Γ ⊢ k : Int    Γ ⊢ λ : Rate
    ────────────────────────────────
    Γ ⊢ Erlang(k, λ) : Dist<Duration>

[T-Triangular]
    Γ ⊢ a : Duration    Γ ⊢ m : Duration    Γ ⊢ b : Duration
    ──────────────────────────────────────────────────────────
    Γ ⊢ Triangular(a, m, b) : Dist<Duration>

[T-Gamma]
    Γ ⊢ α : Float    Γ ⊢ β : Float
    ─────────────────────────────────
    Γ ⊢ Gamma(α, β) : Dist<Duration>

[T-Weibull]
    Γ ⊢ k : Float    Γ ⊢ λ : Float
    ─────────────────────────────────
    Γ ⊢ Weibull(k, λ) : Dist<Duration>

[T-Beta]
    Γ ⊢ α : Float    Γ ⊢ β : Float
    ─────────────────────────────────
    Γ ⊢ Beta(α, β) : Dist<Float>

[T-Pareto]
    Γ ⊢ α : Float    Γ ⊢ x_m : Float
    ────────────────────────────────────
    Γ ⊢ Pareto(α, x_m) : Dist<Duration>
```

**Remaining Discrete Distributions.**

```
[T-Binomial]
    Γ ⊢ n : Int    Γ ⊢ p : Float
    ───────────────────────────────
    Γ ⊢ Binomial(n, p) : Dist<Int>

[T-Geometric]
    Γ ⊢ p : Float
    ──────────────────────────────
    Γ ⊢ Geometric(p) : Dist<Int>

[T-Empirical]
    Γ ⊢ vs : List<T>
    ──────────────────────────────
    Γ ⊢ Empirical(vs) : Dist<T>
```

**Remaining Combinators.**

```
[T-Shift]
    Γ ⊢ D : Dist<Duration>    Γ ⊢ offset : Duration
    ──────────────────────────────────────────────────
    Γ ⊢ shift(D, offset) : Dist<Duration>

[T-Scale]
    Γ ⊢ D : Dist<Duration>    Γ ⊢ factor : Float
    ──────────────────────────────────────────────
    Γ ⊢ scale(D, factor) : Dist<Duration>

[T-MaxOf]
    Γ ⊢ D₁ : Dist<Duration>    Γ ⊢ D₂ : Dist<Duration>
    ──────────────────────────────────────────────────────
    Γ ⊢ max_of(D₁, D₂) : Dist<Duration>

[T-MinOf]
    Γ ⊢ D₁ : Dist<Duration>    Γ ⊢ D₂ : Dist<Duration>
    ──────────────────────────────────────────────────────
    Γ ⊢ min_of(D₁, D₂) : Dist<Duration>
```

### 4.6.1 Distribution Properties (Compile-Time)

The type system tracks the following properties of distributions, used by the queueing semantics (§7):

| Property | Notation | Description |
|----------|----------|-------------|
| Mean | E[D] | Expected value |
| Variance | Var[D] | Variance |
| SCV | c²(D) = Var[D]/E[D]² | Squared coefficient of variation |

**SCV classification:**

| SCV Value | Classification | Interpretation |
|-----------|---------------|----------------|
| c² = 0 | Deterministic | No variability |
| c² < 1 | Low variability | Less than exponential |
| c² = 1 | Moderate (exponential) | Memoryless |
| c² > 1 | High variability | More bursty than exponential |

These properties are used by the VUT equation in §7.5 to compute expected waiting times.

## 4.7 Typing Judgments for Processes

```
    ─────────────────── [T-Stop]
    Γ; Δ ⊢ stop : proc

    ─────────────────── [T-Skip]
    Γ; Δ ⊢ skip : proc

    a : Chan<T> ∈ Γ    Γ ⊢ v : T
    ────────────────────────────── [T-Send]
    Γ; Δ ⊢ a ! v : proc

    a : Chan<T> ∈ Γ    Γ ⊢ v : T
    ────────────────────────────── [T-SyncSend]
    Γ; Δ ⊢ a !! v : proc

    a : Chan<T> ∈ Γ    Γ, x : T; Δ ⊢ P : proc
    ─────────────────────────────────────────── [T-Recv]
    Γ; Δ ⊢ a ? x ; P : proc

    a : Chan<T> ∈ Γ    Γ, x : T; Δ ⊢ P : proc
    ─────────────────────────────────────────── [T-SyncRecv]
    Γ; Δ ⊢ a ?? x ; P : proc

    Γ; Δ ⊢ P : proc    Γ; Δ ⊢ Q : proc
    ────────────────────────────────────── [T-Seq]
    Γ; Δ ⊢ P ; Q : proc

    Γ; Δ₁ ⊢ P : proc    Γ; Δ₂ ⊢ Q : proc
    ─────────────────────────────────────── [T-Par]
    Γ; Δ₁ ⊕ Δ₂ ⊢ P | Q : proc

    Γ; Δ₁ ⊢ P : proc    Γ; Δ₂ ⊢ Q : proc
    ─────────────────────────────────────── [T-Interleave]
    Γ; Δ₁ ⊕ Δ₂ ⊢ P ||| Q : proc

    Γ; Δ₁ ⊢ P : proc    Γ; Δ₂ ⊢ Q : proc    S ⊆ dom(Γ)
    ──────────────────────────────────────────────────────── [T-AlphaPar]
    Γ; Δ₁ ⊕ Δ₂ ⊢ P |[S]| Q : proc

    Γ; Δ ⊢ P : proc    Γ; Δ ⊢ Q : proc
    ────────────────────────────────────── [T-ExtChoice]
    Γ; Δ ⊢ P [] Q : proc

    Γ; Δ ⊢ P : proc    Γ; Δ ⊢ Q : proc
    ────────────────────────────────────── [T-IntChoice]
    Γ; Δ ⊢ P |~| Q : proc

    ∀i. Γ ⊢ wᵢ : Float ∧ wᵢ > 0    ∀i. Γ; Δ ⊢ Pᵢ : proc
    ───────────────────────────────────────────────────────── [T-PChoice]
    Γ; Δ ⊢ pchoice { w₁ -> P₁, ..., wₙ -> Pₙ } : proc

    Γ, a : Chan<T>; Δ ⊢ P : proc
    ──────────────────────────────── [T-Restrict]
    Γ; Δ ⊢ (nu a : Chan<T>) P : proc

    Γ; Δ ⊢ P : proc
    ─────────────────── [T-Repl]
    Γ; Δ ⊢ !P : proc

    Γ ⊢ D : Dist<Duration>
    ──────────────────────── [T-Delay]
    Γ; Δ ⊢ delay(D) : proc

    Γ ⊢ e : Bool    Γ; Δ ⊢ P : proc    Γ; Δ ⊢ Q : proc
    ──────────────────────────────────────────────────────── [T-IfProc]
    Γ; Δ ⊢ if e then P else Q : proc

    r : Resource<n> ∈ Γ    k ≤ n    Γ; Δ, r↓k ⊢ P : proc
    ──────────────────────────────────────────────────────── [T-Acquire]
    Γ; Δ ⊢ acquire(r, k) ; P ; release(r, k) : proc

    Γ ⊢ e : T    Γ, x : T; Δ ⊢ P : proc
    ────────────────────────────────────── [T-LetProc]
    Γ; Δ ⊢ let x = e in P : proc

    Γ ⊢ D : Dist<T>    Γ, x : T; Δ ⊢ P : proc
    ──────────────────────────────────────────── [T-StochLetProc]
    Γ; Δ ⊢ let stochastic x ~ D in P : proc

    Γ ⊢ e : T    ∀i. (Γ ⊢ patᵢ : T ⇒ Γᵢ) ∧ (Γ, Γᵢ; Δ ⊢ Pᵢ : proc)
    ─────────────────────────────────────────────────────────────────── [T-MatchProc]
    Γ; Δ ⊢ match e { pat₁ => P₁, ..., patₙ => Pₙ } : proc

    Γ, X : proc, x̄ : T̄; Δ ⊢ P : proc
    ─────────────────────────────────────────────── [T-Rec]
    Γ; Δ ⊢ rec X(x̄ : T̄). P : proc

    s : Station(T_in, T_out) ∈ Γ    Γ ⊢ e : T_in
    ─────────────────────────────────────────────── [T-StationInvoke]
    Γ; Δ ⊢ s(e) : proc

    s : Station(_, _) ∈ Γ    ∀i. (Γ; Δ ⊢ Pᵢ : proc)
    ─────────────────────────────────────────────────── [T-Monitor]
    Γ; Δ ⊢ monitor(s) { when c₁ => P₁, ..., when cₙ => Pₙ } : proc
```

### 4.7.1 Resource Environments

A *resource environment* Δ tracks the resource units currently held:

```
Δ ::= ∅
    | Δ, r↓k                 -- holding k units of resource r
```

The merge operator ⊕ ensures no over-allocation:

```
    Δ₁(r) + Δ₂(r) ≤ capacity(r)   for all r
    ──────────────────────────────────────────
    Δ₁ ⊕ Δ₂ defined
```

## 4.8 Typing Judgments for Stations

```
    Γ ⊢ T_in : Type    Γ ⊢ T_out : Type
    a_in : Chan<T_in> ∈ Γ    a_out : Chan<T_out> ∈ Γ
    Γ ⊢ Φ : ServiceProc(T_in, T_out)
    c ∈ ℕ⁺     (servers)
    disc ∈ Discipline
    Γ ⊢ D_service : Dist<Duration>
    ───────────────────────────────────────────────────── [T-Station]
    Γ ⊢ station s(a_in -> a_out) { servers: c, discipline: disc,
          service_time: D_service, ... Φ } : Station(T_in, T_out)
```

**Service process typing:**

```
    Γ ⊢ model : String    Γ ⊢ D : Dist<Duration>
    Γ ⊢ on_input : T_in -> T_out
    ──────────────────────────────────────────────── [T-Prompt]
    Γ ⊢ prompt { model, service_time: D, on_input, ... } : ServiceProc(T_in, T_out)

    Γ ⊢ f : T_in -> T_out    Γ ⊢ D : Dist<Duration>
    ──────────────────────────────────────────────────── [T-Compute]
    Γ ⊢ compute { fn: f, service_time: D, ... } : ServiceProc(T_in, T_out)

    Γ ⊢ D : Dist<Duration>
    ──────────────────────────────────────────────────── [T-Human]
    Γ ⊢ human { service_time: D, ... } : ServiceProc(T_in, T_out)
```

## 4.9 Typing Judgments for Arrivals

```
    a : Chan<T> ∈ Γ    Γ ⊢ D : Dist<Duration>    Γ ⊢ job : T
    ─────────────────────────────────────────────────────────────── [T-Arrival]
    Γ ⊢ arrival α : { channel: a, distribution: D, job: job } ok
```

## 4.10 Typing Judgments for Assertions

```
    s : Station(_, _) ∈ Γ    Γ ⊢ bound : Float
    ──────────────────────────────────────────── [T-AssertUtil]
    Γ ⊢ assert utilization(s) <= bound ok

    X : proc ∈ Γ    Γ ⊢ bound : Rate
    ──────────────────────────────────────────── [T-AssertThroughput]
    Γ ⊢ assert throughput(X) >= bound ok

    X : proc ∈ Γ
    ──────────────────────────────────────── [T-AssertLittle]
    Γ ⊢ assert littles_law(X) ok

    X : proc ∈ Γ
    ──────────────────────────────────────── [T-AssertDeadlockFree]
    Γ ⊢ assert deadlock_free(X) ok

    X : proc ∈ Γ
    ──────────────────────────────────────── [T-AssertSteadyState]
    Γ ⊢ assert steady_state(X) ok

    X : proc ∈ Γ
    ──────────────────────────────────────── [T-AssertConservative]
    Γ ⊢ assert conservative(X) ok
```

## 4.11 Type Soundness

The type system satisfies the standard type soundness properties with respect to the operational semantics (§5):

**Theorem 4.1 (Type Preservation).** If `Γ; Δ ⊢ P : proc` and `P → P'`, then `Γ'; Δ' ⊢ P' : proc` for some Γ' ⊇ Γ and Δ' compatible with Δ.

**Theorem 4.2 (Progress).** If `Γ; Δ ⊢ P : proc` and P is not a value (i.e., P ≠ `skip` and P ≠ `stop`), then either P can take a step, or P is waiting on a channel communication or resource acquisition.

Proof sketches are given in Appendix A.

---

*Previous: [Chapter 3 — Abstract Syntax](03-abstract-syntax.md)*
*Next: [Chapter 5 — Operational Semantics](05-operational-semantics.md)*
