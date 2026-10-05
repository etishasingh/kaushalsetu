# -*- coding: utf-8 -*-
"""
API Integration Tests for KaushalSetu FastAPI Application.
Validates HTTP endpoints, status codes, response schemas, and error handling.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

class TestKaushalSetuAPI(unittest.TestCase):
    """Integration test suite for FastAPI REST endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        """GET /health must return 200 with loaded catalogue status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["catalogue_loaded"])
        self.assertGreater(data["total_qualifications"], 0)
        self.assertTrue(data["vectorizer_loaded"])

    def test_list_careers_endpoint(self):
        """GET /api/careers must support pagination and filtering."""
        response = self.client.get("/api/careers?page=1&page_size=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_count", data)
        self.assertEqual(len(data["items"]), 10)
        self.assertEqual(data["page"], 1)

    def test_get_career_details_valid(self):
        """GET /api/careers/{id} with valid ID returns 200 and details."""
        valid_id = "2022/CCM/CGSC/06612"
        response = self.client.get(f"/api/careers/{valid_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["qualification_id"], valid_id)
        self.assertIn("Stainless Steel Fabricator", data["qualification_title"])

    def test_get_career_details_invalid_404(self):
        """GET /api/careers/{id} with nonexistent ID returns 404."""
        response = self.client.get("/api/careers/NON_EXISTENT_ID_000")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("detail", data)

    def test_post_recommendations_valid(self):
        """POST /api/recommendations with valid profile returns ranked cards."""
        payload = {
            "interests": ["welding", "fabrication"],
            "preferred_activities": ["metal arc cutting"],
            "existing_qualification": "10th",
            "prior_experience_years": 4.0,
            "current_district": "Kanpur Nagar",
            "current_state": "Uttar Pradesh",
            "willingness_to_relocate": "within_district",
            "max_duration_hours": 600.0,
            "max_budget_inr": 0.0,
            "top_k": 3
        }
        response = self.client.post("/api/recommendations", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recommendations", data)
        self.assertEqual(len(data["recommendations"]), 3)
        top_card = data["recommendations"][0]
        self.assertIn("hybrid_score", top_card)
        self.assertIn("eligibility_status", top_card)
        self.assertIn("explanation_english", top_card)

    def test_post_recommendations_malformed_input(self):
        """POST /api/recommendations with negative experience returns 422 Unprocessable Entity."""
        bad_payload = {
            "interests": ["welding"],
            "prior_experience_years": -10.0  # Invalid per pydantic ge=0.0
        }
        response = self.client.post("/api/recommendations", json=bad_payload)
        self.assertEqual(response.status_code, 422)

    def test_pagination_invalid_page_zero(self):
        """GET /api/careers?page=0 must return 422 validation error."""
        response = self.client.get("/api/careers?page=0")
        self.assertEqual(response.status_code, 422)

    def test_pagination_invalid_pagesize_too_large(self):
        """GET /api/careers?page_size=150 must return 422 validation error."""
        response = self.client.get("/api/careers?page_size=150")
        self.assertEqual(response.status_code, 422)

    def test_pagination_out_of_bounds_returns_empty_items(self):
        """GET /api/careers?page=999 returns 200 with empty items list."""
        response = self.client.get("/api/careers?page=999&page_size=20")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["items"], [])
        self.assertGreater(data["total_count"], 0)

    def test_post_recommendations_null_and_extra_fields(self):
        """POST /api/recommendations handles null lists and unexpected extra fields gracefully."""
        payload = {
            "interests": None,
            "preferred_activities": None,
            "existing_qualification": "10th",
            "prior_experience_years": 0.0,
            "unexpected_custom_attribute": "this_should_be_ignored_safely"
        }
        response = self.client.post("/api/recommendations", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["results_returned"], 0)

    def test_post_recommendations_empty_object(self):
        """POST /api/recommendations with empty object {} succeeds with UNKNOWN eligibility."""
        response = self.client.post("/api/recommendations", json={})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["results_returned"], 0)
        for card in data["recommendations"]:
            self.assertEqual(card["eligibility_status"], "UNKNOWN")

    def test_error_handling_no_leaked_paths_or_tracebacks(self):
        """Verify 404 and 422 responses do not leak local filesystem paths or stack traces."""
        # 404 test
        res_404 = self.client.get("/api/careers/NON_EXISTENT_ID")
        self.assertEqual(res_404.status_code, 404)
        body_404 = res_404.text
        self.assertNotIn("Traceback", body_404)
        self.assertNotIn("c:\\Users\\", body_404)
        self.assertNotIn("/Users/", body_404)

        # 422 test
        res_422 = self.client.post("/api/recommendations", json={"prior_experience_years": -5.0})
        self.assertEqual(res_422.status_code, 422)
        body_422 = res_422.text
        self.assertNotIn("Traceback", body_422)
        self.assertNotIn("c:\\Users\\", body_422)

    def test_counsellor_chat_requirement_inquiry(self):
        """POST /api/counsellor/chat returns grounded NCVET admission clauses for qualification inquiry."""
        payload = {
            "message": "What are the entry requirements for Stainless Steel Fabricator?",
            "language": "English"
        }
        res = self.client.post("/api/counsellor/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["identified_intent"], "eligibility_requirement")
        self.assertEqual(data["mode"], "grounded_knowledge_base")
        self.assertTrue(data["verified_facts_present"])
        self.assertIn("Entry Requirements", data["answer"])
        self.assertGreater(len(data["retrieved_evidence_summary"]), 0)

    def test_counsellor_chat_comparison(self):
        """POST /api/counsellor/chat compares two qualifications objectively with trade-offs."""
        payload = {
            "message": "Compare Stainless Steel Fabricator vs CNC Milling Operator",
            "language": "English"
        }
        res = self.client.post("/api/counsellor/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["identified_intent"], "comparison")
        self.assertIn("Comparative Evaluation", data["answer"])
        self.assertIn("NSQF Level", data["answer"])

    def test_counsellor_chat_fee_subsidy(self):
        """POST /api/counsellor/chat explains PMKVY subsidy and discloses unlinked centre fees."""
        payload = {
            "message": "Is training fee subsidized under PMKVY 4.0 for welding?",
            "language": "English"
        }
        res = self.client.post("/api/counsellor/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["identified_intent"], "fee_subsidy")
        self.assertIn("PMKVY 4.0", data["answer"])

    def test_counsellor_chat_missing_out_of_domain(self):
        """POST /api/counsellor/chat honestly reports out-of-domain/missing data without hallucination."""
        payload = {
            "message": "What is the placement percentage for quantum computing marine archaeology?",
            "language": "English"
        }
        res = self.client.post("/api/counsellor/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["verified_facts_present"])
        self.assertIn("Topic Not Present", data["answer"])

    def test_counsellor_chat_empty_message_validation(self):
        """POST /api/counsellor/chat with empty string fails with 422 Unprocessable Entity."""
        res = self.client.post("/api/counsellor/chat", json={"message": ""})
        self.assertEqual(res.status_code, 422)

if __name__ == "__main__":
    unittest.main()
