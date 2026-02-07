# STOKED Language Specification

## Chapter 3 — Abstract Syntax

---

This chapter defines the complete abstract syntax of STOKED using Extended Backus-Naur Form (EBNF). All subsequent chapters reference the grammar defined here. See §2.5 for EBNF conventions.

## 3.1 Lexical Structure

### 3.1.1 Identifiers

```ebnf
Ident       ::= Letter { Letter | Digit | '_' }
Letter      ::= 'a' .. 'z' | 'A' .. 'Z'
Digit       ::= '0' .. '9'
QualIdent   ::= Ident { '.' Ident }
```

### 3.1.2 Keywords

The following identifiers are reserved:

```
type      channel   station   resource  arrival
process   let       in        if        then
else      match     with      fn        rec
true      false     send      recv      delay
prompt    compute   human     acquire   release
assert    import    module    as        where
forall    exists    nu        pchoice   priority
batch     schedule  sla       escalate  yield
rework    scrap     wip       limit     discipline
fifo      lifo      spt       edd       ps
stochastic monitor  spc       and       or
not
Some      None
```

### 3.1.3 Literals

```ebnf
IntLit      ::= [ '-' ] Digit { Digit }
FloatLit    ::= [ '-' ] Digit { Digit } '.' Digit { Digit } [ Exponent ]
Exponent    ::= ( 'e' | 'E' ) [ '+' | '-' ] Digit { Digit }
StringLit   ::= '"' { StringChar } '"'
StringChar  ::= any character except '"' and '\' | EscapeSeq
EscapeSeq   ::= '\' ( 'n' | 't' | 'r' | '\\' | '"' )
TimeLit     ::= FloatLit TimeUnit | IntLit TimeUnit
TimeUnit    ::= 'ms' | 's' | 'm' | 'h' | 'd' | 'w'
RateLit     ::= ( FloatLit | IntLit ) '/' TimeUnit
BoolLit     ::= 'true' | 'false'
```

### 3.1.4 Comments

```ebnf
LineComment  ::= '//' { any character except newline }
BlockComment ::= '/*' { any character } '*/'
```

## 3.2 Program Structure

```ebnf
Program     ::= { ModuleDecl } { Import } { TopDecl }

ModuleDecl  ::= 'module' QualIdent [ 'where' ]

Import      ::= 'import' QualIdent [ 'as' Ident ]
             |  'import' QualIdent '(' ImportList ')'

ImportList  ::= Ident { ',' Ident }

TopDecl     ::= TypeDecl
             |  ChannelDecl
             |  StationDecl
             |  ResourceDecl
             |  ArrivalDecl
             |  ProcessDecl
             |  AssertDecl
             |  LetDecl
```

## 3.3 Type Declarations

```ebnf
TypeDecl    ::= 'type' Ident [ TypeParams ] '=' Type

TypeParams  ::= '<' Ident { ',' Ident } '>'

Type        ::= BaseType
             |  CompositeType
             |  ProcessType
             |  ChannelType
             |  DistType
             |  ResourceType
             |  TypeRef
             |  '(' Type ')'

BaseType    ::= 'Bool'
             |  'Int'
             |  'Float'
             |  'String'
             |  'Unit'
             |  'Duration'
             |  'Rate'

CompositeType
            ::= RecordType
             |  VariantType
             |  ListType
             |  SetType
             |  MapType
             |  TupleType
             |  OptionType

RecordType  ::= '{' FieldDecl { ',' FieldDecl } '}'
FieldDecl   ::= Ident ':' Type

VariantType ::= VariantCase { '|' VariantCase }
VariantCase ::= Ident [ '(' Type { ',' Type } ')' ]

ListType    ::= 'List' '<' Type '>'
SetType     ::= 'Set' '<' Type '>'
MapType     ::= 'Map' '<' Type ',' Type '>'
TupleType   ::= '(' Type ',' Type { ',' Type } ')'
OptionType  ::= 'Option' '<' Type '>'

ProcessType ::= 'proc'

ChannelType ::= 'Chan' '<' Type '>'

DistType    ::= 'Dist' '<' Type '>'

ResourceType
            ::= 'Resource' '<' IntLit '>'    /* capacity */

TypeRef     ::= QualIdent [ '<' Type { ',' Type } '>' ]
```

## 3.4 Channel Declarations

```ebnf
ChannelDecl
            ::= 'channel' Ident ':' Type [ '{' ChannelConfig '}' ]

ChannelConfig
            ::= { ChannelConfigItem }

ChannelConfigItem
            ::= 'capacity' ':' ( IntLit | '∞' )
```

## 3.5 Expressions

```ebnf
Expr        ::= Literal
             |  Ident
             |  QualIdent
             |  Expr BinOp Expr
             |  UnOp Expr
             |  Expr '.' Ident                      /* field access */
             |  Expr '(' [ Expr { ',' Expr } ] ')'  /* application */
             |  'fn' '(' [ Param { ',' Param } ] ')' '->' Expr
             |  'let' Binding { ',' Binding } 'in' Expr
             |  'if' Expr 'then' Expr 'else' Expr
             |  'match' Expr '{' { MatchArm } '}'
             |  RecordExpr
             |  ListExpr
             |  TupleExpr
             |  'Some' '(' Expr ')'                     /* option present */
             |  'None'                                   /* option absent */
             |  '(' Expr ')'

Param       ::= Ident ':' Type

Binding     ::= Pattern '=' Expr
             |  'stochastic' Ident '~' DistExpr     /* stochastic binding */

Pattern     ::= Ident
             |  '_'
             |  Literal
             |  Ident '(' [ Pattern { ',' Pattern } ] ')'
             |  '{' FieldPat { ',' FieldPat } '}'
             |  '(' Pattern ',' Pattern { ',' Pattern } ')'

FieldPat    ::= Ident ':' Pattern
             |  Ident                                /* shorthand: x  means  x: x */

MatchArm    ::= Pattern '=>' Expr ','

RecordExpr  ::= '{' FieldInit { ',' FieldInit } '}'
FieldInit   ::= Ident ':' Expr
             |  Ident                                /* shorthand */

ListExpr    ::= '[' [ Expr { ',' Expr } ] ']'

TupleExpr   ::= '(' Expr ',' Expr { ',' Expr } ')'

BinOp       ::= '+' | '-' | '*' | '/' | '%'         /* arithmetic */
             |  '==' | '!=' | '<' | '<=' | '>' | '>='  /* comparison */
             |  'and' | 'or'                          /* logical */
             |  '++'                                  /* string/list concat */

UnOp        ::= '-' | 'not'
```

## 3.6 Process Expressions

This is the core of STOKED. Process expressions describe the control flow and communication structure of a production system.

```ebnf
ProcessDecl ::= 'process' Ident [ '(' [ Param { ',' Param } ] ')' ] '=' Process

Process     ::= 'stop'                                         /* inaction */
             |  'skip'                                         /* successful termination */
             |  Send
             |  Receive
             |  Process ';' Process                            /* sequential composition */
             |  Process '|' Process                            /* synchronized parallel */
             |  Process '|||' Process                          /* interleaved parallel */
             |  Process '|[' SyncSet ']|' Process              /* alphabetized parallel */
             |  Process '[]' Process                           /* external choice */
             |  Process '|~|' Process                          /* internal choice */
             |  PChoice                                        /* probabilistic choice */
             |  Restriction                                    /* new channel */
             |  '!' Process                                    /* replication */
             |  'delay' '(' DistExpr ')'                       /* timed delay */
             |  StationInvoke                                  /* station application */
             |  'let' Binding { ',' Binding } 'in' Process
             |  'if' Expr 'then' Process 'else' Process
             |  'match' Expr '{' { ProcessMatchArm } '}'
             |  AcquireRelease
             |  MonitorExpr
             |  RecProcess                                     /* recursive process */
             |  Ident [ '(' [ Expr { ',' Expr } ] ')' ]       /* process invocation */
             |  '(' Process ')'

RecProcess  ::= 'rec' Ident '(' [ RecParam { ',' RecParam } ] ')' '.' Process
RecParam    ::= Ident ':' Type [ '=' Expr ]                    /* optional default */

Send        ::= Ident '!' Expr                                /* async send */
             |  Ident '!!' Expr                               /* sync send (rendezvous) */

Receive     ::= Ident '?' Pattern                             /* async receive */
             |  Ident '??' Pattern                            /* sync receive */
```

**Note.** A standalone receive `a ? x` (without a continuation process) is syntactic sugar for `a ? x ; skip`. The typing rule [T-Recv] and operational semantics [R-AsyncRecv] both require a continuation; the parser inserts `skip` implicitly.

```ebnf

SyncSet     ::= '{' Ident { ',' Ident } '}'

PChoice     ::= 'pchoice' '{' PChoiceBranch { ',' PChoiceBranch } '}'
PChoiceBranch
            ::= Expr '->' Process                             /* weight -> process */

Restriction ::= '(' 'nu' Ident ':' ChannelType ')' Process

ProcessMatchArm
            ::= Pattern '=>' Process ','

AcquireRelease
            ::= 'acquire' '(' Ident [ ',' IntLit ] ')' ';' Process ';' 'release' '(' Ident [ ',' IntLit ] ')'

MonitorExpr ::= 'monitor' '(' Ident ')' '{' { SPCRule } '}'

SPCRule     ::= 'when' SPCCondition '=>' Process
SPCCondition
            ::= Ident '>' Expr                                /* upper control limit */
             |  Ident '<' Expr                                /* lower control limit */
             |  'trend' '(' Ident ',' IntLit ')'              /* trend of n points */
             |  'run' '(' Ident ',' IntLit ')'                /* run of n points */
             |  'shift' '(' Ident ',' Expr ')'                /* mean shift */
```

## 3.7 Station Declarations

Stations are the workstations of the production system — the servers in queueing-theoretic terms.

```ebnf
StationDecl ::= 'station' Ident StationParams ':' StationSig
                  StationBody

StationParams
            ::= '(' [ StationParam { ',' StationParam } ] ')'
             |  /* empty */

StationParam
            ::= Ident ':' Type

StationSig  ::= ChannelRef '->' ChannelRef
             |  '(' ChannelRef { ',' ChannelRef } ')' '->' '(' ChannelRef { ',' ChannelRef } ')'

ChannelRef  ::= Ident ':' ChannelType
             |  Ident

StationBody ::= '{' StationConfig ServiceProcess '}'

StationConfig
            ::= { ConfigItem }

ConfigItem  ::= 'servers' ':' Expr
             |  'discipline' ':' Discipline
             |  'capacity' ':' Expr                  /* buffer capacity K */
             |  'batch' ':' BatchSpec
             |  'schedule' ':' ScheduleSpec
             |  'wip' 'limit' ':' Expr
             |  'yield' ':' DistExpr                 /* P(good output) */
             |  'rework' ':' ReworkSpec
             |  'priority' ':' Expr
             |  'service_time' ':' DistExpr              /* station-level service time */
```

**Note on dual `service_time` declarations.** When `service_time` appears in both the station configuration and the service process block, the station-level `service_time` governs queueing analysis (§7) while the service process `service_time` governs operational behavior (§5). These should agree; well-formedness could enforce this.

```ebnf
Discipline  ::= 'fifo' | 'lifo' | 'priority' | 'spt' | 'edd' | 'ps'
             |  'is' '(' ( IntLit | '∞' ) ')'       /* infinite-server (delay) */

BatchSpec   ::= '{' 'min' ':' Expr ',' 'max' ':' Expr
                    [ ',' 'timeout' ':' Expr ] '}'

ScheduleSpec
            ::= '{' { ScheduleWindow } '}'
ScheduleWindow
            ::= Expr '..' Expr                       /* time range */

ReworkSpec  ::= '{' 'probability' ':' DistExpr ','
                    'target' ':' Ident '}'           /* rework destination */

ServiceProcess
            ::= PromptService
             |  ComputeService
             |  HumanService

PromptService
            ::= 'prompt' '{' PromptConfig '}'

PromptConfig
            ::= { PromptItem }

PromptItem  ::= 'model' ':' Expr
             |  'temperature' ':' Expr
             |  'system' ':' Expr
             |  'tools' ':' ListExpr
             |  'output' ':' Type
             |  'service_time' ':' DistExpr
             |  'on_input' ':' '(' Pattern ')' '->' Expr

ComputeService
            ::= 'compute' '{' ComputeConfig '}'

ComputeConfig
            ::= { ComputeItem }

ComputeItem ::= 'fn' ':' Expr
             |  'service_time' ':' DistExpr
             |  'deterministic' ':' BoolLit

HumanService
            ::= 'human' '{' HumanConfig '}'

HumanConfig ::= { HumanItem }

HumanItem   ::= 'role' ':' Expr
             |  'sla' ':' Expr
             |  'escalate' ':' EscalateSpec
             |  'service_time' ':' DistExpr
             |  'schedule' ':' ScheduleSpec

EscalateSpec
            ::= '{' 'after' ':' Expr ',' 'to' ':' Ident '}'

StationInvoke
            ::= Ident '(' [ Expr { ',' Expr } ] ')'
```

## 3.8 Distribution Expressions

Distributions are first-class in STOKED. They appear in five positions: arrival rates, service times, yield/quality, routing probabilities, and stochastic let-bindings.

```ebnf
DistExpr    ::= DistPrimitive
             |  DistCombinator
             |  Ident                                /* named distribution */
             |  '(' DistExpr ')'

DistPrimitive
            ::= 'Deterministic' '(' Expr ')'
             |  'Exponential' '(' Expr ')'           /* rate parameter */
             |  'LogNormal' '(' Expr ',' Expr ')'    /* mean, stddev */
             |  'Normal' '(' Expr ',' Expr ')'       /* mean, stddev */
             |  'Uniform' '(' Expr ',' Expr ')'      /* low, high */
             |  'Triangular' '(' Expr ',' Expr ',' Expr ')'  /* low, mode, high */
             |  'Gamma' '(' Expr ',' Expr ')'        /* shape, rate */
             |  'Weibull' '(' Expr ',' Expr ')'      /* shape, scale */
             |  'Erlang' '(' IntLit ',' Expr ')'     /* phases, rate */
             |  'Beta' '(' Expr ',' Expr ')'         /* alpha, beta */
             |  'Pareto' '(' Expr ',' Expr ')'       /* shape, scale */
             |  'Bernoulli' '(' Expr ')'             /* probability */
             |  'Binomial' '(' IntLit ',' Expr ')'   /* trials, probability */
             |  'Poisson' '(' Expr ')'               /* rate */
             |  'Geometric' '(' Expr ')'             /* probability */
             |  'Empirical' '(' ListExpr ')'         /* data points */

DistCombinator
            ::= 'mix' '(' MixComponent { ',' MixComponent } ')'
             |  'truncate' '(' DistExpr ',' Expr ',' Expr ')'  /* dist, low, high */
             |  'shift' '(' DistExpr ',' Expr ')'              /* dist, offset */
             |  'scale' '(' DistExpr ',' Expr ')'              /* dist, factor */
             |  'max_of' '(' DistExpr ',' DistExpr ')'
             |  'min_of' '(' DistExpr ',' DistExpr ')'
             |  'convolve' '(' DistExpr ',' DistExpr ')'       /* sum of independent */

MixComponent
            ::= Expr ':' DistExpr                    /* weight : distribution */
```

## 3.9 Resource Declarations

```ebnf
ResourceDecl
            ::= 'resource' Ident ':' 'Resource' '<' IntLit '>'
                  [ ResourceConfig ]

ResourceConfig
            ::= '{' { ResourceItem } '}'

ResourceItem
            ::= 'priority' ':' Expr
             |  'timeout' ':' Expr
             |  'preemptible' ':' BoolLit
```

## 3.10 Arrival Declarations

```ebnf
ArrivalDecl ::= 'arrival' Ident ':' ArrivalSpec

ArrivalSpec ::= '{' ArrivalConfig '}'

ArrivalConfig
            ::= { ArrivalItem }

ArrivalItem ::= 'channel' ':' Ident
             |  'distribution' ':' DistExpr
             |  'job' ':' Expr                        /* job constructor */
             |  'batch' ':' BatchSpec
             |  'schedule' ':' ScheduleSpec
             |  'class' ':' Ident                     /* job class for BCMP */
```

## 3.11 Performance Assertions

```ebnf
AssertDecl  ::= 'assert' AssertExpr

AssertExpr  ::= PerfMetric CompOp Expr
             |  'littles_law' '(' Ident ')'
             |  'deadlock_free' '(' Ident ')'
             |  'steady_state' '(' Ident ')'
             |  'conservative' '(' Ident ')'
             |  'bounded' '(' Ident ',' Expr ')'
             |  'bottleneck' '(' Ident ')' '==' Ident
             |  'live' '(' Ident ')'

PerfMetric  ::= 'throughput' '(' Ident ')'
             |  'cycle_time' '(' Ident ')' [ '.' Percentile ]
             |  'wip' '(' Ident ')'
             |  'utilization' '(' Ident ')'
             |  'wait_time' '(' Ident ')' [ '.' Percentile ]
             |  'queue_length' '(' Ident ')' [ '.' Percentile ]
             |  'yield_rate' '(' Ident ')'
             |  'scrap_rate' '(' Ident ')'

Percentile  ::= 'mean' | 'p50' | 'p90' | 'p95' | 'p99' | 'max'

CompOp      ::= '<' | '<=' | '>' | '>=' | '==' | '!='
```

## 3.12 Let Declarations (Top-Level)

```ebnf
LetDecl     ::= 'let' Ident [ ':' Type ] '=' Expr
```

## 3.13 Operator Precedence and Associativity

Operators are listed from lowest to highest precedence:

| Precedence | Operator | Associativity | Description |
|-----------|----------|---------------|-------------|
| 1 | `;` | Right | Sequential composition |
| 2 | `\|~\|` | Left | Internal choice |
| 3 | `[]` | Left | External choice |
| 4 | `\|` | Left | Synchronized parallel |
| 5 | `\|\|\|` | Left | Interleaved parallel |
| 6 | `\|[ S ]\|` | Left | Alphabetized parallel |
| 7 | `or` | Left | Logical or |
| 8 | `and` | Left | Logical and |
| 9 | `==`, `!=`, `<`, `<=`, `>`, `>=` | None | Comparison |
| 10 | `+`, `-`, `++` | Left | Additive, concatenation |
| 11 | `*`, `/`, `%` | Left | Multiplicative |
| 12 | `-` (unary), `not` | Right | Unary prefix |
| 13 | `.` | Left | Field access |
| 14 | `(...)` | — | Application |

Sequential composition (`;`) binds most loosely among process operators, so `a!v ; P [] Q` parses as `(a!v ; P) [] Q`. The parallel operators bind tighter than choice operators, so `P [] Q | R` parses as `P [] (Q | R)`.

## 3.14 Syntactic Sugar

The following are defined as syntactic sugar over core constructs:

| Sugar | Desugars to |
|-------|------------|
| `P \|> Q` (pipe) | `(nu c : Chan<T>) (P ; c ! result ; skip) \| (c ? x ; Q)` |
| `retry(n, P)` | `rec X(k: Int = n). if k <= 0 then stop else (P [] X(k-1))` |
| `timeout(d, P, Q)` | `(nu done : Chan<Unit>) ((P ; done ! ()) \|[{done}]\| (delay(Deterministic(d)) ; done ! ())) [] Q` |
| `P >>= f` | See note below |
| `par(Ps)` | Fold of `\|\|\|` over process list Ps |
| `seq(Ps)` | Fold of `;` over process list Ps |

**Note on `>>=`.** The monadic bind `P >>= f` is syntactic sugar for piping a process result through a function. Since STOKED processes communicate via channels rather than return values, `P >>= f` requires P to produce its result on a designated channel. Specifically, `P >>= f` desugars to `(nu c : Chan<T>) (P[c/out] | (c ? x ; f(x)))`, where `out` is the conventional output channel of P. This sugar is primarily useful with station invocations, where the output channel is well-defined.

## 3.15 Well-Formedness Constraints on Syntax

The following constraints are enforced syntactically or by the parser (as opposed to the type system in §4):

1. **Unique top-level names**: No two `TopDecl`s in the same module may bind the same identifier.
2. **Balanced acquire/release**: Every `acquire(r)` must have a corresponding `release(r)` in the same process scope.
3. **Non-empty choice**: `pchoice` must have at least two branches; weights must be positive.
4. **Valid distributions**: Distribution parameters must satisfy domain constraints (e.g., rate > 0 for Exponential).
5. **Station signature arity**: The number of input/output channels in a `StationSig` must match the service process.
6. **Recursive process well-foundedness**: In `rec X(params). P`, the variable X must appear guarded in P (behind a channel operation, delay, or station invocation).

## 3.16 Grammar Summary

The complete grammar comprises the following major syntactic categories:

| Category | Key Non-terminals | Section |
|---------|-------------------|---------|
| Program structure | Program, TopDecl, Import | §3.2 |
| Types | Type, BaseType, CompositeType | §3.3 |
| Channels | ChannelDecl, ChannelConfig | §3.4 |
| Expressions | Expr, Pattern, Binding | §3.5 |
| Processes | Process, Send, Receive, PChoice | §3.6 |
| Stations | StationDecl, ServiceProcess | §3.7 |
| Distributions | DistExpr, DistPrimitive | §3.8 |
| Resources | ResourceDecl | §3.9 |
| Arrivals | ArrivalDecl | §3.10 |
| Assertions | AssertDecl, PerfMetric | §3.11 |

This grammar defines exactly five primitive declaration forms corresponding to the five ORIE concepts:

| Declaration | ORIE Concept | Petri Net (§6) | Queueing (§7) |
|-------------|-------------|----------------|----------------|
| `type` | Job/work item type | Token color set | Job class |
| `channel` | Queue/buffer | Place | Queue |
| `station` | Workstation/server | Transition subnet | Service center |
| `resource` | Shared finite resource | Resource place | — |
| `arrival` | Arrival process | Source transition | External arrival |

---

*Previous: [Chapter 2 — Notation](02-notation.md)*
*Next: [Chapter 4 — Type System](04-type-system.md)*
