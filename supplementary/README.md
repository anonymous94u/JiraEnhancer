# Supplementary appendix

[**Download the complete supplementary appendix (PDF)**](https://github.com/anonymous94u/JiraEnhancer/raw/refs/heads/main/supplementary/supplementary_material.pdf)

One document contains the supplementary methods, Appendices A–D, and Figures S1–S2. Its contents and bookmarks provide navigation within the PDF.

| Part | Contents |
|---|---|
| Supplementary Methods, Sections 1–5 | Related-work comparison (Table S1), workflow and recovery, architecture, record fields, and decomposition procedure (Algorithm S1) |
| Supplementary Figure S1 | The four internal modules, within Methods Section 3 |
| Appendix A | Scoring-model checks (Table A.6) |
| Appendix B | Equal-weight sensitivity analysis (Table B.7) and matched-review radar plot (Figure S2) |
| Appendix C | Scenario-level transaction matrix (Table C.8) |
| Appendix D | Downstream rebalancing case, binding distributions, handoff records, and runtime telemetry (Tables D.9–D.10) |
| References | References cited in the supplement |

The appendix letters and supplementary labels match the main manuscript. The content and numerical results are retained from the earlier component documents.

[Editable LaTeX source](supplementary_material.tex)

To compile the combined source from this directory:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_material.tex
```
