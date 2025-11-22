#!/usr/bin/env zsh
# Cleanup unused docs/scripts artifacts for MVP
# Safe to run multiple times. Only deletes clearly unreferenced or generated files.

set -euo pipefail

print "[cleanup] Starting unused files removal..."

# List of files considered safe to delete (no code/workflow references)
FILES_TO_DELETE=(
  "scripts/testing/performance_analysis_report.json"
  "scripts/testing/performance_optimization_progress_report.md"
  "docs/performance/performance_results.json"
  "docs/archive/greeting_detection.md"
)

removed=0
skipped=0

for f in ${FILES_TO_DELETE[@]}; do
  if [[ -e "$f" ]]; then
    rm -f "$f"
    print "[cleanup] removed: $f"
    ((removed++))
  else
    print "[cleanup] skip (not found): $f"
    ((skipped++))
  fi
done

print "[cleanup] Done. removed=$removed skipped=$skipped"
