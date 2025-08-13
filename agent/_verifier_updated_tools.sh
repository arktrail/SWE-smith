#!/bin/bash

# Check if IDs are provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <id1> [id2] [id3] ..."
    echo "Example: $0 0 5 10"
    exit 1
fi

# Loop through all provided IDs
for ID in "$@"; do
    echo "Evaluating subset${ID}_2000_updated_tools..."

    python -m swesmith.harness.eval \
        --dataset_path /home/ubuntu/SWE-smith/gpt-oss/logs/experiments/subset${ID}_2000.json \
        --predictions_path /home/ubuntu/SWE-smith/gpt-oss/trajectories/subset${ID}_2000_updated_tools/preds.json \
        --run_id subset${ID}_2000_updated_tools \
        --workers 10 \
        -f
    
    echo "Completed evaluation for subset${ID}_2000"
done