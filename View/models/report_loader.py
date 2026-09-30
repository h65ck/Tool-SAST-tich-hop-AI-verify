import json
import os
from pathlib import Path

class ReportLoader:
    def __init__(self, report_path: str):
        self.report_path = Path(report_path)
        # Store next to the report
        self.review_path = self.report_path.parent / "report.review.json"
        self.data = {"summary": {}, "findings": []}
        self.reviews = {}
        self.load_report()
        self.load_reviews()

    def load_report(self):
        if self.report_path.exists():
            try:
                with open(self.report_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                self.data = {"summary": {"error": str(e)}, "findings": []}
        else:
            self.data = {"summary": {"error": f"File {self.report_path} not found"}, "findings": []}

    def save_report_data(self):
        try:
            with open(self.report_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def load_reviews(self):
        if self.review_path.exists():
            try:
                with open(self.review_path, "r", encoding="utf-8") as f:
                    reviews_data = json.load(f)
                    # JSON keys are always strings, convert to integer IDs to match findings
                    self.reviews = {int(k): v for k, v in reviews_data.items()}
            except Exception:
                self.reviews = {}
        else:
            self.reviews = {}

    def save_review(self, finding_id: int, status: str):
        # status can be: "TP" (Confirmed True Positive), "FP" (False Positive), "REV" (Need Review)
        self.reviews[finding_id] = status
        try:
            reviews_to_save = {str(k): v for k, v in self.reviews.items()}
            with open(self.review_path, "w", encoding="utf-8") as f:
                json.dump(reviews_to_save, f, indent=2)
        except Exception:
            pass

    def get_findings(self):
        return self.data.get("findings", [])

    def get_summary(self):
        return self.data.get("summary", {})

    def get_review_status(self, finding_id: int) -> str:
        return self.reviews.get(finding_id, "Untriaged")

    def get_review_display(self, finding_id: int) -> str:
        status = self.get_review_status(finding_id)
        mapping = {
            "TP": "Confirmed True Positive",
            "FP": "False Positive",
            "REV": "Need Review",
            "Untriaged": "Untriaged"
        }
        return mapping.get(status, "Untriaged")

    def get_finding_by_id(self, finding_id: int):
        for f in self.get_findings():
            if f.get("id") == finding_id:
                return f
        return None
