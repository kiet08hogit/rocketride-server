#!/bin/bash

# 1. Create a dummy requirements file representing our new setup
echo "img2table" > req_test.txt
echo "polars>=1.0.0" >> req_test.txt
echo "polars-lts-cpu>=1.0.0" >> req_test.txt

echo "--- SIMULATING OLDER NON-AVX2 CPU ---"
# Create a fresh virtual environment
python3 -m venv venv_old
source venv_old/bin/activate
pip install uv > /dev/null

# The logic depends.py runs: exclude standard polars
echo "polars" > excludes_old.txt
uv pip install -r req_test.txt --excludes excludes_old.txt > /dev/null

# Show the results
pip list | grep -i polars
deactivate
echo ""

echo "--- SIMULATING MODERN AVX2 CPU ---"
python3 -m venv venv_modern
source venv_modern/bin/activate
pip install uv > /dev/null

# The logic depends.py runs: exclude polars-lts-cpu
echo "polars-lts-cpu" > excludes_modern.txt
uv pip install -r req_test.txt --excludes excludes_modern.txt > /dev/null

# Show the results
pip list | grep -i polars
deactivate

# Clean up the temporary files
rm -rf req_test.txt excludes_old.txt excludes_modern.txt venv_old venv_modern
