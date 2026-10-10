#!/bin/bash
# Mac queue wrapper: keeps the machine awake, restarts the queue on any exit except 3 (finished).
#   scripts/queue.sh            (laptop = ian)
cd "$(dirname "$0")/.." || exit 1
LAPTOP="${1:-ian}"
if [ -d "$HOME/automitigate-venv" ]; then source "$HOME/automitigate-venv/bin/activate"; else source .venv/bin/activate; fi
mkdir -p logs
while true; do
  caffeinate -dims python -u scripts/run_queue.py --laptop "$LAPTOP" 2>&1 | tee -a "logs/queue_${LAPTOP}.log"
  rc=${PIPESTATUS[0]}
  if [ "$rc" = "3" ]; then echo "queue finished"; break; fi
  echo "$(date) queue exited with $rc; restarting in 60 s" | tee -a "logs/queue_${LAPTOP}.log"
  sleep 60
done
