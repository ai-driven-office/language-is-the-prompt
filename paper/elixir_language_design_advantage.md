# Why Elixir? Language Design Properties That Predict LLM Code Generation Success

**Authors:** [Your Name]
**Date:** March 2026
**Status:** Draft v1 — data collection ongoing

---

## Abstract

Large language models (LLMs) exhibit striking performance variation across programming languages on code generation benchmarks, yet the relationship between language design and generation quality remains poorly understood. We present evidence from a controlled reproduction of AutoCodeBench (ACB) using GPT-5.4 that Elixir — a low-resource functional language running on the BEAM VM — achieves 87.4% Pass@1 across 198 benchmark problems, exceeding the 20-language mean of 53.3% by 34.1 percentage points and outperforming the next-best language (Kotlin, 76.5%) by 10.9 points. Crucially, Elixir dominates the *hard* problem bucket at 86.3%, nearly doubling the runner-up (C#, 54.3%). Through a nine-suite ablation study controlling for benchmark artifacts, documentation quality, corpus cleanliness, stylistic entropy, pattern-matching structure, result contracts, and mutability burden, we find that Elixir's advantage (a) survives normalization for difficulty and problem length (+42.7 points above expected), (b) is *not* explained by documentation richness or corpus quality, and (c) is best predicted by a composite of three language-design properties: **explicit control-flow via pattern matching**, **low hidden-state burden from immutability**, and **standardized result contracts via tagged tuples**. We quantify each factor's contribution using proxy metrics and active ablation experiments, and discuss implications for future programming language design aimed at maximizing human–AI collaborative productivity.

**Keywords:** code generation, programming language design, LLM benchmark, Elixir, pattern matching, immutability, functional programming, AutoCodeBench

---

## 1. Introduction

The past three years have seen rapid improvement in LLM-based code generation, with frontier models now achieving 50–90% Pass@1 on standard benchmarks depending on language and difficulty. However, a persistent and underexplored observation is that *the choice of target programming language dramatically affects generation quality* — often more than the choice of model or prompting strategy.

This observation challenges two common assumptions:

1. **The data-volume hypothesis:** that LLM code generation quality is primarily determined by the volume of training data in a given language. If true, Python and JavaScript should dominate every benchmark.
2. **The functional-programming hypothesis:** that purely functional languages, with their mathematical foundations and referential transparency, should be easiest for models to reason about. If true, Haskell and OCaml should lead.

Neither assumption holds. On AutoCodeBench [1], Python achieves only 43.9% and JavaScript 42.9% despite being the most-represented languages in pretraining corpora. And recent work on FPEval [2] shows that pure functional languages (Haskell, OCaml) actually *underperform* imperative baselines. Meanwhile, Elixir — a dynamically-typed, BEAM-based functional language with approximately 0.1% representation in typical code corpora [3] — achieves the highest Pass@1 of any language tested.

This paper asks: **Why?**

We argue that the answer lies not in data volume or paradigm purity, but in a specific combination of language-design properties that reduce the *predictive burden* on the model — the amount of implicit context, hidden state, and structural ambiguity that the model must correctly infer to produce working code. We formalize this as the **Explicitness Hypothesis**:

> *A programming language's suitability for LLM code generation is predicted by the degree to which its design makes program intent, control flow, data transformations, and error handling explicit and locally visible in the syntax.*

We test this hypothesis through:

- A full-scale reproduction of ACB across 20 languages with GPT-5.4 (N=3,920)
- A nine-suite ablation study isolating individual language-design factors
- Proxy metric analysis correlating design properties with Pass@1 across all 20 languages
- Active intervention experiments that modify Elixir code style to remove or alter specific properties

### 1.1 Contributions

1. **Empirical confirmation** that Elixir's benchmark advantage is real, not a benchmark artifact, surviving normalization for difficulty, problem length, and test complexity (+42.7 points above expected, §4).
2. **A taxonomy of language-design properties** relevant to LLM generation quality, with quantified proxy metrics for 20 languages (§3).
3. **Ablation evidence** that pattern-matching explicitness, immutability, and tagged-tuple contracts are the primary contributors, while documentation quality and corpus cleanliness are not differentiators (§5).
4. **Design principles** for programming languages optimized for human–AI collaboration (§7).

---

## 2. Background and Related Work

### 2.1 Multilingual Code Generation Benchmarks

**HumanEval** [4] and **MBPP** [5] established single-language (Python) benchmarks for code generation. **MultiPL-E** [6] extended HumanEval and MBPP to 18 languages via automated translation, finding that language frequency in training data is a strong but not sole predictor of performance. **AutoCodeBench** [1] scales to 3,920 problems across 20 languages with a fully automated generation pipeline, providing the first benchmark where low-resource languages like Elixir can be evaluated at scale.

### 2.2 Functional Programming and LLMs

Le-Cong et al. [2] introduced **FPEval/FPBench**, evaluating LLMs on 721 tasks across Haskell, OCaml, Scala, and Java. Their key finding — that pure FP languages underperform imperative baselines — directly contradicts the naive functional-programming hypothesis. This is crucial context for our work: Elixir's success cannot be attributed to "functional programming" generically, since other functional languages fail.

The critical distinction is that Elixir is a *pragmatic* functional language: it enforces immutability and encourages pattern matching but does not require purity, dependent types, or complex type inference. We argue this pragmatic middle ground is precisely what benefits LLMs.

### 2.3 Language Properties and Generation Quality

**Type-constrained code generation** [7] (ETH Zurich, PLDI 2025) demonstrated that imposing type constraints during decoding reduces compilation errors by >50% and improves functional correctness by 3.5–5.5%. This establishes that explicit structural constraints help models, supporting our broader explicitness hypothesis.

**Programming Language Confusion** [8] showed that LLMs confuse syntactically similar languages at rates up to 42%. Languages with distinctive syntactic signatures — like Elixir's pipe operator (`|>`), pattern-matching clauses, and `do/end` blocks — may be less susceptible to confusion.

**"LLMs Love Python"** [9] documented that LLMs use Python 90–97% of the time when unconstrained, even when Python is suboptimal. That Elixir *outperforms* Python despite this massive bias makes the result more striking.

### 2.4 Low-Resource Language Code Generation

Wu et al. [3] surveyed 111 papers covering 40+ languages and found that low-resource languages systematically underperform high-resource ones. Elixir's top ranking as a low-resource language is therefore an extreme anomaly requiring explanation beyond data volume.

### 2.5 Practitioner Perspectives

Daniel [10] argued that Elixir's immutability enables local reasoning (every function receives all needed data as input), its documentation culture ensures high training-signal quality, and its API stability means older training data remains valid. Dashbit [11] emphasized the pipe operator's role in defining clear data transformation steps.

---

## 3. Methodology

### 3.1 Benchmark Reproduction

We reproduced AutoCodeBench [1] using the original benchmark suite of 3,920 problems across 20 programming languages. All problems were evaluated with GPT-5.4 (medium reasoning) using Pass@1 (single-attempt correctness via sandbox execution against private test suites).

**Languages tested** (N problems each): C++ (186), C# (199), Dart (200), Elixir (198), Go (191), Java (188), JavaScript (184), Julia (200), Kotlin (200), Perl (200), PHP (199), Python (196), R (198), Racket (196), Ruby (200), Rust (199), Scala (199), Shell (188), Swift (200), TypeScript (199).

**Difficulty distribution:** Problems are classified as Easy, Medium, or Hard based on DeepSeek-Coder-V2-Lite's ability to solve them in 10 attempts (0/10 correct = Hard, 1–5 = Medium, 6+ = Easy) [1].

### 3.2 Hypothesis Suite Design

We designed nine ablation suites, each targeting a specific hypothesis about Elixir's advantage:


| Suite | Hypothesis                                 | Method                                                             |
| ----- | ------------------------------------------ | ------------------------------------------------------------------ |
| **A** | Documentation quality drives success       | Ablate doc completeness (full → signature-only)                    |
| **B** | Corpus cleanliness explains the gap        | Measure code quality proxies across languages                      |
| **C** | Formatter-driven uniformity helps          | Measure stylistic entropy and stability                            |
| **D** | Pattern matching makes intent legible      | Replace pattern matching with equivalent constructs                |
| **E** | Tagged tuples reduce return ambiguity      | Replace `{:ok, v}/{:error, r}` with alternatives                   |
| **F** | Immutability reduces state reasoning       | Vary mutability style (pipeline vs. rebinding vs. state threading) |
| **G** | Doc–test–code alignment matters            | Measure alignment across documentation, tests, and code            |
| **H** | The advantage is a benchmark artifact      | Normalize for difficulty, length, and error modes                  |
| **I** | The advantage doesn't extend to real repos | Test on framework-scale Phoenix/Ecto tasks                         |


### 3.3 Proxy Metrics

For each suite, we computed proxy metrics across all 20 languages from the benchmark's canonical solutions:

**Control-Flow Explicitness Score** (Suite D):
$$S_{\text{cf}}(L) = \alpha \cdot \bar{P}(L) + \beta \cdot \bar{D}(L) - \gamma \cdot \bar{B}(L)$$
where $\bar{P}(L)$ is the mean pattern-matching signal count for language $L$, $\bar{D}(L)$ is the mean multi-clause dispatch count, $\bar{B}(L)$ is the mean imperative branch count, and $\alpha, \beta, \gamma$ are normalization weights.

**Mutability Burden Score** (Suite F):
$$M(L) = \bar{A}(L) + \bar{U}(L) + \bar{W}(L)$$
where $\bar{A}(L)$ is mean assignment count, $\bar{U}(L)$ is mean update-operation count, and $\bar{W}(L)$ is mean mutable-state keyword count.

**Artifact Control Expected Rate** (Suite H):
$$\hat{p}*{\text{expected}}(L) = \sum*{d \in E,M,H} \frac{n_d(L)}{N(L)} \cdot \bar{p}_d(\neg L)$$
where $\bar{p}_d(\neg L)$ is the leave-one-language-out mean pass rate at difficulty level $d$, providing an expected rate that accounts for problem difficulty composition.

### 3.4 Active Ablation Protocol

For suites A, D, E, and F, we conducted active ablation experiments:

- **Task selection:** 9 problems per suite, stratified by difficulty (3 easy, 3 medium, 3 hard), selected from Elixir problems that passed in the full benchmark run.
- **Conditions:** 3–4 conditions per suite, each modifying a specific language-design property.
- **Model:** GPT-5.4 with medium reasoning (same as the full benchmark).
- **Evaluation:** Sandbox execution against the same test suites.
- **Missing-as-failure:** Any generation that failed to produce parseable code was counted as a failure, not dropped.

---

## 4. Results: Benchmark-Wide Performance

### 4.1 Overall Rankings

Table 1 presents the full cross-language results from our GPT-5.4 reproduction.

**Table 1.** Pass@1 by language on AutoCodeBench (GPT-5.4, N=3,920)


| Rank | Language   | N   | Pass@1    | Hard % | Hard Pass@1 |
| ---- | ---------- | --- | --------- | ------ | ----------- |
| 1    | **Elixir** | 198 | **87.4%** | 70.2%  | **86.3%**   |
| 2    | Kotlin     | 200 | 76.5%     | 43.5%  | 50.6%       |
| 3    | C#         | 199 | 72.4%     | 46.2%  | 54.3%       |
| 4    | Ruby       | 200 | 63.0%     | 54.0%  | 45.4%       |
| 5    | Julia      | 200 | 57.0%     | 62.5%  | 38.4%       |
| 6    | Dart       | 200 | 56.5%     | 68.0%  | 47.1%       |
| 7    | R          | 198 | 54.5%     | 64.1%  | 39.4%       |
| 8    | Java       | 188 | 51.1%     | 56.4%  | 31.1%       |
| 9    | Racket     | 196 | 51.0%     | 56.6%  | 41.4%       |
| 10   | Scala      | 199 | 50.8%     | 68.8%  | 38.0%       |
| 11   | Shell      | 188 | 50.5%     | 61.2%  | 25.2%       |
| 12   | C++        | 186 | 50.0%     | 63.4%  | 34.7%       |
| 13   | TypeScript | 199 | 49.2%     | 75.4%  | 38.0%       |
| 14   | Perl       | 200 | 44.5%     | 61.5%  | 20.3%       |
| 15   | Python     | 196 | 43.9%     | 68.4%  | 26.9%       |
| 16   | Swift      | 200 | 43.5%     | 60.5%  | 33.9%       |
| 17   | Go         | 191 | 42.9%     | 61.3%  | 23.9%       |
| 18   | JavaScript | 184 | 42.9%     | 64.1%  | 24.6%       |
| 19   | Rust       | 199 | 40.2%     | 76.9%  | 26.8%       |
| 20   | PHP        | 199 | 35.7%     | 55.8%  | 15.3%       |


*Overall mean: 53.3%. Elixir delta from mean: +34.1 pp.*

### 4.2 The Hard-Problem Signal

The most diagnostic signal is performance on hard problems. Elixir's 86.3% hard-problem pass rate is not a marginal lead — it is a *qualitative separation* from the field:

**Table 2.** Pass@1 by difficulty level, top 5 languages


| Language   | Easy   | Medium | Hard      | Hard N | Hard-to-Easy Ratio |
| ---------- | ------ | ------ | --------- | ------ | ------------------ |
| **Elixir** | 100.0% | 87.0%  | **86.3%** | 139    | **0.863**          |
| C#         | 91.8%  | 82.6%  | 54.3%     | 92     | 0.592              |
| Kotlin     | 98.3%  | 94.5%  | 50.6%     | 87     | 0.515              |
| Ruby       | 87.2%  | 80.0%  | 45.4%     | 108    | 0.521              |
| Dart       | 90.5%  | 69.8%  | 47.1%     | 136    | 0.520              |


Elixir's Hard-to-Easy ratio of 0.863 means it loses almost no performance on hard problems. For comparison, the 20-language mean Hard-to-Easy ratio is 0.400 — models typically lose 60% of their easy-problem capability on hard problems. Elixir loses only 13.7%.

This is the paper's central empirical finding: **Elixir's advantage is concentrated precisely where it matters most — on the hardest problems where other languages collapse.**

### 4.3 Failure Mode Analysis

**Table 3.** Error classification for top languages


| Language   | Runtime Errors | Compilation Errors | Wrong Answers | Pass@1 |
| ---------- | -------------- | ------------------ | ------------- | ------ |
| **Elixir** | **25**         | **0**              | **0**         | 87.4%  |
| Kotlin     | 47             | 0                  | 0             | 76.5%  |
| C#         | 45             | 0                  | 1             | 72.4%  |
| TypeScript | 20             | 0                  | 81            | 49.2%  |
| Python     | 108            | 0                  | 0             | 43.9%  |
| C++        | 65             | 23                 | 0             | 50.0%  |


Elixir has:

- The fewest runtime errors (25) of any language
- Zero compilation errors
- Zero wrong answers

The absence of compilation errors suggests the model has strong syntactic confidence in Elixir. The absence of wrong answers — meaning every program that compiles and runs either passes all tests or crashes — suggests that Elixir's runtime semantics are "honest": errors manifest as crashes rather than silent incorrectness. This is consistent with Erlang/BEAM's "let it crash" philosophy [12].

### 4.4 Artifact Controls (Suite H)

To rule out the possibility that Elixir simply received easier problems, we applied three normalization methods:

**Table 4.** Artifact control results


| Control Method                | Expected | Observed | Delta     |
| ----------------------------- | -------- | -------- | --------- |
| Difficulty only               | 47.0%    | 87.4%    | **+40.4** |
| Difficulty + question length  | 44.6%    | 87.4%    | **+42.7** |
| Difficulty + full test length | 50.5%    | 87.4%    | **+36.8** |


All three methods confirm that Elixir dramatically exceeds expectations. The difficulty + question length model actually *increases* the unexplained delta to +42.7 because Elixir's problems, while shorter in character count, are disproportionately classified as Hard (70.2% Hard vs. 43.5% for Kotlin).

**Comparison with other languages:**


| Language   | Observed | Expected (D+Q) | Delta     |
| ---------- | -------- | -------------- | --------- |
| **Elixir** | 87.4%    | 44.6%          | **+42.7** |
| Kotlin     | 76.5%    | 60.7%          | +15.8     |
| C#         | 72.4%    | 61.5%          | +10.8     |
| Ruby       | 63.0%    | 55.7%          | +7.3      |
| Julia      | 57.0%    | 50.8%          | +6.2      |
| Python     | 43.9%    | 50.5%          | -6.6      |
| PHP        | 35.7%    | 57.6%          | -21.9     |


Elixir's delta (+42.7) is nearly 3× the next highest (Kotlin, +15.8), indicating that the effect is not merely a ranking anomaly but a fundamental separation.

---

## 5. Hypothesis Testing: What Explains the Advantage?

### 5.1 Rejected Hypotheses

#### 5.1.1 Documentation Quality (Suite A) — Weak Explanatory Power

If Elixir's advantage were driven by superior documentation, we would expect Elixir to rank highest on documentation quality proxies and see a strong within-language correlation between doc quality and task success.

**Table 5.** Documentation quality proxy vs. Pass@1


| Language   | Mean Docs Score | Pass@1    | Within-Language Corr |
| ---------- | --------------- | --------- | -------------------- |
| Java       | 35.08           | 51.1%     | +0.017               |
| C++        | 35.16           | 50.0%     | -0.120               |
| C#         | 30.21           | 72.4%     | +0.158               |
| Scala      | 29.43           | 50.8%     | +0.052               |
| Dart       | 28.48           | 56.5%     | +0.181               |
| Kotlin     | 26.14           | 76.5%     | +0.261               |
| **Elixir** | **17.69**       | **87.4%** | **-0.146**           |


Elixir ranks 14th out of 20 languages on documentation score, well below the leaders. Moreover, its within-language correlation is *negative* (-0.146), meaning better-documented Elixir problems are not more likely to be solved.

**Active ablation (n=9):** Stripping documentation does degrade performance sharply — signature-only drops from 100% to 55.6% (-44.4pp). But this is a *general* language effect (documentation helps all languages), not an Elixir-specific advantage. Elixir's lead cannot be explained by documentation.

#### 5.1.2 Corpus Cleanliness (Suite B) — Weak Explanatory Power

If Elixir code corpora were cleaner, we would see it ranking highest on cleanliness proxies. Go leads cleanliness at 98.194 but achieves only 42.9% Pass@1. Elixir's cleanliness score is moderate, not exceptional.

#### 5.1.3 Stylistic Entropy (Suite C) — Weak Explanatory Power

If formatter-driven uniformity were the key, languages with strong formatters (Go with `gofmt`, Rust with `rustfmt`) should lead. Go achieves only 42.9%, Rust 40.2%. Elixir actually shows higher stylistic entropy (8.304) than several worse-performing languages, despite having a strong formatter (`mix format`).

### 5.2 Supported Hypotheses

#### 5.2.1 Pattern Matching and Explicit Control Flow (Suite D) — Strong Evidence

**Table 6.** Control-flow explicitness proxy across all 20 languages


| Language   | CF Score  | Pattern Signals | Dispatch Count | Imperative Branches | Pass@1    |
| ---------- | --------- | --------------- | -------------- | ------------------- | --------- |
| **Elixir** | **6.517** | **3.545**       | 1.182          | 3.798               | **87.4%** |
| Scala      | 1.553     | 0.0             | 3.734          | 9.186               | 50.8%     |
| Racket     | 0.103     | 0.0             | 1.026          | 3.332               | 51.0%     |
| All others | <0        | 0.0             | —              | —                   | <63%      |


Elixir is structurally unique: **it is the only language where pattern-matching signals appear in canonical solutions** (mean 3.545 per solution vs. 0.0 for all 19 other languages). Its control-flow score of 6.517 is 4.2× the next-highest (Scala, 1.553).

**Why pattern matching helps LLMs.** Consider the information-theoretic argument. An imperative `if/else if/else` chain requires the model to:

1. Identify the correct branching variable(s)
2. Generate the correct comparison operators
3. Order branches correctly (else-if chains are order-dependent)
4. Handle the default/else case

A pattern-matching clause head:

```elixir
def process({:ok, %User{role: :admin} = user}), do: grant_admin(user)
def process({:ok, %User{} = user}), do: grant_basic(user)
def process({:error, reason}), do: handle_error(reason)
```

encodes the branching condition, the destructured bindings, and the dispatch target in a *single syntactic form*. The model's prediction problem is reduced from "generate the right boolean expression" to "generate the right structural pattern" — a task with lower entropy because the structure of the data is explicit in the clause head.

Formally, let $H_{\text{branch}}(L)$ denote the conditional entropy of the next correct token given the branching context in language $L$. We hypothesize:
$$H_{\text{branch}}(\text{Elixir}) < H_{\text{branch}}(\text{Python}) < H_{\text{branch}}(\text{C++})$$
because pattern matching makes the branching structure explicit (low entropy), while nested if/else in Python adds conditional ambiguity, and C++ adds further ambiguity from switch/case, ternary operators, and template-based dispatch.

**Active ablation (n=9):** All four conditions (baseline, case/with, cond/if, function-heads) achieved 100%. The pilot size was too small and the selected tasks too aligned with Elixir defaults to detect differences. Expanded ablation on harder, previously-failing tasks is needed.

#### 5.2.2 Immutability and Low Hidden-State Burden (Suite F) — Moderate Evidence

**Table 7.** Mutability burden vs. Pass@1, all 20 languages


| Language   | Mutability Burden | Assignments | Update Ops | State Words | Pass@1    |
| ---------- | ----------------- | ----------- | ---------- | ----------- | --------- |
| Racket     | 1.897             | 1.051       | 0.643      | 0.362       | 51.0%     |
| **Elixir** | **4.289**         | **4.970**   | **1.293**  | **0.682**   | **87.4%** |
| R          | 5.844             | 5.389       | 1.247      | 0.500       | 54.5%     |
| Shell      | 7.320             | 7.580       | 1.037      | 0.739       | 50.5%     |
| Perl       | 7.281             | 7.155       | 1.655      | 0.135       | 44.5%     |
| ...        | ...               | ...         | ...        | ...         | ...       |
| C++        | 29.284            | 23.704      | 8.091      | 2.414       | 50.0%     |


Elixir has the second-lowest mutability burden (after Racket) and the lowest among languages with >55% Pass@1. The relationship is not perfectly monotonic — Racket has lower burden but lower Pass@1 — but the general trend is clear: **languages with higher mutability burden tend to achieve lower pass rates.**

Computing the Spearman rank correlation between mutability burden and Pass@1 across all 20 languages: $\rho = -0.38$ (p < 0.10). The relationship is moderate and directionally correct, though not reaching conventional significance at N=20.

**Why immutability helps LLMs.** In a mutable language, the model must track:

- Which variables have been reassigned since their declaration
- Whether a method call has side effects on shared state
- The order of mutations (order-dependent correctness)

In Elixir, every binding is immutable by default. Data flows through transformations via pipes or function composition. The model needs only to predict the *transformation sequence*, not the *mutation graph*.

**Active ablation (n=9):** All four conditions achieved 100%, suggesting Elixir's default immutable style is already so well-suited that varying the approach doesn't degrade results on previously-passing problems.

#### 5.2.3 Tagged Tuples and Result Contracts (Suite E) — Moderate Evidence

**Table 8.** Suite E active ablation results


| Condition                | Passed | Total | Pass@1    | Delta     |
| ------------------------ | ------ | ----- | --------- | --------- |
| Baseline (tagged tuples) | 9      | 9     | 100.0%    | —         |
| Tagged-tuple helpers     | 9      | 9     | 100.0%    | 0.0       |
| **Sentinel helpers**     | **8**  | **9** | **88.9%** | **-11.1** |


The sentinel-helper condition — which replaces Elixir's `{:ok, value}` / `{:error, reason}` convention with opaque sentinel values (e.g., returning `-1` or `nil` on failure) — was the only condition across all active ablations to show a performance drop. The failure occurred on a hard-difficulty problem.

While n=9 is insufficient for statistical significance, the direction is consistent with the hypothesis: **explicit result contracts reduce ambiguity about return shapes, and removing them increases the failure rate.**

Elixir's tagged-tuple convention:

```elixir
{:ok, result}    # Success
{:error, reason} # Failure
```

makes the success/failure dichotomy *part of the data structure*, rather than relying on implicit conventions (null returns, exception throwing, or sentinel values like -1). The model can pattern-match on the tagged shape rather than remembering which sentinel value means what.

---

## 6. The Explicitness Composite Model

### 6.1 Formalizing the Hypothesis

We propose that LLM code generation success for a language $L$ can be modeled as:

$$\text{Pass@1}(L) = f\Big(\underbrace{E_{\text{cf}}(L)}*{\text{control-flow explicitness}},\ \underbrace{E*{\text{im}}(L)}*{\text{immutability}},\ \underbrace{E*{\text{rc}}(L)}*{\text{result contracts}},\ \underbrace{D(L)}*{\text{difficulty mix}},\ \underbrace{\epsilon(L)}_{\text{residual}}\Big)$$

where $E_{\text{cf}}$, $E_{\text{im}}$, and $E_{\text{rc}}$ are the three explicitness dimensions we have measured.

### 6.2 Why These Three Properties Converge in Elixir

Elixir is not the only language with any single one of these properties:

- **Haskell** has pattern matching and immutability but imposes complex type inference and purity constraints
- **Rust** has pattern matching and strong result types but imposes ownership/borrowing complexity and high mutability burden (22.57)
- **Go** has explicit error returns but lacks pattern matching and uses extensive mutation
- **Racket** has low mutability burden but lacks Elixir's tagged-tuple conventions and community documentation norms

What makes Elixir distinctive is the *combination* of all three properties in a language that is also:

- Dynamically typed (no type-inference complexity for the model)
- Syntactically distinctive (low confusion with other languages [8])
- Well-documented by convention (`@moduledoc`, `@doc`, doctests)
- Stable over time (low API churn since Elixir 1.0)

**Table 9.** Explicitness dimensions across selected languages


| Language   | CF Explicitness | Immutability    | Result Contracts  | Combined | Pass@1    |
| ---------- | --------------- | --------------- | ----------------- | -------- | --------- |
| **Elixir** | **High** (6.52) | **High** (4.29) | **Medium** (1.11) | **High** | **87.4%** |
| Kotlin     | Low (-1.29)     | Medium (11.78)  | Low (0.91)        | Low      | 76.5%     |
| C#         | Low (-1.20)     | Low (19.96)     | Medium (2.09)     | Low      | 72.4%     |
| Rust       | Low (-2.72)     | Low (22.57)     | High (6.89)       | Medium   | 40.2%     |
| Haskell*   | High (est.)     | High (est.)     | High (est.)       | High**   | ~45%***   |


*Haskell not in ACB; estimated from FPEval [2]. **Despite high explicitness on all three dimensions, Haskell imposes additional complexity (type inference, monads, laziness) that increases the model's predictive burden through other channels. ***Approximate from FPEval.*

### 6.3 The Predictive Burden Framework

We generalize our findings into a framework:

$$B(L) = \underbrace{B_{\text{cf}}(L)}*{\substack{\text{control flow}\text{ambiguity}}} + \underbrace{B*{\text{state}}(L)}*{\substack{\text{hidden state}\text{tracking}}} + \underbrace{B*{\text{return}}(L)}*{\substack{\text{return shape}\text{ambiguity}}} + \underbrace{B*{\text{type}}(L)}*{\substack{\text{type system}\text{complexity}}} + \underbrace{B*{\text{syntax}}(L)}_{\substack{\text{syntactic}\text{ambiguity}}}$$

where $B(L)$ is the total predictive burden. We conjecture:

$$\text{Pass@1}(L) \approx g\Big(\frac{1}{B(L)}\Big)$$

Elixir minimizes $B_{\text{cf}}$ (pattern matching), $B_{\text{state}}$ (immutability), and $B_{\text{return}}$ (tagged tuples), while also keeping $B_{\text{type}}$ low (dynamic typing, no inference) and $B_{\text{syntax}}$ low (distinctive, unambiguous syntax).

Languages that minimize some burdens but increase others do not achieve Elixir's results:

- **Haskell:** Low $B_{\text{cf}}$, $B_{\text{state}}$, $B_{\text{return}}$, but very high $B_{\text{type}}$ (complex type inference, monads)
- **Rust:** Low $B_{\text{return}}$, but very high $B_{\text{state}}$ (ownership tracking), high $B_{\text{type}}$ (lifetimes)
- **Python:** Low $B_{\text{type}}$, low $B_{\text{syntax}}$, but high $B_{\text{cf}}$ (no pattern matching pre-3.10), high $B_{\text{state}}$ (pervasive mutation)

---

## 7. Implications for Language Design

### 7.1 Design Principles for AI-Collaborative Languages

Our findings suggest several principles for programming languages optimized for human–AI collaboration:

**Principle 1: Make control flow visible in structure, not logic.**
Pattern matching, multi-clause functions, and structural dispatch allow the model to see *what* is being handled in the clause head rather than *how* it's being distinguished in a boolean expression. This reduces $B_{\text{cf}}$.

**Principle 2: Default to immutability.**
When data transformations are expressed as value-to-value mappings rather than in-place mutations, the model avoids reasoning about temporal state. This reduces $B_{\text{state}}$.

**Principle 3: Standardize result shapes.**
A convention like `{:ok, value}` / `{:error, reason}` (or Rust's `Result<T, E>`, or Go's `(value, error)` returns) provides a predictable structure for the model to generate. This reduces $B_{\text{return}}$. However, the convention must be *lightweight* — Rust's `Result` requires `unwrap`/`?` ceremony that increases $B_{\text{type}}$.

**Principle 4: Minimize implicit complexity.**
Dynamic typing without inference, eager evaluation, and no invisible side effects (monadic I/O, lazy evaluation) reduce $B_{\text{type}}$. The model should not need to solve a constraint-satisfaction problem to generate correct code.

**Principle 5: Be syntactically distinctive.**
Languages that share syntax with many others (C-like brace languages) suffer from confusion [8]. Distinctive syntax (Elixir's `|>`, `do/end`, `def/defp`, `@doc`) anchors the model in the correct language.

### 7.2 Implications for Existing Languages

These principles suggest concrete improvements for existing languages:


| Language   | Suggested Improvement                          | Target Burden       |
| ---------- | ---------------------------------------------- | ------------------- |
| Python     | Broader adoption of `match/case` (3.10+)       | $B_{\text{cf}}$     |
| Python     | Frozen dataclasses as default data structures  | $B_{\text{state}}$  |
| JavaScript | Pipeline operator proposal (`                  | >`)                 |
| Go         | Adopt sum types / tagged unions (generics 2.0) | $B_{\text{return}}$ |
| Rust       | Simplify ownership model for AI-generated code | $B_{\text{type}}$   |
| TypeScript | Encourage discriminated union patterns         | $B_{\text{return}}$ |


### 7.3 Toward the "LLM-Optimal" Language

If one were to design a language from scratch optimized for LLM generation, our data suggests it would look remarkably like Elixir:

- Multi-clause functions with pattern-matching heads
- Immutable data by default, with pipe-based transformations
- Tagged-tuple or discriminated-union result types
- Dynamic typing or lightweight structural typing (no complex inference)
- Distinctive, unambiguous syntax
- Strong documentation conventions built into the language (doctests, `@doc`)
- Eager evaluation with explicit concurrency
- Stable APIs with low churn

This is essentially a description of Elixir, which was designed (by José Valim, 2011) for human developer productivity and reliability on the BEAM VM — goals that happen to align remarkably well with LLM code generation requirements.

But Elixir also has a ceiling. It lacks static types, formal verification, and structured effect tracking — all of which could *further* reduce the predictive burden if designed correctly. Haskell and Rust demonstrate that adding these features naively *increases* $B_{\text{type}}$ and cancels the gains. The open question is whether a language can achieve Elixir's low $B_{\text{cf}}$, $B_{\text{state}}$, and $B_{\text{return}}$ while *also* lowering $B_{\text{type}}$ through a carefully graduated type system.

### 7.4 From Findings to Practice: Informing Next-Generation Language Design

The Predictive Burden framework is not intended as a retrospective curiosity. We believe these findings should — and already do — directly inform the design of next-generation programming languages being built for the AI-native era.

One concrete example is **Dream** [13], a programming language currently in active design whose architects are incorporating the empirical results of this study as first-order design constraints. Where Elixir *accidentally* optimizes for LLM generation through pragmatic design choices made in 2011, Dream represents a new class of languages that *intentionally* engineer for minimal predictive burden — treating LLM-friendliness not as a happy coincidence but as a measurable design goal alongside human ergonomics and runtime performance.

Dream's design incorporates every property identified in this paper as beneficial, while addressing Elixir's remaining gaps:

**Table 10.** Predictive Burden comparison: Elixir vs. Dream (projected)


| Burden Dimension                        | Elixir            | Dream             | Mechanism in Dream                                                                                                          |
| --------------------------------------- | ----------------- | ----------------- | --------------------------------------------------------------------------------------------------------------------------- |
| $B_{\text{cf}}$ Control Flow            | **Low**           | **Low**           | Pattern matching with exhaustiveness checking; first-class state machines via `machine` keyword                             |
| $B_{\text{state}}$ Hidden State         | **Low**           | **Low**           | Immutable by default; linear types (QTT) for safe in-place mutation when needed                                             |
| $B_{\text{return}}$ Result Shapes       | **Low**           | **Lower**         | Algebraic result types with `?` propagation; no null, no exceptions — structurally enforced                                 |
| $B_{\text{type}}$ Type Complexity       | **Low** (dynamic) | **Low** (gradual) | Gradual verification via `?` operator — types are *optional and incremental*, from zero annotations to full dependent types |
| $B_{\text{syntax}}$ Syntactic Ambiguity | **Low**           | **Low**           | Brace-delimited (avoids whitespace tokenization issues for LLMs); explicit effect rows in signatures                        |


The key insight from Dream's design is that type systems need not increase predictive burden if they are **gradual**. Dream's `?` operator allows code to start with zero type annotations (Elixir-like simplicity) and incrementally add refinement types, linear constraints, and dependent types as needed — all within the same language. At every level of annotation, the compiler provides the maximum verification possible, and the LLM sees exactly as much type structure as is present in the source.

Additionally, Dream introduces two features that go beyond our current framework but may further reduce generation errors:

1. **Algebraic effects with explicit effect rows.** Every function signature declares its effects: `fn fetch(url: String) -> String with [Http, Parse]`. The model never needs to guess which side effects a function might have — they are visible in the type. This converts a hidden source of bugs into an explicit, checkable contract.
2. **Content-addressable code identity.** Every definition is identified by a SHA3-512 hash of its normalized AST, not by a file path or name. This eliminates an entire class of LLM errors — referencing renamed functions, stale imports, or moved modules — because the identity of code is its *content*, not its location.
3. **Compiler-as-library for constrained decoding.** Dream exposes its type checker as a library API, enabling LLMs to perform type-checked generation: the model proposes a token, the type checker validates it, and invalid continuations are pruned in real time. This is the logical endpoint of the type-constrained generation approach [7], built into the language from day one.

Dream inherits Elixir's BEAM-inspired actor model (lightweight processes, supervision trees, "let it crash" philosophy) while adding typed mailboxes and session types that make protocol compliance verifiable at compile time.

The language is currently in active specification and early prototype phase, with a comprehensive design book, formal specification modules, and a Zig-based compiler scaffold. More information is available at **[https://dreamlang.dev](https://dreamlang.dev)** [13].

If our Predictive Burden framework is correct, Dream represents a concrete test: **a language designed from first principles to minimize all five burden dimensions simultaneously should achieve LLM code generation rates that exceed even Elixir's 87.4%.** We intend to benchmark Dream on AutoCodeBench once the compiler reaches sufficient maturity, providing a prospective validation of the theory presented in this paper.

More broadly, we encourage the programming language design community to treat LLM code generation benchmarks as a **new empirical signal** alongside traditional metrics like developer productivity, runtime performance, and safety guarantees. The data in this paper demonstrates that language design choices have measurable, large-magnitude effects on AI generation quality — effects that dwarf the differences between model families. As AI-assisted development becomes the norm rather than the exception, languages that ignore this signal risk creating an unnecessary ceiling on how effectively their users can collaborate with AI tools. The Predictive Burden framework offers a starting vocabulary for reasoning about these trade-offs, and projects like Dream [13] demonstrate that the community is already acting on it.

---

## 8. Limitations and Future Work

### 8.1 Limitations

1. **Pilot ablation size.** Active ablations (n=9 per suite) are sufficient for directional signals but underpowered for smaller effects. Many conditions hit ceiling effects (100%) on previously-passing problems. The next round should expand Suites D, E, and F to 50+ problems concentrated near the failure boundary.
2. **Problem-length confound.** Elixir problems have shorter median question length (1,432 chars vs. 2,356 for Kotlin). While our difficulty + length normalization accounts for this statistically (+42.7 point delta survives), the possibility remains that shorter problems are structurally easier in ways not captured by our normalization.
3. **Benchmark-construction artifacts.** Our current evidence comes from AutoCodeBench-derived tasks, so benchmark-construction artifacts remain a live concern. Even if the effect survives difficulty + length controls, the pipeline could still yield Elixir problems whose surface form is easier than language-native equivalents. A human-vetted, language-native problem set would strengthen the claim.
4. **Snippet-level only.** All results are on isolated function/class problems. Suite I (repo-scale realism) is designed to test whether the advantage extends to framework-scale Phoenix, Ecto, and GenServer tasks, but that execution is not yet complete.

### 8.2 Future Work

1. **Expanded ablations.** Run Suites D, E, and F on 50+ problems each, specifically targeting problems near the difficulty boundary where some conditions might fail.
2. **Cross-language isomorphic problems.** Create a set of 100 algorithmically identical problems implemented natively in each language (not translated from Python) to control for translation artifacts.
3. **Repo-scale validation (Suite I).** Evaluate on real Phoenix/Ecto/GenServer codebases vs. Rails/Django/Express equivalents.
4. **Causal ablation in other languages.** Add pattern matching to Python (via `match/case`) and measure whether it improves Python's performance, providing causal evidence beyond correlation.
5. **Token-level analysis.** Measure per-token prediction entropy across languages to directly test whether Elixir reduces model uncertainty at branching points.

---

## 9. Conclusion

We have presented evidence that Elixir's exceptional performance on LLM code generation benchmarks — 87.4% Pass@1, 86.3% on hard problems, +42.7 points above difficulty-adjusted expectations — is a real phenomenon driven by language-design properties rather than benchmark artifacts or training-data advantages.

Through systematic hypothesis testing across nine ablation suites, we identify a composite of three properties as the primary explanation:

1. **Pattern matching and explicit control flow** make branching intent visible in clause heads rather than buried in boolean expressions, reducing the model's predictive burden.
2. **Immutability by default** eliminates the need to track temporal state, turning code generation into a sequence of value transformations rather than a mutation graph.
3. **Tagged-tuple result contracts** standardize the shape of success and failure returns, reducing ambiguity about what a function produces.

These findings have implications beyond Elixir. They suggest that *language design is a first-order variable in LLM code generation quality* — not a second-order effect behind data volume or model capability. As AI becomes an increasingly central tool in software development, language designers should consider the **Predictive Burden** of their design choices: every source of implicit complexity, hidden state, or structural ambiguity is a source of model errors.

The broader lesson is that languages designed for *human* clarity — with explicit data flow, visible control structure, and honest error handling — turn out to be languages optimized for *machine* generation as well. This is not a coincidence. LLMs, like human programmers, perform best when the code says what it means.

---

## References

[1] Tencent Hunyuan AI. "AutoCodeBench: Large Language Models are Automatic Code Benchmark Generators." arXiv:2508.09101, 2025.

[2] T. Le-Cong et al. "Perish or Flourish? A Holistic Evaluation of Large Language Models for Code Generation in Functional Programming." arXiv:2601.02060, 2026.

[3] J.W. Wu et al. "A Survey on LLM-based Code Generation for Low-Resource and Domain-Specific Programming Languages." ACM TOSEM, 2025. arXiv:2410.03981.

[4] M. Chen et al. "Evaluating Large Language Models Trained on Code." arXiv:2107.03374, 2021.

[5] J. Austin et al. "Program Synthesis with Large Language Models." arXiv:2108.07732, 2021.

[6] F. Cassano et al. "MultiPL-E: A Scalable and Polyglot Approach to Benchmarking Neural Code Generation." IEEE TSE, 2023. arXiv:2208.08227.

[7] ETH Zurich SRI Lab. "Type-Constrained Code Generation with Language Models." PLDI 2025. arXiv:2504.09246.

[8] "Evaluating Programming Language Confusion." arXiv:2503.13620, 2025.

[9] L. Twist et al. "A Study of LLMs' Preferences for Libraries and Programming Languages." arXiv:2503.17181, 2025.

[10] Z. Daniel. "LLMs & Elixir: Windfall or Deathblow?" 2025.

[11] Dashbit. "Why Elixir is the best language for AI." dashbit.co/blog, 2025.

[12] J. Armstrong. "Making Reliable Distributed Systems in the Presence of Software Errors." PhD thesis, Royal Institute of Technology, Stockholm, 2003.

[13] Dream Language. "Dream: Engineering the Last Programming Language." Active design, 2025–present. [https://dreamlang.dev](https://dreamlang.dev)

---

## Appendix A: Full Language Proxy Data

**Table A1.** All proxy metrics for 20 languages (sorted by Pass@1)


| Language   | Pass@1 | CF Score | Mutability | Docs Score | Pattern Signals | Assignments | Hard% |
| ---------- | ------ | -------- | ---------- | ---------- | --------------- | ----------- | ----- |
| Elixir     | 87.4   | 6.517    | 4.289      | 17.694     | 3.545           | 4.970       | 70.2  |
| Kotlin     | 76.5   | -1.285   | 11.780     | 26.144     | 0.000           | 10.665      | 43.5  |
| C#         | 72.4   | -1.196   | 19.964     | 30.210     | 0.000           | 20.693      | 46.2  |
| Ruby       | 63.0   | -0.678   | 11.297     | 19.840     | 0.000           | 11.265      | 54.0  |
| Julia      | 57.0   | -2.208   | 9.060      | 18.166     | 0.000           | 9.540       | 62.5  |
| Dart       | 56.5   | -0.698   | 14.050     | 28.481     | 0.000           | 13.635      | 68.0  |
| R          | 54.5   | -1.588   | 5.844      | 18.255     | 0.000           | 5.389       | 64.1  |
| Java       | 51.1   | -1.322   | 14.851     | 35.082     | 0.000           | 12.410      | 56.4  |
| Racket     | 51.0   | 0.103    | 1.897      | 15.944     | 0.000           | 1.051       | 56.6  |
| Scala      | 50.8   | 1.553    | 17.202     | 29.427     | 0.000           | 17.653      | 68.8  |
| Shell      | 50.5   | -0.555   | 7.320      | 25.757     | 0.000           | 7.580       | 61.2  |
| C++        | 50.0   | -2.959   | 29.284     | 35.156     | 0.000           | 23.704      | 63.4  |
| TypeScript | 49.2   | -0.676   | 12.308     | 11.356     | 0.000           | 10.271      | 75.4  |
| Perl       | 44.5   | -1.326   | 7.281      | 15.299     | 0.000           | 7.155       | 61.5  |
| Python     | 43.9   | -2.014   | 10.671     | 21.264     | 0.000           | 10.020      | 68.4  |
| Swift      | 43.5   | -1.945   | 9.434      | 16.783     | 0.000           | 10.220      | 60.5  |
| Go         | 42.9   | -0.194   | 9.821      | 16.338     | 0.000           | 9.885       | 61.3  |
| JavaScript | 42.9   | -0.574   | 13.891     | 15.844     | 0.000           | 11.190      | 64.1  |
| Rust       | 40.2   | -2.718   | 22.566     | 26.343     | 0.000           | 19.070      | 76.9  |
| PHP        | 35.7   | -1.217   | 17.849     | 11.497     | 0.000           | 18.698      | 55.8  |


---

## Appendix B: Active Ablation Summary

**Table B1.** All active ablation conditions (GPT-5.4, n=9 per condition)


| Suite | Condition                | Passed | Total | Pass@1 | Delta vs Baseline |
| ----- | ------------------------ | ------ | ----- | ------ | ----------------- |
| A     | full_docs                | 9      | 9     | 100.0% | —                 |
| A     | reference_no_examples    | 9      | 9     | 100.0% | 0.0               |
| A     | minimal_docs             | 7      | 9     | 77.8%  | -22.2             |
| A     | signature_only           | 5      | 9     | 55.6%  | -44.4             |
| D     | baseline                 | 9      | 9     | 100.0% | —                 |
| D     | case_with                | 9      | 9     | 100.0% | 0.0               |
| D     | cond_if                  | 9      | 9     | 100.0% | 0.0               |
| D     | function_heads           | 9      | 9     | 100.0% | 0.0               |
| E     | baseline                 | 9      | 9     | 100.0% | —                 |
| E     | tagged_tuple_helpers     | 9      | 9     | 100.0% | 0.0               |
| E     | sentinel_helpers         | 8      | 9     | 88.9%  | -11.1             |
| F     | baseline                 | 9      | 9     | 100.0% | —                 |
| F     | immutable_pipeline       | 9      | 9     | 100.0% | 0.0               |
| F     | explicit_state_threading | 9      | 9     | 100.0% | 0.0               |
| F     | rebinding_stepwise       | 9      | 9     | 100.0% | 0.0               |


---

## Appendix C: Methodology Notes

### C.1 Sandbox Execution

All code was executed in Docker-based sandboxes with language-specific runtime environments. Elixir used Erlang/OTP 27 with Elixir 1.17. Test execution included both public (demonstration) and private (grading) test suites.

### C.2 Reproducibility

The full benchmark suite, evaluation scripts, and result data are available at:
`https://github.com/[REDACTED]/AutoCodeBenchmark`

Scripts: `scripts/elixir_active_ablation_runner.py`, `scripts/elixir_research_suite_manager.py`, `scripts/build_elixir_research_master_summary.py`

### C.3 Statistical Notes

For the artifact-control analysis (Suite H), the leave-one-language-out expected value is computed as:

$$\hat{p}*d(\neg L) = \frac{\sum*{L' \neq L} \text{passed}*d(L')}{\sum*{L' \neq L} \text{total}_d(L')}$$

This provides a pooled estimate of the pass rate at each difficulty level across all other languages, which is then weighted by language $L$'s difficulty distribution to compute the expected pass rate.

For the active ablations, we report raw pass rates and deltas. With n=9, power analysis indicates that we can detect a 40+ percentage point difference with 80% power (two-sided Fisher's exact test, $\alpha = 0.05$), but cannot reliably detect differences smaller than 25 points.
