# PANKTI PDFBox Case Study Reproduction Report

**Author:** Niloofar Asadi  
**Subject system:** Apache PDFBox 2.0.21  
**Assigned study:** Case Study 2 — production workload (Section IV.C)  
**Reference:** Tiwari, D., Zhang, L., Monperrus, M., and Baudry, B., *Production Monitoring to Improve Test Suites*, arXiv:2012.01198v4 (2021).  
**Reproduction repository:** https://github.com/niloofarasadi/pankti-pdfbox-reproduction

## 1. Executive summary

This report documents a partial reproduction and diagnostic investigation of the PDFBox case study in PANKTI. The work concentrated on the method-extraction and method-matching stages, especially the representation of multidimensional Java array parameters in JVM method signatures.

The investigation identified a defect in the inspected signature-generation logic: array parameters were represented with a single `[` prefix regardless of array dimensionality. An experimental correction preserved the array depth. For example, the descriptor for `PDAnnotationMarkup.setInkList(float[][])` changed from the historical `[F` representation to the expected JVM descriptor `[[F`.

The experimental matching diagnostic reported two additional matches (from 2,204 to 2,206) after two changes had been applied: the array-signature correction and a null-declaring-type guard in `MockableSelector`. Because both changes were present in the same experimental run, their individual effects have not been isolated.

**This work does not constitute a complete end-to-end reproduction of the Section IV.C production-workload experiment.** In particular, the production workload has not been independently rerun to regenerate the invocation counts, object profiles, generated tests, and test-improvement results reported in the paper. Historical repository artifacts are distinguished from measurements made during this investigation.

## 2. Reference results: the correct experiment

The assigned target is Case Study 2 (PDFBox) in Section IV.C, which evaluates PANKTI using a production workload. The paper reports the following PDFBox results:

| Metric | Paper result |
|---|---:|
| Invocations of target methods | 121,175 |
| Production object profiles collected | 57,563 |
| Unique profiles / generated differential tests | 13,851 |
| Passing generated tests | 13,614 |
| Failing generated tests | 237 |
| Target methods upgraded to well-tested | 28 of 46 |
| Target methods remaining pseudo-tested | 18 of 46 |

The paper states that 57,563 profiles were collected from 46 effective target methods. After profile deduplication, 13,851 differential tests were generated and executed. The paper's prose reports 13,614 passing tests (98.3%) and 237 failing tests. The PDFBox row in Table III displays a rounded passing percentage of 98.2%; the exact count ratio is approximately 98.3%.

These values are **reference results from the paper**, not results regenerated in this investigation.

### 2.1 Do not confuse Section IV.C with Section IV.E

The repository also contains `pdfbox/execution/system-test-report.csv`. Its TOTAL row records 18,291 tests, 17,655 passing tests, 636 failing tests, 66 well-tested methods, and 45 pseudo-tested methods. These figures correspond to the separate system-test experiment in Section IV.E (Table IV), not the production-workload experiment in Section IV.C.

The two experiments use different workloads and produce different target/test counts. Therefore, the Section IV.E figures must not be used as the reproduction result for Section IV.C.

## 3. Environment and scope of the current investigation

The controlled extraction targeted the PDFBox main-source directory:

`pdfbox/src/main/java`

The recorded extraction output was:

- Methods processed: **5,801**
- Methods extracted: **4,204**
- Nested invocations on fields or parameters: **2,677**

The output was recorded as:

`controlled-main-only/extracted-methods-pdfbox-main-only-void.csv`

A class-name heuristic checked patterns such as `Test...`, `...Test`, `...Tests`, and `...Tester`. It did not identify classes matching those patterns. This is only a heuristic and does not establish that every possible test-related source file was excluded.

The historical extraction artifact contained 6,133 rows. A comparison keyed by declaring class, method name, parameter signature, and return type reported:

| Comparison | Count |
|---|---:|
| Shared signatures | 4,186 |
| Historical-only signatures | 1,947 |
| Controlled-only signatures | 18 |
| Duplicate keys in either dataset | 0 |

The historical and controlled extraction runs have not been shown to use identical source scopes and inputs. Consequently, the difference between 6,133 and 4,204 rows cannot be attributed to the array-signature correction alone. These figures are diagnostic, not a like-for-like reproduction result.

## 4. Extractor changes investigated

### 4.1 Multidimensional-array parameter signatures

The original signature logic inspected during this investigation added only one `[` character whenever a parameter was an array. This loses dimensionality for multidimensional arrays.

For example:

- Java type: `float[]` — expected JVM descriptor: `[F`
- Java type: `float[][]` — expected JVM descriptor: `[[F`
- Java type: `float[][][]` — expected JVM descriptor: `[[[F`

For `PDAnnotationMarkup.setInkList(float[][])`, the historical extraction recorded `[F`, while the experimental extractor recorded `[[F`. This confirms the corrected descriptor for the inspected example.

### 4.2 Null declaring-type guard

A second experimental change added a null guard in `MockableSelector` for invocations without a declaring-type reference. In that case, the selector returns `false` instead of throwing a `NullPointerException`.

This can affect mockability classification. It is therefore a behavioral change and must be considered separately from the signature correction when interpreting matching results.

The experimental Maven build completed successfully after these changes. A successful build confirms compilation and packaging, but does not establish end-to-end reproduction.

## 5. Method-matching diagnostic

The historical diagnostic reported:

| Metric | Historical diagnostic |
|---|---:|
| Eligible Descartes methods | 2,760 |
| Matched methods | 2,204 |
| Unmatched methods | 556 |
| Duplicate matches | 0 |
| Match rate | 79.86% |

After the two experimental changes had been applied, the diagnostic reported:

| Metric | Experimental diagnostic |
|---|---:|
| Matched methods | 2,206 |
| Unmatched methods | 554 |
| Duplicate matches | 0 |
| Match rate | 79.93% |

The two additional matched methods were:

- `PDAnnotationMarkup.setInkList`, involving a two-dimensional `float` array.
- `ByteTrie.addPath`, involving a two-dimensional `byte` array.

The observed increase is consistent with multidimensional-array signature correction helping these cases. However, the array-signature correction and null guard were both included in the experimental run. Without an ablation under identical source scope and inputs, the two additional matches cannot be causally attributed to the array correction alone.

The remaining 554 unmatched methods have not all been classified. It would be incorrect to assume that every unmatched method represents a defect: source-scope differences, eligibility rules, overloads, and selector behavior may also explain mismatches.

## 6. Historical downstream artifacts

Two historical summaries are present in the original experiment repository:

1. `pdfbox/README.md` records 129 instrumented methods, 46 invoked methods, 13,804 generated test cases, 1,840 executed tests, 1,597 passing tests, and 243 failing tests.
2. `pdfbox/execution/system-test-report.csv` records the separate Section IV.E system-test results described in Section 2.1 above.

The README figures have not been reconciled with the Section IV.C production-workload results or with the Section IV.E system-test results. The execution log contains timestamps from November 2020, so it is historical evidence rather than a log of the current investigation.

These artifacts are retained as historical records. They are not presented as newly generated results.

## 7. Findings and limitations

The current evidence supports the following conclusions:

1. The inspected original signature logic did not preserve multidimensional-array depth.
2. The experimental extractor produced the expected `[[F` descriptor for the inspected `float[][]` parameter.
3. The combined experimental changes coincided with two additional matches and a small increase in the matching rate.
4. The current comparison does not isolate the contribution of the array-signature fix from the null guard.
5. The historical and controlled extraction datasets have not been confirmed to use identical source scopes.
6. The production-workload phase of Section IV.C has not been independently rerun end to end.
7. The Section IV.E system-test report is a different experiment and cannot substitute for Section IV.C results.

## 8. Recommended next validation steps

To strengthen the diagnostic result, the following steps are recommended:

1. Run a four-configuration ablation with identical PDFBox source scope and inputs: baseline, array-signature fix only, null guard only, and both changes.
2. Add regression tests for one-, two-, and three-dimensional primitive arrays and one- and two-dimensional reference arrays.
3. Record the exact source revision, commands, Java/Maven versions, input paths, and output hashes for each run.
4. Classify a sample of the remaining unmatched methods by inspected cause before attempting to classify the full set.
5. If the goal is a full Section IV.C reproduction, rerun the production workload, collect object profiles, generate and execute tests, and compare each stage against the paper's reference results.

These are proposed follow-up steps; they have not been completed as part of the current investigation.

## 9. Questions for the authors

I would appreciate guidance on two points:

1. For the two additional method matches, would you recommend first isolating the array-signature correction and the null-declaring-type guard through a controlled ablation under identical inputs?
2. When investigating the remaining unmatched methods, is there a recommended diagnostic procedure for distinguishing descriptor mismatches from source-scope differences and selector-eligibility exclusions?

## 10. Reproduction status

**Status: Partial reproduction / diagnostic investigation.**

The work verified a targeted multidimensional-array descriptor correction and documented a small change in method matching. It also identified the distinction between the production-workload experiment in Section IV.C and the system-test experiment in Section IV.E.

The full Section IV.C production-workload pipeline and its reported outcomes have not been independently regenerated. This report therefore makes no claim of complete reproduction. All historical values, current diagnostic measurements, and proposed follow-up work are explicitly distinguished.

## References

- Tiwari, D., Zhang, L., Monperrus, M., and Baudry, B. *Production Monitoring to Improve Test Suites*. arXiv:2012.01198v4, 2021. https://arxiv.org/abs/2012.01198
- PANKTI source repository: https://github.com/castor-software/pankti
- PANKTI experiment artifacts: https://github.com/castor-software/pankti-experiments
- Apache PDFBox 2.0.21: https://github.com/apache/pdfbox/tree/2.0.21
