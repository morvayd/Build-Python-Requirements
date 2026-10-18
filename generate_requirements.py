import ast
import csv
import json
import argparse
import sys
from pathlib import Path

class DependencyExtractor:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.packages = set()
        self.package_files = {}

    def _extract_from_code(self, code_text, file_path):
        """Parses code text and extracts top-level module names."""
        try:
            tree = ast.parse(code_text)
        except SyntaxError:
            # This can happen if a .py file has invalid syntax or is an empty file
            return

        for node in ast.walk(tree):
            # Case 1: import pandas, import numpy as np
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._add_package_name(alias.name, file_path)
            
            # Case 2: from sklearn.ensemble import RandomForest
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0:  # node.level > 0 means it's a relative import (e.g., from . import utils)
                    if node.module:
                        self._add_package_name(node.module, file_path)

    def _add_package_name(self, module_name, file_path):
        """Extracts the base package name (e.g., 'sklearn' from 'sklearn.ensemble')"""
        base_package = module_name.split('.')[0]
        self.packages.add(base_package)
        relative_path = Path(file_path).resolve().relative_to(self.root_dir.resolve())
        self.package_files.setdefault(base_package, set()).add(relative_path.as_posix())

    def process_py_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self._extract_from_code(f.read(), file_path)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def process_ipynb_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Jupyter notebooks store code in 'cells'
                for cell in data.get('cells', []):
                    if cell.get('cell_type') == 'code':
                        # 'source' can be a list of strings or a single string
                        source = cell.get('source', [])
                        if isinstance(source, list):
                            source = "".join(source)
                        self._extract_from_code(source, file_path)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def _is_excluded_source(self, file_path):
        path_parts = Path(file_path).parts
        return "site-packages" in path_parts or ".ipynb_checkpoints" in path_parts

    def run(self):
        if not self.root_dir.exists():
            print(f"Error: Path {self.root_dir} does not exist.")
            return

        print(f"Scanning directory: {self.root_dir.absolute()}")

        # Recursive scan
        for file_path in self.root_dir.rglob('*'):
            if self._is_excluded_source(file_path):
                continue
            if file_path.suffix == '.py':
                self.process_py_file(file_path)
            elif file_path.suffix == '.ipynb':
                self.process_ipynb_file(file_path)

        # Filter out standard library modules (Optional/Heuristic)
        # Note: This list is small. For a perfect list, one would use sys.stdlib_module_names (Python 3.10+)
        # But for a requirements.txt, it's safer to include everything and let the user clean it,
        # or simply rely on the fact that pip will ignore non-existent packages.
        # However, let's sort them for cleanliness.
        sorted_packages = sorted(list(self.packages))
        return sorted_packages

def main():
    parser = argparse.ArgumentParser(description="Extract Python dependencies from .py and .ipynb files.")
    parser.add_argument("directory", nargs='?', help="The root directory to scan (defaults to current directory)")
    parser.add_argument("-o", "--output", default="requirements.txt", help="Output filename (default: requirements.txt)")
    parser.add_argument("--output-dir", help="Folder to write the output file to (defaults to the scan directory)")
    
    args = parser.parse_args()

    scan_directory = args.directory or "."
    extractor = DependencyExtractor(scan_directory)
    packages = extractor.run()

    if packages:
        # Keep third-party imports even when they are not installed locally.
        filtered_packages = [
            package for package in packages
            if package not in sys.stdlib_module_names
            and not package.startswith("_")
            and not package.startswith("dummy_")
        ]
        install_name_aliases = {
            "cv2": "opencv-python",
            "sklearn": "scikit-learn",
        }
        requirements = sorted({
            install_name_aliases.get(package, package)
            for package in filtered_packages
        })

        output_directory = args.output_dir or scan_directory
        output_path = Path(output_directory) / args.output
        with open(output_path, 'w') as f:
            for pkg in requirements:
                f.write(f"{pkg}\n")

        usage_path = output_path.with_name("RequirementsUsed.csv")
        with open(usage_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Package", "Files"])
            for package in filtered_packages:
                files = "; ".join(sorted(extractor.package_files[package]))
                writer.writerow([package, files])
        
        print(f"\nSuccess! Found {len(packages)} modules ({len(filtered_packages)} non-standard).")
        print(f"Requirements saved to: {output_path}")
        print(f"Package usage saved to: {usage_path}")
    else:
        print("No Python packages found.")

if __name__ == "__main__":
    main()
