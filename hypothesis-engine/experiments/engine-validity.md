# Engine validity — cross-cutting gaps and experiments (EXP-ENG)

Source: `hypothesis-engine/` at commit `0419d4791de3e80afd5b028e27475977dce89cd4`
(engine run 2026-11-23T17:01:48Z). Written 2026-11-24. Status of every experiment: PROPOSED.

Every topic file in this directory depends on this one. The eight hypothesis drafts share one
pipeline, so the gaps below apply to all of them; the topic files cite them as E1–E9 rather than
repeat them.

## What kind of statement each item below is

| Label | Meaning |
|---|---|
| CODE | Read from `scripts/hypothesis_engine.py` at the commit above. A structural statement about what the code does; no data involved. |
| LIVE-CHECK | Observed by querying an external service on 2026-11-24. One observation; the service can change. |
| AUDIT | Computed from `data/*` at the commit above by `sketches/engine_audit.py`. Descriptive counts of the engine's own output. They are not findings about any research topic, and the relevance screen they use is itself lexical. |
| UNCHECKED | Not verified here. |

## Structural gaps (E1–E9)

**E1. A "claim" is the first sentence of an abstract, not a result.** (CODE) `stage_claim` builds
`"On topic {topic}, {title} reports: {first_sentence(abstract)}"`. In most abstracts the first sentence is
motivation ("Large language models (LLMs) have transformed numerous AI applications."), so the staked
text usually has no result, no effect size, and no direction. The falsification condition attached to it
is one of two fixed templates (`derive_falsification`).

**E2. arXiv retrieval is an OR over single words, sorted by date.** (CODE + LIVE-CHECK) `query_arxiv` sends
`search_query=all:<multi-word query>` with `sortBy=submittedDate`. On 2026-11-24 the arXiv API echoed the
query `all:activation aware weight quantization LLM` back as
`all:activation OR all:aware OR all:weight OR all:quantization OR all:LLM`. The first result was
"A Fractional Chern Semimetal: Exact Wavefunction and Conformal Criticality". So arXiv returns the most
recently submitted papers that contain any one query word. arXiv supplies most findings in six of the
eight topics (AUDIT: 46–211 arXiv findings per topic). The same query with explicit `AND` returned
quantization papers. Whether a fixed query (AND-joined or quoted phrase) solves the problem is EXP-ENG-03.

**E3. The "test" is token overlap plus cue words.** (CODE) `corroboration(a, b)` returns +1 when
|tokens(a) ∩ tokens(b)| / min(|a|, |b|) ≥ 0.25 and the counts of negation and positive cue words don't
disagree. The stopword list has 21 words. The function doesn't read numbers, effect directions, tasks
or metrics. A +1 means the two texts share vocabulary. It does not mean one replicates the other.

**E4. Survival is a ratchet.** (CODE) Every run, `stage_test` re-tests each still-active claim against
**all** findings logged for its topic, and `passed`/`failed` accumulate across runs. Because
`corroboration` is deterministic, the same pair adds the same verdict on every run. A claim with one
positive partner and no negative partner reaches `passed ≥ 3` ("survived") within three runs, and
"survived" is absorbing (later runs skip it). AUDIT: the share of claims meeting that condition
(≥1 positive, 0 negative same-topic partners) is 112/142, 159/218, 32/79, 8/18, 38/127, 5/35, 95/133 and
108/121 (AAQ, CAL, CCO, DCM, HVD, RGC, SSP, WMC). With a size-matched partner pool drawn from other topics
the counts are 29, 61, 14, 3, 13, 5, 41 and 25. So the lexical test responds to shared vocabulary within
a topic pool. Given E2, that vocabulary can come from a single shared query word. Whether it tracks
topical relevance or support is EXP-ENG-02.

**E5. Reformulation doesn't narrow the scope.** (CODE) `reformulate` appends
`[restricted: narrower scope within <topic> (run <date>)]` to the text, resets counts, and leaves the
content unchanged. The suffix adds topic-name tokens, which can raise later overlap scores.

**E6. "NEW HYPOTHESIS" will fire on every run once a topic is past the threshold.** (CODE) The marker
fires when a topic has ≥3 surviving claims. By E4, surviving claims never leave the tree except through
escape-hatching, which only applies to failing claims. Once a topic crosses 3, every later run reports it
again. This accounts for the 30 open issues (#42 on 2026-11-23 back through earlier runs). EXP-ENG-04
replays this.

**E7. The hidden-variable stage correlates series that aren't aligned.** (CODE) `stage_hidden` uses the
residual |beta_confidence − 0.5| per claim, in dict insertion order. The candidate
`exogenous:findings_rate` is `findings_per_period[i % len(periods)]`: claim *i* is paired with month
*i mod M*, which isn't the claim's month. Pearson r on these pairs has no temporal meaning. There's also
no significance test and no correction for multiple comparisons across topics. The engine already
removed one artefact candidate (`confidence_trend`, r = 1 by algebra; see the comment in the code). The
three surviving `findings_rate` suggestions for deployment-aware metrics (r = −0.577, −0.577, −0.959,
from 2026-08-31 to 2026-09-10) come from the unaligned construction.

**E8. The confidence numbers are Laplace-smoothed counts of lexical matches.** (CODE)
`beta_confidence = (1 + passed) / (2 + passed + failed)`. "(0.83)" next to a supporting claim means 4
passes and 0 fails at overlap ≥ 0.25. It is not a probability that the claim is true or relevant.

**E9. Claims with no abstract can survive on their titles.** (CODE + AUDIT) Findings with no abstract
become `... reports: (no abstract)`, and that text plus the title can still reach overlap ≥ 0.25. The
headline claim for deployment-aware metrics is one of these. Findings with no abstract: 19/82 (CCO),
12/36 (DCM), and ≤10 in each other topic.

## Gaps the engine itself records

- `unknown_journal.jsonl`: 91 entries, all `escape-hatch` (claims reformulated 3×). Several are
  on-topic papers that the lexical test failed (examples in each topic file). So the escape hatch removes
  relevant items as well as noise.
- `hidden_variables.jsonl`: 5 rows. Two are r = 1.0 `confidence_trend` artefacts that the engine already
  identified as non-exogenous. Three are `findings_rate` rows (see E7).
- No topic has ever recorded a refuted claim ("Contradicted/refuted claims: (none)" in all 8 drafts).

---

## EXP-ENG-01 — Human-labelled relevance and support audit

- **Gap:** E1, E2, E3, E8. Whether any surviving claim is about its topic, and whether it states a result.
- **H1:** In at least 5 of 8 topics, fewer than 50% of surviving claims are on-topic.
  **H0:** In at least 6 of 8 topics, at least 50% are on-topic.
- **Variables:** For each sampled surviving claim, two raters each give three labels: (i) on-topic for
  the topic's stated research question (yes/no), (ii) the claim text states a result, not background or
  motivation (yes/no), (iii) for one randomly drawn partner that gave a +1 verdict, the partner supports
  the claim (supports / unrelated / contradicts).
- **Design:** Sample 40 surviving claims per topic, stratified by source (all of them when a topic has
  fewer than 40: RGC 7, DCM 11). That is about 260 claims. Raters see title, abstract and topic. They
  don't see beta_confidence, source, or each other's labels. Write a one-page codebook in advance with
  5 worked examples per label.
- **Pre-registered prediction:** On-topic rate below 50% (upper Wilson 95% bound below 0.5) in at least
  5 topics. The AUDIT screen gives lexical core-term hit rates of 26/135, 21/208, 26/49, 1/11, 8/44,
  3/7, 16/126 and 13/111; those are the basis for the prediction, not evidence for it.
  **Falsified if** at least 6 topics have an on-topic rate ≥ 50%.
- **Analysis:** Per-topic proportions with Wilson intervals. Cohen's κ per label; if κ < 0.6, revise the
  codebook and relabel a fresh sample. Don't adjudicate the old one into agreement. Also report the share
  of claims that state a result.
- **Threats:** Rater leniency about what counts as on-topic; resolve it by fixing the topic definition
  from `config/topics.json` + `research/TODO.md` in advance. Sampling at one commit gives a snapshot,
  because the drafts change twice a week.
- **Tier:** Laptop, plus about 8–12 person-hours.
- **Would establish:** The construct validity of "surviving claim" at this commit. **Would not
  establish:** Whether any topic's research hypothesis is true or false. That isn't the engine's job,
  and this audit doesn't test it.
- **Sketch:** `sketches/engine_audit.py relevance` (the lexical pre-screen only).

## EXP-ENG-02 — Does the corroboration verdict track human-judged support?

- **Gap:** E3, E4.
- **H1:** The AUC of `corroboration()` = +1 for predicting the human label "partner supports claim" is
  ≤ 0.6. **H0:** AUC > 0.6.
- **Design:** Reuse the EXP-ENG-01 labels. For each claim, label 3 partners: one +1 pair, one random
  same-topic pair with verdict 0, and one pair from another topic. Controls: cross-topic pool and a
  word-salad pool of abstract length. AUDIT, descriptive only: per-pair +1 rates are 0.0219 for the same
  topic, 0.0041 cross-topic and 0.0005 for word salad (`engine_audit.py control`, seed 0, 20 pairs per
  claim).
- **Prediction / falsifier:** AUC ≤ 0.6 with the 95% bootstrap CI upper bound < 0.7. Falsified if the
  CI lower bound is > 0.6.
- **Analysis:** AUC with a stratified bootstrap over claims (2,000 resamples).
- **Threats:** EXP-ENG-01 expects few supporting pairs, which makes the AUC noisy; oversample +1 pairs
  and weight them back.
- **Tier:** Laptop.
- **Would establish:** Whether the test stage measures support at all. **Would not establish:** That
  some other lexical rule would work.

## EXP-ENG-03 — Retrieval ablation: query syntax vs on-topic rate

- **Gap:** E2.
- **H1:** AND-joined arXiv queries raise the on-topic rate of arXiv findings to ≥ 70%.
  **H0:** The on-topic rate stays below 50%.
- **Design:** Run the engine unmodified on a scratch copy (`--config /tmp/x.json --data-dir /tmp/d
  --hypotheses-dir /tmp/h`) with three config variants: (a) the current queries, (b) the same words
  joined with ` AND ` (the engine prefixes only the first term with `all:`, so the variant must spell
  `all:` on each term; check the echoed query in the Atom `<title>`), and (c) quoted phrases. Run it on
  a GitHub runner or anywhere with arXiv egress. Use one run per variant on the same day; each variant
  retrieves 5 results per query per source.
- **Prediction / falsifier:** (b) and (c) ≥ 70% on-topic by human label (EXP-ENG-01 codebook) vs (a)
  < 30%. Falsified if (b) and (c) are both < 50%.
- **Threats:** sortBy=submittedDate still favours recency over relevance; add a `sortBy=relevance` arm.
  Same-day runs return overlapping sets, so dedup across arms before labelling.
- **Tier:** Laptop / CI runner (network).
- **Would establish:** Whether E2 is the main source of off-topic content. **Would not establish:**
  That on-topic claims are supported (that's EXP-ENG-02).
- **Note:** Don't modify the engine. If this succeeds, a config or code change is the owner's call, and
  it would reset what "surviving" means for every topic.

## EXP-ENG-04 — Replay: does NEW HYPOTHESIS track new content?

- **Gap:** E4, E6.
- **H1:** Under the current rules, once a topic first crosses 3 survivors, it is flagged on 100% of
  later runs whether or not new on-topic findings arrive. **H0:** The flags depend on new content.
- **Design:** Offline replay. Order `findings_log.jsonl` by `retrieved_at` and feed run-sized batches
  through a copy of stages 3–7 (imported read-only, writing to a temp dir). Arms: (a) current rules;
  (b) each (claim, partner) pair counted at most once across runs; (c) (b) plus survival only if
  supported by ≥ 3 distinct partners from ≥ 2 sources. Outcomes: flags per run, and flags in runs with
  0 new on-topic findings (by the EXP-ENG-01 lexical screen; human labels if available).
- **Prediction / falsifier:** (a) flags every topic on every run after its first crossing, and (b)/(c)
  flag fewer. Falsified if (a) leaves some topic unflagged in a later run (possible only through
  escape-hatching).
- **Threats:** The replay can't reproduce the exact history if the engine code changed between runs;
  check `git log scripts/` and replay per code version.
- **Tier:** Laptop CPU, minutes.
- **Would establish:** Whether the issue stream carries information. **Would not establish:** Which
  alternative rule is right; that is a design decision that needs EXP-ENG-02.
