"""Trace which cases survive for 'sexual harassment' query."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app.services.kanoon_adapter import get_all_cases
from app.services.tfidf_index import build_index, get_index
from app.config import CASE_EXCLUSION_KEYWORDS

cases = get_all_cases()
idx = build_index(cases)

query = "sexual harassment sexual harassment workplace harassment stalking vishaka"
results = idx.search(query, top_n=50, min_score=0.01)
print(f"Raw hits (min_score=0.01): {len(results)}")
for case, score, bd in results[:10]:
    blob = case.summary.lower() + " " + (case.case_name or "").lower()
    matched_kw = [kw for kw in CASE_EXCLUSION_KEYWORDS if kw in blob]
    print(f"  tfidf={bd['tfidf_score']:.4f}  excluded={matched_kw}")
    print(f"  name={case.case_name[:50]}")
    print(f"  keywords={case.keywords[:4]}")
