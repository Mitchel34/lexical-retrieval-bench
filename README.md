# Lexical Retrieval Bench

A dependency-free, offline Python library comparing unique-token overlap, TF-IDF cosine and a named nonnegative BM25 variant. Every score has additive matched-term explanations, every tie uses ascending document ID, and the JSON interface validates bounded input before ranking.

This is an original synthetic benchmark of lexical ranking and metric correctness. It does not measure semantic understanding or real-corpus retrieval quality. No models, APIs, downloads or third-party dependencies are required. Python 3.10 or newer is required.

## Try the tiny demo

From this directory:

```sh
python3 -m lexical_retrieval_bench.demo
python3 -m unittest discover -s tests -v
```

Open [the static demo](demo/index.html) directly in a browser; it has no network assets. Its three hand-written documents and illustrative scores are not benchmark findings. Tests use hand-built examples and explicitly invented receipt fixtures, never the full comparison.

## Strict JSON CLI

```sh
python3 -m lexical_retrieval_bench < request.json
```

Example `request.json`:

```json
{"version":1,"ranker":"overlap","k":2,"documents":[{"id":"a","text":"amber amber"},{"id":"b","text":"blue"}],"queries":[{"id":"q","text":"amber absent"}],"qrels":[{"query_id":"q","grades":[{"document_id":"a","grade":2}]}]}
```

The response includes deterministic rankings, matched terms with contributions and Recall@5, MRR@10 and nDCG@10. Metrics use top10 even when display `k` is smaller. A positive judgment is a grade greater than zero; an omitted document is grade0. Exactly one qrels entry is required for every query, including queries with no positives. No-positive and zero-IDCG metrics are zero.

Input is at most256KiB, with at most64 documents,36 queries and nesting depth8. Document text is at most2048 characters/256 tokens; query text256 characters/32 tokens; combined text at most65536 characters. IDs contain1–32 ASCII letters, digits, underscores or hyphens. `k` is an integer1–10 and grades are integers0–2. Booleans do not count as integers. Unknown fields/references, duplicates, nonfinite values, invalid UTF-8/surrogates and malformed/oversized input are rejected. Error output is a bounded JSON code, exit2; success exits0. See [the complete frozen contract](PLAN.md) for exact fields, limits and errors.

## Python API

```python
from lexical_retrieval_bench.core import rank, metrics, answer, tokenize

rows = rank([{"id": "a", "text": "amber blue"},
             {"id": "b", "text": "amber"}], "blue", "tfidf", k=2)
values = metrics([row["document_id"] for row in rows], {"a": 2}, ["a", "b"])
```

`rank` returns objects with `document_id`, `score` and `matched_terms`. `metrics` accepts a unique, possibly partial list of known document IDs and complete graded truth. `answer` accepts the validated CLI request shape. Invalid direct inputs raise `ValueError`. The package initializer does not import the evaluator; the receipt converter operates independently of scoring code.

## Methods

Tokens are maximal ASCII alphanumeric runs, with ASCII uppercase lowered. Non-ASCII characters separate tokens; there is no stemming, stop-word removal or alias expansion. Query repetitions are deduplicated by every ranker.

- **Overlap:** number of distinct shared tokens.
- **TF-IDF cosine:** document raw term frequency times `1+ln((N+1)/(df+1))`; binary query weights times that same IDF. Out-of-vocabulary query terms are ignored in normalization. Zero norms give zero.
- **BM25:** the nonnegative `ln(N/df)` variant with `k1=1.2`, `b=0.75`, binary query weights and no additive delta. Ubiquitous terms contribute zero.

Scores are sums of the displayed per-term contributions, sorted by token for deterministic floating-point accumulation. Every document, including score-zero documents, participates in the descending-score/ascending-ID ordering. Ranking explanations describe lexical evidence only.

Metric gain is `2**grade-1` and discount is `log2(rank+1)`. Ideal DCG comes from complete qrels, not only retrieved items. The tests contain independently hand-calculated score and graded-metric oracles.

Conceptual references: Stanford's *Introduction to Information Retrieval* sections on [TF-IDF](https://nlp.stanford.edu/IR-book/html/htmledition/tf-idf-weighting-1.html), [cosine](https://nlp.stanford.edu/IR-book/html/htmledition/queries-as-vectors-1.html), [BM25 variants](https://nlp.stanford.edu/IR-book/html/htmledition/okapi-bm25-a-non-binary-model-1.html), and [ranked retrieval evaluation](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html). Code, prose and synthetic vocabulary here are original.

## Frozen evaluation and result provenance

[PLAN.md](PLAN.md) fixes seeds7,23,101;48 documents and36 queries per seed; three paired exact/noisy/mismatch strata; and latent topic/facet qrels independent of scoring. The declared workload has324 first-pass rankings and exactly324 repeated rankings within one admitted evaluation. It reports81 seed/ranker/stratum metric means and9 accounting values. Complete deterministic computation is acceptance; no ranker is required to win.

The admitted run completed once with all12 integrity checks passing. [Measured results and limitations](RESULTS.md) report all81 seed-level values,9 accounting metrics and27 receipt-derived equal-seed mean/sample-deviation pairs. [Machine-readable results](results.json) preserve full numeric values. Exact-query Recall@5 is1.0 for TF-IDF and BM25; noisy-query means fall to0.425926 and0.351852. All mismatch scores are zero, so their0.111111 Recall@5 is incidental stable-ID tie credit. These findings apply only to the fixed fictional construction.

The full evaluator is separate from ordinary tests and requires its admitted resource-controlled execution. Do not treat the tiny demo or invented test receipts as measured findings. A receipt exporter preserves the90 values and derives equal-seed means/sample deviations without ranking documents:

```sh
python3 -m lexical_retrieval_bench.export RECEIPT NEW_OUTPUT SOURCE_SHA256 RECEIPT_SHA256
```

The expected hashes must come from the independently retained, successfully closed-out production operation. Hashes establish byte identity; the converter does not prove process custody or registry admission. It refuses existing output files. Private receipt fields, paths and process identities are never copied into public results.

All mismatch query tokens are absent from the corpus; their zero-score ties can retrieve a relevant ID by chance. Exact/noisy performance is only a property of these declared fictional documents, not evidence about real-user relevance, embedding models or production RAG. Three deterministic seeds are a sensitivity check, not a representative corpus sample or confidence interval.

## Offline package

The original stdlib wheel builder uses existing local Python only. A clean offline installation completed once in a fresh private environment, without an index, dependency download or external network request. All30 original tests passed against the installed package outside the source tree; installed CLI and demo checks also passed. All9 wheel entries and12 installed RECORD entries were independently verified. [Installation evidence and reproduction steps](INSTALLATION.md) record the artifact hash and resource scope. Python3.14.7 was tested; the declared3.10 minimum has not been tested on older interpreters. No package-registry publication is part of this project.
