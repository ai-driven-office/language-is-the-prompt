# GPT-5.4 MiniGit Ranking and Comparison to `paper/main.tex`

This note does two things:

1. lists the current language ranking from the Codex/GPT-5.4 MiniGit benchmark
2. compares that ranking to the claims in [`paper/main.tex`](../../../paper/main.tex)

## 1. Current Ranking

Ranking below is sorted by **total wall-clock time** for the single-run MiniGit benchmark.

All 16 language configurations passed both phases, so this ranking is primarily about **speed and token/cost efficiency**, not about differential correctness.

| Rank | Language | Total time | Estimated cost | v2 LOC | Result |
|------|----------|-----------:|---------------:|-------:|--------|
| 1 | Ruby | 87.9s | $0.24 | 267 | 2/2 phases passed |
| 2 | Python/mypy | 93.4s | $0.26 | 240 | 2/2 phases passed |
| 3 | Python | 94.9s | $0.26 | 244 | 2/2 phases passed |
| 4 | Lua | 97.4s | $0.26 | 350 | 2/2 phases passed |
| 5 | JavaScript | 99.0s | $0.27 | 273 | 2/2 phases passed |
| 6 | OCaml | 112.0s | $0.29 | 271 | 2/2 phases passed |
| 7 | Perl | 121.6s | $0.29 | 314 | 2/2 phases passed |
| 8 | Scheme | 134.8s | $0.31 | 308 | 2/2 phases passed |
| 9 | Elixir | 139.0s | $0.32 | 299 | 2/2 phases passed |
| 10 | TypeScript | 140.8s | $0.28 | 276 | 2/2 phases passed |
| 11 | Rust | 152.3s | $0.37 | 328 | 2/2 phases passed |
| 12 | C | 165.6s | $0.37 | 725 | 2/2 phases passed |
| 13 | Java | 184.2s | $0.40 | 386 | 2/2 phases passed |
| 14 | Ruby/Steep | 200.2s | $0.43 | 384 | 2/2 phases passed |
| 15 | Haskell | 216.7s | $0.57 | 265 | 2/2 phases passed |
| 16 | Go | 253.6s | $0.55 | 527 | 2/2 phases passed |

## 2. What The Paper Claims

The paper argues that Elixir's main advantage in AutoCodeBench is not simply "functional programming" or "small syntax," but **model legibility**:

- explicit contracts
- locally visible intent
- documentation architecture
- low predictive burden

The strongest paper claims are about **Pass@1 on a large benchmark with many naturally occurring tasks**, not about raw generation speed on one small CLI exercise.

Important paper points:

- The abstract and introduction argue that Elixir strongly outperforms Python on AutoCodeBench because its ecosystem makes intent and contracts locally visible.
- The paper also explicitly says the result is **not** that Elixir is always universally superior.
- Most importantly for this comparison, the paper later states that on the **exact-task multilingual panel**, *Elixir no longer dominates when all languages are given identical task specifications*.

That last point is the key connection to this MiniGit benchmark.

## 3. Why Elixir Is Not #1 Here

### Short answer

Your intuition is mostly right: the task is probably **too small, too controlled, and too easy** for Elixir's benchmark advantage from the paper to fully show up.

But the more precise version is:

> this benchmark mostly collapses into a **time/cost race among languages that all already pass**, whereas the paper is about **correctness separation under richer, noisier, less-uniform tasks**

### The main reasons

#### 1. The benchmark saturates correctness

In this MiniGit run, every language went 2/2 on phase-level pass/fail.

That means pass rate stops being a useful discriminator. Once all languages solve the task, the ranking becomes mostly:

- how quickly the model settles on a working solution
- how many tokens it spends getting there
- how much boilerplate/config/setup the language encourages

That is a very different objective from AutoCodeBench Pass@1.

#### 2. The task framing is uniform across languages

The paper's strongest Elixir result comes from native benchmark tasks where language ecosystems interact with naturally occurring code, docs, and task framing.

MiniGit is the opposite:

- one spec
- one test harness
- one small problem family
- same structure for every language

That matters because `paper/main.tex` itself says that once task framing is equalized across Elixir, Python, and TypeScript, Elixir no longer uniquely dominates. This MiniGit benchmark is much closer to that controlled-panel regime than to AutoCodeBench's native-task regime.

#### 3. MiniGit rewards low-friction scripting and filesystem work

This task is mostly:

- file IO
- CLI argument parsing
- simple data structures
- deterministic string formatting
- a little state management

That naturally favors languages where the model can produce a compact single-file or near-single-file script with minimal setup. Ruby and Python are especially strong here. JavaScript and Lua also benefit from low ceremony.

Elixir is still good here, but this task does not especially reward:

- rich embedded documentation pipelines
- docs/contracts/examples living close to real library APIs
- runtime documentation retrieval
- OTP/BEAM architectural strengths

Those are central to the paper's explanation.

#### 4. Time is the headline metric here

This benchmark ranks by elapsed time and estimated cost. The paper's headline metric is Pass@1.

Those are related but not equivalent.

A language can be:

- excellent at getting the model to the correct answer eventually
- but not the absolute fastest for a small scripting task

That seems plausible for Elixir here. Elixir did fine. It just did not win the latency race.

#### 5. The task is probably below the ambiguity threshold where Elixir's explicitness helps most

The paper's "Explicitness Hypothesis" is strongest when the model must recover:

- intent
- contracts
- control flow
- data transformations
- failure modes

from imperfect or partial local context.

MiniGit is relatively explicit already:

- the spec is direct
- the test suite is concrete
- the required behavior is narrow
- there is limited architectural ambiguity

So the benchmark may not create enough predictive burden for Elixir's structural advantages to separate it from the pack.

### A useful way to phrase it

Elixir not being number 1 here does **not** really falsify the paper.

Instead, it suggests a narrower conclusion:

> Elixir's advantage is strongest when the evaluation stresses correctness under ambiguity, heterogeneous task framing, and documentation-mediated understanding. It is weaker when the evaluation is a small, uniform, fully specified coding exercise where nearly every language reaches full correctness and the real competition becomes token/latency efficiency.

## 4. What This MiniGit Result Seems To Support In The Paper

This new benchmark actually supports several paper claims:

1. **Elixir is not "universally best" in every benchmark shape.**
   The paper already says this.

2. **Benchmark design matters.**
   MiniGit is much more controlled than AutoCodeBench, and the ranking changes a lot.

3. **The measured metric matters.**
   Pass@1 and wall-clock speed are not interchangeable.

4. **Uniform tasks compress language differences.**
   Once every language gets to 100% phase pass rate, the ranking mostly measures efficiency, not semantic robustness.

## 5. My Best Current Conclusion

If I had to summarize the comparison in one paragraph:

> AutoCodeBench is measuring something closer to "how often does the model get heterogeneous real-world tasks right from benchmark-native framing?" MiniGit is measuring something closer to "how quickly can the model produce a small, fully specified CLI utility in each language?" Those are different questions. Elixir may be especially strong on the first because of explicitness and documentation architecture, while Ruby/Python may be better on the second because small scripting tasks reward low ceremony and fast convergence more than documentation-mediated semantic recovery.

## 6. If You Want A Better Follow-Up For The Paper's Hypothesis

To test the paper's explanation more directly inside this repo, the next benchmark should move closer to the paper's causal story:

- use a larger multi-module task instead of one small CLI
- include ambiguous requirements or richer surrounding docs
- include extension tasks where the model must infer contracts rather than just satisfy explicit shell tests
- score both **correctness** and **time**, not time alone
- run multiple trials, because one run mostly shows ordering under one sample path

That would better test whether Elixir's advantage appears when predictive burden actually matters.
