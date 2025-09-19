from app.db.db import SessionLocal
from sqlalchemy import func
from app.db.models import Submission, SubmissionTest, Question
from collections import defaultdict

def compute_weak_topics(user_id: int, min_attempts: int = 3, threshold: float = 0.7):
    db = SessionLocal()
    try:
        subs = db.query(Submission).filter(Submission.user_id==user_id).all()
        topics_stats = defaultdict(lambda: {"attempts": 0, "passed": 0})
        for s in subs:
            q = db.get(Question, s.question_id)
            if not q or not q.topics:
                continue
            passed = s.passed
            total = s.total if s.total else 0
            for topic in q.topics:
                topics_stats[topic]["attempts"] += total
                topics_stats[topic]["passed"] += passed

            ret = []

            for topics, v in topics_stats.items():
                attempts = v["attempts"]
                passed = v["passed"]
                if attempts >= min_attempts:
                    acc = passed/attempts if attempts > 0 else 0.0
                    if acc < threshold:
                        ret.append({"topic": topic, "attempts": attempts, "accuracy": acc})

            ret.sort(key = lambda x: x["accuracy"])
            return ret
    
    finally:
        db.close()
