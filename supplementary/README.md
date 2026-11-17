# Supplementary appendix

[**Download the complete supplementary appendix (PDF)**](https://github.com/anonymous94u/JiraEnhancer/raw/refs/heads/main/supplementary/supplementary_material.pdf)

One document contains the supplementary methods, Appendices A–D, and Figures S1–S2. It uses plain English and explains technical terms as they appear. Use the contents and bookmarks to move between sections.

| Part | Contents |
|---|---|
| Supplementary Methods, Sections 1–5 | Related work (Table S1), review and recovery, system design, decision records, and steps for splitting epics into stories (Algorithm S1) |
| Supplementary Figure S1 | The four parts of the AI engine, within Methods Section 3 |
| Appendix A | Checks of the scoring formulas (Table A.6) |
| Appendix B | Whether equal weights change the comparison (Table B.7), with a chart of reviewer ratings (Figure S2) |
| Appendix C | Update test results for each scenario (Table C.8) |
| Appendix D | An implementation case: moving subscriptions between service instances, with recorded results (Tables D.9–D.10) |
| References | References cited in the supplement |

The appendix letters and labels match the main manuscript. The simpler wording preserves the results, equations, citations, and limits of the evidence. The earlier component documents remain in the repository; this combined PDF is the current version.

[Editable LaTeX source](supplementary_material.tex)

To compile the combined source from this directory:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_material.tex
```
