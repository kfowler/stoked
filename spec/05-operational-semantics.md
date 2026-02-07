# STOKED Language Specification

## Chapter 5 — Operational Semantics

---

This chapter defines the operational semantics of STOKED as a labeled transition system (LTS). The semantics is given in the structural operational semantics (SOS) style, following Plotkin's approach. We define configurations, labels, structural congruence, and reduction rules for all process constructors defined in §3.6.

## 5.1 Configurations

A *configuration* represents the global state of a STOKED system at a point in time.

**Definition 5.1 (Configuration).** A configuration is a tuple:

```
C = ⟨P, σ, β, ρ, t⟩
```

where:
- P is a process expression
- σ : Var → Value is the value store (substitution)
- β : ChanName → Queue(Value) is the buffer state (channel contents)
- ρ : ResName → ℕ is the resource state (available units)
- t ∈ ℝ≥₀ is the global clock

**Initial configuration:** For a program with arrivals ᾱ, channels ā, and resources r̄:

```
C₀ = ⟨P_main, ∅, β₀, ρ₀, 0⟩
```

where β₀(a) = ε (empty queue) for all a ∈ ā, and ρ₀(r) = capacity(r) for all r ∈ r̄.

## 5.2 Labels

Labels classify the observable actions of the system.

**Definition 5.2 (Labels).**

```
μ ::= τ                           -- internal (silent) action
    | a!v                         -- send value v on channel a
    | a?v                         -- receive value v from channel a
    | a!!v                        -- synchronous send
    | a??v                        -- synchronous receive
    | tick(δ)                     -- time passage of δ units
    | acquire(r, k)               -- acquire k units of resource r
    | release(r, k)               -- release k units of resource r
    | fire(s, v_in, v_out)        -- station s fires: input v_in, output v_out
    | sample(D, v)                -- sample value v from distribution D
    | arrive(α, v)                -- arrival α generates job v
```

## 5.3 Structural Congruence

**Definition 5.3 (Structural Congruence).** The relation ≡ is the smallest congruence on processes satisfying:

```
/* Parallel composition is commutative, associative, with unit skip */
P | Q  ≡  Q | P                                    [SC-ParComm]
(P | Q) | R  ≡  P | (Q | R)                        [SC-ParAssoc]
P | stop  ≡  P                                     [SC-ParUnit]

/* Interleaved parallel is commutative, associative */
P ||| Q  ≡  Q ||| P                                [SC-IntComm]
(P ||| Q) ||| R  ≡  P ||| (Q ||| R)                [SC-IntAssoc]
P ||| stop  ≡  P                                   [SC-IntUnit]

/* Sequential composition has right unit skip */
P ; skip  ≡  P                                     [SC-SeqUnit]
skip ; P  ≡  P                                     [SC-SeqUnitL]
stop ; P  ≡  stop                                    [SC-SeqStop]

/* Restriction */
(nu a) (nu b) P  ≡  (nu b) (nu a) P                [SC-ResComm]
(nu a) P | Q  ≡  (nu a) (P | Q)   if a ∉ fn(Q)    [SC-ResExt]
(nu a) stop  ≡  stop                                [SC-ResDead]

/* Replication */
!P  ≡  P | !P                                      [SC-Repl]

/* Alpha-conversion */
(nu a) P  ≡  (nu b) P[b/a]     if b ∉ fn(P)          [SC-Alpha]

/* Choice */
P [] Q  ≡  Q [] P                                  [SC-ExtComm]
P |~| Q  ≡  Q |~| P                                [SC-IntComm2]
```

where fn(P) denotes the set of free channel names in P.

## 5.4 Core Reduction Rules

### 5.4.1 Sequential Composition

```
    ⟨P, σ, β, ρ, t⟩ →_μ ⟨P', σ', β', ρ', t'⟩
    ─────────────────────────────────────────────────────────── [R-SeqL]
    ⟨P ; Q, σ, β, ρ, t⟩ →_μ ⟨P' ; Q, σ', β', ρ', t'⟩

    ──────────────────────────────────────────── [R-SeqSkip]
    ⟨skip ; Q, σ, β, ρ, t⟩ →_τ ⟨Q, σ, β, ρ, t⟩
```

### 5.4.2 Channel Communication (Asynchronous)

```
    a ∈ dom(β)
    ──────────────────────────────────────────────────────── [R-AsyncSend]
    ⟨a ! v, σ, β, ρ, t⟩ →_{a!v} ⟨skip, σ, β[a ↦ β(a)·v], ρ, t⟩

    a ∈ dom(β)    β(a) = v · q
    ──────────────────────────────────────────────────────────── [R-AsyncRecv]
    ⟨a ? x ; P, σ, β, ρ, t⟩ →_{a?v} ⟨P[v/x], σ, β[a ↦ q], ρ, t⟩
```

**Remark**: Async send enqueues; async receive dequeues from the head (FIFO by default). The discipline can be overridden per-channel.

### 5.4.3 Channel Communication (Synchronous / Rendezvous)

```
    ──────────────────────────────────────────────────────────────────── [R-Rendezvous]
    ⟨(a !! v ; P) | (a ?? x ; Q), σ, β, ρ, t⟩
      →_τ ⟨P | Q[v/x], σ, β, ρ, t⟩
```

Synchronous communication requires both sender and receiver to be ready simultaneously. No buffering occurs.

### 5.4.4 Station Firing

**Notation.** For a station s with server count c, we write active(s) for the number of jobs currently being processed by s, and station_process(s) for the service process function Phi associated with s.

A station fires when:
1. There is a job available on the input channel
2. A server is available (utilization < 1)
3. Required resources are available

```
    s = station(a_in -> a_out) { servers: c, service_time: D, ... Φ }
    β(a_in) = v · q          /* job available */
    active(s) < c             /* server available */
    d ~ D                     /* sample service time */
    v_out = Φ(v)              /* apply service process */
    ──────────────────────────────────────────────────────────────── [R-StationFire]
    ⟨station_process(s), σ, β, ρ, t⟩
      →_{fire(s,v,v_out)} ⟨station_process(s), σ, β[a_in ↦ q][a_out ↦ β(a_out)·v_out], ρ, t+d⟩
```

**Station with yield and rework:**

```
    /* Same preconditions as R-StationFire, plus: */
    y ~ yield_dist            /* sample yield */
    ──────────────────────────────────────────────────────── [R-StationYield]
    if y = Good:
      β' = β[a_in ↦ q][a_out ↦ β(a_out)·v_out]
    if y = Rework:
      β' = β[a_in ↦ q][a_rework ↦ β(a_rework)·v]
    if y = Scrap:
      β' = β[a_in ↦ q]       /* job discarded */
```

### 5.4.5 Resource Management

```
    ρ(r) ≥ k
    ────────────────────────────────────────────────────────────── [R-Acquire]
    ⟨acquire(r, k) ; P ; release(r, k), σ, β, ρ, t⟩
      →_{acquire(r,k)} ⟨P ; release(r, k), σ, β, ρ[r ↦ ρ(r)-k], t⟩

    ────────────────────────────────────────────────────────────── [R-Release]
    ⟨release(r, k), σ, β, ρ, t⟩
      →_{release(r,k)} ⟨skip, σ, β, ρ[r ↦ ρ(r)+k], t⟩
```

### 5.4.6 Parallel Composition

**Synchronized parallel** (P | Q): both components can proceed independently on non-shared actions; they must synchronize on shared channel actions.

```
    ⟨P, σ, β, ρ, t⟩ →_μ ⟨P', σ', β', ρ', t'⟩    μ ≠ a!v, a?v for shared a
    ──────────────────────────────────────────────────────────────────── [R-ParL]
    ⟨P | Q, σ, β, ρ, t⟩ →_μ ⟨P' | Q, σ', β', ρ', t'⟩

    /* symmetric rule [R-ParR] for Q */

    ⟨P, σ, β, ρ, t⟩ →_{a!v} ⟨P', σ₁, β₁, ρ, t⟩
    ⟨Q, σ, β, ρ, t⟩ →_{a?v} ⟨Q', σ₂, β₂, ρ, t⟩
    ──────────────────────────────────────────────────── [R-ParSync]
    ⟨P | Q, σ, β, ρ, t⟩ →_τ ⟨P' | Q', σ₁∪σ₂, β, ρ, t⟩
```

**Remark.** In [R-ParSync], the buffer state β is unchanged because the synchronized communication transfers the value directly from sender to receiver without intermediate buffering.

**Interleaved parallel** (P ||| Q): components proceed fully independently; no synchronization.

```
    ⟨P, σ, β, ρ, t⟩ →_μ ⟨P', σ', β', ρ', t'⟩
    ──────────────────────────────────────────────── [R-IntlL]
    ⟨P ||| Q, σ, β, ρ, t⟩ →_μ ⟨P' ||| Q, σ', β', ρ', t'⟩

    /* symmetric rule [R-IntlR] for Q */
```

**Alphabetized parallel** (P |[S]| Q): synchronize on channels in set S.

```
    ⟨P, σ, β, ρ, t⟩ →_μ ⟨P', σ', β', ρ', t'⟩    chan(μ) ∉ S
    ──────────────────────────────────────────────────────────── [R-AlphaIndep]
    ⟨P |[S]| Q, σ, β, ρ, t⟩ →_μ ⟨P' |[S]| Q, σ', β', ρ', t'⟩

    ⟨P, σ, β, ρ, t⟩ →_{a!v} ⟨P', ...⟩    ⟨Q, σ, β, ρ, t⟩ →_{a?v} ⟨Q', ...⟩    a ∈ S
    ─────────────────────────────────────────────────────────────────────────────── [R-AlphaSync]
    ⟨P |[S]| Q, σ, β, ρ, t⟩ →_τ ⟨P' |[S]| Q', ...⟩
```

### 5.4.7 Choice

**External choice** (P [] Q): the environment (first observable action) resolves the choice.

```
    ⟨P, σ, β, ρ, t⟩ →_μ ⟨P', σ', β', ρ', t'⟩    μ ≠ τ
    ─────────────────────────────────────────────────────── [R-ExtL]
    ⟨P [] Q, σ, β, ρ, t⟩ →_μ ⟨P', σ', β', ρ', t'⟩

    /* symmetric rule [R-ExtR] for Q */
```

**Internal choice** (P |~| Q): the system nondeterministically resolves.

```
    ──────────────────────────────────────────── [R-IntL]
    ⟨P |~| Q, σ, β, ρ, t⟩ →_τ ⟨P, σ, β, ρ, t⟩

    ──────────────────────────────────────────── [R-IntR]
    ⟨P |~| Q, σ, β, ρ, t⟩ →_τ ⟨Q, σ, β, ρ, t⟩
```

**Probabilistic choice:**

```
    Σᵢ wᵢ = W    pᵢ = wᵢ / W
    ──────────────────────────────────────────────────────────── [R-PChoice]
    ⟨pchoice { w₁ -> P₁, ..., wₙ -> Pₙ }, σ, β, ρ, t⟩
      →_τ ⟨Pᵢ, σ, β, ρ, t⟩    with probability pᵢ
```

### 5.4.8 Time Passage

```
    d ~ D
    ──────────────────────────────────────────────────── [R-Delay]
    ⟨delay(D), σ, β, ρ, t⟩ →_{tick(d)} ⟨skip, σ, β, ρ, t+d⟩
```

Time advances globally: all parallel components observe the same clock.

```
    ⟨P, σ, β, ρ, t⟩ →_{tick(δ)} ⟨P', σ, β, ρ, t+δ⟩
    ⟨Q, σ, β, ρ, t⟩ →_{tick(δ)} ⟨Q', σ, β, ρ, t+δ⟩
    ────────────────────────────────────────────────────── [R-TimePar]
    ⟨P | Q, σ, β, ρ, t⟩ →_{tick(δ)} ⟨P' | Q', σ, β, ρ, t+δ⟩

    ⟨P, σ, β, ρ, t⟩ →_{tick(δ)} ⟨P', σ, β, ρ, t+δ⟩
    ⟨Q, σ, β, ρ, t⟩ →_{tick(δ)} ⟨Q', σ, β, ρ, t+δ⟩
    ────────────────────────────────────────────────────── [R-TimeIntl]
    ⟨P ||| Q, σ, β, ρ, t⟩ →_{tick(δ)} ⟨P' ||| Q', σ, β, ρ, t+δ⟩

    ⟨P, σ, β, ρ, t⟩ →_{tick(δ)} ⟨P', σ, β, ρ, t+δ⟩
    ⟨Q, σ, β, ρ, t⟩ →_{tick(δ)} ⟨Q', σ, β, ρ, t+δ⟩
    ────────────────────────────────────────────────────── [R-TimeAlpha]
    ⟨P |[S]| Q, σ, β, ρ, t⟩ →_{tick(δ)} ⟨P' |[S]| Q', σ, β, ρ, t+δ⟩

    ⟨P, σ, β, ρ, t⟩ →_{tick(δ)} ⟨P', σ, β, ρ, t+δ⟩
    ⟨Q, σ, β, ρ, t⟩ →_{tick(δ)} ⟨Q', σ, β, ρ, t+δ⟩
    ────────────────────────────────────────────────────── [R-TimeChoice]
    ⟨P [] Q, σ, β, ρ, t⟩ →_{tick(δ)} ⟨P' [] Q', σ, β, ρ, t+δ⟩
```

**Remark.** Internal choice (`P |~| Q`) and probabilistic choice (`pchoice`) resolve instantly via τ-transitions and do not require time passage rules; maximal progress ensures they resolve before time advances.

**Maximal progress**: Internal (τ) actions take priority over time passage. Time advances only when no τ-actions are enabled (the *timelock-freedom* condition).

### 5.4.9 Routing

Routing is determined by the process structure. Explicit routing occurs through channel communication; probabilistic routing through `pchoice`:

```
    /* Probabilistic routing after station output */
    a_out ? x ;
    pchoice {
      p₁ -> b₁ ! x,    /* route to station/channel b₁ with probability p₁ */
      p₂ -> b₂ ! x,    /* route to station/channel b₂ with probability p₂ */
      ...
    }
```

This desugars to a combination of [R-AsyncRecv] and [R-PChoice].

### 5.4.10 Restriction

```
    ⟨P, σ, β[a ↦ ε], ρ, t⟩ →_μ ⟨P', σ', β', ρ', t'⟩    a ∉ labels(μ)
    ─────────────────────────────────────────────────────────────────── [R-Res]
    ⟨(nu a) P, σ, β, ρ, t⟩ →_μ ⟨(nu a) P', σ', β'|_{-a}, ρ', t'⟩
```

Restriction creates a fresh private channel. Actions on restricted channels are internalized (not observable).

### 5.4.11 Replication

```
    ⟨P | !P, σ, β, ρ, t⟩ →_μ ⟨C', ...⟩
    ────────────────────────────────────── [R-Repl]
    ⟨!P, σ, β, ρ, t⟩ →_μ ⟨C', ...⟩
```

Replication unfolds by structural congruence [SC-Repl].

### 5.4.12 Let Binding, Conditional, and Match in Processes

```
    σ' = σ[x ↦ eval(e, σ)]
    ─────────────────────────────────────────────────────── [R-LetProc]
    ⟨let x = e in P, σ, β, ρ, t⟩ →_τ ⟨P, σ', β, ρ, t⟩

    v sampled from D
    ─────────────────────────────────────────────────────────── [R-StochLetProc]
    ⟨let stochastic x ~ D in P, σ, β, ρ, t⟩ →_τ ⟨P[v/x], σ, β, ρ, t⟩

    eval(e, σ) = true
    ─────────────────────────────────────────────────────────── [R-IfTrue]
    ⟨if e then P else Q, σ, β, ρ, t⟩ →_τ ⟨P, σ, β, ρ, t⟩

    eval(e, σ) = false
    ─────────────────────────────────────────────────────────── [R-IfFalse]
    ⟨if e then P else Q, σ, β, ρ, t⟩ →_τ ⟨Q, σ, β, ρ, t⟩

    eval(e, σ) = v    match(v, patᵢ) = σᵢ    (first matching arm)
    ─────────────────────────────────────────────────────────── [R-MatchProc]
    ⟨match e { pat₁ => P₁, ..., patₙ => Pₙ }, σ, β, ρ, t⟩
      →_τ ⟨Pᵢ, σ ∪ σᵢ, β, ρ, t⟩
```

### 5.4.13 Recursive Processes

```
    ─────────────────────────────────────────────────── [R-Rec]
    ⟨rec X(x̄ = v̄). P, σ, β, ρ, t⟩
      →_τ ⟨P[rec X(x̄). P / X][v̄/x̄], σ, β, ρ, t⟩
```

Recursion unfolds by substituting the recursive definition for X and binding the parameters.

### 5.4.14 Process Invocation

**[R-ProcInvoke]:** Process invocation (where X is defined by `process X(x₁, ..., xₙ) = P`):

```
    ─────────────────────────────────────────────────────── [R-ProcInvoke]
    ⟨X(v₁, ..., vₙ), σ, β, ρ, t⟩ →_τ ⟨P[v₁/x₁, ..., vₙ/xₙ], σ, β, ρ, t⟩
```

### 5.4.15 Station Invocation

```
    s = station(a_in -> a_out) { servers: c, service_time: D, ... Φ }
    d ~ D                       /* sample service time */
    v_out = Φ(v_in)             /* apply service process */
    ─────────────────────────────────────────────────────────── [R-StationInvoke]
    ⟨s(v_in), σ, β, ρ, t⟩
      →_{fire(s, v_in, v_out)} ⟨skip, σ, β[a_out ↦ β(a_out)·v_out], ρ, t+d⟩
```

Station invocation applies the station's service process to the input value, samples a service time delay, and deposits the output on the station's output channel.

### 5.4.16 Monitor (SPC)

```
    metric(s) violates condition cᵢ
    ──────────────────────────────────────────────── [R-Monitor]
    ⟨monitor(s) { ..., when cᵢ => Pᵢ, ... }, σ, β, ρ, t⟩
      →_τ ⟨Pᵢ, σ, β, ρ, t⟩
```

Monitor blocks are reactive: they trigger when an SPC condition is violated.

    ∀i. metric(s) does not violate condition cᵢ
    ─────────────────────────────────────────────────────── [R-MonitorQuiescent]
    ⟨monitor(s) { when c₁ => P₁, ..., when cₙ => Pₙ }, σ, β, ρ, t⟩
      →_{tick(δ)} ⟨monitor(s) { when c₁ => P₁, ..., when cₙ => Pₙ }, σ, β, ρ, t+δ⟩

In the absence of violations, the monitor allows time to pass and re-evaluates conditions after each tick.

## 5.5 Arrival Semantics

Arrivals inject jobs into the system according to their distribution:

```
    α = arrival { channel: a, distribution: D, job: j }
    d ~ D                      /* sample inter-arrival time */
    ──────────────────────────────────────────────────────── [R-Arrive]
    ⟨arrival_process(α), σ, β, ρ, t⟩
      →_{arrive(α, j)} ⟨arrival_process(α), σ, β[a ↦ β(a)·j], ρ, t+d⟩
```

The arrival process is persistent (self-replicating) — it continues generating jobs indefinitely.

## 5.6 Stochastic Operational Semantics

The *stochastic* operational semantics augments the LTS with rates and probabilities, yielding a Continuous-Time Markov Chain (CTMC) when all distributions are exponential, or a Generalized Semi-Markov Process (GSMP) otherwise.

**Definition 5.4 (Stochastic Configuration).** A stochastic configuration extends the configuration with a set of enabled clocks:

```
C_s = ⟨P, σ, β, ρ, t, Ω⟩
```

where Ω is a set of *(event, remaining-time)* pairs.

**Race condition semantics**: When multiple events are enabled, the event with the smallest remaining time fires first (the *race policy*). For exponential distributions, this reduces to the standard CTMC race condition.

```
    Ω = {(e₁, d₁), (e₂, d₂), ..., (eₙ, dₙ)}
    dᵢ = min{d₁, ..., dₙ}
    ──────────────────────────────────────────── [R-Race]
    Event eᵢ fires; advance clock by dᵢ; resample clock for eᵢ;
    subtract dᵢ from all other remaining times.
```

### 5.6.1 CTMC Embedding

When all service times and inter-arrival times are exponentially distributed, the stochastic operational semantics induces a CTMC with:

- **State space**: The set of reachable configurations
- **Transition rate** from C to C' via action μ: the rate parameter of the exponential distribution triggering the transition
- **Generator matrix** Q: Q(C, C') = rate(C →_μ C') for C ≠ C'

The steady-state distribution π (if it exists) satisfies πQ = 0, Σπ = 1.

### 5.6.2 GSMP Embedding

For general distributions, the stochastic semantics induces a Generalized Semi-Markov Process:

- **State**: (configuration, clock vector)
- **Events**: enabled transitions
- **Clock distributions**: the service/arrival distributions
- **Event selection**: race policy (minimum remaining time)

## 5.7 Semantic Properties

**Theorem 5.1 (Determinacy of τ-free processes).** If P is τ-free (contains no internal choice, no probabilistic choice, and no overlapping receives), then the LTS is deterministic: for any label μ ≠ τ, at most one transition C →_μ C' exists.

**Theorem 5.2 (Compositionality).** The semantics is compositional: the transitions of `P | Q` are determined solely by the transitions of P and Q individually, plus the synchronization rules.

**Theorem 5.3 (Time consistency).** Time advances uniformly across all parallel components. If C →_{tick(δ)} C', then the global clock in C' equals the global clock in C plus δ.

---

*Previous: [Chapter 4 — Type System](04-type-system.md)*
*Next: [Chapter 6 — Petri Net Semantics](06-petri-net-semantics.md)*
