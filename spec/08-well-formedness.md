# STOKED Language Specification

## Chapter 8 — Well-Formedness Conditions

---

This chapter defines the well-formedness conditions that a STOKED system must satisfy beyond type correctness. These conditions ensure that the system has meaningful operational, structural, and performance properties. Each condition is stated formally and linked to both the Petri net analysis (§6) and queueing analysis (§7) that can verify it.

## 8.1 Overview

A STOKED system S is *well-formed* if it satisfies all of the following:

| # | Condition | Static/Dynamic | Verification Method |
|---|-----------|---------------|---------------------|
| WF-1 | Type safety | Static | Type checking (§4) |
| WF-2 | Deadlock-freedom | Static/Dynamic | Siphon/trap analysis or reachability (§6.7) |
| WF-3 | Boundedness | Static | P-invariant analysis (§6.6) |
| WF-4 | Conservation | Static | P-invariant analysis (§6.6) |
| WF-5 | Routing completeness | Static | Graph reachability |
| WF-6 | Resource sufficiency | Static | Integer programming |
| WF-7 | Stability | Static | Traffic equation analysis (§7.3) |
| WF-8 | SPC well-formedness | Static | Constraint checking |

## 8.2 Type Safety (WF-1)

**Condition WF-1.** A STOKED system S is type-safe if:
1. Every top-level declaration is well-typed under the global environment Γ_S.
2. Type preservation holds: if `Γ; Δ ⊢ P : proc` and P → P', then `Γ'; Δ' ⊢ P' : proc`.
3. Progress holds: every well-typed, non-terminal process can take a step or is waiting on a communication/resource.

**Verification**: Standard type checking algorithm (bidirectional type checking with constraint solving for distribution parameters). The type preservation and progress theorems are proved in Appendix A.

### 8.2.1 Channel Type Safety

A stronger condition for channels:

**Condition WF-1a (Channel Safety).** For every channel `a : Chan<T>`:
1. Every send `a ! v` satisfies `Γ ⊢ v : T`.
2. Every receive `a ? x` binds x to type T.
3. If a has finite capacity K, then the type system statically ensures (via resource typing or bounded model checking) that the channel never accumulates more than K items.

### 8.2.2 Resource Type Safety

**Condition WF-1b (Resource Safety).** For every resource `r : Resource<n>`:
1. Every `acquire(r, k)` has k ≤ n.
2. Every `acquire(r, k)` has a matching `release(r, k)` on every execution path.
3. The total acquired units across all parallel components never exceeds n.

Condition WF-1b.3 is enforced by the resource environment merge operator ⊕ (§4.7.1).

**Note.** The binary merge operator ⊕ extends to n-way parallel composition by iterated pairwise application: Δ₁ ⊕ Δ₂ ⊕ ... ⊕ Δₙ. Since ⊕ is commutative and associative (when defined), the order of merging does not matter. The key property is that `Σᵢ Δᵢ(r) ≤ capacity(r)` for all resources r — i.e., the total resource demand across all parallel components does not exceed capacity.

## 8.3 Deadlock-Freedom (WF-2)

**Condition WF-2 (Deadlock-Freedom).** A STOKED system S is deadlock-free if: for every reachable configuration C (other than successful termination), at least one transition is enabled.

Formally, using the Petri net translation:

```
∀M ∈ Reach(⟦S⟧). (M ≠ M_final) ⟹ (∃t ∈ T. M [t⟩)
```

### 8.3.1 Sufficient Conditions

The following are sufficient conditions for deadlock-freedom, listed from weakest to strongest:

**Condition WF-2a (Structural).** Every siphon of ⟦S⟧ contains an initially marked trap (Theorem 6.3). This is checkable in polynomial time on the net structure.

**Condition WF-2b (Resource Ordering).** If resources are ordered and all processes acquire resources in strictly increasing order, then resource-induced deadlocks are impossible (standard resource-ordering theorem).

**Condition WF-2c (Communication Pattern).** If the communication graph (stations as nodes, channels as edges) is acyclic, then communication-induced deadlocks are impossible.

**Condition WF-2d (Full Verification).** Reachability analysis of ⟦S⟧ confirms no dead marking is reachable. This is complete but may be computationally expensive for large state spaces.

### 8.3.2 Deadlock and the `assert` Construct

```
assert deadlock_free(S)
```

This assertion requires WF-2. A conforming implementation must verify deadlock-freedom (by any of the methods above) and report failure if the condition cannot be established.

## 8.4 Boundedness (WF-3)

**Condition WF-3 (Boundedness).** A STOKED system S is *k-bounded* if no channel (place in ⟦S⟧) accumulates more than k tokens:

```
∀M ∈ Reach(⟦S⟧). ∀p ∈ P. M(p) ≤ k
```

### 8.4.1 Sources of Unboundedness

1. **Unbounded arrivals without backpressure**: An arrival feeding a finite-capacity station without flow control.
2. **Replication without WIP limits**: `!P` without a resource or WIP constraint.
3. **Faster production than consumption**: A fast station feeding a slow station without buffering limits.

### 8.4.2 Ensuring Boundedness

Boundedness is ensured by a positive P-invariant covering all places (Theorem 6.2). STOKED systems ensure this when:

1. Every channel has a finite `capacity` declaration, OR
2. The system is closed (no external arrivals), OR
3. WIP limits (`wip limit: k`) are declared on stations, OR
4. Resource constraints limit concurrency

```
assert bounded(S, k)
```

## 8.5 Conservation / Flow Balance (WF-4)

**Condition WF-4 (Conservation).** A STOKED system S satisfies conservation if the weighted sum of tokens is constant across all reachable markings:

```
∃y > 0. ∀M ∈ Reach(⟦S⟧). y^T · M = y^T · M₀
```

### 8.5.1 Flow Balance Equations

Conservation implies flow balance at every station:

```
For each station s:
    λ_in(s) = λ_out(s) + λ_rework(s) + λ_scrap(s)
```

where:
- λ_in(s) = total arrival rate to station s
- λ_out(s) = total departure rate of good output
- λ_rework(s) = total rate of rework (recirculated jobs)
- λ_scrap(s) = total rate of scrapped/discarded jobs

**Special case (no scrap):** If yield is always Good or Rework (no scrap), then conservation is automatic: every job that enters eventually exits or recirculates.

```
assert conservative(S)
```

## 8.6 Routing Completeness (WF-5)

**Condition WF-5 (Routing Completeness).** Every job entering the system has a path to an exit:

1. **Reachability**: For every channel a reachable from an arrival, there exists a finite path through stations and routing decisions leading to a system exit (a channel with no consumers, or an explicit exit/sink).

2. **Probability 1 completion**: For every job class c, the probability of eventually exiting the system is 1. This requires that rework loops have escape probability:

```
For every cycle in the routing graph:
    ∏_{edges in cycle} p_e < 1
```

i.e., every cycle has a net exit probability > 0.

3. **Routing coverage**: At every routing decision point (pchoice), the branch probabilities sum to 1.

### 8.6.1 Formal Statement

```
∀ job class c. ∀ entry node n₀.
    P(job of class c starting at n₀ eventually exits) = 1
```

This is equivalent to: the routing matrix R is *substochastic* (not stochastic) for the augmented system with an absorbing exit state, and (I - R) is invertible.

## 8.7 Resource Sufficiency (WF-6)

**Condition WF-6 (Resource Sufficiency).** The system can make progress despite finite resources:

```
∀ reachable C. ∃ transition enabled at C that does not require an unavailable resource.
```

This is stronger than deadlock-freedom: it ensures that resource contention does not starve any part of the system.

### 8.7.1 Minimum Resource Requirement

For each resource r, the minimum capacity required to avoid starvation:

```
capacity(r) ≥ max_path { Σ_{stations s on path} k_s(r) }
```

where k_s(r) is the number of units of r required by station s, and the max is over all paths a job can take simultaneously holding resources.

## 8.8 Stability (WF-7)

**Condition WF-7 (Stability).** An open STOKED system (with external arrivals) is *stable* if every station's utilization is strictly less than 1:

```
∀ station s. ρ(s) = λ(s) / (c(s) · μ(s)) < 1
```

where λ(s) is the effective arrival rate (from traffic equations, §7.3), c(s) is the server count, and μ(s) is the service rate.

### 8.8.1 Stability Analysis

1. **Solve traffic equations**: Compute effective arrival rates λ(s) for each station.
2. **Check utilization**: Verify ρ(s) < 1 for all stations.
3. **Account for rework**: Effective arrival rate includes rework: λ_eff(s) = λ_ext(s) + λ_rework(s), where λ_rework(s) = Σⱼ λ(j) · p_rework(j,s).

```
assert steady_state(S)
```

This assertion requires WF-7. A system that is not stable will have unbounded WIP and cycle times.

### 8.8.2 Stability with Rework

Rework loops increase effective utilization. For a station with self-rework probability p_r (i.e., fraction p_r of completed jobs return to the same station), the effective arrival rate is λ_eff(s) = λ_ext(s) / (1 - p_r), where λ_ext(s) is the external (non-rework) arrival rate. The effective utilization is:

```
ρ_eff(s) = λ_ext(s) / ((1 - p_r) · c(s) · μ(s))
```

The stability condition ρ_eff(s) < 1 requires that the base service capacity exceeds the amplified arrival rate. This is more restrictive than the no-rework case by a factor of 1/(1 - p_r).

## 8.9 SPC Well-Formedness (WF-8)

**Condition WF-8 (SPC Well-Formedness).** Every `monitor` block satisfies:

1. **Metric exists**: The monitored metric (e.g., cycle_time, throughput) is defined for the referenced station or system.
2. **Control limits are consistent**: UCL > LCL (upper > lower control limit).
3. **Run/trend parameters are positive**: Run length and trend length are positive integers.
4. **Escalation targets exist**: Every `escalate { to: s }` references a defined station or process.
5. **No infinite escalation**: The escalation graph is acyclic.

## 8.10 Combined Well-Formedness

**Definition 8.1 (Well-Formed System).** A STOKED system S is *well-formed* if it satisfies WF-1 through WF-8.

**Definition 8.2 (Performance-Analyzable System).** A well-formed STOKED system S is *performance-analyzable* if additionally:
1. All distributions have finite mean and variance (so SCV is defined).
2. The system is stable (WF-7).
3. The routing graph is connected (every station is reachable from some arrival).

For performance-analyzable systems, the queueing analysis (§7) produces finite, meaningful performance metrics.

## 8.11 Verification Summary

| Assertion | Checks | Method |
|-----------|--------|--------|
| `deadlock_free(S)` | WF-2 | Siphon/trap or reachability |
| `bounded(S, k)` | WF-3 | P-invariant |
| `conservative(S)` | WF-4 | P-invariant |
| `steady_state(S)` | WF-7 | Traffic equations + utilization |
| `live(S)` | WF-2 + WF-7 | Combined structural + stability |
| `littles_law(S)` | Numerical | L = λW ± ε |
| `bottleneck(S) == s` | WF-7 | argmax utilization |
| `throughput(S) >= r` | WF-7 | Queueing analysis |
| `cycle_time(S).p95 <= t` | WF-7 | Queueing analysis + distribution |
| `wip(S) <= k` | WF-3 | Queueing analysis or P-invariant |
| `utilization(s) <= u` | WF-7 | Traffic equations |

---

*Previous: [Chapter 7 — Queueing Semantics](07-queueing-semantics.md)*
*Next: [Chapter 9 — Standard Library](09-standard-library.md)*
