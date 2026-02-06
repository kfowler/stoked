# PRAXIS Language Specification

## Appendix A — Proof Sketches

---

This appendix provides proof sketches for the main theorems stated in the specification. Full formal proofs are deferred to companion technical reports.

## A.1 Type Preservation (Theorem 4.1)

**Theorem 4.1 (Type Preservation).** If `Γ; Δ ⊢ P : proc` and `P → P'`, then there exist Γ' ⊇ Γ and Δ' compatible with Δ such that `Γ'; Δ' ⊢ P' : proc`.

**Proof sketch.** By structural induction on the derivation of P → P'. We show representative cases:

**Case [R-SeqSkip]:** `skip ; Q → Q`

```
Given: Γ; Δ ⊢ skip ; Q : proc
By inversion of [T-Seq]: Γ; Δ ⊢ skip : proc  and  Γ; Δ ⊢ Q : proc
Therefore: Γ; Δ ⊢ Q : proc  ✓
```

**Case [R-AsyncRecv]:** `a ? x ; P → P[v/x]` where v is dequeued from channel a

```
Given: Γ; Δ ⊢ a ? x ; P : proc
By inversion of [T-Recv]: a : Chan<T> ∈ Γ  and  Γ, x : T; Δ ⊢ P : proc
Since v was in channel a: Γ ⊢ v : T  (by channel type safety, WF-1a)
By the substitution lemma: Γ; Δ ⊢ P[v/x] : proc  ✓
```

**Case [R-Rendezvous]:** `(a !! v ; P) | (a ?? x ; Q) → P | Q[v/x]`

```
Given: Γ; Δ₁ ⊕ Δ₂ ⊢ (a !! v ; P) | (a ?? x ; Q) : proc
By inversion of [T-Par]:
    Γ; Δ₁ ⊢ a !! v ; P : proc
    Γ; Δ₂ ⊢ a ?? x ; Q : proc
By inversion of [T-SyncSend]: a : Chan<T> ∈ Γ,  Γ ⊢ v : T,  Γ; Δ₁ ⊢ P : proc
By inversion of [T-SyncRecv]: Γ, x : T; Δ₂ ⊢ Q : proc
By substitution lemma: Γ; Δ₂ ⊢ Q[v/x] : proc
By [T-Par]: Γ; Δ₁ ⊕ Δ₂ ⊢ P | Q[v/x] : proc  ✓
```

**Case [R-Acquire]:** `acquire(r, k) ; P ; release(r, k) → P ; release(r, k)` when ρ(r) ≥ k

```
Given: Γ; Δ ⊢ acquire(r, k) ; P ; release(r, k) : proc
By inversion of [T-Acquire]: r : Resource<n> ∈ Γ,  k ≤ n,  Γ; Δ, r↓k ⊢ P : proc
After acquisition: resource env becomes Δ' = Δ, r↓k (holding k units)
Need to show: Γ; Δ' ⊢ P ; release(r, k) : proc
By [T-Seq] with Γ; Δ' ⊢ P : proc (given) and release types trivially  ✓
```

**Case [R-PChoice]:** `pchoice { w₁ -> P₁, ..., wₙ -> Pₙ } → Pᵢ`

```
Given: Γ; Δ ⊢ pchoice { w₁ -> P₁, ..., wₙ -> Pₙ } : proc
By inversion of [T-PChoice]: ∀i. Γ; Δ ⊢ Pᵢ : proc
Therefore for any chosen i: Γ; Δ ⊢ Pᵢ : proc  ✓
```

**Case [R-StationFire]:** Station s fires with input v, producing output v_out

```
Given: Station s is well-typed with ServiceProc(T_in, T_out)
Input v : T_in (from channel typing)
Service process Φ : T_in → T_out
Therefore v_out = Φ(v) : T_out
Output channel has type Chan<T_out>
Typing preserved  ✓
```

The remaining cases ([R-SeqL], [R-ParL], [R-ParR], [R-ExtL], [R-IntL], [R-IntR], [R-Delay], [R-Res], [R-Repl]) follow by straightforward induction using the induction hypothesis on subterms. □

## A.2 Progress (Theorem 4.2)

**Theorem 4.2 (Progress).** If `Γ; Δ ⊢ P : proc` and P ∉ {skip, stop}, then either:
1. P can take a step (∃μ, P'. P →_μ P'), or
2. P is blocked on a channel communication (waiting for a matching send/receive), or
3. P is blocked on resource acquisition (waiting for resource availability).

**Proof sketch.** By structural induction on P.

**Case P = a ! v:** Rule [R-AsyncSend] always applies (async send to buffer). Progress holds (case 1).

**Case P = a ? x ; Q:** If β(a) ≠ ε, rule [R-AsyncRecv] applies (case 1). If β(a) = ε, P is blocked on channel (case 2).

**Case P = a !! v ; Q:** P is blocked until a matching `a ?? x` is available (case 2). If a matching receiver exists in a parallel component, [R-Rendezvous] fires.

**Case P = P₁ ; P₂:** By IH on P₁: either P₁ steps (then [R-SeqL] applies), P₁ = skip (then [R-SeqSkip] applies), P₁ = stop (then P₁ ; P₂ is stuck — but stop ; Q is a type error by convention, as stop represents deadlock), or P₁ is blocked (P inherits the block).

**Case P = P₁ | P₂:** By IH on P₁ and P₂. If either can step independently, [R-ParL] or [R-ParR] applies. If both are blocked on complementary channel actions, [R-ParSync] applies. Otherwise P is blocked.

**Case P = P₁ [] P₂:** If either branch can perform a non-τ action, [R-ExtL] or [R-ExtR] applies. Otherwise both branches are blocked.

**Case P = P₁ |~| P₂:** [R-IntL] or [R-IntR] always applies (unconditional τ-step). Progress holds (case 1).

**Case P = pchoice { ... }:** [R-PChoice] always applies. Progress holds (case 1).

**Case P = delay(D):** [R-Delay] always applies (sampling a delay). Progress holds (case 1).

**Case P = acquire(r, k) ; Q ; release(r, k):** If ρ(r) ≥ k, [R-Acquire] applies (case 1). Otherwise, blocked on resource (case 3).

**Case P = (nu a) Q:** By IH on Q. If Q steps with a non-a action, [R-Res] applies. If Q steps with an a-action, it is internalized.

**Case P = !Q:** By structural congruence [SC-Repl], !Q ≡ Q | !Q. Then by IH on Q, if Q can step, [R-ParL] applies. □

## A.3 Behavioral Equivalence (Theorem 6.1)

**Theorem 6.1 (Behavioral Equivalence).** For every well-typed PRAXIS process P:
```
traces(SOS(P)) = traces(PN(⟦P⟧))
```

**Proof sketch.** By structural induction on P. We establish a *bisimulation relation* R between SOS configurations and Petri net markings:

```
R = { (C, M) | C = ⟨P, σ, β, ρ, t⟩ and M encodes β and ρ in ⟦P⟧ }
```

We show that R is a (weak) bisimulation:

**Forward direction** (SOS simulates PN): For each PN transition M [t⟩ M', we show there exists an SOS step C →_μ C' with (C', M') ∈ R.

**Backward direction** (PN simulates SOS): For each SOS step C →_μ C', we show there exists a PN transition (or sequence of immediate transitions followed by one timed transition) M [t₁⟩...M' with (C', M') ∈ R.

**Key cases:**

**Send/Receive ↔ Place deposit/withdraw:** An SOS send `a ! v` deposits into buffer β(a); the corresponding PN transition deposits a token in place p_a. The color of the token encodes v.

**Station firing:** The SOS rule [R-StationFire] corresponds exactly to the subnet (t_start, t_done) firing sequence in §6.3.2. The enabling conditions match: input place non-empty (job available), idle server token available (server free).

**Parallel composition ↔ Place fusion:** The SOS parallel rules ([R-ParL], [R-ParR], [R-ParSync]) correspond to independent PN transitions (for non-shared actions) and synchronized firing (for shared channels via fused places).

**Probabilistic choice ↔ Weighted immediate transitions:** [R-PChoice] selects branch i with probability wᵢ/Σwⱼ; the corresponding immediate transitions in ⟦pchoice⟧ have weights wᵢ, yielding the same selection probabilities.

**Restriction ↔ Internal place:** Restriction hides channel a; the corresponding PN has p_a as an internal place not part of the external interface. This matches: the PN can still use p_a internally, but external observers cannot interact with it. □

## A.4 Conservation via P-Invariants (Theorem 6.2)

**Theorem 6.2 (Conservation).** For every well-formed PRAXIS system S (satisfying WF-4), the translated net ⟦S⟧ has a positive P-invariant covering all places.

**Proof sketch.** We construct the P-invariant explicitly.

**Step 1: Station conservation.** For each station s with c servers, the vector with y(p_idle(s)) = 1 and y(p_busy(s)) = 1 is a P-invariant (the number of idle + busy servers is always c). This follows directly from the station subnet structure: t_start moves a token from p_idle to p_busy; t_done moves it back.

**Step 2: Resource conservation.** For each resource r with capacity n, the vector with y(p_r) = 1 and y(p_held(s,r)) = 1 for all stations s using r is a P-invariant (total resource tokens is always n).

**Step 3: Flow conservation.** For an open system, we show that the incidence matrix C_N of ⟦S⟧ satisfies: for the vector y with y(p) = 1 for all channel places p and y(p) = 0 for station internal places, y^T · C_N = 0 except at source and sink transitions.

For a closed system (no sources or sinks), y^T · C_N = 0 exactly, giving a P-invariant.

**Step 4: Combination.** The P-invariants from Steps 1-3 can be combined (P-invariants form a vector space) to produce a positive P-invariant covering all places, provided:
- Every channel place is part of at least one station's input or output
- Every station's internal places are covered by the station conservation invariant
- Every resource place is covered by the resource conservation invariant

These conditions are exactly the well-formedness conditions WF-4 and WF-5 (conservation and routing completeness). □

## A.5 Stability Implies Finite Performance Metrics (Theorem 7.3 Prerequisite)

**Proposition A.1.** If a PRAXIS system S satisfies WF-7 (stability), then all performance metrics (throughput, cycle time, WIP, utilization) are finite and well-defined.

**Proof sketch.** Stability (ρ(s) < 1 for all stations s) implies:

1. **Ergodicity**: The underlying CTMC (or GSMP) is ergodic — a unique steady-state distribution exists.

2. **Finite moments**: Under ergodicity, the expected queue length L_q, expected waiting time W_q, and expected cycle time W are all finite for each station.

3. **Little's Law**: L = λW holds in steady state (by Little's theorem, which requires only that the system is ergodic and the limits exist).

4. **Throughput = arrival rate**: In steady state, throughput equals the effective arrival rate at each station (departure rate = arrival rate when the system is stable).

For Jackson/BCMP networks (§7.3, §7.4), these results are exact. For general networks using the VUT approximation (§7.5), the approximations are finite and meaningful whenever stability holds. □

## A.6 Little's Law Invariant

**Theorem (Little's Law).** For any stable PRAXIS subsystem S: L = λ · W.

**Proof sketch.** Little's Law is a general result that holds for *any* system in steady state, regardless of distribution assumptions, service discipline, or routing policy. The proof follows from:

1. Define N(t) = number of arrivals in [0, t] and D(t) = number of departures in [0, t].
2. WIP at time t: L(t) = N(t) - D(t).
3. Total sojourn time up to t: W_total(t) = ∫₀ᵗ L(s) ds.
4. If the limits exist: λ = lim N(t)/t, L = lim L̄(t), W = lim W_total(t)/N(t).
5. Then L̄(t) = W_total(t)/t = (N(t)/t) · (W_total(t)/N(t)), and taking limits: L = λ · W. □

---

*Previous: [Chapter 10 — Examples](10-examples.md)*
*Next: [Appendix B — Equivalences](appendix-b-equivalences.md)*
