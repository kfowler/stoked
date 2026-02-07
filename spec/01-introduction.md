# STOKED Language Specification

## Part I: Foundations

### Chapter 1 — Introduction

**Version**: 0.1.0 (Draft)
**Status**: Working Specification

---

## 1.1 Motivation

Modern distributed software systems are production systems in the Operations Research & Industrial Engineering (ORIE) sense: artifacts (code, configurations, models) flow through a network of workstations (development, review, testing, deployment, monitoring), are transformed by servers (human engineers, automated tools, LLM-based agents), experience congestion and variability, and must meet throughput and cycle-time targets.

Yet the tools used to specify, analyze, and orchestrate these systems lack the formal foundation that manufacturing and logistics have enjoyed for decades. Agent orchestration frameworks describe *what* to do but not *how fast* or *how reliably*. Workflow engines capture sequencing but ignore queueing effects. DevOps pipelines are operationally concrete but analytically opaque.

**STOKED** — **S**tochastic **T**yped **O**perations **K**it for **E**ngineering **D**elivery — bridges this gap. It is a formal specification language for compiling high-level descriptions of productive processes into graphs of prompt-based processes for developing, deploying, monitoring, and maintaining distributed software systems.

STOKED is *not* a generic agent orchestration DSL. It is a **production system specification language** grounded in ORIE, where:

- **Workstations** are prompt-based LLM agents, deterministic compute steps, or human task queues.
- **Jobs** are software artifacts: pull requests, test reports, deployment manifests, incident tickets.
- **The graph** is a queueing network with formal performance semantics.

## 1.2 Design Philosophy

STOKED rests on five principles:

1. **Dual semantics by construction.** Every STOKED program has both a *control-flow* interpretation (what can happen) via Coloured Generalized Stochastic Petri Nets, and a *performance* interpretation (how fast it happens) via queueing network extraction. These are not separate models glued together; they arise from a single unified formal model.

2. **Stochastic from day one.** Variability is not an afterthought. Arrival processes, service times, yield rates, and routing probabilities are first-class language constructs with distribution types. The Squared Coefficient of Variation (SCV, c² = Var/Mean²) links the language's stochastic specifications directly to queueing performance via the VUT equation.

3. **Process-algebraic composition.** STOKED inherits the compositional reasoning power of CSP and the pi-calculus. Systems are built from primitive processes using sequential composition, parallel composition (synchronized, interleaved, and alphabetized), choice (external, internal, probabilistic), channel communication (asynchronous and synchronous), restriction, and replication. Every operator has a precise Petri net translation and queueing interpretation.

4. **ORIE-native abstractions.** The language provides first-class constructs for concepts from Factory Physics and queueing theory: stations with service disciplines, finite resources (WIP caps, Kanban), arrival processes, routing policies, batch processing, rework loops, and performance assertions (throughput, cycle time, utilization, WIP bounds, Little's Law, bottleneck identification).

5. **Specification, not implementation.** STOKED is a specification language. This document defines its syntax, type system, and formal semantics. It does not prescribe a runtime, compiler, or execution engine. Conforming implementations may target simulation, analytical solvers, model checkers, or direct execution — provided they respect the semantics defined herein.

## 1.3 Relationship to Existing Formalisms

### 1.3.1 CSP (Communicating Sequential Processes)

STOKED adopts CSP's process-algebraic style: named processes, sequential and parallel composition, external and internal choice, channel-based communication, and algebraic laws for reasoning about equivalence. From CSP, STOKED inherits:

- The alphabet model of synchronization (§5.4.6, Parallel Composition)
- External choice (`[]`) and internal choice (`|~|`) operators
- Traces, failures, and divergences as semantic domains (Appendix B)
- Refinement as the primary notion of correctness

STOKED extends CSP with:
- Probabilistic and stochastic choice (`pchoice`, distribution-valued delays)
- Asymmetric send/receive on typed channels (from pi-calculus)
- Resource semantics (finite shared resources with acquire/release)

### 1.3.2 Pi-Calculus

From the pi-calculus, STOKED adopts:

- **Channel mobility**: channels are first-class values that can be sent over other channels
- **Restriction** (`(nu a) P`): dynamic creation of fresh, private channels
- **Replication** (`!P`): unbounded parallel copies
- **Typed channels**: channels carry values of specified types

STOKED does not adopt the full generality of higher-order pi-calculus (process passing). Channels carry *data*, not processes.

### 1.3.3 Petri Nets

STOKED programs translate to Coloured Generalized Stochastic Petri Nets (CGSPNs), which provide:

- **Structural analysis**: P-invariants for conservation (flow balance), T-invariants for repeatability, siphons and traps for deadlock analysis
- **Reachability analysis**: boundedness, liveness, reversibility
- **Stochastic analysis**: steady-state probabilities, throughput, utilization via the underlying CTMC

The translation (§6) maps channels to places, stations to transition subnets, and composition operators to net composition operations. A behavioral equivalence theorem (Theorem 6.1) establishes that the operational semantics and the Petri net semantics agree.

### 1.3.4 Queueing Theory

STOKED programs yield queueing network models, drawing on:

- **Jackson networks**: open networks of M/M/c stations with product-form solutions
- **BCMP theorem**: generalized product-form networks with multiple job classes, various service disciplines, and state-dependent routing
- **GI/G/c approximations**: the VUT equation (Utilization × Variability × Time) from Factory Physics, connecting the SCV of arrival and service processes to expected waiting times
- **Mean Value Analysis (MVA)**: exact analysis of closed queueing networks
- **Little's Law**: L = λW as a system-wide invariant and verification condition

### 1.3.5 Factory Physics

The ORIE grounding of STOKED draws directly on the laws of Factory Physics (Hopp & Spearman):

- **Little's Law**: WIP = Throughput × Cycle Time
- **The VUT Equation**: CT_q = V × U × T (variability × utilization × natural process time)
- **Bottleneck Rate (r_b)** and **Raw Process Time (T_0)**: determining throughput bounds
- **Critical WIP (W_0 = r_b × T_0)**: the WIP level at which a balanced line achieves maximum throughput with minimum cycle time
- **Practical Worst Case**: CT_pw = T_0 + (W-1)/(r_b) as the cycle time when variability is maximized

## 1.4 Scope and Limitations

### In Scope

- Formal syntax (EBNF grammar) for all language constructs
- Type system with kinds, distribution types, and resource types
- Structural operational semantics (labeled transition system)
- Translation to Coloured Generalized Stochastic Petri Nets
- Queueing network extraction and performance analysis framework
- Well-formedness conditions (type safety, deadlock-freedom, boundedness, stability)
- Standard library of distributions, station patterns, and process combinators
- Worked examples across the software lifecycle domain

### Out of Scope

- Compiler or interpreter implementation
- Runtime system design
- Concrete integration with LLM APIs, CI/CD platforms, or ticketing systems
- User interface or developer tooling
- Formal verification tool implementation (model checker, theorem prover)

## 1.5 Document Organization

This specification is organized in three parts with two appendices:

| Part | Chapters | Content |
|------|----------|---------|
| **I. Foundations** | 1–3 | Motivation (this chapter), notation conventions, abstract syntax |
| **II. Semantics** | 4–7 | Type system, operational semantics, Petri net translation, queueing extraction |
| **III. Verification & Library** | 8–10 | Well-formedness conditions, standard library, worked examples |
| **Appendix A** | — | Proof sketches |
| **Appendix B** | — | Equivalence relations and algebraic laws |

**Dependency graph**: Chapter 3 (abstract syntax) is the keystone — all subsequent chapters reference its grammar. Chapter 4 (type system) is required by Chapters 5–8. Chapters 6 and 7 are mutually independent but both depend on Chapter 5. Chapter 9 depends on Chapters 3–4. Chapter 10 depends on all prior chapters.

## 1.6 Typographic Conventions

See Chapter 2 for the complete notation guide. In brief:

- `monospace` for STOKED syntax and keywords
- *italic* for meta-variables and defined terms on first use
- **bold** for emphasis and defined names
- Mathematical notation (Γ, ⊢, →) for formal judgments
- `[[P]]` for the Petri net translation function
- `Q(P)` for the queueing model extraction function

## 1.7 Versioning

This specification follows semantic versioning. The current version is **0.1.0**, indicating an initial draft subject to revision. Breaking changes to syntax or semantics increment the major version. Extensions that preserve backward compatibility increment the minor version.

---

*Next: [Chapter 2 — Notation](02-notation.md)*
