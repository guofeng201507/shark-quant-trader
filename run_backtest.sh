#!/bin/bash

# Quick backtest script for Shark Quant Trader
# Usage: ./run_backtest.sh [start_date] [end_date]

START_DATE=${1:-"2020-01-01"}
END_DATE=${2:-"2023-12-31"}

echo "=========================================="
echo "Shark Quant Trader - Backtest Mode"
echo "=========================================="
echo "Start Date: $START_DATE"
echo "End Date: $END_DATE"
echo "=========================================="

poetry run python main.py --mode backtest --start-date $START_DATE --end-date $END_DATE