#!/usr/bin/env zsh
set -euo pipefail

# cleanup targets (files)
FILES=(
  backend/app/routers/mvp_chat.py
  backend/app/services/hybrid_search_service.py
  backend/app/services/classification_service.py
  backend/app/models/classification_models.py
  backend/app/tests/services/test_hybrid_search_consolidated.py
  backend/app/tests/services/test_classification_consolidated.py
  backend/app/tests/services/test_classification_aggregation.py
  backend/app/tests/services/test_rag_service_basic.py
  backend/app/tests/services/test_rag_service_additional.py
  backend/app/tests/services/test_embedding_consolidated.py
  docker-compose.monitoring.yml
  docs/guides/search-hybrid-guide.md
  docs/guides/search_result_detail_refactor.md
  docs/sphinx_docs/services/hybrid_search_service.rst
  docs/sphinx_docs/services/classification_service.rst
)

# cleanup targets (directories)
DIRS=(
  monitoring
)

removed_files=()
for f in $FILES; do
  if [[ -e "$f" ]]; then
    if git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
      git rm -f "$f" >/dev/null 2>&1 || rm -f "$f"
    else
      rm -f "$f"
    fi
    removed_files+="$f"
  fi
done

removed_dirs=()
for d in $DIRS; do
  if [[ -d "$d" ]]; then
    if git ls-files --error-unmatch "$d" >/dev/null 2>&1; then
      git rm -r -f "$d" >/dev/null 2>&1 || rm -rf "$d"
    else
      rm -rf "$d"
    fi
    removed_dirs+="$d"
  fi
done

print "[cleanup] removed files:"; for x in $removed_files; do print "  - $x"; done
print "[cleanup] removed dirs:"; for x in $removed_dirs; do print "  - $x"; done

print "[cleanup] done. You can now run backend tests."
