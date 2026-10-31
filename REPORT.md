# Reproducing the PANKTI PDFBox Case Study: Method Signatures and Matching

**Author:** Niloofar Asadi\
**Research area:** Software engineering, software testing, and
AI-assisted software engineering\
**Subject system:** Apache PDFBox 2.0.21\
**Reference paper:** Deepika Tiwari, Long Zhang, Martin Monperrus, and
Benoit Baudry, *Production Monitoring to Improve Test Suites*, Section
IV.C and Table IV. https://arxiv.org/pdf/2012.01198\
**Code and artifacts:** PANKTI repository and the PDFBox experiment
artifacts described below

## 1. Motivation and research question

As part of my attempt to reproduce the PDFBox case study in Section IV.C
of the PANKTI paper, I examined the method-extraction and
method-matching stages. I focused on whether the extracted parameter
signatures correctly represent Java array types and whether signature
mismatches could explain some methods that were not matched to the
instrumentation candidates.

The main question for this investigation is:

> To what extent does correcting multidimensional-array descriptors
> explain the unmatched methods in the PDFBox case study, when the
> source scope and other selector behavior are held constant?

This is a partial reproduction and a diagnostic investigation. I do not
claim to have reproduced the complete end-to-end PANKTI pipeline.

## 2. Experimental setup and evidence

The controlled extraction targeted PDFBox's main source tree:

`pdfbox/src/main/java`

The extraction reported:

-   Methods processed: **5,801**
-   Methods extracted: **4,204**
-   Nested invocations on fields or parameters: **2,677**

The CSV produced by this run is recorded at:

`controlled-main-only/extracted-methods-pdfbox-main-only-void.csv`

The controlled extraction contained 4,204 rows, while the historical
extraction file contained 6,133 rows. A signature comparison using
declaring class, method name, parameter signature, and return type as
the key reported 4,186 shared signatures, 1,947 historical-only
signatures, 18 controlled-only signatures, and no duplicate keys in
either dataset.

These counts are useful diagnostics, but the historical and controlled
runs do not have a confirmed identical source scope. Therefore, the
row-count difference cannot be attributed to the signature correction
alone.

I also applied a class-name heuristic using `Test...`, `...Test`,
`...Tests`, and `...Tester`. It did not identify matching classes under
the tested patterns. This is only a heuristic; it does not prove that
all test-related code was excluded.

## 3. Code changes examined

### 3.1 Multidimensional-array parameter signatures

In the original extractor logic I inspected, an array parameter was
represented with one `[` character regardless of its number of
dimensions. For example, the historical record for
`PDAnnotationMarkup.setInkList(float[][])` used `[F`. The JVM descriptor
for a two-dimensional float array is `[[F`.

In the experimental extractor copy, I changed the signature generation
to preserve the number of array dimensions. The controlled extraction
recorded `[[F` for `PDAnnotationMarkup.setInkList`.

The matching diagnostic also reported that
`PDAnnotationMarkup.setInkList` and `ByteTrie.addPath` became matchable
after the experimental changes. Both involve multidimensional array
parameters. This is consistent with the descriptor correction helping
these cases.

However, because the experimental run included another change described
below, the current comparison does not isolate the array-signature fix
as the sole cause of the two additional matches.

### 3.2 Null declaring-type guard in `MockableSelector`

I also added a guard in the experimental `MockableSelector` for
invocations with no declaring-type reference. In this case, the selector
returns `false` rather than raising a `NullPointerException`.

This is a behavioral change: it can affect which methods are classified
as mockable. It should not be bundled with the signature correction when
drawing causal conclusions about the matching result.

The experimental Maven build completed successfully after these changes.
A successful build verifies compilation and packaging, but it does not
by itself verify the full reproduction.

## 4. Method-matching diagnostic

The historical matching diagnostic reported:

| Metric | Historical diagnostic |
|---|---:|
| Eligible Descartes methods | 2,760 |
| Matched methods | 2,204 |
| Unmatched methods | 556 |
| Duplicate matches | 0 |
| Match rate | 79.86% |

After the experimental changes, the diagnostic reported:

| Metric | Experimental diagnostic |
|---|---:|
| Matched methods | 2,206 |
| Unmatched methods | 554 |
| Duplicate matches | 0 |
| Match rate | 79.93% |

The match count increased by two, from 2,204 to 2,206, and the reported
match rate increased by approximately 0.07 percentage points. The two
newly matched methods were `PDAnnotationMarkup.setInkList` and
`ByteTrie.addPath`.

This is a small but interpretable change. It supports further
investigation of array descriptors, but it does not show that all
remaining unmatched methods are bugs or should necessarily be
instrumented.

## 5. Distinguishing the two PDFBox experiments in the paper

### 5.1 Case Study 2 — production workload (Section IV.C)

The task assigned to me is to reproduce Case Study 2 in Section IV.C. In the paper, this is the PDFBox production-workload experiment. The reference results for PDFBox are 121,175 target-method invocations, 57,563 collected production object profiles, 13,851 unique profiles / generated differential tests, 13,614 passing tests, and 237 failing tests. The paper reports that 28 of the 46 effective target methods become well-tested after adding the generated tests. These are the reference values that a reproduction of Section IV.C should compare against.

The current investigation described in this report has focused mainly on extraction, method signatures, and matching diagnostics. It has not independently regenerated the complete production workload, object-profile collection, generated-test set, and test-improvement assessment needed to claim reproduction of these Section IV.C results.

### 5.2 Separate system-test experiment (Section IV.E, Table IV)

The repository also contains `pdfbox/execution/system-test-report.csv`. Its `TOTAL` row for PDFBox records 18,291 tests, 17,655 passing tests, 636 failing tests, 66 methods marked `well-tested`, and 45 marked `pseudo-tested`. These figures match the PDFBox row in Table IV, which belongs to the separate system-test experiment in Section IV.E. They are not the production-workload results of Case Study 2 in Section IV.C.

### 5.3 Other historical README summary


The repository contains two historical summaries that initially appear
inconsistent.

### 5.1 `pdfbox/README.md`

The README records 129 instrumented methods, 46 invoked methods, 13,804
generated test cases, 1,840 executed tests, 1,597 passing tests, and 243
failing tests.

### 5.2 `pdfbox/execution/system-test-report.csv`

The CSV's `TOTAL` row records 18,291 tests, 17,655 passing tests, 636
failing tests, 66 methods marked `well-tested`, and 45 marked
`pseudo-tested`. The per-method report contains 111 method rows, plus
the `TOTAL` row.

These CSV totals match the PDFBox row in Table IV of the paper's
system-test experiment: 18,291 PANKTI tests, 17,655 passing, 636
failing, and 66 of 111 effective targets classified as well-tested, with
45 remaining pseudo-tested. The paper also reports 150 system tests and
111 effective targets out of 138 target methods for PDFBox in this
experiment.

The README summary should not be substituted for these system-test
figures. It may refer to a different experiment stage, configuration, or
artifact version, but I have not established its provenance. The
repository's execution log includes timestamps from 3 November 2020,
confirming that at least that log is historical rather than a record of
my current controlled extraction.

This distinction matters: the CSV provides evidence that the repository
contains a report consistent with the paper's system-test results, but
it does not establish that I regenerated those downstream results during
this investigation.

## 6. Interpretation

The most defensible conclusion from the current evidence is narrow:

1.  The original signature logic I inspected did not preserve
    multidimensional-array depth.
2.  The experimental extractor produced the expected `[[F` descriptor
    for `PDAnnotationMarkup.setInkList(float[][])`.
3.  The combined experimental changes coincided with two additional
    matched methods and a small increase in the matching rate.
4.  The current results do not isolate the contribution of the
    array-signature change from the null-declaring-type guard.
5.  Historical downstream artifacts can be compared with the paper, but
    they must not be described as newly reproduced results.

The main unresolved issue is causal attribution: did the array-signature
correction itself account for both new matches, and what explains the
remaining 554 unmatched methods?

## 7. Optional diagnostic follow-up: controlled ablation

A small controlled ablation would make the method-matching diagnosis substantially stronger, but it was not explicitly requested in the assignment. It is optional and should not replace the main goal of reproducing the Section IV.C production-workload experiment.
without requiring an immediate rerun of the entire production workload.
I propose running the same extraction and matching procedure with the
same PDFBox source scope and the same input artifacts under four
configurations:

| Configuration | Array-signature fix | Null guard |
|---|---|---|
| A — baseline | No | No |
| B — signature only | Yes | No |
| C — guard only | No | Yes |
| D — combined changes | Yes | Yes |

For each configuration, record the exact source revision, command,
source scope, number of extracted methods, eligible methods, matched and
unmatched methods, duplicate matches, and match rate. The existing
historical result can serve as a reference, but it should only be
treated as the baseline if its source scope and inputs can be confirmed
to match.

Before running the full comparison, add small regression tests for JVM
descriptors such as:

-   `float[]` → `[F`
-   `float[][]` → `[[F`
-   `float[][][]` → `[[[F`
-   `String[]` → `[Ljava/lang/String;`
-   `String[][]` → `[[Ljava/lang/String;`

Also test that `MockableSelector` behaves as intended when the
declaring-type reference is null. This would help distinguish a
descriptor bug from a classification side effect.

The most informative next analysis would classify the remaining
unmatched methods by reason, for example: signature mismatch,
source-scope mismatch, overload ambiguity, missing or ineligible method,
or selector exclusion. These categories should be based on inspection
rather than assumed in advance. A short unmatched-method sample can
establish whether the proposed categories are useful before analyzing
all 554 methods.

## 8. Questions for discussion

The current findings raise two research questions that would be useful
to discuss with the authors:

1.  **Attribution:** Is it reasonable to attribute the two additional
    matches to multidimensional-array descriptor correction, or should
    the array fix and null guard first be evaluated independently under
    identical source scope and inputs?
2.  **Remaining unmatched methods:** Is there an expected explanation or
    diagnostic procedure for the remaining unmatched methods? In
    particular, would the authors recommend prioritizing JVM descriptor
    normalization, source-scope alignment, or selector eligibility
    checks when investigating these mismatches?

These questions are intended to clarify the reproduction methodology and
strengthen the evidence, rather than to challenge the paper's reported
results.

## 9. Limitations and current status

This work has not regenerated the full end-to-end case study, and the
provenance of the README's separate downstream figures remains
unresolved. The controlled extraction and matching diagnostics are the
results of the current investigation; the historical test reports are
treated as existing artifacts.

**Current status: Partial reproduction.** I verified a targeted
multidimensional-array signature correction and observed two additional
matches in a diagnostic run that also included a selector guard. A
controlled ablation with identical inputs is the next step needed to
attribute the improvement confidently.
