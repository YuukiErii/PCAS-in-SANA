# SANA PCAS LaTeX Report

This folder contains the LaTeX version of the project report.

## Files

- `sana_pcas_report.tex`: main report source.
- Figures are referenced from `../../results/figures/`.

## Build

Use XeLaTeX because the report is written in Chinese and uses `ctexart`.

```powershell
cd C:\Users\Mahiru\Desktop\ERII\PKU\Semester8\DL\项目汇报\SANA\report\latex
latexmk -xelatex -interaction=nonstopmode sana_pcas_report.tex
```

If `latexmk` is unavailable, run XeLaTeX twice:

```powershell
xelatex -interaction=nonstopmode sana_pcas_report.tex
xelatex -interaction=nonstopmode sana_pcas_report.tex
```

The required LaTeX packages are standard in common TeX Live or MiKTeX installations:
`ctex`, `fontspec`, `geometry`, `graphicx`, `booktabs`, `tabularx`,
`tcolorbox`, `caption`, `subcaption`, `fancyhdr`, `hyperref`, and `cleveref`.
