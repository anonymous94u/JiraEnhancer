# Supplementary material

| Material | Contents | Files |
|---|---|---|
| Appendices A and B | Scoring-model checks for internal and public issue text, followed by the detailed equal-weight sensitivity analysis. | [PDF](appendices_a_b.pdf) · [LaTeX](appendices_a_b.tex) |
| Module architecture | Four diagrams show story enhancement, epic-to-story decomposition, prompt generation, and the RL controller, with the original explanation. | [PDF](module_architecture.pdf) · [LaTeX](module_architecture.tex) |
| Appendices C and D | The scenario-level transaction matrix and the downstream rebalancing case, including binding distributions, handoff records, and runtime telemetry. | [PDF](appendices_c_d.pdf) · [LaTeX](appendices_c_d.tex) |

The moved text, numerical values, table contents, and diagram images are retained. Cross-references are updated for the separate documents. Tables A.7 and B.8 follow the main paper's six tables; Tables C.9, D.10, and D.11 continue this numbering. Table 6b refers to the main paper's mutation-safety panel. The module diagram is Supplementary Figure S1.

To rebuild from this directory with a LaTeX installation:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error appendices_a_b.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error module_architecture.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error appendices_c_d.tex
```
