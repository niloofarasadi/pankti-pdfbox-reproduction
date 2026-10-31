# Historical execution-artifact audit

This note records a focused audit of the existing PDFBox execution scripts and CSV artifacts. It documents repository artifacts inspected during the reproduction investigation; it does **not** claim that the historical experiments were rerun.

## 1. Unit-test LOC selection pipeline

The inspected `execution/loc_covered.py` script:

1. Searches the PDFBox module's `src/test/java` tree for Java files whose names contain `Test` and do not contain `pankti`.
2. Extracts public test methods whose names match its simple `test...` pattern.
3. Runs each discovered test method separately.
4. Generates a JaCoCo HTML report and calculates covered lines from its total row.
5. Writes a CSV with `file_loc`, `test_class`, `test_method`, and `loc_covered` columns.

The script's configured output path is the module-level `unit-test-loc.csv`. The existing artifact inspected in the experiment folder is instead:

`execution/unit-tests-loc/pdfbox-unit-test-loc.csv`

The headers and sample rows are consistent with the script's output schema, but the path difference means the inspected CSV cannot be proven to have been produced by this exact script invocation.

The inspected `execution/pankti-system-test.py` reads a supplied LOC CSV and selects rows with `loc_covered >= 1500` before running the corresponding test methods. A read-only count of the existing PDFBox CSV gave:

| Measure | Existing CSV |
|---|---:|
| Test-method rows | 373 |
| Rows with `loc_covered >= 1500` | 149 |
| Rows below the threshold | 224 |
| Maximum `loc_covered` | 7,345 |
| Share meeting the threshold | 39.9% |

These are counts from the existing CSV, not evidence that all 149 tests were successfully run in a particular historical PANKTI execution. The simple source parser in `loc_covered.py` may also miss test methods whose declarations do not match its one-line public-method pattern.

## 2. Historical workload execution scripts

The inspected `execution/run.sh` defines five workload PDFs (000752, 000753, 000809, 000810, and 000817), plus overlay PDF 000142. For each of the five workload PDFs it invokes ten PDFBox operations with the Glowroot Java agent. This is a 5-by-10 workload command structure; the script inspection alone does not prove every command completed successfully.

The inspected `execution/overhead-run.sh` repeats `run.sh` ten times and removes `/tmp/pankti-object-data/` before each iteration. It is a historical shell script and was **not** executed as part of this audit.

The inspected `execution/coverage.sh` uses JaCoCo during the same workload operations. `execution/test_coverage.sh` merges six module-level JaCoCo execution-data files and generates an HTML report. These coverage workflows are distinct from Glowroot/PANKTI production-object-profile collection.

## 3. Historical overhead artifacts

Earlier inspection of `execution/overhead/` identified `run-regular.sh`, `with-pankti.csv`, `without-pankti.csv`, `overhead-per-target.csv`, Glowroot logs, and per-target logs.

Previously calculated historical averages were:

| Configuration | CPU | Memory |
|---|---:|---:|
| Without PANKTI | 3.70% | 0.375% |
| With Glowroot | 21.01% | 1.135% |
| With PANKTI and Glowroot | 20.63% | 3.444% |

These figures should not be collapsed into a single PANKTI overhead percentage. The available measurements have differing comparability and sample conditions; the audit does not establish a controlled, like-for-like overhead estimate.

## 4. Provenance still unresolved

The scripts inspected here do not generate the top-level `execution/report.csv` or `execution/system-test-report.csv`. The LOC scripts explain how unit-test selection data can be generated and consumed, but they do not establish the producer or exact run provenance of the two summary reports.

The existing `system-test-report.csv` remains a separate historical system-test artifact. Its totals align with the paper's Section IV.E system-test experiment; they must not be substituted for the Section IV.C production-workload result.

## 5. Reproducibility and safety notes

- All findings above come from reading scripts and existing artifacts; no historical shell script was executed for this audit.
- The scripts contain hard-coded Linux paths and shell commands, so they are not directly executable in Windows CMD.
- The audit does not modify or regenerate any original experiment output.
- The provenance of `report.csv` and `system-test-report.csv` remains an open question.


## 6. Cross-check against the public PANKTI repositories

A read-only inspection of the public `ASSERT-KTH/pankti` documentation confirms the four-stage workflow: Extract, Instrument, Execute, and Generate. During Execute, Glowroot/PANKTI stores serialized object profiles under `/tmp/pankti-object-data/` and writes `invoked-methods.csv`. The separate `pankti-generate` tool consumes the project path, invoked-methods CSV, and object-profile directory, then writes generated Java test classes under its `output/generated/<project-name>/` directory.

This documents the producer of the object-profile inputs and generated test source files. It does **not** document a producer for the experiment summary file `execution/report.csv`.

The public `ASSERT-KTH/pankti-experiments` PDFBox directory contains the same `execution/report.csv`, `execution/system-test-report.csv`, execution scripts, and LOC-selection files inspected locally. Its `data/analysis.ipynb` contains a manually constructed project-level dataframe with the PDFBox aggregate values 121,175 invocations, 57,563 collected profiles, and 13,851 unique profiles. A search through the notebook's code cells for `report.csv`, `system-test-report.csv`, and the report column names did not reveal code that writes either execution summary CSV. The notebook includes analysis of object-profile size files, but this does not establish the summary CSV's producer.

### 6.1 Three different PDFBox test-count summaries

The public artifacts and paper contain three non-identical summaries:

| Artifact / reference | Generated or unique profiles | Executed tests | Passing | Failing |
|---|---:|---:|---:|---:|
| Paper, Section IV.C production workload | 13,851 | 13,851 differential tests | 13,614 | 237 |
| `execution/report.csv` TOTAL row | 13,851 unique profiles | 2,238 | 2,001 | 237 |
| `pdfbox/README.md` | 13,804 generated test cases | 1,840 | 1,597 | 243 |

The paper reports 28 of 46 effective target methods upgraded to well-tested and 18 remaining pseudo-tested. The execution CSV TOTAL row instead labels 29 methods as tested/partially-tested and 17 as pseudo-tested. The README reports 17 tested, 11 partially tested, and 18 pseudo-tested, which sums to 28 methods upgraded and 18 remaining pseudo-tested, matching the paper's classification counts when tested and partially-tested are combined.

These differences are unresolved. In particular, the matching generated/unique-profile total and failing-test count in `report.csv` do not explain why its executed and passing test counts differ from the paper. The README's generated, executed, passing, and failing counts also do not match the paper exactly. Do not silently substitute one set of values for another or describe the local CSV as an exact regenerated paper result.

### 6.2 Current provenance conclusion

The public PANKTI documentation establishes where object profiles and generated test source files come from. The public experiment repository establishes that the summary CSVs are historical artifacts committed alongside the scripts. However, no inspected public script or notebook has yet been identified as the code that creates `execution/report.csv` or `execution/system-test-report.csv`.

The precise producer, generation command, and reason for the differing test totals remain unresolved. Further progress requires tracing the historical post-processing/Descartes assessment step or obtaining the original experimenter's clarification. This audit did not execute or modify any historical experiment.
