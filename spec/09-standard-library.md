# STOKED Language Specification

## Chapter 9 — Standard Library

---

This chapter defines the standard library of STOKED: built-in distributions, queue disciplines, common station patterns, common process patterns, and built-in performance analysis functions. All standard library entities are available without explicit import.

## 9.1 Built-In Distributions

### 9.1.1 Continuous Distributions

All continuous distributions produce values of type `Dist<Duration>` (or `Dist<Float>` where noted).

| Distribution | Syntax | Parameters | Mean | SCV (c²) |
|-------------|--------|-----------|------|----------|
| Deterministic | `Deterministic(v)` | v > 0 | v | 0 |
| Exponential | `Exponential(λ)` | λ > 0 (rate) | 1/λ | 1 |
| Erlang | `Erlang(k, λ)` | k ∈ ℕ⁺, λ > 0 | k/λ | 1/k |
| LogNormal | `LogNormal(μ, σ)` | σ > 0 | e^(μ+σ²/2) | e^(σ²) - 1 |
| Normal | `Normal(μ, σ)` | σ > 0 | μ | σ²/μ² |
| Uniform | `Uniform(a, b)` | a < b | (a+b)/2 | (b-a)²/(3(a+b)²) |
| Triangular | `Triangular(a, m, b)` | a ≤ m ≤ b | (a+m+b)/3 | see below |
| Gamma | `Gamma(α, β)` | α, β > 0 | α/β | 1/α |
| Weibull | `Weibull(k, λ)` | k, λ > 0 | λ·Γ(1+1/k) | see §7.5.2 |
| Beta | `Beta(α, β)` | α, β > 0 | α/(α+β) | β/((α+β)²(α+β+1)·(α/(α+β))²) |
| Pareto | `Pareto(α, x_m)` | α > 2 (finite variance), x_m > 0 | αx_m/(α-1) | 1/(α(α-2)) |

**Note on Normal distribution.** When Normal(μ, σ) is used for `Dist<Duration>`, μ should be positive (μ > 0) to ensure the mean service time is meaningful. Negative samples may arise from the distribution tails; in practice, implementations should truncate or reject negative samples for Duration-typed contexts.

**Triangular SCV:**
```
Var = (a² + m² + b² - am - ab - mb) / 18
c² = Var / ((a+m+b)/3)²
```

### 9.1.2 Discrete Distributions

| Distribution | Syntax | Parameters | Range | Mean |
|-------------|--------|-----------|-------|------|
| Bernoulli | `Bernoulli(p)` | 0 ≤ p ≤ 1 | {true, false} | p |
| Binomial | `Binomial(n, p)` | n ∈ ℕ, 0 ≤ p ≤ 1 | {0, ..., n} | np |
| Poisson | `Poisson(λ)` | λ > 0 | ℕ | λ |
| Geometric | `Geometric(p)` | 0 < p ≤ 1 | ℕ⁺ | 1/p |
| Empirical | `Empirical([v₁, ..., vₙ])` | n ≥ 1 | {v₁, ..., vₙ} | (Σvᵢ)/n |

### 9.1.3 Distribution Combinators

| Combinator | Syntax | Semantics |
|-----------|--------|-----------|
| Mixture | `mix(w₁: D₁, ..., wₙ: Dₙ)` | Draw from Dᵢ with probability wᵢ/Σwⱼ |
| Truncation | `truncate(D, lo, hi)` | Condition D on [lo, hi] |
| Shift | `shift(D, offset)` | X + offset where X ~ D |
| Scale | `scale(D, factor)` | factor · X where X ~ D |
| Maximum | `max_of(D₁, D₂)` | max(X₁, X₂) where X₁ ~ D₁, X₂ ~ D₂ |
| Minimum | `min_of(D₁, D₂)` | min(X₁, X₂) where X₁ ~ D₁, X₂ ~ D₂ |
| Convolution | `convolve(D₁, D₂)` | X₁ + X₂ where X₁ ~ D₁, X₂ ~ D₂ (independent) |

**Note.** The distribution combinator `shift(D, offset)` shares its name with the SPC condition `shift(metric, threshold)` (§3.6). Context disambiguates: `shift` in a `DistExpr` position is the distribution combinator; `shift` in an `SPCCondition` position is the SPC mean-shift detector.

### 9.1.4 Useful Derived Distributions

```stoked
// Bimodal service time (fast path + slow path)
let bimodal_service = mix(
  0.8: LogNormal(log(5m), 0.3),   // 80% fast
  0.2: LogNormal(log(30m), 0.5)   // 20% slow
)

// Service time with setup + processing
let setup_plus_process = convolve(
  Deterministic(2m),               // fixed setup
  Exponential(1/10m)               // variable processing
)

// Bounded service time (no outliers beyond 1h)
let bounded_service = truncate(LogNormal(log(15m), 0.8), 1m, 1h)
```

## 9.2 Queue Disciplines

| Discipline | Syntax | Description | BCMP Type |
|-----------|--------|-------------|-----------|
| First-In First-Out | `fifo` | Standard FIFO | Type 1 |
| Last-In First-Out | `lifo` | Stack order (preemptive) | Type 4 |
| Processor Sharing | `ps` | Equal service share | Type 2 |
| Infinite Server | `is(∞)` | No queueing (delay station) | Type 3 |
| Shortest Processing Time | `spt` | Minimize mean cycle time | General |
| Earliest Due Date | `edd` | Minimize max tardiness | General |
| Priority | `priority` | Strict priority classes | General |

## 9.3 Common Station Patterns

### 9.3.1 Delay Station

A station with infinite servers — every job starts service immediately (no queueing). Models pure delays like network latency, cool-down periods, or SLA wait times.

```stoked
station Delay(name: String, time: Dist<Duration>)
  : in -> out
{
  discipline: is(∞)
  service_time: time
  compute {
    fn: fn(x) -> x    // identity: pass through unchanged
    service_time: time
  }
}
```

**Queueing**: Type 3 (IS) station. L = λ · E[S], no waiting time.

### 9.3.2 Inspect Station

A station that inspects items and routes them by quality. Models code review, QA testing, or automated validation.

```stoked
station Inspect(
  pass_rate: Float,
  rework_target: Chan<T>
) : input -> output
{
  servers: 1
  discipline: fifo
  yield: Bernoulli(pass_rate)
  rework: { probability: 1.0 - pass_rate, target: rework_target }
  human {
    role: "inspector"
    service_time: LogNormal(log(15m), 0.5)
  }
}
```

**Queueing**: Introduces a rework loop with effective processing time E[S]/(1-p_rework). See §7.8.

### 9.3.3 Fork Station

Splits a single input into multiple parallel outputs. Models decomposition tasks like breaking a feature into subtasks.

```stoked
station Fork(n: Int) : input -> (out_1, ..., out_n) {
  servers: 1
  discipline: fifo
  compute {
    fn: fn(x) -> split(x, n)
    service_time: Deterministic(0s)
    deterministic: true
  }
}
```

### 9.3.4 Join Station

Waits for all inputs to arrive, then produces a single combined output. Models synchronization points like "all tests pass" or "all approvals received."

```stoked
station Join(n: Int) : (in_1, ..., in_n) -> output {
  servers: 1
  discipline: fifo
  compute {
    fn: fn(parts) -> merge(parts)
    service_time: Deterministic(0s)
    deterministic: true
  }
}
```

**Queueing**: The Join station's effective service time includes the *synchronization delay* — the time waiting for the last of n parallel items. If each parallel path has cycle time distribution Dᵢ, the join delay is max(D₁, ..., Dₙ).

### 9.3.5 KanbanStation

A station with explicit WIP limit, providing backpressure. When WIP reaches the limit, upstream stations are blocked.

```stoked
station KanbanStation(
  wip_cap: Int,
  service: Dist<Duration>
) : input -> output
{
  servers: 1
  discipline: fifo
  wip limit: wip_cap
  service_time: service
  compute {
    fn: fn(x) -> process(x)
    service_time: service
  }
}
```

**Petri net**: The WIP limit is enforced by a *complementary place* p_wip with initial marking = wip_cap. Each start transition consumes from p_wip; each completion transition produces to p_wip.

### 9.3.6 BatchStation

A station that accumulates items and processes them in batches. Models batch builds, bulk deployments, or grouped reviews.

```stoked
station BatchStation(
  min_batch: Int,
  max_batch: Int,
  batch_timeout: Duration,
  service: Dist<Duration>
) : input -> output
{
  servers: 1
  discipline: fifo
  batch: { min: min_batch, max: max_batch, timeout: batch_timeout }
  service_time: service
  compute {
    fn: fn(batch) -> process_batch(batch)
    service_time: service
  }
}
```

## 9.4 Common Process Patterns

### 9.4.1 RetryLoop

Retry a process up to n times on failure. The choice to retry is an internal (system) decision after observing failure, so it uses internal choice (`|~|`) rather than external choice.

```stoked
process RetryLoop(n: Int, body: proc, on_fail: proc) =
  if n <= 0 then
    on_fail
  else
    body |~| RetryLoop(n - 1, body, on_fail)
```

**Queueing**: Creates a geometric rework loop with escape probability p_success per attempt. Expected iterations = 1/p_success, bounded by n.

### 9.4.2 Pipeline

Sequential chain of stations.

```stoked
process Pipeline(stages: List<proc>) =
  match stages {
    [] => skip,
    [single] => single,
    head :: tail => head ; Pipeline(tail),
  }
```

**Queueing**: Serial network. Cycle time = Σ CT_station. Bottleneck = max utilization station.

### 9.4.3 FanOutFanIn

Parallel execution of n copies, then join.

```stoked
process FanOutFanIn(
  split_ch: Chan<T>,
  work_chs: List<Chan<T>>,
  join_ch: Chan<List<T>>,
  work: proc
) =
  split_ch ? item ;
  (par(work_chs |> map(fn(ch) -> ch ! item ; work)))
  |[{join_ch}]|
  (join_ch ?? results ; skip)
```

**Note.** The synchronous receive `join_ch ?? results` (rendezvous) is used instead of async receive to ensure the join completes atomically — the joining process blocks until all parallel workers have deposited their results and the join channel is ready.

**Queueing**: CT = max(CT_parallel_paths) + CT_fork + CT_join. Throughput limited by slowest parallel path.

### 9.4.4 CircuitBreaker

Stop sending work to a station if it exceeds error/latency thresholds.

```stoked
process CircuitBreaker(
  target: proc,
  fallback: proc,
  threshold: Int,
  reset_time: Duration
) =
  rec Loop(err_count: Int = 0).
    if err_count >= threshold then
      delay(Deterministic(reset_time)) ;
      Loop(0)
    else
      (target ; Loop(err_count))
      []
      (fallback ; Loop(err_count + 1))
```

### 9.4.5 RateLimiter

Throttle arrivals to a maximum rate.

```stoked
process RateLimiter(max_rate: Rate, downstream: proc) =
  rec Throttle().
    delay(Deterministic(1/max_rate)) ;
    downstream ;
    Throttle()
```

## 9.5 Built-In Performance Functions

These functions are available in `assert` declarations and expressions.

### 9.5.1 System-Level Metrics

| Function | Type | Description |
|----------|------|-------------|
| `throughput(S)` | System → Rate | Steady-state throughput |
| `cycle_time(S)` | System → Dist<Duration> | Cycle time distribution |
| `wip(S)` | System → Float | Expected WIP (L) |
| `bottleneck(S)` | System → Station | Station with max utilization |
| `critical_wip(S)` | System → Float | W₀ = r_b × T₀ |
| `raw_process_time(S)` | System → Duration | T₀ = Σ E[Sᵢ] × Vᵢ |
| `bottleneck_rate(S)` | System → Rate | r_b = max(λᵢ/cᵢ) |

### 9.5.2 Station-Level Metrics

| Function | Type | Description |
|----------|------|-------------|
| `utilization(s)` | Station → Float | ρ = λ/(c·μ) |
| `wait_time(s)` | Station → Dist<Duration> | Time in queue |
| `queue_length(s)` | Station → Float | Expected queue length (L_q) |
| `service_time(s)` | Station → Dist<Duration> | Service time distribution |
| `yield_rate(s)` | Station → Float | P(good output) |
| `scrap_rate(s)` | Station → Float | P(scrapped) |
| `effective_process_time(s)` | Station → Duration | E[S]/(1-p_rework) |

### 9.5.3 Percentile Accessors

Cycle time and wait time metrics support percentile accessors:

```stoked
cycle_time(S).mean      // E[CT]
cycle_time(S).p50       // median
cycle_time(S).p90       // 90th percentile
cycle_time(S).p95       // 95th percentile
cycle_time(S).p99       // 99th percentile
cycle_time(S).max       // maximum (may be ∞ for unbounded distributions)
```

### 9.5.4 Verification Functions

| Function | Type | Description |
|----------|------|-------------|
| `littles_law(S)` | System → Bool | Checks L = λW ± ε |
| `deadlock_free(S)` | System → Bool | Structural deadlock-freedom |
| `steady_state(S)` | System → Bool | All stations stable (ρ < 1) |
| `conservative(S)` | System → Bool | Flow balance (P-invariant exists) |
| `bounded(S, k)` | (System, Int) → Bool | k-bounded |
| `live(S)` | System → Bool | Every transition can eventually fire |

## 9.6 Time and Rate Arithmetic

```stoked
// Time literals and arithmetic
let build_time = 5m
let review_time = 30m
let total = build_time + review_time        // 35m : Duration
let scaled = 2.0 * build_time               // 10m : Duration

// Rate literals and arithmetic
let arrival_rate = 10/d                      // 10 per day : Rate
let service_rate = 1/30m                     // 1 per 30 min : Rate
let utilization = arrival_rate / service_rate // 0.208 : Float

// Little's Law computation
let expected_wip = arrival_rate * cycle_time(System).mean  // Float
```

## 9.7 Built-In Collection Functions

The following functions operate on `List<T>` and are available without import:

| Function | Type | Description |
|----------|------|-------------|
| `map(f, xs)` | `(T -> U, List<T>) -> List<U>` | Apply f to each element |
| `filter(f, xs)` | `(T -> Bool, List<T>) -> List<T>` | Keep elements where f is true |
| `fold(f, init, xs)` | `((U, T) -> U, U, List<T>) -> U` | Left fold |
| `length(xs)` | `List<T> -> Int` | Number of elements |
| `head(xs)` | `List<T> -> T` | First element |
| `tail(xs)` | `List<T> -> List<T>` | All but first |
| `concat(xs, ys)` | `(List<T>, List<T>) -> List<T>` | Concatenation (also `++`) |
| `zip(xs, ys)` | `(List<T>, List<U>) -> List<(T, U)>` | Pair elements |
| `range(n)` | `Int -> List<Int>` | `[0, 1, ..., n-1]` |
| `split(x, n)` | `(T, Int) -> List<T>` | Replicate x into n copies |
| `merge(xs)` | `List<T> -> T` | Combine list elements (type-dependent) |

---

*Previous: [Chapter 8 — Well-Formedness Conditions](08-well-formedness.md)*
*Next: [Chapter 10 — Examples](10-examples.md)*
