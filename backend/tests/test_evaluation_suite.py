# -*- coding: utf-8 -*-
"""
Independent Evaluation & Automated Test Suite for KaushalSetu.
Covers all 12 mandatory validation scenarios:
1. Missing learner profile fields
2. No matching qualifications (gibberish/out-of-domain)
3. Ineligible learner (insufficient schooling & experience)
4. Unknown eligibility requirements (unspecified criteria)
5. Alternative eligibility routes (multi-clause NCVET logic)
6. Missing or stale source information (unlinked providers/fees)
7. Duplicate qualifications (disambiguation via display_title)
8. Empty skill lists (graceful defaults)
9. Invalid and unknown qualification IDs (404/safe lookup)
10. Ranking consistency and deterministic results (reproducibility)
11. Malformed API requests (validation errors)
12. No eligible results (all filtered out)

Also runs an audited IR benchmark using immutable qualification_id strings
and calculates P@3, P@5, R@5, MRR, Catalogue Coverage, and Eligibility Accuracy.
"""

import sys
import json
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.config import AUDIT_DIR
from backend.data_loader import DataLoader
from backend.recommendation_service import RecommendationService
from backend.schemas import LearnerProfileRequest
from backend.eligibility import evaluate_eligibility

class TestKaushalSetuIndependentEvaluation(unittest.TestCase):
    """Automated 12-scenario test suite."""

    @classmethod
    def setUpClass(cls):
        cls.loader = DataLoader.get_instance()
        cls.service = RecommendationService(data_loader=cls.loader)

    # 1. Missing learner profile fields
    def test_01_missing_learner_profile_fields(self):
        req = LearnerProfileRequest(existing_qualification=None, prior_experience_years=0.0)
        resp = self.service.get_recommendations(req)
        self.assertGreater(resp.results_returned, 0)
        # Verify unknown eligibility is not crashed or falsely confirmed
        for card in resp.recommendations:
            self.assertEqual(card.eligibility_status, 'UNKNOWN')

    # 2. No matching qualifications (out-of-domain query)
    def test_02_no_matching_qualifications_gibberish(self):
        req = LearnerProfileRequest(
            interests=["astrophysics quantum cryptography neurosurgery"],
            existing_qualification="10th"
        )
        resp = self.service.get_recommendations(req)
        self.assertIsInstance(resp.recommendations, list)
        # Even with zero lexical match, returns fallback catalogue items without crashing
        self.assertLessEqual(resp.results_returned, 5)

    # 3. Ineligible learner
    def test_03_ineligible_learner(self):
        # Learner with no schooling applying for Level 5 course
        status, reason, _ = evaluate_eligibility(
            "10th | Passed | 4 years; 12th | Passed | 1 year",
            existing_qualification="none",
            prior_experience_years=0.0
        )
        self.assertEqual(status, 'INELIGIBLE')
        self.assertIn("Does not meet alternative criteria", reason)

    # 4. Unknown eligibility requirements
    def test_04_unknown_eligibility_requirements(self):
        status, reason, _ = evaluate_eligibility(
            "",
            existing_qualification="10th",
            prior_experience_years=2.0
        )
        self.assertEqual(status, 'UNKNOWN')
        self.assertIn("unspecified", reason.lower())

    # 5. Alternative eligibility routes
    def test_05_alternative_eligibility_routes(self):
        clause = "10th | Passed | 4 years; 12th | Passed | 1 year | NTC/NAC; 8th | Passed | 6 years"
        
        # Pathway A: 12th pass with 1 year exp
        sA, rA, pathA = evaluate_eligibility(clause, existing_qualification="12th", prior_experience_years=1.0)
        self.assertEqual(sA, 'ELIGIBLE')
        self.assertIn("12th", pathA[0])

        # Pathway B: 8th pass with 6 years exp
        sB, rB, pathB = evaluate_eligibility(clause, existing_qualification="8th", prior_experience_years=6.0)
        self.assertEqual(sB, 'ELIGIBLE')
        self.assertIn("8th", pathB[0])

    # 6. Missing or stale source information
    def test_06_missing_source_information_handling(self):
        req = LearnerProfileRequest(
            interests=["welding"],
            existing_qualification="10th",
            prior_experience_years=4.0,
            exclude_unknown_location=False,
            exclude_unknown_fees=False
        )
        resp = self.service.get_recommendations(req)
        # Ensure unlinked options are preserved and labeled with missing info
        has_missing_info = any(len(c.missing_information) > 0 for c in resp.recommendations)
        self.assertTrue(has_missing_info)

    # 7. Duplicate qualifications disambiguation
    def test_07_duplicate_qualification_titles(self):
        cat = self.service.catalogue
        # Check that display_title is unique or clearly distinguished
        dups = cat[cat.duplicated('qualification_title', keep=False)]
        self.assertGreater(len(dups), 0)
        display_titles = dups['display_title'].tolist()
        self.assertEqual(len(display_titles), len(set(display_titles)), "Display titles must disambiguate duplicate titles")

    # 8. Empty skill lists
    def test_08_empty_skill_lists(self):
        req = LearnerProfileRequest(interests=[], preferred_activities=[], existing_qualification="10th")
        resp = self.service.get_recommendations(req)
        self.assertEqual(resp.results_returned, req.top_k)

    # 9. Invalid and unknown qualification IDs
    def test_09_invalid_and_unknown_qualification_ids(self):
        card = self.service.get_career_by_id("NON_EXISTENT_ID_99999")
        self.assertIsNone(card)

    # 10. Ranking consistency and deterministic results
    def test_10_ranking_consistency_and_determinism(self):
        req = LearnerProfileRequest(
            interests=["cnc operator", "lathe milling"],
            existing_qualification="10th",
            prior_experience_years=2.0,
            top_k=5
        )
        resp1 = self.service.get_recommendations(req)
        resp2 = self.service.get_recommendations(req)
        ids1 = [c.qualification_id for c in resp1.recommendations]
        ids2 = [c.qualification_id for c in resp2.recommendations]
        self.assertEqual(ids1, ids2)

    # 11. Malformed API requests (validation error handling)
    def test_11_malformed_request_validation(self):
        with self.assertRaises(Exception):
            # Negative experience years should trigger validation error
            LearnerProfileRequest(prior_experience_years=-5.0)

    # 12. No eligible results (all filtered out)
    def test_12_no_eligible_results_strict_mode(self):
        req = LearnerProfileRequest(
            interests=["welding"],
            existing_qualification="8th",
            prior_experience_years=0.0,
            max_duration_hours=5.0,  # Minimum course in catalogue is 30 hours, so 0 qualify
            exclude_unknown_eligibility=True,
            exclude_unknown_location=True
        )
        resp = self.service.get_recommendations(req)
        # Should return 0 results gracefully without crashing
        self.assertEqual(resp.results_returned, 0)


def run_benchmark_and_save():
    """
    Executes transparent evaluation benchmark using persistent qualification_id strings
    and saves report to outputs/audit/evaluation_benchmark_results.json.
    """
    loader = DataLoader.get_instance()
    service = RecommendationService(data_loader=loader)

    # Benchmark queries with documented relevance targets using persistent qualification_id
    # Note: These relevance targets were defined as synthetic expert heuristic references
    benchmark_definitions = [
        {
            "query_type": "Manufacturing / Thermal & Arc Trades",
            "query": "welding fabrication manual metal arc shielded gas",
            "relevant_qualification_ids": [
                "2022/CCM/CGSC/06612",          # Stainless Steel Fabricator
                "QG-02-CG-03939-2025-V2-CGSSC", # Assistant Manual Metal Arc Welding Welder
                "QG-03-CG-03940-2025-V2-CGSSC", # Manual Metal Arc Welding Welder
                "QG-05-CG-03945-2025-V2-CGSSC", # Stainless Steel Fabricator 2025
                "QG-04-CG-03944-2025-V2-CGSSC"  # Senior Welder
            ]
        },
        {
            "query_type": "Precision Machining / Subtractive",
            "query": "cnc lathe machine milling operator programmer precision",
            "relevant_qualification_ids": [
                "QG-4.5-CG-03188-2024-V2-DGT",   # MACHINIST & OPERATOR ADVANCE MACHINE TOOL
                "QG-05-CG-01976-2024-V1-CUTM",   # CNC Milling Programmer
                "QG-03-CG-02398-2024-V1-MSME.",  # ASST. OPERATOR - CNC MILLING (TOOL ROOM)
                "QG-4.5-CG-03193-2024-V2-DGT"    # TURNER
            ]
        },
        {
            "query_type": "Automation & Instrumentation",
            "query": "process control instrumentation valve calibration automation",
            "relevant_qualification_ids": [
                "2022/ETR/IASC/06501",           # Instrumentation Technician (Process Control)
                "2022/ETR/IASC/06497",           # Instrumentation Technician (Control Valve)
                "2022/ETR/IASC/06498"            # Junior Instrumentation Technician
            ]
        }
    ]

    p3_list, p5_list, r5_list, mrr_list = [], [], [], []
    retrieved_unique_ids = set()

    group_results = {}

    for b in benchmark_definitions:
        q_text = b["query"]
        rel_ids = set(b["relevant_qualification_ids"])
        
        req = LearnerProfileRequest(interests=[q_text], existing_qualification="10th", top_k=5)
        resp = service.get_recommendations(req)
        retrieved_ids = [c.qualification_id for c in resp.recommendations]
        retrieved_unique_ids.update(retrieved_ids)

        p3 = len(set(retrieved_ids[:3]).intersection(rel_ids)) / 3.0
        p5 = len(set(retrieved_ids[:5]).intersection(rel_ids)) / 5.0
        r5 = len(set(retrieved_ids[:5]).intersection(rel_ids)) / max(len(rel_ids), 1)

        rr = 0.0
        for rank, qid in enumerate(retrieved_ids, 1):
            if qid in rel_ids:
                rr = 1.0 / rank
                break

        p3_list.append(p3)
        p5_list.append(p5)
        r5_list.append(r5)
        mrr_list.append(rr)

        group_results[b["query_type"]] = {
            "query": q_text,
            "precision_at_3": round(p3, 3),
            "precision_at_5": round(p5, 3),
            "recall_at_5": round(r5, 3),
            "reciprocal_rank": round(rr, 3)
        }

    # Eligibility engine accuracy test
    elig_test_cases = [
        ("10th | Passed | 4 years", "10th", 4.0, "ELIGIBLE"),
        ("10th | Passed | 4 years", "10th", 0.0, "INELIGIBLE"),
        ("12th | Passed | 1 year", "12th", 1.0, "ELIGIBLE"),
        ("Ability to read and write | No Experience", "none", 0.0, "INELIGIBLE"),
        ("Ability to read and write | No Experience", "literate", 0.0, "ELIGIBLE"),
        ("", "10th", 2.0, "UNKNOWN"),
        ("8th | Passed | No Experience", None, 0.0, "UNKNOWN"),
    ]
    correct_elig = 0
    for clause, edu, exp, expected in elig_test_cases:
        status, _, _ = evaluate_eligibility(clause, existing_qualification=edu, prior_experience_years=exp)
        if status == expected:
            correct_elig += 1
    elig_accuracy = round(correct_elig / len(elig_test_cases), 4)

    benchmark_summary = {
        "evaluation_protocol": "Synthetic Expert-Annotated Heuristic Query Benchmark",
        "sample_size_queries": len(benchmark_definitions),
        "mean_precision_at_3": round(float(sum(p3_list) / len(p3_list)), 4),
        "mean_precision_at_5": round(float(sum(p5_list) / len(p5_list)), 4),
        "mean_recall_at_5": round(float(sum(r5_list) / len(r5_list)), 4),
        "mean_reciprocal_rank": round(float(sum(mrr_list) / len(mrr_list)), 4),
        "catalogue_coverage_count": len(retrieved_unique_ids),
        "catalogue_coverage_pct": round((len(retrieved_unique_ids) / len(service.catalogue)) * 100, 2),
        "eligibility_engine_unit_accuracy": elig_accuracy,
        "results_by_query_group": group_results,
        "limitations_and_caveats": [
            "Relevance labels represent internal engineering heuristics, NOT multi-annotator blind user trials.",
            "Queries are synthetic test archetypes representing broad trade domains.",
            "Metrics serve as non-regression unit tests, not validated production accuracy claims."
        ]
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = AUDIT_DIR / "evaluation_benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_summary, f, indent=2)

    print(f"Benchmark results saved to {out_file}.")
    return benchmark_summary

if __name__ == "__main__":
    print("=" * 65)
    print("RUNNING 12-SCENARIO AUTOMATED EVALUATION SUITE")
    print("=" * 65)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKaushalSetuIndependentEvaluation)
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)
    
    if test_result.wasSuccessful():
        print("\nALL 12 SCENARIO TESTS PASSED.")
        print("\nRUNNING BENCHMARK EVALUATION...")
        summary = run_benchmark_and_save()
        print(json.dumps(summary, indent=2))
    else:
        print("\nUNIT TESTS FAILED.")
        sys.exit(1)
