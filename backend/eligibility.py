# -*- coding: utf-8 -*-
"""
Rule-Based Eligibility and Constraint Engine for KaushalSetu.
Evaluates multi-clause NCVET admission criteria, location proximity, duration windows,
and voluntary fee constraints with strict guarantees on handling UNKNOWN information.
"""

import re
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List
from backend.config import EDUCATION_LEVELS

def parse_clause(clause_str: str) -> Dict[str, Any]:
    """
    Parses an individual NCVET qualification admission clause.
    Example: '10th | Passed | 4 years' or 'Ability to read and write | No Experience'
    """
    parts = [p.strip() for p in str(clause_str).split('|')]
    edu_raw = parts[0] if len(parts) > 0 else ''
    status = parts[1] if len(parts) > 1 else ''
    exp_raw = parts[2] if len(parts) > 2 else ''
    
    # Extract years of required experience
    exp_req = 0.0
    exp_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:year|yr)', exp_raw.lower())
    if exp_match:
        exp_req = float(exp_match.group(1))
    elif 'no experience' in exp_raw.lower():
        exp_req = 0.0
        
    # Extract required education level from hierarchy
    req_level = 0
    edu_lower = edu_raw.lower()
    for key, lvl in sorted(EDUCATION_LEVELS.items(), key=lambda x: -len(x[0])):
        if key in edu_lower:
            req_level = max(req_level, lvl)
            break
            
    # Extract required prior NSQF level if specified
    req_nsqf = None
    nsqf_match = re.search(r'level\s*([0-9]+(?:\.[0-9]+)?)', (edu_raw + ' ' + status).lower())
    if nsqf_match:
        req_nsqf = float(nsqf_match.group(1))
        
    return {
        'edu_raw': edu_raw,
        'req_edu_level': req_level,
        'req_exp_years': exp_req,
        'req_nsqf': req_nsqf,
        'raw_clause': str(clause_str).strip()
    }

def evaluate_eligibility(eligibility_str: str,
                         existing_qualification: str = None,
                         prior_experience_years: float = 0.0,
                         prior_nsqf_level: float = None) -> Tuple[str, str, List[str]]:
    """
    Evaluates multi-clause NCVET entry requirements against a learner's profile.
    Returns: (status: 'ELIGIBLE'|'INELIGIBLE'|'UNKNOWN', reason: str, eligible_pathways: list)
    """
    # 1. Missing catalogue requirements
    if not eligibility_str or pd.isna(eligibility_str) or str(eligibility_str).strip() == '':
        return ('UNKNOWN', 'Eligibility criteria unspecified in official catalogue record.', [])
    
    # 2. Missing learner educational background
    if existing_qualification is None or str(existing_qualification).strip() == '':
        return ('UNKNOWN', 'Learner educational background not provided; admission requirements cannot be validated.', [])
        
    clauses = [c.strip() for c in str(eligibility_str).split(';') if c.strip()]
    if not clauses:
        return ('UNKNOWN', 'No parseable eligibility clauses found in catalogue record.', [])
        
    learner_edu_lvl = EDUCATION_LEVELS.get(str(existing_qualification).lower().strip(), 0)
    learner_exp = float(prior_experience_years) if prior_experience_years is not None else 0.0
    learner_nsqf = float(prior_nsqf_level) if prior_nsqf_level is not None else None
    
    eligible_clauses = []
    ineligible_clauses = []
    
    for c in clauses:
        parsed = parse_clause(c)
        edu_ok = (learner_edu_lvl >= parsed['req_edu_level'])
        exp_ok = (learner_exp >= parsed['req_exp_years'])
        nsqf_ok = True
        if parsed['req_nsqf'] is not None:
            nsqf_ok = (learner_nsqf is not None and learner_nsqf >= parsed['req_nsqf'])
            
        if edu_ok and exp_ok and nsqf_ok:
            eligible_clauses.append(c)
        else:
            fail_notes = []
            if not edu_ok:
                fail_notes.append(f"requires {parsed['edu_raw']} (learner has {existing_qualification})")
            if not exp_ok:
                fail_notes.append(f"requires {parsed['req_exp_years']} yrs exp (learner has {learner_exp})")
            if not nsqf_ok:
                fail_notes.append(f"requires Level {parsed['req_nsqf']}")
            ineligible_clauses.append(f"[{c} -> {', '.join(fail_notes)}]")
            
    if eligible_clauses:
        return ('ELIGIBLE', f"Meets entry requirement via pathway: {eligible_clauses[0]}", eligible_clauses)
    else:
        return ('INELIGIBLE', f"Does not meet alternative criteria: {'; '.join(ineligible_clauses[:2])}", [])

def evaluate_location_constraint(provider_district_list: List[str],
                                 provider_state_list: List[str],
                                 current_district: str = None,
                                 current_state: str = None,
                                 willingness_to_relocate: str = "within_district") -> Tuple[str, str]:
    """Evaluates location proximity against confirmed provider centres."""
    if not current_district and not current_state:
        return ('ELIGIBLE', 'No location constraints supplied by learner.')
        
    dist_list = [str(d).strip() for d in provider_district_list if d and str(d).strip()]
    state_list = [str(s).strip() for s in provider_state_list if s and str(s).strip()]
    
    # Missing location data
    if not dist_list and not state_list:
        return ('UNKNOWN', 'Training centre locations not linked in current catalogue; state-wide search required.')
        
    reloc = str(willingness_to_relocate).lower().strip()
    
    if reloc in ['nationally', 'willing to relocate nationally']:
        return ('ELIGIBLE', f"Training available nationally in: {', '.join(dist_list)} ({', '.join(state_list)}).")
        
    if current_district and any(d.lower() == current_district.lower() for d in dist_list):
        return ('ELIGIBLE', f"Direct accredited centre active in {current_district}.")
        
    if reloc in ['state_capital', 'within_state'] and current_state:
        if any(s.lower() == current_state.lower() for s in state_list):
            return ('ELIGIBLE', f"Available within home state ({current_state}).")
            
    return ('INELIGIBLE', f"Available centres in {', '.join(dist_list)} ({', '.join(state_list)}) are outside {current_district}.")

def evaluate_duration_constraint(duration_expected_hours: float,
                                 max_duration_hours: float = None) -> Tuple[str, str]:
    """Evaluates whether training duration fits within learner's time window."""
    if max_duration_hours is None:
        return ('ELIGIBLE', 'No duration constraint specified.')
        
    if np.isnan(duration_expected_hours) or duration_expected_hours is None:
        return ('UNKNOWN', 'Course duration unspecified in catalogue record.')
        
    if duration_expected_hours <= max_duration_hours:
        return ('ELIGIBLE', f"Duration of {duration_expected_hours:.0f} hours is within budget of {max_duration_hours:.0f} hours.")
    else:
        return ('INELIGIBLE', f"Duration of {duration_expected_hours:.0f} hours exceeds learner limit of {max_duration_hours:.0f} hours.")

def evaluate_budget_constraint(fee_amount_min: float,
                               fee_text: str,
                               max_budget_inr: float = None) -> Tuple[str, str]:
    """Evaluates whether course fee fits within learner's voluntary budget limit."""
    if max_budget_inr is None:
        return ('ELIGIBLE', 'No budget limit specified by learner.')
        
    if np.isnan(fee_amount_min) or fee_amount_min is None:
        return ('UNKNOWN', f"Course fee unverified in current records ({fee_text}).")
        
    if fee_amount_min <= max_budget_inr:
        return ('ELIGIBLE', f"Course fee of ₹{fee_amount_min:,.0f} meets learner budget of ₹{max_budget_inr:,.0f} ({fee_text}).")
    else:
        return ('INELIGIBLE', f"Course fee of ₹{fee_amount_min:,.0f} exceeds learner budget of ₹{max_budget_inr:,.0f} ({fee_text}).")
