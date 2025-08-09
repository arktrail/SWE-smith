#!/bin/bash

# Check if indices are provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <index1> [index2] [index3] ..."
    echo "Example: $0 5 10 15"
    exit 1
fi

# Loop through all provided indices
for IDX in "$@"; do
    echo "Processing subset${IDX}_2000..."
    
    sweagent run-batch --num_workers 16 \
        --instances.deployment.docker_args=--memory=10g \
        --config /home/ubuntu/SWE-smith/agent/swesmith_gen_claude_gpt_oss.yaml \
        --instances.path /home/ubuntu/SWE-smith/gpt-oss/logs/experiments/subset${IDX}_2000.json \
        --output_dir /home/ubuntu/SWE-smith/gpt-oss/trajectories/subset${IDX}_2000 \
        --random_delay_multiplier=1 \
        --agent.model.temperature 0.8
    
    echo "Completed subset${IDX}_2000"
done