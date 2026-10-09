# Measured synthetic results

One admitted evaluation completed all324 first-pass rankings and324 exact repeats. All12 integrity checks passed. No winner threshold was applied and no trial was omitted. These tables derive only from the retained successful receipt; no ranking was rerun. Full-precision values are in [results.json](results.json).

## Equal-seed summaries

Each cell is mean ± sample standard deviation across the three seed means (denominator2). Each seed/stratum mean covers12 queries. Standard deviation describes sensitivity to these constructed seeds, not a confidence interval or real-corpus uncertainty. Values below are rounded to6 decimals for display only.

| Ranker | Stratum | Recall@5 | MRR@10 | nDCG@10 |
|---|---|---:|---:|---:|
| overlap | exact | 0.462963 ± 0.042431 | 0.833333 ± 0.072169 | 0.737788 ± 0.041539 |
| overlap | noisy | 0.305556 ± 0.048113 | 0.535913 ± 0.166551 | 0.503274 ± 0.094417 |
| overlap | mismatch | 0.111111 ± 0.000000 | 0.209292 ± 0.003666 | 0.140466 ± 0.013382 |
| tfidf | exact | 1.000000 ± 0.000000 | 1.000000 ± 0.000000 | 0.976606 ± 0.002843 |
| tfidf | noisy | 0.425926 ± 0.080188 | 0.521759 ± 0.154762 | 0.590307 ± 0.098687 |
| tfidf | mismatch | 0.111111 ± 0.000000 | 0.209292 ± 0.003666 | 0.140466 ± 0.013382 |
| bm25 | exact | 1.000000 ± 0.000000 | 1.000000 ± 0.000000 | 0.950346 ± 0.001312 |
| bm25 | noisy | 0.351852 ± 0.016038 | 0.508796 ± 0.171236 | 0.541364 ± 0.098251 |
| bm25 | mismatch | 0.111111 ± 0.000000 | 0.209292 ± 0.003666 | 0.140466 ± 0.013382 |

## All81 seed-level quality values

| Seed | Ranker | Stratum | Recall@5 | MRR@10 | nDCG@10 |
|---:|---|---|---:|---:|---:|
| 7 | overlap | exact | 0.5 | 0.79166666666666663 | 0.722344268386788 |
| 7 | overlap | noisy | 0.25 | 0.35079365079365082 | 0.39803138912919556 |
| 7 | overlap | mismatch | 0.1111111111111111 | 0.20717592592592593 | 0.13273961051712135 |
| 7 | tfidf | exact | 1 | 1 | 0.97824729915490127 |
| 7 | tfidf | noisy | 0.33333333333333331 | 0.3430555555555555 | 0.4763531575577849 |
| 7 | tfidf | mismatch | 0.1111111111111111 | 0.20717592592592593 | 0.13273961051712135 |
| 7 | bm25 | exact | 1 | 1 | 0.94958874018775008 |
| 7 | bm25 | noisy | 0.33333333333333331 | 0.31111111111111112 | 0.42793308350935888 |
| 7 | bm25 | mismatch | 0.1111111111111111 | 0.20717592592592593 | 0.13273961051712135 |
| 23 | overlap | exact | 0.47222222222222215 | 0.91666666666666663 | 0.78483708594399226 |
| 23 | overlap | noisy | 0.33333333333333331 | 0.67361111111111116 | 0.58054247940306081 |
| 23 | overlap | mismatch | 0.1111111111111111 | 0.20717592592592593 | 0.13273961051712135 |
| 23 | tfidf | exact | 1 | 1 | 0.97332352975153846 |
| 23 | tfidf | noisy | 0.47222222222222215 | 0.61111111111111105 | 0.64722827088491419 |
| 23 | tfidf | mismatch | 0.1111111111111111 | 0.20717592592592593 | 0.13273961051712135 |
| 23 | bm25 | exact | 1 | 1 | 0.94958874018775008 |
| 23 | bm25 | noisy | 0.3611111111111111 | 0.61111111111111105 | 0.59991145828573467 |
| 23 | bm25 | mismatch | 0.1111111111111111 | 0.20717592592592593 | 0.13273961051712135 |
| 101 | overlap | exact | 0.41666666666666669 | 0.79166666666666663 | 0.70618402097445088 |
| 101 | overlap | noisy | 0.33333333333333331 | 0.58333333333333337 | 0.53124952224233368 |
| 101 | overlap | mismatch | 0.1111111111111111 | 0.21352513227513226 | 0.15591779531942571 |
| 101 | tfidf | exact | 1 | 1 | 0.97824729915490127 |
| 101 | tfidf | noisy | 0.47222222222222215 | 0.61111111111111105 | 0.64733821694485727 |
| 101 | tfidf | mismatch | 0.1111111111111111 | 0.21352513227513226 | 0.15591779531942571 |
| 101 | bm25 | exact | 1 | 1 | 0.95186033723203545 |
| 101 | bm25 | noisy | 0.3611111111111111 | 0.60416666666666663 | 0.5962486372796606 |
| 101 | bm25 | mismatch | 0.1111111111111111 | 0.21352513227513226 | 0.15591779531942571 |

## All9 accounting metrics

These counts describe the primary datasets; deterministic regeneration copies used for equality checking do not add trials.

| Metric | Observed |
|---|---:|
| seed_count | 3 |
| documents_per_seed | 48 |
| total_documents | 144 |
| queries_per_seed | 36 |
| total_queries | 108 |
| ranker_count | 3 |
| first_pass_rankings | 324 |
| repeat_rankings | 324 |
| total_rankings | 648 |

## What the results mean

TF-IDF and this BM25 variant retrieve all three positives within five for exact queries in every seed. Noisy query contamination reduces Recall@5 to equal-seed means0.425926 and0.351852 respectively; overlap gives0.305556. TF-IDF has higher noisy nDCG here, while overlap has higher noisy MRR than either weighted ranker. These are descriptive observations of this fixed construction, not a general ranking recommendation.

All mismatch tokens are absent from the corpus. All scores are therefore zero and every ranker returns the same stable document-ID order. Its Recall@5=0.111111, MRR@10=0.209292 and nDCG@10=0.140466 are incidental tie credit, not semantic matching. The same topic/facet qrels apply across each exact/noisy/mismatch query triplet.

The48 documents per seed,12 fictional topics, simple word-frequency patterns and shared latent facets are intentionally small and transparent. They do not represent real user queries, languages, corpora, relevance annotation or production retrieval systems. Three seed choices do not establish statistical generalization. Repeated rankings establish deterministic equality in this admitted run, not correctness by themselves; hand-calculated tests and independent static review supply separate evidence.

## Resource observations

| Field | Observed | Scope |
|---|---:|---|
| Charged CPU seconds | 60.0 | Full conservative reservation; no refund |
| Measured CPU seconds before closeout | 1.5162799999999999 | Worker and supervisor before final receipt/database work; lower bound |
| Runner wall seconds | 1.5412735410500318 | Runner execution interval, not publication or project lifetime |
| Conservative peak bytes | 64897024 | Sum of process high-water marks, not simultaneous RSS |
| Worker peak bytes | 31457280 | Worker high-water mark |
| Supervisor peak bytes | 33439744 | Supervisor high-water mark |

The admitted envelope was60 aggregate CPU seconds,256MiB operational memory and a120-second whole-operation wall target, with one compute thread plus a supervisor. The actual inner runner allowance was59.75 CPU seconds plus a0.25-second closeout margin, and115 wall seconds plus a5-second closeout allowance. The120-second target is not a hard whole-operation wall bound. Memory and CPU controls are operational bounds for trusted code, not hostile-process-tree hard containment. Exporting, ordinary tests, installation and publication are separate resource scopes. The30-test ordinary suite and three-document demo are not included in the evaluation observations.

## Exact source and reproduction

Evaluated `lexical_retrieval_bench/core.py` SHA256:

`62968d4553ff9d05c08dc1f3fa390dd605af971b77a5000ffb5f76f4ea97bd8d`

The same source implements the library and the pure `evaluate()` entry point. [PLAN.md](PLAN.md) freezes every vocabulary/length/noise rule, latent qrel, seed, ID permutation, stratum and formula. A compatible admitted stdlib host runner takes this single source, permits only its `math` import, calls `evaluate()` exactly once under the declared caps, and captures the returned `checks` and `metrics` as bounded JSON. This repository does not include the private admission/custody infrastructure; ordinary demo and test commands are not full-evaluation commands. Independent reproduction needs its own compatible resource supervision.

Keep the supplied source unchanged. The evaluator generates each primary seed dataset, verifies deterministic regeneration, then performs324 rankings followed by exactly324 repeated rankings within that one call. Inspect all12 checks and90 keys; never discard weak strata or rerun to obtain a preferred result. A fresh independently supervised reproduction would be a new experiment, not the retained receipt behind these published results.

Use the reviewed exporter with the expected retained source/receipt digests to reproduce `results.json` byte-for-byte. It reads no corpus, runs no ranker and refuses existing output paths. Derived means and deviations use only retained per-seed means. Private receipt bytes and coordination/process identities are intentionally excluded from the public repository.

## Verification history

Independent review identified and resolved a direct-API aggregate-text bound and missing meaningful test cases before gates passed. An initial ordinary test wrapper returned signal14 after its19 tests reported success; that attempt remains failed in private evidence. The wrapper disarmed its timer before shutdown for subsequent successful28- and30-test runs. The historical signal cause was not separately replayed. The genuine benchmark ran once, passed all12 checks, and was independently verified before export.
