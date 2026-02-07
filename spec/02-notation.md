# STOKED Language Specification

## Chapter 2 — Notation and Conventions

---

## 2.1 Meta-Variables

Throughout this specification, the following meta-variable conventions are used consistently. Primed (x'), subscripted (x_i), and overlined (x̄) variants follow the same conventions.

### 2.1.1 Identifiers and Names

| Meta-variable | Ranges over | Example |
|---------------|------------|---------|
| x, y, z | Value variables | `x`, `pr`, `ticket` |
| a, b, c | Channel names | `a`, `review_queue`, `deploy_ch` |
| f, g | Function names | `f`, `classify`, `route` |
| s | Station names | `s`, `CodeReview`, `BuildServer` |
| r | Resource names | `r`, `gpu_pool`, `reviewer_cap` |
| X, Y | Process variables | `X`, `MainLoop`, `Handler` |
| A, B | Type variables | `A`, `B` |

### 2.1.2 Syntactic Categories

| Meta-variable | Ranges over | Defined in |
|---------------|------------|------------|
| P, Q, R | Processes | §3.6 |
| T, U, S | Types | §3.3 |
| D | Distributions | §3.8 |
| K | Kinds | §4.1 |
| v, w | Values | §3.5 |
| e | Expressions | §3.5 |
| pat | Patterns | §3.5 |
| Σ | Station definitions | §3.7 |
| Φ | Service processes | §3.7 |

### 2.1.3 Semantic Domains

| Meta-variable | Ranges over | Defined in |
|---------------|------------|------------|
| Γ | Type environments | §4.3 |
| Δ | Resource environments | §4.7.1 |
| σ | Substitutions | §4.4 |
| C | Configurations | §5.1 |
| μ | Labels (actions) | §5.2 |
| N | Petri nets | §6.1 |
| Q | Queueing models | §7.1 |

**Disambiguation.** Several symbols are conventionally overloaded across mathematical domains. Context resolves ambiguity:
- **μ** denotes *labels* (actions) in the operational semantics (§5) and *service rate* in queueing notation (§2.4.1, §7). When both appear in the same context, labels are written μ and service rates are written μ_s or 1/E[S].
- **K** denotes *kinds* in the type system (§4.1) and *system capacity* (buffer + servers) in queueing notation (§2.4.2). These never co-occur in a single judgment.
- **Q** denotes *processes* as a meta-variable (§2.1.2), *queueing models* as a semantic domain (this table), and the *CTMC generator matrix* (§5.6.1). Usage is clear from context: Q(·) always denotes the queueing extraction function, and the generator matrix Q appears only in §5.6.

## 2.2 Judgment Forms

The specification uses the following judgment forms.

### 2.2.1 Typing Judgments

| Judgment | Meaning |
|----------|---------|
| Γ ⊢ e : T | Expression e has type T in environment Γ |
| Γ ⊢ P : proc | Process P is well-typed in environment Γ |
| Γ; Δ ⊢ P : proc | Process P is well-typed with resource environment Δ |
| ⊢ T : K | Type T has kind K |
| T <: U | Type T is a subtype of type U |
| Γ ⊢ D : Dist(T) | Distribution D has distribution type over T |

### 2.2.2 Reduction Judgments

| Judgment | Meaning |
|----------|---------|
| C →  C' | Configuration C reduces to C' (silent/internal) |
| C →_μ C' | Configuration C performs action μ and becomes C' |
| C →_t C' | Configuration C advances by time t |
| P ≡ Q | Processes P and Q are structurally congruent |

### 2.2.3 Translation Judgments

| Judgment | Meaning |
|----------|---------|
| ⟦P⟧ = N | Process P translates to Petri net N |
| Q(P) = M | Process P extracts to queueing model M |

### 2.2.4 Verification Judgments

| Judgment | Meaning |
|----------|---------|
| ⊨ φ | Property φ holds |
| P ⊨ deadlock_free | Process P is deadlock-free |
| P ⊨ bounded(k) | Process P is k-bounded |
| N ⊨ conservative | Net N satisfies conservation (flow balance) |

## 2.3 Typographic Conventions

### 2.3.1 Fonts and Styles

| Convention | Usage | Example |
|-----------|-------|---------|
| `monospace` | STOKED keywords, syntax, code | `station`, `channel`, `P ; Q` |
| *italic* | Meta-variables, first use of defined terms | *process*, *station*, T |
| **bold** | Defined names, emphasis | **Definition 4.1** |
| SMALL CAPS | Rule names | [T-Send], [R-Comm] |
| Sans-serif | Semantic functions | ⟦·⟧, Q(·) |

### 2.3.2 Brackets and Delimiters

| Notation | Meaning |
|----------|---------|
| `{ ... }` | STOKED block syntax |
| ⟨ ... ⟩ | Tuples and sequences |
| ⟦ ... ⟧ | Semantic translation brackets |
| ⌈ ... ⌉ | Ceiling |
| ⌊ ... ⌋ | Floor |
| \| ... \| | Cardinality or absolute value |
| [x ↦ v] | Substitution of v for x |

### 2.3.3 Set and Sequence Notation

| Notation | Meaning |
|----------|---------|
| ∅ | Empty set |
| x̄ | Sequence x₁, x₂, ..., xₙ |
| x̄ : T̄ | Sequence x₁ : T₁, x₂ : T₂, ..., xₙ : Tₙ |
| {x̄} | Set {x₁, x₂, ..., xₙ} |
| dom(Γ) | Domain of environment Γ |
| Γ, x : T | Environment extension |
| Γ₁ ∘ Γ₂ | Environment composition |

## 2.4 Mathematical Notation

### 2.4.1 Probability and Statistics

| Notation | Meaning |
|----------|---------|
| E[X] | Expected value of random variable X |
| Var[X] | Variance of random variable X |
| c²_X = Var[X] / E[X]² | Squared coefficient of variation (SCV) |
| F_X(t) = P(X ≤ t) | Cumulative distribution function |
| f_X(t) | Probability density/mass function |
| X ~ D | Random variable X follows distribution D |
| λ | Arrival rate (jobs per unit time) |
| μ | Service rate (jobs per unit time at a single server) |
| ρ = λ / (c · μ) | Utilization (traffic intensity per server) |

### 2.4.2 Queueing Notation

| Notation | Meaning |
|----------|---------|
| L | Average number in system (WIP) |
| L_q | Average number in queue |
| W | Average time in system (cycle time) |
| W_q | Average waiting time in queue |
| c | Number of parallel servers |
| K | System capacity (buffer + servers) |
| r_b | Bottleneck rate |
| T_0 | Raw process time (sum of mean station times) |
| W_0 = r_b · T_0 | Critical WIP |

### 2.4.3 Petri Net Notation

| Notation | Meaning |
|----------|---------|
| (P, T, F, W, M₀) | Petri net: places, transitions, flow, weights, initial marking |
| M(p) | Number of tokens in place p under marking M |
| M [t⟩ M' | Transition t fires, transforming M to M' |
| •t | Pre-set of transition t: {p ∈ P \| (p,t) ∈ F} |
| t• | Post-set of transition t: {p ∈ P \| (t,p) ∈ F} |

## 2.5 EBNF Conventions

The grammar in Chapter 3 uses the following EBNF conventions:

| Notation | Meaning |
|----------|---------|
| `terminal` | Terminal symbol (keyword or punctuation) |
| NonTerminal | Non-terminal symbol |
| `::=` | Production rule |
| `\|` | Alternative |
| `[ ... ]` | Optional (zero or one) |
| `{ ... }` | Repetition (zero or more) |
| `( ... )` | Grouping |
| `'...'` | Literal string |
| `/* ... */` | Grammar comment |

Operator precedence and associativity are defined inline with the grammar productions. Ambiguities are resolved by the precedence table in §3.13.

## 2.6 Time Units

STOKED supports the following time unit literals:

| Unit | Abbreviation | Equivalent |
|------|-------------|------------|
| millisecond | `ms` | 0.001s |
| second | `s` | 1s |
| minute | `m` | 60s |
| hour | `h` | 3600s |
| day | `d` | 86400s |
| week | `w` | 604800s |

Time values are rational numbers with units. Arithmetic on time values requires compatible units; the type system enforces dimensional consistency (§4.2).

## 2.7 Cross-Reference Conventions

Within this specification:

- **§N.M** refers to Section M of Chapter N
- **Definition N.M** refers to a numbered definition
- **Theorem N.M** refers to a numbered theorem or proposition
- **Rule [Name]** refers to a named inference rule
- **Figure N.M** refers to a numbered figure
- **Table N.M** refers to a numbered table

Forward references are marked with the target chapter when the construct has not yet been defined.

---

*Previous: [Chapter 1 — Introduction](01-introduction.md)*
*Next: [Chapter 3 — Abstract Syntax](03-abstract-syntax.md)*
