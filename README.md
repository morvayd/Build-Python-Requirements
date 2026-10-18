# How to Use the Script

## Getting Started

### 1. Save the Code
Save the script provided above as `generate_requirements.py`.

### 2. Navigate to the Directory
Open your terminal or command prompt and use `cd` to navigate to the folder where you saved the script.

### 3. Execute the Script
Run the script by pointing it to your project folder. If you don't provide a path, it will automatically scan the **current directory**. By default, `requirements.txt` is saved in the folder being scanned; when no folder is specified, it is saved in the current working directory.

#### Example Commands

**Scan a specific folder:**
```bash
python generate_requirements.py /path/to/your/notebooks_folder
```

**Scan the current folder:**
```bash
python generate_requirements.py
```

#### Customizing the Output Filename
If you want to specify a custom output filename (e.g., `new_requirements.txt`), use the `-o` flag:

```bash
python generate_requirements.py /path/to/your/notebooks_folder -o new_requirements.txt
```

**Choosing the Output Folder**
Use `--output-dir` to write the requirements file to a different folder. If omitted, it is written to the folder being scanned:

```bash
python generate_requirements.py /path/to/your/notebooks_folder --output-dir /path/to/output_folder
```

You can combine the output folder with a custom filename:

```bash
python generate_requirements.py /path/to/your/notebooks_folder --output-dir /path/to/output_folder -o dependencies.txt
```

### 4. Install the Packages
Activate the Python environment where you want the packages installed. Since the requirements file is saved in the folder being scanned by default, change to that folder before running pip:

```bash
cd /path/to/your/notebooks_folder
python -m pip install -r requirements.txt
```

If you used `--output-dir`, provide the path to the generated file instead:

```bash
python -m pip install -r /path/to/output_folder/requirements.txt
```

## Script Behavior (as implemented)

The script is a CLI dependency scanner that does the following:

* Recursively scans the supplied directory with `Path.rglob("*")`.
* Parses only `.py` files and Jupyter `.ipynb` files.
* Uses Python's `ast` module to read real imports rather than scanning raw text, so comments like `# import pandas` are ignored.
* Extracts the base import name from nested modules, so `from sklearn.ensemble import RandomForest` becomes `sklearn`.
* Ignores relative imports such as `from . import utils`.
* Skips paths under `site-packages` and `.ipynb_checkpoints` so installed packages or notebook checkpoints are not treated as project dependencies.
* Filters out standard-library modules using `sys.stdlib_module_names` and ignores names starting with `_` or `dummy_`.
* Writes two files in the selected output directory:
    * `requirements.txt` — deduplicated install names for the detected third-party packages.
    * `RequirementsUsed.csv` — a catalog with the header `Package,Files`, listing each retained import name and the files that referenced it.

## Key Features

* **Recursive Scanning**: Uses `pathlib.Path.rglob` to find files in every nested subdirectory, skipping files under `site-packages` and `.ipynb_checkpoints` directories so installed-package and notebook-checkpoint imports are not treated as project requirements.
* **Smart Parsing**:
    * **Robustness**: Uses `ast.parse` (the same logic Python uses to read code), ensuring it is not fooled by comments like `# import pandas`.
    * **Jupyter Support**: Specifically handles Jupyter's JSON structure by looking for "code" type cells.
    * **Base Module Extraction**: Correctly identifies the base package for imports. For example, `from sklearn.ensemble import RandomForest` correctly results in `sklearn`.
    * **Relative Import Protection**: Specifically ignores relative imports (e.g., `from . import utils`) so that local files do not end up in your `requirements.txt`.
    * **Dependency Filtering**: Excludes Python's standard-library modules and import names beginning with `_` or `dummy_`, while retaining other third-party imports whether or not they are installed in the environment running the scanner. Standard-library filtering uses `sys.stdlib_module_names` and requires Python 3.10 or newer.
    * **Usage Catalogue**: Writes `RequirementsUsed.csv` beside the requirements file, with one row per retained package and a semicolon-separated list of scan-relative `.py` and `.ipynb` files that import it.

## Important: "Import Name" vs. "Install Name"

Some packages have different names for importing versus installing. `RequirementsUsed.csv` records the **import name**; `requirements.txt` uses the install name for the mappings listed below.

For import names without a known mapping, check the package's PyPI name if pip cannot install an entry from `requirements.txt`.

| Import Name | Install Name (PyPI) |
| :--- | :--- |
| `import cv2` | `opencv-python` |
| `import sklearn` | `scikit-learn` |
