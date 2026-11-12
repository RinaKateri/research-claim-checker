"""Small verdict-accuracy evaluation using the existing claim checker."""

import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from lmnr import Laminar, evaluate

from claim_checker import check_claim

ROOT = Path(__file__).resolve().parent

CASES = [
    {
        "data": {
            "paper_id": "fictional-webcam-001",
            "claim": "The method was tested on seated participants",
        },
        "target": "supported",
    },
    {
        "data": {
            "paper_id": "fictional-webcam-001",
            "claim": "The study included 100 adult participants",
        },
        "target": "contradicted",
    },
    {
        "data": {
            "paper_id": "fictional-webcam-001",
            "claim": "The method accurately estimates heart rate during exercise",
        },
        "target": "insufficient_evidence",
    },
    {
        "data": {
            "paper_id": "fictional-seedling-002",
            "claim": "Seedlings receiving 12 hours of light had greater mean height than those receiving 8 hours",
        },
        "target": "supported",
    },
    {
        "data": {
            "paper_id": "fictional-seedling-002",
            "claim": "Fertilizer was used in both groups",
        },
        "target": "contradicted",
    },
    {
        "data": {
            "paper_id": "fictional-seedling-002",
            "claim": "The 12-hour lighting schedule improves basil growth outdoors",
        },
        "target": "insufficient_evidence",
    },
]


def executor(data):
    return check_claim(data["paper_id"], data["claim"])


def verdict_accuracy(output, target):
    return int(output["verdict"] == target)


def main():
    load_dotenv(ROOT / ".env")
    for name in ("OPENAI_API_KEY", "LMNR_PROJECT_API_KEY"):
        if not os.getenv(name):
            raise SystemExit(f"Missing {name}; configure it in local .env.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    print("Running 6 cases, one trial each; 12 OpenAI requests expected.")
    try:
        evaluate(
            data=CASES,
            executor=executor,
            evaluators={"verdict_accuracy": verdict_accuracy},
            name=f"baseline-{timestamp}",
            group_name="claim-checker-verdict",
            concurrency_limit=1,
            trials=1,
            project_api_key=os.environ["LMNR_PROJECT_API_KEY"],
            metadata={
                "prompt_version": "baseline",
                "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                "dataset_version": "fictional-six-v1",
            },
        )
    finally:
        Laminar.flush()


if __name__ == "__main__":
    main()
