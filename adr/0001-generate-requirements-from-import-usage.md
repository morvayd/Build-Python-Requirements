# ADR 0001: Generate requirements.txt from project import usage

- Status: Accepted
- Date: 2026-10-17

## Context

This project contains a utility script that scans a Python project directory and generates a dependency list from the imports used in source files and notebooks. The goal is to help users move from a working environment to a reproducible environment without manually maintaining a list of package names.

The script is designed for a typical workflow where a developer has a notebook or project tree with many Python files and wants a quick approximation of the packages that matter. It must:

- inspect both `.py` files and Jupyter `.ipynb` files
- detect import statements in code, not comments or strings
- avoid including local modules and relative imports
- exclude standard-library modules and common false positives
- generate a reproducible requirements file that is usable by `pip install -r`
- record which project files referenced each package in a CSV usage catalog

## Decision

We will implement a static dependency extractor using Python's built-in `ast` parser and Jupyter JSON cell inspection.

The tool will:

1. recursively scan the target directory
2. parse `.py` files and code cells from `.ipynb` files
3. collect top-level import names, such as `sklearn` from `from sklearn.ensemble import RandomForest`
4. ignore relative imports like `from . import utils`
5. skip paths under `site-packages` and `.ipynb_checkpoints`
6. exclude standard-library modules and names beginning with `_` or `dummy_`
7. map a small set of known import-name aliases to their pip install names (`cv2` -> `opencv-python`, `sklearn` -> `scikit-learn`)
8. write `requirements.txt` and `RequirementsUsed.csv` to the chosen output directory

This is intentionally a lightweight static analysis tool rather than a full environment snapshot. It is intended to produce a practical starting point for a dependency file, not a perfect lock file.

## Consequences

### Positive

- Fast and easy to run against a codebase or notebook folder.
- Works without activating the target environment or importing every package.
- Good for projects where the code is the source of truth for dependency needs.
- Produces both a pip-installable package list and a file-level usage report.

### Negative

- Static analysis can miss dynamically imported modules or names that are assembled at runtime.
- Some packages are imported under one name but installed under another, so alias mapping requires maintenance.
- The output is best-effort and may require human review before being treated as a final dependency manifest.
- It does not capture transitive dependencies or environment-specific package versions.

### Trade-offs

This approach favors simplicity and readability over deep dependency resolution. It is well suited to project discovery and onboarding but should not be treated as a definitive package-lock or environment snapshot.

## Status

The project currently uses this approach as its standard requirements-generation workflow.
