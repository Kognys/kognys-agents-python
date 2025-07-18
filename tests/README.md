# Kognys Agent Testing

This directory contains the integration tests for the Kognys research. The tests are designed to be run with `pytest` and are structured to validate the different phases of the agent's graph execution.

## ⚙️ First-Time Setup & Pre-Test Cleanup

Before running the tests, especially after making changes to the source code, it's a good practice to clean up any stale cache files. These files can sometimes cause mocks or recent code changes to not be applied correctly.

### Step 1: Clean Cache Files

Run the following commands from the project's **root directory** to remove any cached Python files and pytest cache.

```bash
# Remove all Python cache folders
find . -type d -name "__pycache__" -exec rm -r {} +

# Remove the pytest cache directory
rm -rf .pytest_cache
```

###Step 2: Install Dependencies

Ensure all required packages for both the project and testing are installed.

```bash
# Install packages from your requirements file
pip install -r requirements.txt

# Install the kognys package in "editable" mode
# This ensures that your tests always use the latest version of your code
pip install -e .
```

### Step 3: Run the Tests

Once the cleanup is done and dependencies are installed, you can run all tests using pytest.

```bash
# Run all tests
pytest tests/
```

To see logs, run the tests with the `-s` flag.

```bash
pytest -s tests/
```

For the API tests, run the api server:

```bash
python -m uvicorn api_main:app --reload
```

then run the test:

```bash
python -m pytest -s tests/test_api.py
```
