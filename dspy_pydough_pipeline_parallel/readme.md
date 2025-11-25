# Dspy pydough pipeline

## Overview

This repository contains the DSPy Pydough prompt evaluation and prediction pipeline for text-to-SQL generation. The pipeline evaluates different prompts and model configurations to generate PyDough queries from natural language questions, comparing predictions against ground truth using multiple evaluation metrics. It supports parallel processing with multiple API keys and ensemble methods to select the best predictions from multiple attempts. 

### Project Structure

```
dspy_pydough_pipeline_parallel/
├── main.py                          # Main entry point - configure and run experiments here
├── download_bird_database.sh        # Script to download and setup BIRD-SQL databases
├── environment.yml                  # Conda environment configuration
├── data/
│   ├── datasets/                   # SQLite database files
│   │   └── BIRD-SQL/
│   │       └── databases/
│   │       │      └── databases/       # BIRD-SQL databases
│   |       |                  
│   │       └── metadata/             # Database metadata (JSON graph)
│   │           
│   │               
│   ├── prompts/                     # Prompt templates and context
│   │   └── cheatsheet.md
│   └── questions/                   # Question datasets
│       ├── bird_30.csv
│      
├── evaluation/
│   ├── eval.py                      # Evaluation metrics
│   └── prompt_evaluation.py         # Internal parallel processing logic
├── predictors/
│   ├── predictor.py                 # Prediction factory
│   ├── pydough_ensemble.py          # Ensemble base classes
│   ├── question_prediction.py       # Question preparation logic
│   └── ensembles/                   # Ensemble strategies
│       ├── frequency.py             # Most frequent prediction
│       ├── density.py               # Most information-dense prediction
│       ├── random.py                # Random selection
│       ├── heuristics.py            # Heuristic-based selection
│       └── size.py                  # Size-based selection
├── utils/
│   ├── caching/
│   │   └── sqlite_cache.py          # SQLite caching utilities
│   ├── helpers/
│   │   ├── mlflow_tracking.py       # MLflow integration
│   │   └── pydough_helper.py        # Helper functions
│   ├── generate_markdown.py         # Markdown generation utilities
│   └── utils.py                     # General utilities
└── results/                         # Output directory (generated after execution)
```

---

## Requirements
- **Linux environment or WSL (Windows Subsystem for Linux)** - Required for bash scripts and proper file handling
- Python 3.10+ recommended
- Conda or miniconda installed
- Dependencies defined in `environment.yml`
- `wget` and `unzip` utilities (typically pre-installed on Linux/WSL)

---

## Installation (Step by Step)

### 1. Download BIRD-SQL Databases

Before setting up the environment, you need to download the required databases. From the repository root:

```bash
cd dspy_pydough_pipeline_parallel
chmod +x download_bird_database.sh
./download_bird_database.sh
```

This script will:
- Download the BIRD-SQL dataset (dev.zip) from the official repository
- Extract the databases
- Place them in the correct directory structure: `data/databases/datasets/BIRD-SQL/databases/`
- Clean up temporary files

**Note:** The download is approximately 8GB and may take some time depending on your connection.

### 2. Navigate to the project directory
From the repository root:
```bash
cd dspy_pydough_pipeline_parallel
```

### 3. Create environment with Conda 
```bash
conda env create -f environment.yml -n dspy-pydough
conda activate dspy-pydough
```

---

## Data Preparation

After running the database download script, verify that:
- Database files exist in `data/datasets/BIRD-SQL/databases/`
- Question datasets are present in `data/questions/` (e.g., `bird_10.csv`)
- Metadata exists in `data/datasets/BIRD-SQL/metadata/`
- Prompt templates are in `data/prompts/` (e.g., `cheatsheet_8_1.md`)

---

## API Key Configuration

The pipeline requires API keys to function. These are loaded from a `.env` file in the project root.

### Setup Instructions

1. Create a `.env` file in the root directory of the project (same level as `dspy_pydough_pipeline_parallel/`)

2. Add your API key(s) to the `.env` file:

**Single API Key:**
```env
API_KEY=your_api_key_here
```

**Multiple API Keys (for load balancing or redundancy):**
```env
API_KEY_1=your_first_api_key_here
API_KEY_2=your_second_api_key_here
API_KEY_3=your_third_api_key_here
API_KEY_N=your_n_api_key_here
```

3. The pipeline loads these keys automatically:

**For single key:**
```python
env = load_dotenv()

api_keys = [
    os.getenv("API_KEY")
]
```

**For multiple keys:**
```python
env = load_dotenv()

api_keys = [
    os.getenv("API_KEY_1"),
    os.getenv("API_KEY_2"),
    os.getenv("API_KEY_3"),
    os.getenv("API_KEY_4"),
    os.getenv("API_KEY_5"),
    os.getenv("API_KEY_6"),
]  # add the keys in the .env file
```

***IMPORTANT: Update the main.py file to match your API key configuration***

Open main.py and locate the API keys section. You must modify this code to match the number and names of API keys in your .env file.

### Custom .env Path

If your `.env` file is located elsewhere, you can specify the path:

```python
env = load_dotenv("/path/to/your/.env")
```

Or use a relative path:
```python
env = load_dotenv("config/.env")
```

**Important:** Never commit your `.env` file to version control. Add it to `.gitignore` (It's already included in the .gitignore)

---

## Running the Pipeline

The pipeline is executed through the `main.py` file, where you configure your experiment parameters. The `evaluation/prompt_evaluation.py` module is used internally and should not be run directly from the console.

### Basic Execution

```bash
python main.py
```

Check console output and results in the `results/` directory.

---

## Experiment Configuration

All experiment settings are configured directly in `main.py`. Here's a breakdown of the key components:

### Main Configuration Parameters

```python
processes_per_key = 3              # Number of parallel processes per API key
experiment_name = "Bird_COT"       # Name for your experiment
results_path = "results"           # Directory for detailed results
summary_path = "results"           # Directory for summary outputs
cache_path = "/home/cache/Bird_COT"  # Cache directory for predictions
```

### Data Paths

```python
db_base_path = "data/databases/datasets/BIRD-SQL/databases/"  # SQLite databases location
metadata_base_path = "data/metadata/datasets/BIRD-SQL/metadata/"  # Metadata JSON files
questions_df = pd.read_csv("data/questions/bird_10.csv")  # Questions dataset
context = Path("data/prompts/cheatsheet.md").read_text()  # Prompt context
```

### Prediction Factory

The `PydoughPredictionFactory` creates prediction instances with specific configurations:

```python
factory1 = PydoughPredictionFactory(
    model='gemini/gemini-2.5-flash',  # Model to use for predictions
    temperature=0.2,                   # Sampling temperature (0.0-1.0)
    context=context,                   # Prompt context/instructions
    cache_path=cache_path,             # Where to cache results
    db_base_path=db_base_path,         # Database directory
    dspy_cache=True,                   # Enable DSPy caching
    experiment_name=experiment_name,   # Experiment identifier
    retries=3                          # Number of retry attempts on failure
)
```

**Key Parameters:**
- **model**: The LLM model identifier (e.g., `gemini/gemini-2.5-flash`)
- **temperature**: Controls randomness in predictions (lower = more deterministic)
- **context**: System prompt or instructions loaded from markdown file
- **cache_path**: Directory to store cached predictions and dataframes for reuse
- **dspy_cache**: Enable/disable DSPy's internal caching mechanism
- **retries**: Number of retry attempts for query erros
### Ensemble Strategies

The pipeline supports multiple ensemble methods for selecting the best prediction from multiple generated outputs:

#### 1. Frequency Ensemble
Selects the most frequently occurring prediction across multiple runs.

```python
from predictors.ensembles.frequency import FrequencyEnsemble

ensemble = FrequencyEnsemble([(factory1, 3)])  # Using factory1 with 3 tries(3 differend predictions)
```

**Use case**: Best when you want the most consistent/stable prediction across multiple attempts.

#### 2. Density Ensemble
Selects the prediction with the highest byte density (most information-dense output).

```python
from predictors.ensembles.density import DensityEnsemble

ensemble = DensityEnsemble([(factory1, 3)])  # Using factory1 with 3 tries(3 differend predictions)
```

**Use case**: Useful when you want the most detailed or comprehensive response.

#### 3. Random Ensemble
Randomly selects one prediction from all generated outputs.

```python
from predictors.ensembles.random import RandomEnsemble

ensemble = RandomEnsemble([(factory1, 3)])  # Using factory1 with 3 tries(3 differend predictions)
```

**Use case**: Useful for baseline comparisons or when you want unbiased sampling from the generated predictions.

#### 4. Heuristics Ensemble
Applies heuristic rules to select the best prediction.

```python
from predictors.ensembles.heuristics import HeuristicsEnsemble

ensemble = HeuristicsEnsemble([(factory1, 3)])  # Using factory1 with 3 tries(3 differend predictions)
```

**Use case**: When you have domain-specific rules for determining quality.

#### 5. Size Ensemble
Selects prediction based on size criteria.

```python
from predictors.ensembles.size import SizeEnsemble

ensemble = SizeEnsemble([(factory1, 3)])  # Using factory1 with 3 tries(3 differend predictions)
```

**Use case**: When prediction length correlates with quality in your domain.

### Multiple Factories

You can combine multiple factories with different configurations:

```python
factory1 = PydoughPredictionFactory(model='gemini/gemini-2.5-flash', temperature=0.2, ...)
factory2 = PydoughPredictionFactory(model='gemini/gemini-2.5-pro', temperature=0.5, ...)

# Make 3 different predictions for Factory1, and 2 predictions for Factory2.
ensemble = FrequencyEnsemble([(factory1, 3), (factory2, 2)])
```

---

## Understanding the Results

After running the pipeline, results are generated in the specified `results_path` and `summary_path` directories.

### Output Files

#### 1. Detailed Results CSV
A CSV file containing individual question results with the following information:
- Original question data
- Generated SQL predictions
- Match status (whether the prediction matched the ground truth)
- Evaluation metrics per question

Example: If you run 20 questions, you'll get a CSV with 20 rows, each containing the complete question data and whether the ensemble-selected prediction was correct.

#### 2. Summary JSON
A comprehensive summary with overall experiment metrics:

```json
{
    "Experiment dataset": "Bird_test",
    "Total questions": 94,
    "Total custom hits": 56,
    "Total bird hits": 55,
    "Upper_bound_compare_df %": 60.63829787234043,
    "Upper_bound_bird_hits %": 59.57446808510638,
    "Upper_bound_sutom_bird_hits %": 59.57446808510638,
    "Acuraccy custom %": 59.57446808510638,
    "Acuraccy bird %": 58.51063829787234,
    "Acuraccy mod bird %": 58.51063829787234,
    "Total timeouts question": 1,
    "Total Query error": 0
}
```

### Evaluation Metrics Explained

**Ensemble Selection Results:**
- **Acuraccy custom %**: Flexible business logic evaluation that allows for variations in correct answers
- **Acuraccy bird %**: Strict BIRD benchmark evaluation requiring exact match (including column order)
- **Acuraccy mod bird %**: Modified BIRD evaluation that accepts correct DataFrames even if columns are in different order

**Upper Bounds (Maximum Achievable):**
- **Upper_bound_compare_df %**: Maximum possible accuracy if the best prediction was always selected (custom evaluation)
- **Upper_bound_bird_hits %**: Maximum possible accuracy if the best prediction was always selected (BIRD evaluation)
- **Upper_bound_sutom_bird_hits %**: Maximum possible accuracy combining both evaluation methods

The upper bounds represent the theoretical ceiling of performance across all generated predictions, showing the potential improvement if perfect ensemble selection were achieved.

**Error Tracking:**
- **Total timeouts question**: Number of questions that exceeded time limits
- **Total Query error**: Number of questions that resulted in SQL execution errors

---

## Key Files and Their Purpose
- **`main.py`** — Main pipeline entry point
- **`download_bird_database.sh`** — Database download and setup script
- **`evaluation/prompt_evaluation.py`** — Prompt evaluation and metrics testing
- **`predictors/`** — Prediction models and wrappers
- **`utils/`** — Shared utilities and helper functions
- **`results/`** — Generated output (CSV/JSON files, logs)

---

## Notes

- Keep sensitive credentials out of the repository; use environment variables
- Ensure you're running on a Linux environment or WSL for proper script execution
- The BIRD-SQL database download is required before running experiments
- Results are cached to avoid redundant API calls
- If you encounter database errors, dataframe generation failures, or issues with generated PyDough/SQL code, try deleting the cache folder. A corrupted cache may be causing these problems.