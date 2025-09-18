#!/usr/bin/env zsh
set -euo pipefail

# Cleanup script for removing compound search / strategic recommendation related files (MVP scope)
# Run from repository root

print "[cleanup] Starting removal of non-MVP features: 複合条件検索 / 戦略的推薦機能"

# Files to remove
typeset -a FILES=(
  backend/app/services/query_normalization_service.py
  backend/app/tests/integration/test_full_flow_integration.py
  backend/app/tests/performance/test_performance_quality_metrics.py
  backend/app/tests/services/test_aggregation_basic.py
  backend/app/tests/services/test_aggregation_comprehensive.py
  backend/app/tests/services/test_aggregation_queries.py
  backend/app/tests/services/test_aggregation_queries_fixed.py
  backend/app/tests/services/test_complex_numeric_patterns.py
  backend/app/tests/services/test_llm_service.py
)

# Use git rm when in a git repo; fallback to rm -f
use_git=0
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  use_git=1
fi

for f in ${FILES[@]}; do
  if [[ -e "$f" ]]; then
    if [[ $use_git -eq 1 ]]; then
      print "[cleanup] git rm $f"
      git rm -f "$f"
    else
      print "[cleanup] rm -f $f"
      rm -f "$f"
    fi
  else
    print "[cleanup] skip (not found): $f"
  fi
done

# Remove empty directories left behind
print "[cleanup] Removing empty directories under backend/app/tests/{services,performance,integration}"
for d in backend/app/tests/services backend/app/tests/performance backend/app/tests/integration; do
  [[ -d "$d" ]] && find "$d" -type d -empty -delete || true
done

print "[cleanup] Done. Review 'git status' and run tests: pytest backend/app/tests/test_mvp_chat_basic.py -q"
