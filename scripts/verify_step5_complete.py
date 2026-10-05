# -*- coding: utf-8 -*-
"""
Verification Script for Step 5: Complete Application Testing.
Performs real HTTP requests against running FastAPI backend for all 9 specified test conditions:
1. Health status.
2. Career catalogue browsing.
3. A valid recommendation request.
4. An incomplete learner profile.
5. An unknown eligibility case.
6. A qualification-detail lookup.
7. A grounded counsellor question.
8. A question whose answer is missing from the datasets.
9. Invalid requests and backend errors.
"""

import sys
import json
import httpx
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 70)
    print("STEP 5: COMPLETE END-TO-END APPLICATION HTTP VERIFICATION")
    print(f"Target Server: {BASE_URL}")
    print("=" * 70)

    client = httpx.Client(timeout=10.0)
    results = {}

    # 1. Health status
    print("\n[1/9] Testing GET /health...")
    r1 = client.get(f"{BASE_URL}/health")
    print(f"Status: {r1.status_code} | Body: {r1.json()}")
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}"
    results["1_health_status"] = {"status": r1.status_code, "data": r1.json()}

    # 2. Career catalogue browsing
    print("\n[2/9] Testing GET /api/careers (Paginated)...")
    r2 = client.get(f"{BASE_URL}/api/careers?page=1&page_size=5")
    print(f"Status: {r2.status_code} | Total: {r2.json()['total_count']} | Items returned: {len(r2.json()['items'])}")
    assert r2.status_code == 200
    assert len(r2.json()['items']) == 5
    results["2_catalogue_browsing"] = {"status": r2.status_code, "total_count": r2.json()['total_count'], "sample_title": r2.json()['items'][0]['qualification_title']}

    # 3. Valid recommendation request
    print("\n[3/9] Testing POST /api/recommendations (Valid Profile)...")
    p3 = {
        "interests": ["welding", "fabrication"],
        "preferred_activities": ["manual metal arc welding"],
        "existing_qualification": "10th",
        "prior_experience_years": 4.0,
        "current_district": "Kanpur Nagar",
        "current_state": "Uttar Pradesh",
        "top_k": 3
    }
    r3 = client.post(f"{BASE_URL}/api/recommendations", json=p3)
    print(f"Status: {r3.status_code} | Recommendations returned: {r3.json()['results_returned']}")
    assert r3.status_code == 200
    assert r3.json()['results_returned'] == 3
    results["3_valid_recommendation"] = {
        "status": r3.status_code,
        "top_match": r3.json()['recommendations'][0]['qualification_title'],
        "top_score": r3.json()['recommendations'][0]['hybrid_score'],
        "eligibility": r3.json()['recommendations'][0]['eligibility_status']
    }

    # 4. Incomplete learner profile (education missing)
    print("\n[4/9] Testing POST /api/recommendations (Incomplete Profile: null education)...")
    p4 = {
        "interests": ["automotive"],
        "existing_qualification": None,
        "prior_experience_years": 2.0
    }
    r4 = client.post(f"{BASE_URL}/api/recommendations", json=p4)
    print(f"Status: {r4.status_code} | Recommendations returned: {r4.json()['results_returned']}")
    assert r4.status_code == 200
    # Every card must be UNKNOWN
    for card in r4.json()['recommendations']:
        assert card['eligibility_status'] == 'UNKNOWN', f"Expected UNKNOWN, got {card['eligibility_status']}"
    results["4_incomplete_profile"] = {"status": r4.status_code, "all_unknown": True, "reason": r4.json()['recommendations'][0]['eligibility_reason']}

    # 5. Unknown eligibility requirement case
    print("\n[5/9] Testing Unknown Eligibility Requirements...")
    # Profile with no schooling exploring standard courses
    p5 = {
        "interests": ["sheet metal"],
        "existing_qualification": "none",
        "exclude_unknown_eligibility": False
    }
    r5 = client.post(f"{BASE_URL}/api/recommendations", json=p5)
    print(f"Status: {r5.status_code} | Recommendations returned: {r5.json()['results_returned']}")
    assert r5.status_code == 200
    results["5_unknown_eligibility_case"] = {"status": r5.status_code, "returned_count": r5.json()['results_returned']}

    # 6. Qualification-detail lookup
    print("\n[6/9] Testing GET /api/careers/{id} (Stainless Steel Fabricator)...")
    qid = "2022/CCM/CGSC/06612"
    r6 = client.get(f"{BASE_URL}/api/careers/{qid}")
    print(f"Status: {r6.status_code} | Title: {r6.json()['qualification_title']} | Awarding: {r6.json()['awarding_body']}")
    assert r6.status_code == 200
    assert r6.json()['qualification_id'] == qid
    results["6_qualification_detail_lookup"] = {
        "status": r6.status_code,
        "qualification_id": qid,
        "title": r6.json()['qualification_title'],
        "nsqf": r6.json()['nsqf_level'],
        "nqr_url": r6.json()['source_nqr_url']
    }

    # 7. Grounded counsellor question
    print("\n[7/9] Testing POST /api/counsellor/chat (Grounded requirement question)...")
    p7 = {"message": "What are the entry requirements for Stainless Steel Fabricator?"}
    r7 = client.post(f"{BASE_URL}/api/counsellor/chat", json=p7)
    print(f"Status: {r7.status_code} | Intent: {r7.json()['identified_intent']} | Verified Facts: {r7.json()['verified_facts_present']}")
    assert r7.status_code == 200
    assert r7.json()['identified_intent'] == "eligibility_requirement"
    assert r7.json()['verified_facts_present'] == True
    results["7_grounded_counsellor_question"] = {
        "status": r7.status_code,
        "intent": r7.json()['identified_intent'],
        "mode": r7.json()['mode'],
        "answer_snippet": r7.json()['answer'][:200] + "..."
    }

    # 8. Question whose answer is missing from the datasets
    print("\n[8/9] Testing POST /api/counsellor/chat (Out of domain / missing data)...")
    p8 = {"message": "What is the placement percentage for quantum computing marine archaeology?"}
    r8 = client.post(f"{BASE_URL}/api/counsellor/chat", json=p8)
    print(f"Status: {r8.status_code} | Intent: {r8.json()['identified_intent']} | Verified Facts: {r8.json()['verified_facts_present']}")
    assert r8.status_code == 200
    assert r8.json()['verified_facts_present'] == False
    assert "Topic Not Present" in r8.json()['answer']
    results["8_missing_dataset_question"] = {
        "status": r8.status_code,
        "verified_facts_present": False,
        "answer_snippet": r8.json()['answer'][:200] + "..."
    }

    # 9. Invalid requests and backend errors
    print("\n[9/9] Testing Invalid Requests & Error Handling...")
    r9_404 = client.get(f"{BASE_URL}/api/careers/INVALID_ID_99999")
    print(f"Nonexistent ID: HTTP {r9_404.status_code} (Expected 404)")
    assert r9_404.status_code == 404

    r9_422_exp = client.post(f"{BASE_URL}/api/recommendations", json={"prior_experience_years": -10.0})
    print(f"Negative Experience: HTTP {r9_422_exp.status_code} (Expected 422)")
    assert r9_422_exp.status_code == 422

    r9_422_page = client.get(f"{BASE_URL}/api/careers?page=0")
    print(f"Page 0: HTTP {r9_422_page.status_code} (Expected 422)")
    assert r9_422_page.status_code == 422

    r9_422_chat = client.post(f"{BASE_URL}/api/counsellor/chat", json={"message": ""})
    print(f"Empty Chat Message: HTTP {r9_422_chat.status_code} (Expected 422)")
    assert r9_422_chat.status_code == 422

    results["9_invalid_requests_and_errors"] = {
        "404_nonexistent_id": r9_404.status_code,
        "422_negative_experience": r9_422_exp.status_code,
        "422_page_zero": r9_422_page.status_code,
        "422_empty_chat_message": r9_422_chat.status_code
    }

    print("\n" + "=" * 70)
    print("ALL 9 TEST SCENARIOS EXECUTED AND PASSED SUCCESSFULLY!")
    print("=" * 70)

    # Save results
    out_path = Path(__file__).resolve().parent.parent / "outputs" / "audit" / "step5_verification_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved test run results to: {out_path}")

if __name__ == "__main__":
    run_tests()
