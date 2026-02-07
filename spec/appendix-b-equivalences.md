# STOKED Language Specification

## Appendix B — Equivalences and Algebraic Laws

---

This appendix defines the equivalence relations and algebraic laws for STOKED processes. These relations support compositional reasoning: verifying properties of a system by reasoning about its components.

## B.1 Trace Equivalence

**Definition B.1 (Trace).** A *trace* of process P is a finite sequence of observable actions:

```
tr = ⟨μ₁, μ₂, ..., μₙ⟩
```

where each μᵢ is a non-τ label and there exists a sequence of configurations:

```
C₀ →*_τ →_{μ₁} C₁ →*_τ →_{μ₂} C₂ →*_τ ... →_{μₙ} Cₙ
```

(where →*_τ denotes zero or more τ-steps).

**Definition B.2 (Trace Set).**

```
traces(P) = { tr | P can perform trace tr }
```

**Definition B.3 (Trace Equivalence).**

```
P =_T Q  iff  traces(P) = traces(Q)
```

Trace equivalence is the coarsest behavioral equivalence. It does not distinguish processes that differ only in their branching structure or deadlock potential.

### B.1.1 Trace Refinement

**Definition B.4 (Trace Refinement).**

```
P ⊑_T Q  iff  traces(P) ⊆ traces(Q)
```

P ⊑_T Q means "P is trace-refined by Q": every trace of P is also a trace of Q. Equivalently, Q permits all behaviors that P permits (and possibly more). In specification terms, P is a tighter specification than Q.

## B.2 Bisimulation

**Definition B.5 (Strong Bisimulation).** A relation R on processes is a *strong bisimulation* if whenever (P, Q) ∈ R:

1. If P →_μ P', then ∃Q'. Q →_μ Q' and (P', Q') ∈ R
2. If Q →_μ Q', then ∃P'. P →_μ P' and (P', Q') ∈ R

**Definition B.6 (Strong Bisimilarity).**

```
P ~ Q  iff  ∃ strong bisimulation R. (P, Q) ∈ R
```

**Definition B.7 (Weak Bisimulation).** A relation R is a *weak bisimulation* if whenever (P, Q) ∈ R:

1. If P →_μ P' and μ ≠ τ, then ∃Q'. Q →*_τ →_μ →*_τ Q' and (P', Q') ∈ R
2. If P →_τ P', then ∃Q'. Q →*_τ Q' and (P', Q') ∈ R
3. Symmetric conditions for Q

**Definition B.8 (Weak Bisimilarity).**

```
P ≈ Q  iff  ∃ weak bisimulation R. (P, Q) ∈ R
```

### B.2.1 Hierarchy of Equivalences

```
P ~ Q  ⟹  P ≈ Q  ⟹  P =_T Q
```

Strong bisimilarity implies weak bisimilarity implies trace equivalence. The converses do not hold in general.

## B.3 Performance Equivalence

STOKED introduces a notion of equivalence specific to its queueing semantics.

**Definition B.9 (Performance Equivalence).** Two processes P and Q are *performance-equivalent*, written P ≡_perf Q, if:

1. They have the same queueing network structure: Q(P) and Q(Q) have the same topology (nodes, routing matrix)
2. For all stations s: E[Service(s)] in Q(P) = E[Service(s)] in Q(Q)
3. For all stations s: c²(Service(s)) in Q(P) = c²(Service(s)) in Q(Q)
4. For all stations s: server count c(s) in Q(P) = c(s) in Q(Q)

**Theorem B.1.** If P ≡_perf Q, then for all performance metrics m ∈ {throughput, cycle_time, wip, utilization}:

```
m(Q(P)) = m(Q(Q))
```

**Proof sketch.** Performance metrics depend only on the queueing network parameters (arrival rates, service rates, SCVs, server counts, routing probabilities). Since performance equivalence requires identical parameters and topology, the metrics are identical. □

### B.3.1 Performance Refinement

**Definition B.10 (Performance Refinement).** P ⊑_perf Q if:

```
throughput(Q(Q)) ≥ throughput(Q(P))
cycle_time(Q(Q)).mean ≤ cycle_time(Q(P)).mean
wip(Q(Q)) ≤ wip(Q(P))
```

This captures the notion that Q is "at least as good" as P in performance terms.

## B.4 Algebraic Laws

The following algebraic laws hold for STOKED processes. Each law states an equivalence (strong bisimilarity ~, weak bisimilarity ≈, or trace equivalence =_T) between process expressions.

### B.4.1 Laws of Sequential Composition

```
skip ; P  ~  P                                      [Seq-UnitL]
P ; skip  ~  P                                      [Seq-UnitR]
(P ; Q) ; R  ~  P ; (Q ; R)                         [Seq-Assoc]
stop ; P  ~  stop                                    [Seq-StopL]
```

**Remark.** There is no simplification law for `P ; stop` in general. If P terminates (reduces to `skip`), then `P ; stop` reduces to `stop` via [SC-SeqUnit] and [Seq-StopL]. If P diverges, `P ; stop` behaves as P. The asymmetry between [Seq-StopL] (`stop` absorbs on the left) and the absence of a right-stop law reflects the fact that sequential composition is not commutative.

### B.4.2 Laws of Parallel Composition

```
P | Q  ~  Q | P                                     [Par-Comm]
(P | Q) | R  ~  P | (Q | R)                         [Par-Assoc]
P | stop  ~  P                                      [Par-Unit]
P ||| Q  ~  Q ||| P                                 [Intl-Comm]
(P ||| Q) ||| R  ~  P ||| (Q ||| R)                 [Intl-Assoc]
P ||| stop  ~  P                                    [Intl-Unit]
```

**Remark.** [Par-Unit] follows the pi-calculus convention where `stop` denotes inaction (the process `0`). An inert process composed in parallel contributes no transitions and is absorbed. This differs from CSP's `STOP`, which actively refuses all events and can block synchronizing partners. In STOKED, `stop` is inert (pi-calculus style); potential deadlock arises from *cyclic dependency*, not from a single stopped component.

### B.4.3 Laws of Choice

```
P [] Q  ~  Q [] P                                   [Ext-Comm]
P [] P  ~  P                                        [Ext-Idem]
P [] stop  ~  P                                     [Ext-Unit]
(P [] Q) [] R  ~  P [] (Q [] R)                     [Ext-Assoc]
P |~| Q  ≈  Q |~| P                                [Int-Comm]
P |~| P  ≈  P                                      [Int-Idem]
```

### B.4.4 Laws of Probabilistic Choice

```
pchoice { 1 -> P, 0 -> Q }  ~  P                   [PChoice-Degen1]
pchoice { p -> P, (1-p) -> P }  ~  P               [PChoice-Idem]
pchoice { p -> P, (1-p) -> Q }
  ~  pchoice { (1-p) -> Q, p -> P }                [PChoice-Comm]
```

### B.4.5 Laws of Restriction

```
(nu a) stop  ~  stop                                 [Res-Stop]
(nu a) skip  ~  skip                                 [Res-Skip]
(nu a) (nu b) P  ~  (nu b) (nu a) P                 [Res-Comm]
(nu a) (P | Q)  ~  P | (nu a) Q     if a ∉ fn(P)   [Res-Ext]
```

### B.4.6 Laws of Replication

```
!P  ~  P | !P                                       [Repl-Unfold]
!(P | Q)  ~  !P | !Q     if fn(P) ∩ fn(Q) = ∅      [Repl-Par]
!stop  ~  stop                                       [Repl-Stop]
```

**Remark.** [Repl-Par] requires P and Q to share no free names. Without this restriction, `!(P | Q)` pairs each copy of P with a copy of Q, while `!P | !Q` allows arbitrary matchings — these are not bisimilar in general.

### B.4.7 Laws of Delay

```
delay(Deterministic(0))  ~  skip                     [Delay-Zero]
delay(D₁) ; delay(D₂)  ≡_perf  delay(convolve(D₁, D₂))  [Delay-Convolve]
```

Note: [Delay-Convolve] is a *performance* equivalence, not a strong bisimilarity, because the intermediate state (after D₁, before D₂) is observable in the LTS.

### B.4.8 Distribution Laws

```
P | delay(D)  ≈  delay(D) | P                       [Par-Delay-Comm]
```

For station-level reasoning:

```
station s { service_time: D }
  ≡_perf  station s { service_time: D' }
  when E[D] = E[D'] and c²(D) = c²(D')            [Station-SCV]
```

Two stations with the same mean and SCV are performance-equivalent under the VUT approximation.

### B.4.9 Laws of Send/Receive

```
(nu a)((a ! v ; P) | (a ? x ; Q))  ≈  (nu a)(P | Q[v/x])  [Comm-Async]

(a !! v ; P) | (a ?? x ; Q)  ~  P | Q[v/x]                 [Comm-Sync]
```

**Remark.** [Comm-Async] requires restriction `(nu a)` to ensure channel `a` is private with exactly one sender and one receiver. Without restriction, other parallel components could also interact with `a`.

### B.4.10 Expansion Law

For alphabetized parallel, the expansion law decomposes synchronization:

```
(a ! v ; P) |[{a}]| (a ? x ; Q)
  ~  τ ; (P |[{a}]| Q[v/x])                         [Alpha-Sync]

(b ! v ; P) |[{a}]| (c ? x ; Q)
  ~  (b ! v ; P |[{a}]| Q)                          [Alpha-Indep]
    when b ∉ {a} and c ∉ {a}
```

## B.5 Congruence Properties

**Theorem B.2.** Strong bisimilarity (~) is a congruence for all STOKED operators:

```
If P ~ P', then:
    P ; Q  ~  P' ; Q
    Q ; P  ~  Q ; P'
    P | Q  ~  P' | Q
    P ||| Q  ~  P' ||| Q
    P |[S]| Q  ~  P' |[S]| Q
    P [] Q  ~  P' [] Q
    P |~| Q  ~  P' |~| Q
    (nu a) P  ~  (nu a) P'
    !P  ~  !P'
```

**Proof sketch.** For each operator, the bisimulation relation is constructed by pairing corresponding configurations. The key insight is that each operator's semantics is defined compositionally (the transitions of the composite depend only on the transitions of the components), so substituting bisimilar components preserves the bisimulation property. □

**Theorem B.3.** Weak bisimilarity (≈) is a congruence for all STOKED operators except external choice (`[]`). In particular, ≈ is a congruence for internal choice (`|~|`), probabilistic choice (`pchoice`), parallel composition, sequential composition, restriction, and replication.

**Remark.** The failure of weak bisimilarity to be a congruence for external choice is standard in process algebra (the "problem of the external choice"). STOKED inherits this from CSP. For external choice, trace-failures equivalence (not defined here) is the appropriate congruence.

**Remark.** Probabilistic choice preserves weak bisimilarity because the τ-transition resolving the choice is matched by a corresponding τ-transition in the bisimulating process — the weights (probabilities) are preserved by definition of probabilistic bisimulation. For a full treatment, see Segala and Lynch's probabilistic automata framework.

**Theorem B.4.** Performance equivalence (≡_perf) is a congruence for sequential composition, parallel composition, and choice operators (where the queueing network structure is preserved).

## B.6 Derived Laws for STOKED Patterns

### B.6.1 Pipeline Absorption

```
Pipeline([P]) ~ P                                    [Pipe-Single]
Pipeline(Ps ++ Qs) ~ Pipeline(Ps) ; Pipeline(Qs)    [Pipe-Split]
```

### B.6.2 Fan-Out/Fan-In Simplification

```
FanOutFanIn(ch, [ch₁], join_ch, work) ~ work         [Fan-Single]
```

A fan-out to a single worker is equivalent to just doing the work.

### B.6.3 Retry Simplification

```
RetryLoop(0, body, fallback) ~ fallback               [Retry-Zero]
RetryLoop(1, body, fallback) ~ body [] fallback        [Retry-One]
```

### B.6.4 Kanban Equivalence

A station with WIP limit W and c servers, operating at utilization ρ < 1, is performance-equivalent to the same station without WIP limit when W is sufficiently large:

```
KanbanStation(W, D) with c servers
  ≡_perf  Station(D) with c servers
  when W >> W₀ = r_b · T₀                            [Kanban-Large-WIP]
```

(The WIP limit is non-binding when WIP is far above critical WIP.)

## B.7 Fairness

**Definition B.11 (Fair Execution).** An execution of a STOKED system is *fair* if every continuously enabled transition eventually fires.

**Theorem B.5 (Fairness under Stochastic Semantics).** Under the stochastic operational semantics (§5.6) with continuous distributions, every execution is almost surely fair — every continuously enabled transition fires with probability 1.

**Proof sketch.** Under the race condition semantics with continuous distributions, the probability that any particular event is delayed indefinitely is 0 (since the minimum of finitely many continuous random variables is almost surely achieved by each variable infinitely often in the limit). □

---

*Previous: [Appendix A — Proof Sketches](appendix-a-proofs.md)*
