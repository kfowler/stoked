# STOKED Language Specification

## Chapter 6 — Petri Net Semantics

---

This chapter defines the translation ⟦·⟧ from STOKED processes to Coloured Generalized Stochastic Petri Nets (CGSPNs). The Petri net semantics provides a structural model suitable for analysis of boundedness, liveness, deadlock-freedom, conservation, and steady-state performance.

## 6.1 Target Formalism: CGSPNs

**Definition 6.1 (Coloured Generalized Stochastic Petri Net).** A CGSPN is a tuple:

```
N = (P, T, F, C, G, E, W, D, M₀)
```

where:
- P is a finite set of *places*
- T = T_imm ∪ T_timed is a finite set of *transitions* (immediate and timed), P ∩ T = ∅
- F ⊆ (P × T) ∪ (T × P) is the set of *arcs*
- C : P → ColorSet assigns a *color set* (token type) to each place
- G : T → Guard assigns an enabling *guard* (boolean predicate on bindings) to each transition
- E : F → ArcExpr assigns an *arc expression* to each arc (determining tokens consumed/produced)
- W : T_imm → ℕ⁺ assigns *weights* to immediate transitions (for conflict resolution)
- D : T_timed → Dist assigns a *firing delay distribution* to each timed transition
- M₀ : P → Multiset is the *initial marking*

**Definition 6.2 (Enabling and Firing).** A transition t ∈ T is enabled at marking M with binding b if:
1. For every input place p ∈ •t: E(p,t)(b) ⊆ M(p) (sufficient tokens with matching colors)
2. G(t)(b) = true (guard satisfied)

When enabled transition t fires with binding b, the new marking M' is:
```
M'(p) = M(p) - E(p,t)(b) + E(t,p)(b)    for all p ∈ P
```

**Timed semantics**: Timed transitions have a firing delay sampled from D(t). Immediate transitions fire in zero time and have priority over timed transitions.

## 6.2 Translation Overview

The translation ⟦·⟧ maps each STOKED construct to a CGSPN subnet, with *interface places* for composition. The key correspondences are:

| STOKED Construct | Petri Net Element |
|-----------------|-------------------|
| Channel `a : Chan<T>` | Place p_a with color set C(T) |
| Station `s` | Transition subnet (input place → timed transition → output place) |
| Resource `r : Resource<n>` | Resource place p_r with initial marking n |
| Arrival `α` | Source transition (timed, self-enabling) |
| Process operator | Net composition operation |

## 6.3 Translation of Primitive Constructs

### 6.3.1 Channels → Places

```
⟦channel a : Chan<T>⟧ = place p_a with C(p_a) = ⟦T⟧
```

The color set ⟦T⟧ maps STOKED types to Petri net color sets:

| STOKED Type | Color Set |
|------------|-----------|
| `Bool` | {true, false} |
| `Int` | ℤ |
| `Float` | ℝ |
| `String` | Σ* |
| `{ f₁: T₁, ..., fₙ: Tₙ }` | ⟦T₁⟧ × ... × ⟦Tₙ⟧ |
| `C₁(T̄₁) \| ... \| Cₖ(T̄ₖ)` | ⟦T̄₁⟧ + ... + ⟦T̄ₖ⟧ (tagged union) |
| `List<T>` | ⟦T⟧* (sequences) |

### 6.3.2 Stations → Transition Subnets

A station with c servers translates to a subnet with three places and two transitions:

```
⟦station s(a_in -> a_out) { servers: c, service_time: D, ... }⟧ =

    Places:
        p_queue(s)    -- waiting queue (shared with p_{a_in})
        p_busy(s)     -- jobs in service
        p_idle(s)     -- idle servers

    Transitions:
        t_start(s)    -- immediate: move job from queue to service
        t_done(s)     -- timed with delay D: complete service

    Arcs:
        (p_queue(s), t_start(s))  weight 1
        (p_idle(s), t_start(s))   weight 1
        (t_start(s), p_busy(s))   weight 1
        (p_busy(s), t_done(s))    weight 1
        (t_done(s), p_idle(s))    weight 1
        (t_done(s), p_{a_out})    weight 1

    Initial marking:
        M₀(p_idle(s)) = c
        M₀(p_busy(s)) = 0
```

This is the standard M/G/c queueing subnet in Petri net form. The p_idle place limits concurrency to c.

**Station with yield/rework:**

```
⟦station s { ..., yield: Y, rework: { probability: p_r, target: a_rework } }⟧ =

    Additional transitions:
        t_yield(s)    -- immediate, weight = ⌊(1-p_r) × 1000⌋
        t_rework(s)   -- immediate, weight = ⌊p_r × 1000⌋

    Additional arcs:
        (p_busy(s), t_yield(s))    -- good output
        (t_yield(s), p_{a_out})
        (p_busy(s), t_rework(s))   -- rework
        (t_rework(s), p_{a_rework})
```

**Scrap handling.** When yield produces scrap (the probability 1 - p_yield that routes to neither the output nor the rework target), the scrap token is consumed by a sink transition t_scrap with weight = floor((1 - p_yield) * 1000). An additional immediate transition t_scrap(s) fires from p_busy(s) to a sink place p_scrap(s), where the token is absorbed. The `scrap_rate` metric (§3.11) measures the throughput of this transition.

### 6.3.3 Resources → Resource Places

```
⟦resource r : Resource<n>⟧ = place p_r with M₀(p_r) = n, C(p_r) = {•}
```

Stations that require resource r include arcs:
```
    (p_r, t_start(s))   weight k    -- acquire k units
    (t_done(s), p_r)    weight k    -- release k units
```

### 6.3.4 Arrivals → Source Transitions

```
⟦arrival α : { channel: a, distribution: D, job: j }⟧ =

    Transition:
        t_α           -- timed with delay D, self-enabling

    Arcs:
        (t_α, p_a)    weight 1

    Self-enabling:
        t_α has no input places (source transition)
        After firing, t_α is immediately re-enabled with a new delay sample from D
```

## 6.4 Translation of Process Operators

### 6.4.1 Sequential Composition

```
⟦P ; Q⟧ = N_P ⊕_seq N_Q
```

where ⊕_seq merges the *terminal place* of N_P with the *initial place* of N_Q:

```
    N_P has terminal place p_end(P)
    N_Q has initial place p_start(Q)
    Merge: p_end(P) ≡ p_start(Q)
```

### 6.4.2 Synchronized Parallel Composition

```
⟦P | Q⟧ = N_P ⊕_sync N_Q
```

where ⊕_sync fuses places corresponding to shared channels:

```
    For each channel a ∈ fn(P) ∩ fn(Q):
        p_a in N_P  ≡  p_a in N_Q     (place fusion)
```

Both N_P and N_Q execute concurrently. Shared channels are represented by the same place, so communication occurs by token passing through the fused place.

### 6.4.3 Interleaved Parallel Composition

```
⟦P ||| Q⟧ = N_P ⊕_intl N_Q
```

where ⊕_intl creates a *token-based mutual exclusion* structure if needed, or simply juxtaposes the subnets if they share no places:

```
    If fn(P) ∩ fn(Q) = ∅:
        N_P ⊕_intl N_Q = N_P ∪ N_Q (disjoint union)
    Else:
        Shared channels become separate places with explicit copy transitions
```

### 6.4.4 Alphabetized Parallel Composition

```
⟦P |[S]| Q⟧ = N_P ⊕_S N_Q
```

where ⊕_S fuses only the places corresponding to channels in the synchronization set S:

```
    For each channel a ∈ S:
        p_a in N_P  ≡  p_a in N_Q
    For each channel a ∈ (fn(P) ∩ fn(Q)) \ S:
        p_a in N_P and p_a in N_Q remain separate
```

### 6.4.5 External Choice

```
⟦P [] Q⟧ =

    Places:
        p_choose     -- choice point (initial marking: 1)

    Transitions (immediate):
        t_left       -- choose P
        t_right      -- choose Q

    Arcs:
        (p_choose, t_left)    weight 1
        (p_choose, t_right)   weight 1
        (t_left, p_start(N_P))   weight 1
        (t_right, p_start(N_Q))  weight 1

    Guard:
        G(t_left) = "first observable action of P is enabled"
        G(t_right) = "first observable action of Q is enabled"
```

The environment resolves external choice by enabling one branch's guard.

### 6.4.6 Internal and Probabilistic Choice

```
⟦P |~| Q⟧ =
    Same structure as external choice, but:
        W(t_left) = W(t_right) = 1    (equal weight, nondeterministic)
        No environment-dependent guards

⟦pchoice { w₁ -> P₁, ..., wₙ -> Pₙ }⟧ =
    Same structure with n immediate transitions:
        W(t_i) = wᵢ                   (weighted by branch probabilities)
```

### 6.4.7 Restriction

```
⟦(nu a : Chan<T>) P⟧ = ⟦P⟧ with p_a marked as internal (no external interface)
```

Restriction hides the place corresponding to channel a from the external interface. This prevents composition operators from fusing it with other nets.

### 6.4.8 Replication

```
⟦!P⟧ =
    Places:
        p_trigger    -- always marked (initial marking: 1)

    Transitions:
        t_spawn      -- immediate, creates a new instance

    Arcs:
        (p_trigger, t_spawn)   weight 1
        (t_spawn, p_trigger)   weight 1    -- re-enable immediately
        (t_spawn, p_start(N_P)) weight 1   -- start new instance

    The subnet N_P is parameterized: each firing of t_spawn creates
    a fresh copy with fresh internal places.
```

**Remark.** Unbounded replication (`!P`) can generate an unbounded number of fresh places via `t_spawn`, violating the finite place set of Definition 6.1. In practice, replication is bounded by resource constraints, WIP limits, or finite channel capacities, yielding a finite unfolding. Conforming analyses should either (a) unfold to a finite depth bounded by the system's WIP or resource limits, or (b) use symbolic/parameterized techniques that handle infinite-state Petri nets.

### 6.4.9 Timed Delay

```
⟦delay(D)⟧ =
    Places:
        p_wait       -- initial marking: 1
        p_done       -- terminal

    Transitions:
        t_delay      -- timed with delay D

    Arcs:
        (p_wait, t_delay)   weight 1
        (t_delay, p_done)   weight 1
```

### 6.4.10 Primitive Processes

```
⟦stop⟧ =
    Places:
        p_stop       -- a single place, initially marked

    No transitions. The subnet is inert: the token remains in p_stop
    indefinitely, representing permanent inaction.


⟦skip⟧ =
    Places:
        p_done       -- terminal place, initially marked

    No transitions. The token in p_done signals successful termination
    and is available for sequential composition (§6.4.1) to consume.
```

### 6.4.11 Send and Receive

```
⟦a ! v⟧ =
    Transition:
        t_send       -- immediate

    Arcs:
        (p_control, t_send)   weight 1    -- consume control token
        (t_send, p_a)         weight 1    -- produce token in channel place

    The token deposited in p_a has color ⟦v⟧.


⟦a ? x ; P⟧ =
    Transition:
        t_recv       -- immediate

    Arcs:
        (p_a, t_recv)         weight 1    -- consume from channel place
        (t_recv, p_start(N_P)) weight 1   -- enable continuation

    Binding: x is bound to the color of the consumed token.
```

**Synchronous (rendezvous) communication:**

```
⟦(a !! v ; P) | (a ?? x ; Q)⟧ =
    Places:
        p_send_ready     -- sender ready (initial marking: 1)
        p_recv_ready     -- receiver ready (initial marking: 1)

    Transitions:
        t_rendezvous     -- immediate

    Arcs:
        (p_send_ready, t_rendezvous)    weight 1
        (p_recv_ready, t_rendezvous)    weight 1
        (t_rendezvous, p_start(N_P))    weight 1
        (t_rendezvous, p_start(N_Q))    weight 1

    Binding: x is bound to ⟦v⟧. No intermediate place is needed —
    the value transfer occurs atomically at the rendezvous transition.
    Unlike async communication, no channel place is involved.
```

### 6.4.12 Station Invocation

```
⟦s(v)⟧ =
    Equivalent to the station's transition subnet (§6.3.2), instantiated with
    input value v. The subnet fires t_start (immediate) then t_done (timed),
    depositing the result on the station's output channel place.
```

### 6.4.13 Recursive Processes

```
⟦rec X(x̄). P⟧ =
    Unfold the recursion to a finite depth bounded by resource/WIP constraints.
    Each unfolding creates a copy of ⟦P⟧ with a back-arc from the terminal
    place to the initial place, forming a cycle in the net.

    For tail-recursive processes (X appears only at the end of P):
        Add arc: (p_end(N_P), t_loop) and (t_loop, p_start(N_P))
        where t_loop is an immediate transition.
```

### 6.4.14 Let Binding, Conditional, Match

```
⟦let x = e in P⟧ = ⟦P[eval(e)/x]⟧
    (Immediate substitution; no net structure added.)

⟦if e then P else Q⟧ =
    Same structure as external choice (§6.4.5), with:
        G(t_left) = eval(e) = true
        G(t_right) = eval(e) = false

⟦match e { pat₁ => P₁, ..., patₙ => Pₙ }⟧ =
    Generalization of conditional: n immediate transitions with
    mutually exclusive guards G(t_i) = match(eval(e), patᵢ).
```

### 6.4.15 Monitor (SPC)

```
⟦monitor(s) { when c₁ => P₁, ..., when cₙ => Pₙ }⟧ =
    An observer subnet that reads (but does not consume) tokens from
    station s's performance counters. Each SPC rule cᵢ maps to an
    immediate transition t_spc_i with guard G(t_spc_i) = cᵢ violated,
    whose firing enables subnet ⟦Pᵢ⟧.
```

### 6.4.16 WIP Limits

```
⟦station s { ..., wip limit: W, ... }⟧ =
    Extends the station subnet (§6.3.2) with a complementary place:

    Additional place:
        p_wip(s)     -- initial marking: W

    Additional arcs:
        (p_wip(s), t_start(s))   weight 1   -- consume WIP token on entry
        (t_done(s), p_wip(s))    weight 1   -- restore WIP token on exit

    When M(p_wip(s)) = 0, t_start(s) is disabled (backpressure).
```

## 6.5 Behavioral Equivalence

**Theorem 6.1 (Behavioral Equivalence).** For every well-typed STOKED process P:

```
traces(SOS(P)) = traces(PN(⟦P⟧))
```

where:
- SOS(P) is the labeled transition system defined by the operational semantics (§5)
- PN(⟦P⟧) is the reachability graph of the translated Petri net
- traces extracts the set of observable action sequences

*Proof sketch*: By structural induction on P. Each case shows that the translation preserves the enabling conditions and firing effects of every reduction rule. See Appendix A for the complete proof sketch.

**Corollary 6.1.** If ⟦P⟧ is deadlock-free (every reachable marking enables at least one transition), then P is deadlock-free under the operational semantics.

**Corollary 6.2.** If ⟦P⟧ is k-bounded (no place accumulates more than k tokens), then no channel in P accumulates more than k jobs.

## 6.6 Structural Analysis via P-Invariants

**Definition 6.3 (P-Invariant).** A vector y ∈ ℤ|P| is a P-invariant of net N if y^T · C_N = 0, where C_N is the incidence matrix (C_N[p,t] = E(t,p) - E(p,t)).

A P-invariant y satisfies: for all reachable markings M, y^T · M = y^T · M₀ (weighted token count is conserved).

**Application to STOKED:**

| STOKED Property | P-Invariant |
|----------------|-------------|
| Server conservation (station s) | y(p_idle(s)) + y(p_busy(s)) = c |
| Resource conservation (resource r) | y(p_r) + Σ_s y(p_held(s,r)) = capacity(r) |
| WIP conservation (closed system) | Σ_a y(p_a) + Σ_s y(p_busy(s)) = W_0 |
| Flow balance (station s) | tokens_in(s) = tokens_out(s) + tokens_rework(s) + tokens_scrap(s) |

**Theorem 6.2 (Conservation).** For every well-formed STOKED system S (§8.5), the translated net ⟦S⟧ has a positive P-invariant covering all places, implying S is bounded and conservative.

## 6.7 Siphons and Traps

**Definition 6.4.** A set of places S ⊆ P is a *siphon* if •S ⊆ S• (every transition that outputs to S also inputs from S). A set Q ⊆ P is a *trap* if Q• ⊆ •Q (every transition that inputs from Q also outputs to Q).

**Theorem 6.3 (Deadlock-Freedom via Traps).** If every siphon of ⟦P⟧ contains an initially marked trap, then ⟦P⟧ (and hence P) is deadlock-free.

This provides a structural sufficient condition for deadlock-freedom, checkable without reachability analysis.

---

*Previous: [Chapter 5 — Operational Semantics](05-operational-semantics.md)*
*Next: [Chapter 7 — Queueing Semantics](07-queueing-semantics.md)*
