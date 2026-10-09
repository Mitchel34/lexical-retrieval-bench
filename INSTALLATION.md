# Verified offline installation

Version0.1.0 was built and installed once in a fresh private environment using existing Python3.14.7 and bundled local pip26.2.1. No package index, cache download, dependency download or external network request was used. The original standard-library builder creates a pure-Python wheel. Python3.10 is the declared minimum; older interpreters were not tested.

The installed package was imported and tested from outside the source tree. All30 unchanged original tests passed, with zero failures or skips:16 core tests,6 CLI tests and8 reporting/export tests. The installed three-document demo returned IDs a,b,c with scores1,0,0 and all three relevance metrics1. Empty stdin produced the bounded `invalid_json` error, exit2 and no stderr. These are tiny behavior checks, separate from the scientific evaluation, which was not rerun.

All9 wheel entries and12 installed RECORD entries were independently checked against actual bytes, sizes and hashes. The evaluated source, six package modules, wheel builder, original tests, frozen protocol, static demo and measured results remained unchanged. The private installation supervisor and terminal receipts are excluded from this repository.

## Artifact identity

Wheel: `lexical_retrieval_bench-0.1.0-py3-none-any.whl`

SHA256: `0ecbf43432acbe86c18b2e6f5a031d185da29979474baaea9acac5390401c50b`

Evaluated and installed `core.py` SHA256: `62968d4553ff9d05c08dc1f3fa390dd605af971b77a5000ffb5f76f4ea97bd8d`

The artifact was retained privately for verification; no package registry release or license grant was made. The builder fixes ZIP member order, timestamps and metadata and writes a hashed RECORD. Installed metadata can contain local installation details, so raw installed records are retained privately rather than copied into public documentation.

## Reproduce an offline installation

With an existing compatible Python that includes `venv` and bundled `ensurepip`, choose a new directory outside this source checkout. Replace `SOURCE` below with the source checkout path and `STAGING` with the new outside directory. These commands describe independent reproduction; they were not rerun to prepare these docs.

```sh
mkdir "$STAGING"
cd "$STAGING"
export PIP_CONFIG_FILE=/dev/null
export PIP_NO_INDEX=1
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
python3 -I -B "$SOURCE/build_wheel.py" lexical_retrieval_bench-0.1.0-py3-none-any.whl
python3 -I -B -m venv venv
venv/bin/python -I -B -m pip --isolated --disable-pip-version-check --no-cache-dir install --no-index --no-deps --no-compile lexical_retrieval_bench-0.1.0-py3-none-any.whl
venv/bin/python -I -B -m lexical_retrieval_bench.demo
```

The actual verification additionally hashed every installed package file and each RECORD entry, confirmed installed identity outside source, and ran unchanged test copies against the installed package. Do not add this repository to `PYTHONPATH` when checking an installation: that can silently test source instead of installed bytes. The private suite process prohibited full evaluator/generator calls; those guards were not propagated to the unchanged CLI child processes, whose routes were separately inspected and contain no such calls.

## Resource scope

The installation receipt observed3.385191 precloseout aggregate CPU seconds,3.679998292122036 active wall seconds and146325504 bytes for its operational parent-plus-maximum-sequential-child-plus-nested-CLI peak measure. Staging allocation before closeout was13807616 bytes. CPU excludes final receipt/database closeout; nested CLI CPU is included in waited-descendant totals without double counting.

The admitted envelope was60 CPU seconds,256MiB operational memory,256MiB disk and120 total wall seconds, with115 seconds allowed for active execution. Current heavy-work absence was sampled before dispatch and child launches; this did not provide atomic exclusion against another owner's later activity. Memory and opaque descendant handling were operational observations, not hard whole-tree containment. These installation observations are separate from the evaluation's60-second conservative CPU ledger charge and its measured precloseout resources.

## Documentation reconciliation

The installation froze16 input files. After verification, only README.md was updated and this INSTALLATION.md was added to describe completed installation. All seven build inputs, three original test modules, PLAN.md, RESULTS.md, results.json, static demo and .gitignore retain their installation-snapshot bytes. No build, installation, ranking or evaluation was rerun for this documentation update.
