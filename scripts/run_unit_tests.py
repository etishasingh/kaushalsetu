# -*- coding: utf-8 -*-
"""
Unit Tests for KaushalSetu Recommendation Engine
Covers:
1. Eligibility parsing & education ladder logic
2. Constraint checking (education, location, duration, budget)
3. Unknown-field handling & non-discarding guarantees
4. Hybrid ranking score boundedness and weight normalization
5. Graceful handling of empty or missing query inputs
"""

import unittest
import numpy as np
import pandas as pd
from test_engine import (
    LearnerPreference,
    parse_clause,
    evaluate_eligibility,
    evaluate_location_constraint,
    evaluate_duration_constraint,
    evaluate_budget_constraint,
    build_career_catalogue,
    HybridRecommender,
    ContentBasedRetriever,
    SemanticRetriever,
    normalize_text
)

class TestKaushalSetuRecommendationEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.catalogue = build_career_catalogue()
        cls.recommender = HybridRecommender(cls.catalogue)

    def test_text_normalization(self):
        """Ensures technical abbreviations, spaces, and casing are preserved cleanly."""
        raw = "  CNC Milling & TIG • Welding \u00a0 Level 4  \r\n"
        norm = normalize_text(raw)
        self.assertEqual(norm, "CNC Milling & TIG Welding Level 4")

    def test_eligibility_ladder_parsing(self):
        """Tests education hierarchy logic and alternative pathways."""
        clause = "10th | Passed | 4 years; 12th | Passed | 1 year"
        
        # 10th pass learner with 0 experience -> Ineligible
        learner_10_0 = LearnerPreference(existing_qualification='10th', prior_experience_years=0.0)
        status, reason = evaluate_eligibility(clause, learner_10_0)
        self.assertEqual(status, 'INELIGIBLE')
        self.assertIn('needs 4.0 yrs exp', reason)

        # 10th pass learner with 4 years experience -> Eligible
        learner_10_4 = LearnerPreference(existing_qualification='10th', prior_experience_years=4.0)
        status, reason = evaluate_eligibility(clause, learner_10_4)
        self.assertEqual(status, 'ELIGIBLE')
        self.assertIn('10th | Passed | 4 years', reason)

        # 12th pass learner with 1 year experience -> Eligible
        learner_12_1 = LearnerPreference(existing_qualification='12th', prior_experience_years=1.0)
        status, reason = evaluate_eligibility(clause, learner_12_1)
        self.assertEqual(status, 'ELIGIBLE')
        self.assertIn('12th | Passed | 1 year', reason)

    def test_unknown_eligibility_handling(self):
        """Verifies that missing eligibility criteria returns UNKNOWN and is not silently disqualified."""
        learner = LearnerPreference(existing_qualification='10th')
        status, reason = evaluate_eligibility('', learner)
        self.assertEqual(status, 'UNKNOWN')
        self.assertIn('unspecified', reason.lower())

        status, reason = evaluate_eligibility(None, learner)
        self.assertEqual(status, 'UNKNOWN')

    def test_location_constraints(self):
        """Tests confirmed vs unlinked provider location checking."""
        learner_kanpur = LearnerPreference(
            current_district='Kanpur Nagar',
            current_state='Uttar Pradesh',
            willingness_to_relocate='within_district'
        )
        
        # Row with linked provider in Kanpur
        row_kanpur = pd.Series({
            'provider_district_list': ['Kanpur Nagar'],
            'provider_state_list': ['Uttar Pradesh']
        })
        status, reason = evaluate_location_constraint(row_kanpur, learner_kanpur)
        self.assertEqual(status, 'ELIGIBLE')
        self.assertIn('Direct center available in Kanpur Nagar', reason)

        # Row with unlinked provider (unknown location)
        row_unlinked = pd.Series({
            'provider_district_list': [],
            'provider_state_list': []
        })
        status, reason = evaluate_location_constraint(row_unlinked, learner_kanpur)
        self.assertEqual(status, 'UNKNOWN')
        self.assertIn('Centre locations not linked', reason)

        # Row with provider in distant district when unwilling to relocate
        row_pune = pd.Series({
            'provider_district_list': ['Pune'],
            'provider_state_list': ['Maharashtra']
        })
        status, reason = evaluate_location_constraint(row_pune, learner_kanpur)
        self.assertEqual(status, 'INELIGIBLE')

    def test_duration_constraints(self):
        """Tests duration constraints with numeric hours and missing durations."""
        learner = LearnerPreference(max_duration_hours=600.0)

        # Under budget
        row_ok = pd.Series({'duration_expected_hours': 390.0})
        status, reason = evaluate_duration_constraint(row_ok, learner)
        self.assertEqual(status, 'ELIGIBLE')

        # Exceeds budget
        row_exceed = pd.Series({'duration_expected_hours': 1200.0})
        status, reason = evaluate_duration_constraint(row_exceed, learner)
        self.assertEqual(status, 'INELIGIBLE')

        # Missing duration
        row_missing = pd.Series({'duration_expected_hours': np.nan})
        status, reason = evaluate_duration_constraint(row_missing, learner)
        self.assertEqual(status, 'UNKNOWN')

    def test_budget_constraints(self):
        """Tests fee verification and government funded programs."""
        learner_free_only = LearnerPreference(max_budget_inr=0.0)

        # Government funded (PMKVY free)
        row_free = pd.Series({'fee_amount_min': 0.0, 'fee_text': 'Government Funded (PMKVY 4.0)'})
        status, reason = evaluate_budget_constraint(row_free, learner_free_only)
        self.assertEqual(status, 'ELIGIBLE')

        # Paid course exceeding budget
        row_paid = pd.Series({'fee_amount_min': 18500.0, 'fee_text': '₹18,500'})
        status, reason = evaluate_budget_constraint(row_paid, learner_free_only)
        self.assertEqual(status, 'INELIGIBLE')

        # Unknown fee
        row_unknown = pd.Series({'fee_amount_min': np.nan, 'fee_text': 'Unknown'})
        status, reason = evaluate_budget_constraint(row_unknown, learner_free_only)
        self.assertEqual(status, 'UNKNOWN')

    def test_unknown_fields_non_discarding_policy(self):
        """
        Critical Responsible AI Test:
        Verifies that options with unknown location or fees are NOT discarded
        by default, but ARE filtered if learner explicitly requests exclusion.
        """
        learner_default = LearnerPreference(
            interests=['welding'],
            current_district='Kanpur Nagar',
            max_budget_inr=0.0,
            exclude_unknown_location=False,
            exclude_unknown_fees=False
        )
        recs_default = self.recommender.recommend(learner_default, top_k=10)
        has_unknown_location = any(r['location_status'] == 'UNKNOWN' for r in recs_default)
        has_unknown_fee = any(r['fee_status'] == 'UNKNOWN' for r in recs_default)
        self.assertTrue(has_unknown_location, "Catalogue options with unknown location should not be silently discarded by default")
        self.assertTrue(has_unknown_fee, "Catalogue options with unknown fee should not be silently discarded by default")

        # Now test with strict exclusion flag
        learner_strict = LearnerPreference(
            interests=['welding'],
            current_district='Kanpur Nagar',
            max_budget_inr=0.0,
            exclude_unknown_location=True,
            exclude_unknown_fees=True
        )
        recs_strict = self.recommender.recommend(learner_strict, top_k=10)
        for r in recs_strict:
            self.assertNotEqual(r['location_status'], 'UNKNOWN')
            self.assertNotEqual(r['fee_status'], 'UNKNOWN')

    def test_ranking_score_boundedness_and_weights(self):
        """Verifies that all hybrid scores are strictly bounded in [0, 1] and weights sum to 1."""
        self.assertAlmostEqual(sum(self.recommender.weights.values()), 1.0, places=5)
        
        learner = LearnerPreference(
            interests=['machining', 'cnc'],
            preferred_activities=['lathe operation', 'precision cutting'],
            existing_qualification='10th',
            prior_experience_years=2.0
        )
        recs = self.recommender.recommend(learner, top_k=5)
        for r in recs:
            score = r['hybrid_score']
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
            for comp_name, comp_val in r['score_breakdown'].items():
                self.assertGreaterEqual(comp_val, 0.0)
                self.assertLessEqual(comp_val, 1.0)

    def test_graceful_handling_of_empty_inputs(self):
        """Ensures recommender handles empty interests/activities without crashing."""
        learner_empty = LearnerPreference(interests=[], preferred_activities=[])
        recs = self.recommender.recommend(learner_empty, top_k=3)
        self.assertIsInstance(recs, list)
        self.assertEqual(len(recs), 3)

if __name__ == '__main__':
    unittest.main()
