# STOKED Language Specification

## Chapter 10 — Examples

---

This chapter presents three complete, worked examples that demonstrate the full STOKED language across the software lifecycle domain. Each example includes type declarations, channel/station definitions, process definitions, performance assertions, and analysis.

---

## 10.1 Example A: CI/CD Pipeline with Code Review

### 10.1.1 Problem Description

A software team processes pull requests through: automated build → code review (human) → automated testing → deployment. Code review may request rework (30% of the time). PRs arrive at 10/day on average. The team wants to ensure < 2-day p95 cycle time and ≥ 95% throughput.

### 10.1.2 Type Declarations

```stoked
module Examples.CICD

type PRStatus = Pending | Building | InReview | Testing | Deploying | Done | Failed

type PullRequest = {
  id: Int,
  author: String,
  title: String,
  files_changed: Int,
  status: PRStatus,
  priority: Int,
  created_at: Duration
}

type BuildResult = {
  pr: PullRequest,
  success: Bool,
  artifacts: List<String>,
  duration: Duration
}

type ReviewResult = {
  pr: PullRequest,
  approved: Bool,
  comments: List<String>,
  reviewer: String
}

type TestResult = {
  pr: PullRequest,
  passed: Bool,
  coverage: Float,
  failures: List<String>
}

type DeployResult = {
  pr: PullRequest,
  environment: String,
  success: Bool,
  version: String
}
```

### 10.1.3 Channel Declarations

```stoked
channel pr_queue     : Chan<PullRequest>
channel build_queue  : Chan<PullRequest>
channel review_queue : Chan<BuildResult>
channel test_queue   : Chan<ReviewResult>
channel deploy_queue : Chan<TestResult>
channel done_queue   : Chan<DeployResult>
channel rework_queue : Chan<ReviewResult>    // rework loop back to build
```

### 10.1.4 Resource Declarations

```stoked
resource build_agents   : Resource<4>     // 4 parallel build agents
resource review_capacity: Resource<3>     // 3 concurrent reviewers
resource deploy_slots   : Resource<1>     // 1 deployment slot (serialized)

// Escalation targets (human process references)
process TechLead = review_queue ? pr ; CodeReview(pr) ; skip
```

### 10.1.5 Station Declarations

```stoked
station BuildServer : build_queue -> review_queue {
  servers: 4
  discipline: fifo
  service_time: LogNormal(log(8m), 0.6)    // median 8min, variable
  compute {
    fn: fn(pr) -> { pr: pr, success: true, artifacts: ["app.jar"], duration: 0s }
    service_time: LogNormal(log(8m), 0.6)
  }
}

station CodeReview : review_queue -> test_queue {
  servers: 3
  discipline: fifo
  service_time: LogNormal(log(45m), 0.8)   // median 45min, high variability
  yield: Bernoulli(0.70)                    // 70% approval rate
  rework: { probability: 0.30, target: rework_queue }
  human {
    role: "senior_engineer"
    sla: 4h
    escalate: { after: 4h, to: TechLead }
    service_time: LogNormal(log(45m), 0.8)
    schedule: { 9h..17h }                   // business hours only
  }
}

station TestRunner : test_queue -> deploy_queue {
  servers: 8
  discipline: fifo
  service_time: LogNormal(log(12m), 0.4)    // median 12min, moderate variability
  compute {
    fn: fn(review) -> { pr: review.pr, passed: true, coverage: 0.85, failures: [] }
    service_time: LogNormal(log(12m), 0.4)
  }
}

station Deployer : deploy_queue -> done_queue {
  servers: 1
  discipline: fifo
  service_time: Triangular(2m, 5m, 15m)     // 2-15min, mode 5min
  compute {
    fn: fn(test) -> { pr: test.pr, environment: "production", success: true, version: "1.0" }
    service_time: Triangular(2m, 5m, 15m)
  }
}

// Rework station: author fixes issues from code review
station ReworkStation : rework_queue -> build_queue {
  servers: 6
  discipline: fifo
  service_time: LogNormal(log(30m), 0.7)    // median 30min to fix
  human {
    role: "developer"
    service_time: LogNormal(log(30m), 0.7)
  }
}
```

### 10.1.6 Arrival Declaration

```stoked
arrival PRArrivals : {
  channel: pr_queue
  distribution: Exponential(10/d)            // 10 PRs per day, Poisson arrival
  job: { id: 0, author: "dev", title: "feature", files_changed: 5,
         status: Pending, priority: 1, created_at: 0s }
}
```

### 10.1.7 Process Definition

```stoked
process CICDPipeline =
  // Main pipeline with rework loop
  (nu internal_build : Chan<PullRequest>)
  (
    // Arrival -> Build
    (!( pr_queue ? pr ;
        build_queue ! pr ;
        skip ))
    |||
    // Build -> Review -> Test -> Deploy (with rework)
    (!( build_queue ? pr ;
        acquire(build_agents, 1) ;
        BuildServer(pr) ;                      // deposits BuildResult on review_queue
        release(build_agents, 1) ;

        review_queue ? build_result ;           // receive BuildResult
        acquire(review_capacity, 1) ;
        CodeReview(build_result) ;              // deposits ReviewResult on test_queue
        release(review_capacity, 1) ;
        // Rework loop handled by CodeReview's yield/rework config

        test_queue ? reviewed_pr ;
        TestRunner(reviewed_pr) ;               // deposits TestResult on deploy_queue

        deploy_queue ? tested_pr ;
        acquire(deploy_slots, 1) ;
        Deployer(tested_pr) ;                   // deposits DeployResult on done_queue
        release(deploy_slots, 1) ;
        skip ))
    |||
    // Rework path
    (!( rework_queue ? rework_pr ;
        ReworkStation(rework_pr) ;
        build_queue ! rework_pr.pr ;
        skip ))
  )
```

### 10.1.8 Performance Assertions

```stoked
// Throughput: at least 9.5/day (95% of arrival rate, accounting for scrap)
assert throughput(CICDPipeline) >= 9.5/d

// Cycle time: p95 under 2 days
assert cycle_time(CICDPipeline).p95 <= 2d

// WIP: no more than 25 active PRs
assert wip(CICDPipeline) <= 25

// Utilization: no station over 85%
assert utilization(CodeReview) <= 0.85
assert utilization(Deployer) <= 0.85

// Structural properties
assert deadlock_free(CICDPipeline)
assert steady_state(CICDPipeline)
assert conservative(CICDPipeline)
assert littles_law(CICDPipeline)

// Bottleneck identification
assert bottleneck(CICDPipeline) == CodeReview
```

### 10.1.9 Performance Analysis

**Traffic equations** (§7.3.1):

```
λ(BuildServer) = 10/d + λ(ReworkStation)
λ(CodeReview)  = λ(BuildServer) = 10/d + λ(ReworkStation)
λ(ReworkStation) = 0.30 · λ(CodeReview)
λ(TestRunner)  = 0.70 · λ(CodeReview)
λ(Deployer)    = λ(TestRunner)

Solving: λ(CodeReview) = 10/(1-0.30) = 14.29/d
         λ(ReworkStation) = 0.30 · 14.29 = 4.29/d
         λ(BuildServer) = 14.29/d
         λ(TestRunner) = 10/d
         λ(Deployer) = 10/d
```

**Utilization** (§7.3.2):

> **Note on LogNormal means:** For `LogNormal(log(m), σ)`, the *median* is m but the
> *mean* is m · exp(σ²/2). The utilization formula ρ = λ/(c · μ) requires the mean
> service time (1/μ), so we must use the corrected mean, not the median.

```
Mean service times (LogNormal correction: mean = median · exp(σ²/2)):
  BuildServer:   8m  · exp(0.36/2) = 8m  · 1.197 ≈  9.58m
  CodeReview:    45m · exp(0.64/2) = 45m · 1.377 ≈ 61.97m
  TestRunner:    12m · exp(0.16/2) = 12m · 1.083 ≈ 13.00m
  Deployer:      Triangular(2m, 5m, 15m) → mean = (2+5+15)/3 = 7.33m
  ReworkStation: 30m · exp(0.49/2) = 30m · 1.277 ≈ 38.32m

ρ(BuildServer)   = 14.29/d / (4 · 1/(9.58m))  = 14.29/(4·1440/9.58)  = 14.29/601.3  ≈ 0.024
ρ(CodeReview)    = 14.29/d / (3 · 1/(61.97m)) = 14.29/(3·1440/61.97) = 14.29/69.7   ≈ 0.205
ρ(TestRunner)    = 10/d    / (8 · 1/(13.00m)) = 10/(8·1440/13.00)    = 10/886.2     ≈ 0.011
ρ(Deployer)      = 10/d    / (1 · 1/(7.33m))  = 10/(1·1440/7.33)     = 10/196.5     ≈ 0.051
ρ(ReworkStation) = 4.29/d  / (6 · 1/(38.32m)) = 4.29/(6·1440/38.32)  = 4.29/225.4   ≈ 0.019
```

Note: Code review has the highest utilization (ρ ≈ 0.205), confirming it as the bottleneck. In practice, the schedule constraint (business hours only) effectively triples the utilization to ~0.61 during working hours.

**Raw process time** (using corrected LogNormal means):

```
T₀ = E[BuildServer] + E[CodeReview] + E[TestRunner] + E[Deployer]
   = 9.58m + 61.97m + 13.00m + 7.33m
   ≈ 91.88m ≈ 92m
```

**Little's Law verification**:

```
L = λ · W
Expected WIP ≈ (10/d) · E[CT]
With E[CT] ≈ T₀ + queueing delays ≈ 92m + delays
L ≈ 10/d · (92m / (1440m/d)) ≈ 0.64 jobs  (steady state, low utilization)
```

---

## 10.2 Example B: Incident Response System

### 10.2.1 Problem Description

An incident response system receives alerts, triages them by severity, and routes them through appropriate response channels. Critical incidents require immediate human response; warnings are handled by automated remediation with human oversight. The system must maintain a p99 response time under 15 minutes for critical incidents.

### 10.2.2 Declarations

```stoked
module Examples.IncidentResponse

type Severity = Critical | Warning | Info

type Alert = {
  id: Int,
  source: String,
  severity: Severity,
  message: String,
  timestamp: Duration
}

type TriageResult = {
  alert: Alert,
  assigned_to: String,
  priority: Int,
  runbook: Option<String>
}

type RemediationResult = {
  alert: Alert,
  action_taken: String,
  success: Bool,
  duration: Duration
}

type IncidentReport = {
  alert: Alert,
  resolution: String,
  root_cause: String,
  duration: Duration,
  responder: String
}

channel alert_stream     : Chan<Alert>
channel triage_queue     : Chan<Alert>
channel critical_queue   : Chan<TriageResult>
channel warning_queue    : Chan<TriageResult>
channel info_queue       : Chan<TriageResult>
channel remediation_queue: Chan<TriageResult>
channel escalation_queue : Chan<RemediationResult>
channel resolved_queue   : Chan<IncidentReport>

resource oncall_engineers : Resource<3>
resource auto_remediation : Resource<10>

// Escalation target for critical incidents
process IncidentCommander = critical_queue ? triaged ;
  CriticalResponse(triaged) ;
  resolved_queue ! { alert: triaged.alert, resolution: "escalated",
                     root_cause: triaged.runbook, duration: 0m,
                     responder: triaged.assigned_to } ;
  skip
```

### 10.2.3 Stations

```stoked
station AlertTriage : triage_queue -> (critical_queue, warning_queue, info_queue) {
  servers: 2
  discipline: priority
  service_time: mix(
    0.6: Deterministic(5s),       // 60% auto-classified
    0.4: LogNormal(log(2m), 0.5)  // 40% need AI classification
  )
  prompt {
    model: "claude-sonnet"
    temperature: 0.1
    system: "Classify incident severity based on alert data"
    output: TriageResult
    service_time: mix(0.6: Deterministic(5s), 0.4: LogNormal(log(2m), 0.5))
    on_input: (alert) -> { alert: alert, assigned_to: "auto", priority: 1, runbook: None }
  }
}

station CriticalResponse : critical_queue -> resolved_queue {
  servers: 3
  discipline: fifo
  service_time: LogNormal(log(30m), 0.9)    // high variability
  human {
    role: "oncall_engineer"
    sla: 15m
    escalate: { after: 15m, to: IncidentCommander }
    service_time: LogNormal(log(30m), 0.9)
    schedule: { 0h..24h }                    // 24/7
  }
}

station AutoRemediation : remediation_queue -> (resolved_queue, escalation_queue) {
  servers: 10
  discipline: fifo
  service_time: LogNormal(log(1m), 0.6)
  yield: Bernoulli(0.80)                     // 80% auto-fix success
  rework: { probability: 0.20, target: escalation_queue }
  compute {
    fn: fn(triage) -> { alert: triage.alert, action_taken: "auto_remediate",
                        success: true, duration: 0s }
    service_time: LogNormal(log(1m), 0.6)
  }
}

station HumanEscalation : escalation_queue -> resolved_queue {
  servers: 3
  discipline: priority
  service_time: LogNormal(log(20m), 0.7)
  human {
    role: "senior_sre"
    sla: 30m
    service_time: LogNormal(log(20m), 0.7)
  }
}

station InfoLogger : info_queue -> resolved_queue {
  discipline: is(∞)         // infinite server (delay), no queueing
  service_time: Deterministic(1s)
  compute {
    fn: fn(triage) -> { alert: triage.alert, resolution: "logged",
                        root_cause: "info", duration: 1s, responder: "system" }
    service_time: Deterministic(1s)
  }
}
```

### 10.2.4 Arrival

```stoked
arrival AlertStream : {
  channel: alert_stream
  distribution: Exponential(100/d)           // 100 alerts per day
  job: { id: 0, source: "monitoring", severity: Warning,
         message: "alert", timestamp: 0s }
}
```

### 10.2.5 Process Definition

```stoked
process IncidentResponseSystem =
  (
    // Ingest alerts
    !(alert_stream ? alert ;
      triage_queue ! alert ;
      skip)
    |||
    // Triage and route by severity
    !(triage_queue ? alert ;
      AlertTriage(alert) ;
      match alert.severity {
        Critical => critical_queue ! alert,
        Warning  => remediation_queue ! alert,
        Info     => info_queue ! alert,
      })
    |||
    // Critical path: human response
    !(critical_queue ? triaged ;
      acquire(oncall_engineers, 1) ;
      CriticalResponse(triaged) ;
      release(oncall_engineers, 1) ;
      resolved_queue ! { alert: triaged.alert, resolution: "critical_resolved",
                         root_cause: triaged.runbook, duration: 0m,
                         responder: triaged.assigned_to } ;
      skip)
    |||
    // Warning path: auto-remediation with human fallback
    !(remediation_queue ? triaged ;
      acquire(auto_remediation, 1) ;
      AutoRemediation(triaged) ;
      release(auto_remediation, 1) ;
      // 80% resolved automatically; 20% escalated via yield/rework
      skip)
    |||
    // Escalation path
    !(escalation_queue ? failed ;
      acquire(oncall_engineers, 1) ;
      HumanEscalation(failed) ;
      release(oncall_engineers, 1) ;
      resolved_queue ! { alert: failed.alert, resolution: failed.action_taken,
                         root_cause: "escalation", duration: failed.duration,
                         responder: "senior_sre" } ;
      skip)
    |||
    // Info path: just log
    !(info_queue ? triaged ;
      InfoLogger(triaged) ;
      skip)
  )
```

### 10.2.6 SPC Monitoring

```stoked
monitor(CriticalResponse) {
  when cycle_time > 15m =>
    escalation_queue ! current_incident,

  when trend(cycle_time, 5) =>
    // 5 consecutive increasing response times
    alert_stream ! { id: 0, source: "spc", severity: Warning,
                     message: "Response time trending up", timestamp: 0s },

  when shift(throughput, -0.2) =>
    // 20% throughput drop
    alert_stream ! { id: 0, source: "spc", severity: Critical,
                     message: "Throughput degradation", timestamp: 0s },
}
```

### 10.2.7 Performance Assertions

```stoked
// Critical alert response time
assert cycle_time(CriticalResponse).p99 <= 15m

// Overall system throughput
assert throughput(IncidentResponseSystem) >= 95/d

// Auto-remediation success rate
assert yield_rate(AutoRemediation) >= 0.80

// Stability
assert steady_state(IncidentResponseSystem)
assert deadlock_free(IncidentResponseSystem)
assert littles_law(IncidentResponseSystem)

// Engineer utilization (avoid burnout)
assert utilization(CriticalResponse) <= 0.70
assert utilization(HumanEscalation) <= 0.60
```

### 10.2.8 Analysis

**Routing probabilities** (from severity distribution):
```
P(Critical) = 0.10, P(Warning) = 0.60, P(Info) = 0.30

λ(AlertTriage) = 100/d
λ(CriticalResponse) = 10/d
λ(AutoRemediation) = 60/d
λ(InfoLogger) = 30/d
λ(HumanEscalation) = 0.20 · 60/d = 12/d
```

**Note.** The routing probabilities arise from the severity distribution of incoming alerts, not from an explicit `pchoice`. The `match alert.severity` in the process definition is deterministic routing based on the alert's data field. The probabilities P(Critical) = 0.10, P(Warning) = 0.60, P(Info) = 0.30 reflect the assumed severity distribution of the arrival population. In a complete specification, this would be declared as a job class distribution in the arrival declaration.

**Utilization**:
```
ρ(CriticalResponse) = 10/d / (3 · 1/(30m)) = 10/144 = 0.069
ρ(AutoRemediation) = 60/d / (10 · 1/(1m)) = 60/14400 = 0.004
ρ(HumanEscalation) = 12/d / (3 · 1/(20m)) = 12/216 = 0.056
```

All well within targets. The bottleneck is CriticalResponse at 6.9% utilization — low because we have 3 on-call engineers for 10 critical alerts/day.

---

## 10.3 Example C: Multi-Team Kanban Feature Delivery

### 10.3.1 Problem Description

A product organization with three teams (Frontend, Backend, Platform) delivers features through a Kanban system. Features are decomposed into tasks, worked in parallel, and integrated. The system has WIP limits at each stage. The goal is to deliver features at ≥ 2/week with cycle time p90 ≤ 10 days.

### 10.3.2 Declarations

```stoked
module Examples.KanbanDelivery

type FeatureSize = Small | Medium | Large

type Feature = {
  id: Int,
  title: String,
  size: FeatureSize,
  priority: Int,
  team_assignments: List<String>
}

type Task = {
  feature_id: Int,
  team: String,
  description: String,
  estimated_effort: Duration
}

type TaskResult = {
  task: Task,
  completed: Bool,
  actual_effort: Duration
}

type IntegrationResult = {
  feature: Feature,
  tasks: List<TaskResult>,
  integration_passed: Bool
}

type DeliveryResult = {
  feature: Feature,
  version: String,
  deployed_at: Duration
}

// Kanban board channels (each with WIP limit)
channel backlog          : Chan<Feature>
channel ready_for_dev    : Chan<Feature>
channel frontend_wip     : Chan<Task>
channel backend_wip      : Chan<Task>
channel platform_wip     : Chan<Task>
channel frontend_done    : Chan<TaskResult>
channel backend_done     : Chan<TaskResult>
channel platform_done    : Chan<TaskResult>
channel integration_queue: Chan<List<TaskResult>>
channel qa_queue         : Chan<IntegrationResult>
channel release_queue    : Chan<IntegrationResult>
channel delivered        : Chan<DeliveryResult>
channel rework_dev       : Chan<IntegrationResult>   // integration rework

// WIP limits as resources
resource frontend_wip_limit  : Resource<3>
resource backend_wip_limit   : Resource<4>
resource platform_wip_limit  : Resource<2>
resource integration_limit   : Resource<1>
resource release_limit       : Resource<1>
```

### 10.3.3 Stations

```stoked
// Product manager decomposes features into tasks
station FeatureDecomposition : ready_for_dev -> (frontend_wip, backend_wip, platform_wip) {
  servers: 1
  discipline: priority
  service_time: LogNormal(log(2h), 0.5)
  human {
    role: "product_manager"
    service_time: LogNormal(log(2h), 0.5)
    schedule: { 9h..17h }
  }
}

// Frontend team
station FrontendDev : frontend_wip -> frontend_done {
  servers: 3
  discipline: fifo
  wip limit: 3
  // Service time depends on feature size (weighted mixture approximation)
  service_time: mix(
    0.3: LogNormal(log(1d), 0.6),   // Small
    0.5: LogNormal(log(3d), 0.7),   // Medium
    0.2: LogNormal(log(5d), 0.8)    // Large
  )
  prompt {
    model: "claude-opus"
    temperature: 0.3
    system: "Implement frontend task according to design spec"
    tools: ["code_editor", "browser_preview", "test_runner"]
    output: TaskResult
    service_time: LogNormal(log(2d), 0.7)
    on_input: (task) -> { task: task, completed: true, actual_effort: 0s }
  }
}

// Backend team
station BackendDev : backend_wip -> backend_done {
  servers: 4
  discipline: fifo
  wip limit: 4
  service_time: LogNormal(log(2d), 0.7)
  prompt {
    model: "claude-opus"
    temperature: 0.2
    system: "Implement backend service according to API spec"
    tools: ["code_editor", "api_tester", "db_console"]
    output: TaskResult
    service_time: LogNormal(log(2d), 0.7)
    on_input: (task) -> { task: task, completed: true, actual_effort: 0s }
  }
}

// Platform team
station PlatformDev : platform_wip -> platform_done {
  servers: 2
  discipline: fifo
  wip limit: 2
  service_time: LogNormal(log(3d), 0.8)
  prompt {
    model: "claude-opus"
    temperature: 0.2
    system: "Implement infrastructure and platform changes"
    tools: ["terraform", "kubernetes", "monitoring"]
    output: TaskResult
    service_time: LogNormal(log(3d), 0.8)
    on_input: (task) -> { task: task, completed: true, actual_effort: 0s }
  }
}

// Integration testing (join + test)
station IntegrationTest : integration_queue -> (qa_queue, rework_dev) {
  servers: 1
  discipline: fifo
  service_time: LogNormal(log(4h), 0.6)
  yield: Bernoulli(0.75)         // 75% pass integration on first try
  rework: { probability: 0.25, target: rework_dev }
  compute {
    fn: fn(tasks) -> { feature: tasks[0].task.feature_id,
                       tasks: tasks, integration_passed: true }
    service_time: LogNormal(log(4h), 0.6)
  }
}

// QA validation
station QAValidation : qa_queue -> release_queue {
  servers: 2
  discipline: fifo
  service_time: LogNormal(log(1d), 0.6)
  human {
    role: "qa_engineer"
    service_time: LogNormal(log(1d), 0.6)
    schedule: { 9h..17h }
  }
}

// Release / deployment
station ReleaseDeploy : release_queue -> delivered {
  servers: 1
  discipline: fifo
  service_time: Triangular(30m, 1h, 3h)
  compute {
    fn: fn(result) -> { feature: result.feature, version: "1.0",
                        deployed_at: 0s }
    service_time: Triangular(30m, 1h, 3h)
  }
}
```

### 10.3.4 Arrival

```stoked
arrival FeatureRequests : {
  channel: backlog
  distribution: Exponential(3/w)              // 3 features per week
  job: { id: 0, title: "feature", size: Medium, priority: 1,
         team_assignments: ["frontend", "backend"] }
}
```

### 10.3.5 Process Definition

```stoked
process KanbanSystem =
  (
    // Pull from backlog to ready (respecting WIP)
    !(backlog ? feature ;
      ready_for_dev ! feature ;
      skip)
    |||
    // Decompose and fan out to teams
    !(ready_for_dev ? feature ;
      FeatureDecomposition(feature) ;
      // Fork: send tasks to each assigned team
      (frontend_wip ! { feature_id: feature.id, team: "frontend",
                        description: "frontend work", estimated_effort: 2d }
       |||
       backend_wip ! { feature_id: feature.id, team: "backend",
                       description: "backend work", estimated_effort: 2d }
       |||
       platform_wip ! { feature_id: feature.id, team: "platform",
                        description: "platform work", estimated_effort: 3d })
      ; skip)
    |||
    // Team work (parallel, WIP-limited)
    !(acquire(frontend_wip_limit, 1) ;
      frontend_wip ? task ;
      FrontendDev(task) ;
      frontend_done ! task ;
      release(frontend_wip_limit, 1) ;
      skip)
    |||
    !(acquire(backend_wip_limit, 1) ;
      backend_wip ? task ;
      BackendDev(task) ;
      backend_done ! task ;
      release(backend_wip_limit, 1) ;
      skip)
    |||
    !(acquire(platform_wip_limit, 1) ;
      platform_wip ? task ;
      PlatformDev(task) ;
      platform_done ! task ;
      release(platform_wip_limit, 1) ;
      skip)
    |||
    // Join: wait for all team results, then integrate
    !(frontend_done ? fe_result ;
      backend_done ? be_result ;
      platform_done ? pl_result ;
      acquire(integration_limit, 1) ;
      integration_queue ! [fe_result, be_result, pl_result] ;
      IntegrationTest([fe_result, be_result, pl_result]) ;
      release(integration_limit, 1) ;
      skip)
    |||
    // QA
    !(qa_queue ? integrated ;
      QAValidation(integrated) ;
      release_queue ! integrated ;
      skip)
    |||
    // Release
    !(acquire(release_limit, 1) ;
      release_queue ? validated ;
      ReleaseDeploy(validated) ;
      release(release_limit, 1) ;
      skip)
    |||
    // Rework path: integration failures go back to dev
    !(rework_dev ? failed ;
      // Re-dispatch to the team that had the failing component
      frontend_wip ! { feature_id: failed.feature.id, team: "frontend",
                       description: "integration fix", estimated_effort: 1d } ;
      skip)
  )
```

### 10.3.6 Performance Assertions

```stoked
// Feature delivery rate
assert throughput(KanbanSystem) >= 2/w

// Cycle time
assert cycle_time(KanbanSystem).p90 <= 10d
assert cycle_time(KanbanSystem).mean <= 7d

// WIP bounds (Kanban limits)
assert wip(KanbanSystem) <= 15

// Station utilization
assert utilization(FrontendDev) <= 0.80
assert utilization(BackendDev) <= 0.80
assert utilization(PlatformDev) <= 0.80

// Integration success rate
assert yield_rate(IntegrationTest) >= 0.75

// Structural properties
assert deadlock_free(KanbanSystem)
assert steady_state(KanbanSystem)
assert conservative(KanbanSystem)
assert littles_law(KanbanSystem)
```

### 10.3.7 Performance Analysis

**Traffic equations**:

> **Note on rework routing:** The process definition routes all integration
> rework to `frontend_wip` only (a simplification). In a more realistic model,
> rework would be dispatched to the team responsible for the failing component.
> The equations below reflect the simplified process as written.

```
λ(FeatureDecomposition) = 3/w
λ(IntegrationTest) = 3/w / (1 - 0.25) = 4/w       (rework loop: 25% fed back)
λ(FrontendDev) = 3/w + 0.25 · λ(IntegrationTest) = 3/w + 1/w = 4/w  (new features + rework)
λ(BackendDev) = 3/w                                 (no rework routed here)
λ(PlatformDev) = 3/w                                (no rework routed here)
λ(QAValidation) = 0.75 · λ(IntegrationTest) = 3/w
λ(ReleaseDeploy) = 3/w
```

**Raw process time** (serial path):
```
T₀ = E[Decomp] + max(E[Frontend], E[Backend], E[Platform]) + E[Integration]
     + E[QA] + E[Release]
   = 2h + max(2d, 2d, 3d) + 4h + 1d + 1h
   = 2h + 3d + 4h + 1d + 1h
   ≈ 4d + 7h ≈ 4.3d
```

The parallel fork (Frontend/Backend/Platform) is dominated by the longest path (Platform at 3d mean). The join introduces a synchronization delay — the expected maximum of three LogNormal random variables.

**Critical WIP**:
```
W₀ = r_b · T₀

r_b (bottleneck rate) — PlatformDev at 2 servers, 3d mean service:
r_b = 2/(3d) = 0.667/d

W₀ = 0.667/d · 4.3d ≈ 2.87 ≈ 3 features
```

**Little's Law verification**:
```
L = λ · W = (3/w) · (4.3d) = 3 · 4.3/7 ≈ 1.84 features in system

With queueing delays and rework, expect L ≈ 3-5 features, well within the WIP limit of 15.
```

---

*Previous: [Chapter 9 — Standard Library](09-standard-library.md)*
*Next: [Appendix A — Proof Sketches](appendix-a-proofs.md)*
