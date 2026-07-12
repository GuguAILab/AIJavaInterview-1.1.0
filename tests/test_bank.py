"""Question bank — structure and integrity."""
import json
import os

import pytest

BANK = os.path.join(os.path.dirname(__file__), "..", "data", "question_bank.json")
LEVELS = {"Junior (0-2 yrs)", "Mid-level (2-5 yrs)", "Senior (5+ yrs)"}


@pytest.fixture(scope="module")
def bank():
    with open(BANK, encoding="utf-8") as f:
        return json.load(f)


def test_bank_loads(bank):
    assert isinstance(bank, dict) and bank


def test_every_topic_has_all_three_levels(bank):
    for topic, levels in bank.items():
        assert set(levels) == LEVELS, f"{topic} -> {set(levels)}"


def test_no_empty_levels(bank):
    for topic, levels in bank.items():
        for lvl, qs in levels.items():
            assert qs, f"{topic} / {lvl} is empty"


def test_bank_is_substantial(bank):
    total = sum(len(q) for t in bank.values() for q in t.values())
    assert total >= 5000, f"only {total:,} questions"
