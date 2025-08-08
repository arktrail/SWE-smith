#!/bin/bash

sweagent run-batch --num_workers 1 \
    --instances.deployment.docker_args=--memory=10g \
    --config /home/ubuntu/SWE-smith/agent/swesmith_gen_claude_gpt_oss.yaml \
    --instances.path /home/ubuntu/SWE-smith/gpt-oss/logs/experiments/subset0.json \
    --output_dir /home/ubuntu/SWE-smith/gpt-oss/trajectories/test_run \
    --random_delay_multiplier=1 \
    --agent.model.temperature 0.8

# Remember to set CLAUDE_API_KEY_ROTATION=key1:::key2:::key3
