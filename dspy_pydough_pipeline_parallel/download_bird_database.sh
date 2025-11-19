#!/bin/bash

# Script to download and setup BIRD-SQL databases
# Run from: pydough_pipeline_parallel/

set -e  # Stop on error

echo "=== Downloading dev.zip ==="
wget -O train.zip https://bird-bench.oss-cn-beijing.aliyuncs.com/train.zip 

echo "=== Extracting train.zip ==="
unzip -q train.zip

echo "=== Extracting train_databases.zip ==="
unzip -q train/train_databases.zip

echo "=== Moving train_databases content ==="
cp -r train_databases/* data/datasets/BIRD-SQL/databases/

echo "=== Cleaning up temporary files ==="
rm -rf train.zip train train_databases __MACOSX

echo "=== Completed! ==="
echo "Databases are located at: dspy_pydough_pipeline_parallel/data/databases/datasets/BIRD-SQL/databases/"