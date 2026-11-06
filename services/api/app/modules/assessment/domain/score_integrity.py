"""Versioned *automatic-sum* assessment evidence contracts (v1 and v2).

Legacy rows (version 0) lack an assertion of complete per-question evidence.
The verifier never reconstructs missing data or mutates a grade. Manual scoring,
bonuses and moderation require a distinct, explicitly specified future contract.
"""
from math import isfinite
from hashlib import sha256
from hmac import compare_digest
import json

AUTO_SUM_CONTRACT_VERSION = 1
SNAPSHOT_AUTO_SUM_VERSION = 2
LEGACY_UNVERIFIED_VERSION = 0


def _field(item, name):
    return item.get(name) if isinstance(item, dict) else getattr(item, name, None)


def _number(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and isfinite(value))


def verified_auto_sum(result, attempt, catalog, course_id, pass_percent):
    """True only for *complete*, unambiguous auto-graded question breakdowns.

    catalog: {question_id: (course_id, points)} from the authoritative question
    table. All attempt questions, including unmapped ones, must be represented.
    Reject unknown/duplicate IDs, stale courses, altered point values, malformed
    totals or verdicts. No tolerance: auto-sum is integer and deterministic.
    """
    ids = _field(attempt, 'question_ids')
    details = _field(result, 'questions')
    if (not isinstance(ids, (tuple, list)) or not ids or
        not all(isinstance(qid, str) and qid for qid in ids) or
        len(ids) != len(set(ids)) or
        not isinstance(details, (tuple, list)) or len(details) != len(ids) or
        not _number(pass_percent) or not 0 <= pass_percent <= 100):
        return False
    for key in ('earned', 'possible', 'percent'):
        if not _number(_field(result, key)):
            return False
    earned_total = possible_total = 0
    seen = set()
    for row in details:
        qid = _field(row, 'question_id')
        if not isinstance(qid, str) or qid not in ids or qid in seen:
            return False
        seen.add(qid)
        meta = catalog.get(qid)
        if not isinstance(meta, (tuple, list)) or len(meta) != 2 or meta[0] != course_id:
            return False
        points = meta[1]
        earned, possible, correct = (_field(row, 'earned'), _field(row, 'possible'),
                                     _field(row, 'correct'))
        if (not isinstance(points, int) or isinstance(points, bool) or points <= 0 or
            not _number(earned) or not _number(possible) or possible != points or
            not isinstance(correct, bool) or earned not in (0, points) or
            correct != (earned == points)):
            return False
        earned_total += earned
        possible_total += possible
    if (seen != set(ids) or possible_total <= 0 or
        _field(result, 'earned') != earned_total or
        _field(result, 'possible') != possible_total or
        _field(result, 'percent') != round(100 * earned_total / possible_total)):
        return False
    passed = _field(result, 'passed')
    if isinstance(passed, bool):
        result_passed = passed
    elif type(passed) is int and passed in (0, 1):
        result_passed = bool(passed)
    else:
        return False
    return result_passed == (_field(result, 'percent') >= pass_percent)


def _snapshot_bytes(snapshot):
    """Deterministic fingerprint; an unkeyed hash detects drift, NOT privileged DB tampering."""
    return json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def snapshot_digest(snapshot):
    return sha256(_snapshot_bytes(snapshot)).hexdigest()


def make_auto_sum_snapshot(result, attempt, catalog, course_id, pass_percent):
    """Capture immutable grading *inputs* in the atomic grade transaction.

    Called only after authoritative catalog and original v1 sum are checked.
    Never backfill a historical result from the current mutable question bank.
    """
    if not verified_auto_sum(result, attempt, catalog, course_id, pass_percent):
        raise ValueError('assessment_auto_sum_integrity_required')
    if not isinstance(course_id, str) or not course_id or not isinstance(attempt.blueprint_id, str):
        raise ValueError('assessment_auto_sum_integrity_required')
    if type(pass_percent) is not int or not 0 <= pass_percent <= 100:
        raise ValueError('assessment_auto_sum_integrity_required')
    snapshot = {
        'schema': SNAPSHOT_AUTO_SUM_VERSION,
        'attempt_id': result.attempt_id,
        'blueprint_id': attempt.blueprint_id,
        'curriculum_course_id': course_id,
        'pass_percent': pass_percent,
        'questions': [
            {'question_id': qid, 'course_id': catalog[qid][0], 'points': catalog[qid][1]}
            for qid in attempt.question_ids
        ],
    }
    return snapshot, snapshot_digest(snapshot)


def verified_snapshot_auto_sum(result, attempt, curriculum_course_id):
    """Revalidate version-2 evidence independently from the mutable question bank.

    Returns (verified, points_by_question). Strict snapshot schema is deliberate:
    unrecognized grading rules must not be interpreted as automatic sums.
    """
    empty = (False, {})
    snap = _field(result, 'grading_snapshot')
    expected_hash = _field(result, 'grading_snapshot_sha256')
    if (not isinstance(snap, dict) or set(snap) != {
        'schema', 'attempt_id', 'blueprint_id', 'curriculum_course_id',
        'pass_percent', 'questions'
    } or type(snap.get('schema')) is not int or snap['schema'] != SNAPSHOT_AUTO_SUM_VERSION
        or snap.get('attempt_id') != _field(result, 'attempt_id')
        or snap.get('blueprint_id') != _field(attempt, 'blueprint_id')
        or not isinstance(curriculum_course_id, str) or not curriculum_course_id
        or snap.get('curriculum_course_id') != curriculum_course_id
        or type(snap.get('pass_percent')) is not int or not 0 <= snap['pass_percent'] <= 100
        or not isinstance(expected_hash, str) or len(expected_hash) != 64
        or not isinstance(snap.get('questions'), list)):
        return empty
    try:
        if not compare_digest(snapshot_digest(snap), expected_hash):
            return empty
    except (ValueError, TypeError, OverflowError):
        return empty
    catalog = {}
    for entry in snap['questions']:
        if (not isinstance(entry, dict) or set(entry) != {'question_id','course_id','points'}
            or not isinstance(entry['question_id'], str) or not entry['question_id']
            or entry['question_id'] in catalog
            or entry['course_id'] != curriculum_course_id
            or type(entry['points']) is not int or entry['points'] <= 0):
            return empty
        catalog[entry['question_id']] = (entry['course_id'], entry['points'])
    ids = _field(attempt, 'question_ids')
    if not isinstance(ids, (tuple, list)) or [x['question_id'] for x in snap['questions']] != list(ids):
        return empty
    if not verified_auto_sum(result, attempt, catalog, curriculum_course_id, snap['pass_percent']):
        return empty
    return True, {qid: points for qid, (_, points) in catalog.items()}
