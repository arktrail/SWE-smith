#!/bin/bash

# Check if indices are provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <index1> [index2] [index3] ..."
    echo "Example: $0 5 10 15"
    exit 1
fi

# Configuration
SLEEP_DURATION=30  # Sleep time between runs in seconds
CLEANUP_DOCKER_CACHE=true  # Set to false to skip Docker cache cleanup
CLEANUP_SYSTEM_CACHE=false  # Set to false to skip system cache cleanup

# Function to perform cache cleanup
cleanup_cache() {
    echo "Starting cache cleanup..."
    
    if [ "$CLEANUP_DOCKER_CACHE" = true ]; then
        echo "Cleaning up Docker cache..."
        # Remove unused Docker containers, networks, images, and build cache
        docker system prune -f
        # Remove unused volumes (be careful with this one)
        docker volume prune -f
        # Clean build cache specifically
        docker builder prune -f
    fi
    
    if [ "$CLEANUP_SYSTEM_CACHE" = true ]; then
        echo "Cleaning up system cache..."
        # Clear page cache, dentries and inodes
        sync
        echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
        
        # Clean up temporary files (optional)
        sudo find /tmp -type f -atime +1 -delete 2>/dev/null || true
        
        # Clean up log files that might be getting large (optional)
        sudo journalctl --vacuum-time=1d 2>/dev/null || true
    fi
    
    echo "Cache cleanup completed"
}

# Get total number of indices for progress tracking
TOTAL_RUNS=$#
CURRENT_RUN=0

# Loop through all provided indices
for IDX in "$@"; do
    CURRENT_RUN=$((CURRENT_RUN + 1))
    echo "============================================"
    echo "Processing subset${IDX}_2000... (Run $CURRENT_RUN of $TOTAL_RUNS)"
    echo "============================================"
    
    # Record start time
    START_TIME=$(date +%s)
    
    sweagent run-batch --num_workers 16 \
        --instances.deployment.docker_args=--memory=10g \
        --config /home/ubuntu/SWE-smith/agent/swesmith_gen_gpt_oss_updated_tools.yaml \
        --instances.path /home/ubuntu/SWE-smith/gpt-oss/logs/experiments/subset${IDX}_2000.json \
        --output_dir /home/ubuntu/SWE-smith/gpt-oss/trajectories/subset${IDX}_2000_updated_tools \
        --random_delay_multiplier=1 \
        --agent.model.temperature 0.8
    
    # Record end time and calculate duration
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo "Completed subset${IDX}_2000 (took ${DURATION} seconds)"
    
    # Skip cleanup and sleep for the last run
    if [ $CURRENT_RUN -lt $TOTAL_RUNS ]; then
        echo ""
        echo "Performing cleanup before next run..."
        cleanup_cache
        
        echo "Sleeping for ${SLEEP_DURATION} seconds before next run..."
        sleep $SLEEP_DURATION
        echo ""
    fi
done

echo "============================================"
echo "All runs completed!"
echo "============================================"