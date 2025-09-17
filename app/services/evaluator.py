import time, logging, json
from app.services.judge0_client import execute_code
from typing import List, Dict, Any

log = logging.getLogger("evaluator")

def _normalize_output(s: str)-> str:
    if s is None:
        return ""
    
    return "\n".join([line.rstrip() for line in s.strip().splitlines()]).strip()


def _compare_outputs(expected_output: str, actual_output: str, numeric_tolerance: float = 1e-6) -> bool:
    exp = _normalize_output(expected_output)
    act = _normalize_output(actual_output)

    try:
        if exp != "" and act != "":
            fe = float(exp)
            fa = float(act)

            return abs(fe - fa) <= numeric_tolerance
    except Exception:
        pass
    return exp == act

def run_tests_for_submission(src_code: str, language_id: int, testcases: List[Dict[str, str]]) -> Dict[str, Any]:

    results = []
    start = time.time()
    passed = 0
    for idx, tc in enumerate(testcases):
        stdin = tc.get("input", "")
        expected = tc.get("output", "")

        try:
            res = execute_code(src_code, language_id, stdin, expected)
        except Exception as e:
            log.exception("Judge0 failed for testcase %s", idx)
            res = {"stdout": None, "stderr": str(e), "status": {"id": -1, "description": "ExecutionError"}, "time": None, "memory": None}

        ok = False
        stdout = res.get("stdout")
        ok = _compare_outputs(expected, stdout)
        results.append({
            "index": idx,
            "stdin": stdin,
            "expected": expected,
            "stdout": stdout,
            "stderr": res.get("stderr"),
            "status": res.get("status"),
            "time": res.get("time"),
            "memory": res.get("memory"),
            "passed": ok
        })
        if ok:
            passed += 1
    
    total = len(testcases)
    score = (passed / total) * 100 if total > 0 else 0.0
    duration = time.time() - start
    return {
        "total": total,
        "passed": passed,
        "score_percent": score,
        "duration_s": duration,
        "tests": results
    }

# Backward-compatible alias
run_test_for_submission = run_tests_for_submission
