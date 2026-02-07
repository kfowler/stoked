# STOKED Language Specification

## Chapter 7 — Queueing Semantics

---

This chapter defines the queueing model extraction function Q(·) that maps STOKED systems to queueing network models. The queueing semantics provides the performance analysis framework: throughput, cycle time, utilization, WIP bounds, and bottleneck identification.

## 7.1 Queueing Model Extraction

**Definition 7.1 (Queueing Model).** The queueing model extracted from a STOKED system is a tuple:

```
Q(S) = (Nodes, Classes, Arrivals, Routing, Service, Capacities)
```

where:
- Nodes = {n₁, ..., nₖ} is the set of *service nodes* (one per station)
- Classes = {c₁, ..., cₘ} is the set of *job classes* (one per distinct type flowing through the network)
- Arrivals : Classes × Nodes → Dist maps (class, node) pairs to external arrival distributions (or ⊥ if no external arrivals)
- Routing : (Classes × Nodes) → Distribution(Classes × Nodes ∪ {exit}) maps each (class, node) pair to a routing distribution over next destinations
- Service : Classes × Nodes → (c, Dist, Discipline) maps each (class, node) pair to (server count, service time distribution, queue discipline)
- Capacities : Nodes → ℕ ∪ {∞} maps nodes to buffer capacities

### 7.1.1 Extraction Rules

```
Q(station s(a_in -> a_out) { servers: c, discipline: disc, service_time: D, ... }) =
    node n_s with:
        Service(*, n_s) = (c, D, disc)

Q(arrival α : { channel: a, distribution: D_arr, job: j, class: cls }) =
    Arrivals(cls, n_s) = D_arr     where n_s is the station consuming from channel a

Q(pchoice { w₁ -> (b₁ ! x), ..., wₙ -> (bₙ ! x) } after station s) =
    For each bᵢ leading to station sᵢ:
        Routing(cls, n_s)(cls, n_{sᵢ}) = wᵢ / Σⱼ wⱼ
```

## 7.2 Station Classification

Each STOKED station is classified according to the BCMP theorem's four server types, based on its service discipline and service time distribution:

### 7.2.1 BCMP Type Classification

| BCMP Type | Discipline | Service Distribution | STOKED Station Config |
|-----------|-----------|---------------------|----------------------|
| Type 1 | FCFS (FIFO) | Exponential, class-independent | `discipline: fifo`, `service_time: Exponential(μ)` |
| Type 2 | PS (Processor Sharing) | General, class-dependent | `discipline: ps` |
| Type 3 | IS (Infinite Server / Delay) | General, class-dependent | `discipline: is(∞)` or `servers: ∞` |
| Type 4 | LCFS-PR (Preemptive LIFO) | General, class-dependent | `discipline: lifo`, `preemptible: true` |

**Definition 7.2 (BCMP Compatibility).** A STOKED system is *BCMP-compatible* if every station falls into one of the four BCMP types. BCMP-compatible systems admit product-form solutions for steady-state probabilities.

### 7.2.2 Non-BCMP Stations

Stations with non-standard configurations (e.g., SPT discipline, batch processing, WIP limits) are classified as *general* stations. Performance analysis for systems containing general stations uses approximation methods (§7.5).

## 7.3 Open Network Analysis (Jackson Networks)

**Definition 7.3 (Jackson Network Conditions).** A STOKED system forms a Jackson network if:
1. All arrivals are Poisson (exponential inter-arrival times)
2. All service times are exponential
3. All stations use FIFO discipline
4. Routing is probabilistic (Markovian) and class-independent
5. All stations have infinite buffer capacity

### 7.3.1 Traffic Equations

For a Jackson network with external arrival rates λ₀ᵢ to station i and routing matrix R:

```
λᵢ = λ₀ᵢ + Σⱼ λⱼ · rⱼᵢ     for all stations i
```

In matrix form: **λ** = **λ₀** + **λ** · R, solving to **λ** = **λ₀** · (I - R)⁻¹.

**Theorem 7.1 (Jackson's Theorem).** If all λᵢ satisfy λᵢ < cᵢ · μᵢ (stability), then the steady-state distribution has product form:

```
π(n₁, ..., nₖ) = ∏ᵢ πᵢ(nᵢ)
```

where πᵢ is the marginal distribution for station i, identical to an independent M/M/cᵢ queue with arrival rate λᵢ.

### 7.3.2 Performance Metrics (Jackson)

For each station i in a Jackson network:

```
Utilization:     ρᵢ = λᵢ / (cᵢ · μᵢ)
Expected WIP:    Lᵢ = ρᵢ/(1-ρᵢ) · C(cᵢ, ρᵢ·cᵢ) + cᵢ·ρᵢ      (M/M/c formula)
Expected CT:     Wᵢ = Lᵢ / λᵢ                                   (Little's Law)
Throughput:      THᵢ = λᵢ                                        (stable system)
```

where C(c, a) is the Erlang-C probability (probability that an arriving job must wait):

```
C(c, a) = (aᶜ/c!) · (1/(1-a/c)) / (Σₖ₌₀ᶜ⁻¹ aᵏ/k! + (aᶜ/c!) · (1/(1-a/c)))
```

## 7.4 Closed Network Analysis (MVA)

For closed STOKED systems (no external arrivals; fixed WIP), Mean Value Analysis computes exact performance metrics.

**Definition 7.4 (Closed System).** A STOKED system is closed if it has no `arrival` declarations and the total WIP is fixed by initial channel contents and WIP limits.

### 7.4.1 MVA Algorithm

For a closed network with N jobs and K stations:

```
Initialize: Lᵢ(0) = 0 for all i

For n = 1, 2, ..., N:
    /* Step 1: Compute waiting times */
    Wᵢ(n) = 1/μᵢ · (1 + Lᵢ(n-1))     for single-server stations
    Wᵢ(n) = 1/μᵢ                       for infinite-server (delay) stations

    /* Step 2: Compute throughput */
    TH(n) = n / Σᵢ Vᵢ · Wᵢ(n)

    /* Step 3: Compute queue lengths */
    Lᵢ(n) = TH(n) · Vᵢ · Wᵢ(n)        for all i

where Vᵢ is the visit ratio of station i (from solving λ = λ · R).
```

### 7.4.2 Multi-Class MVA

For multiple job classes, the MVA algorithm generalizes to:

```
For population vector n = (n₁, ..., nₘ) over m classes:
    Wᵢc(n) = 1/μᵢc · (1 + Σ_{classes c'} Lᵢc'(n - eₘ))

    THc(n) = nc / Σᵢ Vᵢc · Wᵢc(n)

    Lᵢc(n) = THc(n) · Vᵢc · Wᵢc(n)
```

## 7.5 GI/G/c Approximations (VUT Equation)

For stations that do not meet Jackson or BCMP conditions, STOKED uses the VUT equation from Factory Physics to approximate expected waiting times.

### 7.5.1 The VUT Equation

**Definition 7.5 (VUT Equation).** For a GI/G/c station:

```
                    ⎛ c²ₐ + c²ₛ ⎞   ⎛  ρ^(√(2(c+1)))  ⎞
CT_q ≈  E[S] · ⎜ ────────── ⎟ · ⎜ ─────────────── ⎟
                    ⎝      2      ⎠   ⎝   c · (1 - ρ)    ⎠
          \_____________/   \________________/
               V                    U × T
          (Variability)     (Utilization × Time)
```

where:
- E[S] = mean service time (T: the natural process time)
- c²ₐ = SCV of inter-arrival times (arrival variability)
- c²ₛ = SCV of service times (service variability)
- ρ = utilization = λ / (c · μ)
- c = number of servers

For the single-server case (c = 1), this reduces to the Kingman formula: CT_q ≈ E[S] · ((c²ₐ + c²ₛ)/2) · (ρ/(1-ρ)).

**Interpretation**: Waiting time is the product of three factors:
1. **V (Variability)**: Average of arrival and service SCVs. High variability → long waits.
2. **U (Utilization)**: A convex, rapidly increasing function of ρ. As ρ → 1, waits → ∞.
3. **T (Time)**: The mean service time. Longer service → proportionally longer waits.

### 7.5.2 SCV Computation

The SCV of each distribution primitive is known analytically:

| Distribution | Mean E[X] | SCV c² |
|-------------|----------|--------|
| Deterministic(v) | v | 0 |
| Exponential(λ) | 1/λ | 1 |
| Erlang(k, λ) | k/λ | 1/k |
| LogNormal(μ, σ) | exp(μ + σ²/2) | exp(σ²) - 1 |
| Uniform(a, b) | (a+b)/2 | (b-a)²/(3(a+b)²) |
| Gamma(α, β) | α/β | 1/α |
| Weibull(k, λ) | λ·Γ(1+1/k) | Γ(1+2/k)/Γ(1+1/k)² - 1 |

For distribution combinators:

```
c²(mix(w₁:D₁, ..., wₙ:Dₙ)) =
    (Σᵢ pᵢ · (E[Dᵢ]² + Var[Dᵢ])) / (Σᵢ pᵢ · E[Dᵢ])² - 1

c²(convolve(D₁, D₂)) =
    (Var[D₁] + Var[D₂]) / (E[D₁] + E[D₂])²
```

### 7.5.3 Departure Variability

The SCV of departures from a GI/G/c station (which becomes the SCV of arrivals to downstream stations):

```
c²_d = 1 + (1 - ρ²) · (c²_a - 1) + ρ² / √c · (c²_s - 1)
```

This is the *Departure Approximation* (Whitt), used to propagate variability through the network.

### 7.5.4 Network Decomposition

For a general network, performance is computed by iterating:

```
1. Solve traffic equations for arrival rates λᵢ
2. Initialize c²_a(i) for external arrivals
3. For each station i:
   a. Compute ρᵢ, CT_q(i) using VUT
   b. Compute c²_d(i) using departure approximation
4. Update c²_a for downstream stations:
   c²_a(j) = Σᵢ (λᵢ·rᵢⱼ/λⱼ) · c²_d(i) + 1 - Σᵢ (λᵢ·rᵢⱼ/λⱼ)
5. Repeat steps 3-4 until convergence
```

## 7.6 Little's Law as Invariant

**Theorem 7.2 (Little's Law).** For any stable STOKED (sub)system S in steady state:

```
L = λ · W
```

where:
- L = E[WIP in S] (average number of jobs in the system)
- λ = throughput of S (average arrival rate = average departure rate at steady state)
- W = E[Cycle Time through S] (average time a job spends in the system)

**Application in STOKED**: Little's Law holds at every level:
- **System-wide**: WIP_total = TH_system × CT_system
- **Per-station**: WIP_station = TH_station × CT_station
- **Per-queue**: L_q = λ × W_q

The `assert littles_law(S)` construct (§3.10) verifies this invariant numerically for the extracted queueing model.

## 7.7 Bottleneck Analysis

**Definition 7.6 (Bottleneck Station).** The bottleneck station is the station with the highest utilization:

```
s_bottleneck = argmaxₛ ρ(s)
```

**Definition 7.7 (Bottleneck Rate).** The bottleneck rate r_b is:

```
r_b = max_s { λ_s / c_s }    (arrival rate per server)
```

equivalently, r_b = max_s { μ_s · ρ_s } for single-class systems.

**Performance bounds (Factory Physics):**

```
Best Case (no variability):
    TH_best = min(W / T₀, r_b)        for WIP = W
    CT_best = max(T₀, W / r_b)

Practical Worst Case (maximal variability):
    CT_pwc = T₀ + (W - 1) / r_b

Worst Case (complete congestion):
    CT_wc = W · T₀
```

where T₀ = Σᵢ E[Sᵢ] · Vᵢ is the raw process time and W is the WIP level.

**Critical WIP**: W₀ = r_b · T₀ is the WIP level at which a balanced line achieves maximum throughput with minimum cycle time.

The `assert bottleneck(S) == s` construct verifies that station s is the bottleneck.

## 7.8 Rework Loop Analysis

Rework loops (stations that route defective items back for reprocessing) affect both throughput and variability.

**Definition 7.8 (Effective Processing Time with Rework).** For a station with rework probability p_r:

```
E[S_eff] = E[S] / (1 - p_r)                    /* effective mean service time */
c²_eff = c²_s + 2·p_r·(1-p_r)·(E[S]/E[S_eff])²  /* effective SCV */
```

The rework loop amplifies both the mean and variability of processing time, worsening queueing performance.

### 7.8.1 Multi-Station Rework

For rework loops involving multiple stations (e.g., code review → fix → re-review), the effective processing time is:

```
E[S_loop] = Σᵢ E[Sᵢ] / (1 - p_r)
c²_loop = (Σᵢ Var[Sᵢ] + rework_variance) / E[S_loop]²
```

where rework_variance accounts for the geometric number of rework cycles.

## 7.9 Batch Processing

Stations with batch processing (`batch: { min: b_min, max: b_max, timeout: t_max }`) modify the queueing model:

```
Effective service time: E[S_batch] = E[S] / E[B]
Effective arrival rate: λ_batch = λ / E[B]

where E[B] is the expected batch size, determined by the batch formation process:
    E[B] = b_max if arrivals are frequent relative to batch timeout
    E[B] ≈ b_min if arrivals are sparse
```

## 7.10 Relationship to Petri Net Semantics

The queueing model extraction and the Petri net translation are consistent:

**Theorem 7.3 (Performance Consistency).** For a STOKED system S:

```
TH(Q(S)) = TH(CTMC(⟦S⟧))
```

where TH(Q(S)) is the throughput computed from the queueing model, and TH(CTMC(⟦S⟧)) is the throughput computed from the CTMC underlying the stochastic Petri net — provided all distributions are exponential (so both the Jackson/BCMP analysis and the CTMC analysis are exact).

For general distributions, the queueing approximation (VUT) and the GSMP of the Petri net may differ; the queueing model provides a computationally efficient approximation.

---

*Previous: [Chapter 6 — Petri Net Semantics](06-petri-net-semantics.md)*
*Next: [Chapter 8 — Well-Formedness Conditions](08-well-formedness.md)*
