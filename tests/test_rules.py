import re

from agent.rules import (
    CATEGORY_FIXES,
    CATEGORY_RULES,
    HYPOTHESIS_EVALUATION_RULES,
    HYPOTHESIS_TEMPLATES,
    KEYWORD_WEIGHT,
    UNKNOWN,
)


def test_every_category_has_hypotheses() -> None:
    for category in CATEGORY_RULES:
        assert category in HYPOTHESIS_TEMPLATES
        assert len(HYPOTHESIS_TEMPLATES[category]) > 0

    assert UNKNOWN in HYPOTHESIS_TEMPLATES


def test_hypothesis_causes_are_unique() -> None:
    causes = [
        template.cause
        for templates in HYPOTHESIS_TEMPLATES.values()
        for template in templates
    ]

    assert len(causes) == len(set(causes))


def test_hypothesis_scores_are_valid() -> None:
    for templates in HYPOTHESIS_TEMPLATES.values():
        for template in templates:
            assert 0.0 <= template.initial_score <= 1.0


def test_strong_signals_have_stronger_weights() -> None:
    for rule in CATEGORY_RULES.values():
        if rule.strong_signals:
            assert rule.strong_weight > KEYWORD_WEIGHT


def test_every_known_hypothesis_has_evaluation_rule() -> None:
    for category, templates in HYPOTHESIS_TEMPLATES.items():
        if category == UNKNOWN:
            continue

        for template in templates:
            assert template.cause in HYPOTHESIS_EVALUATION_RULES


def test_evaluation_rule_weights_are_valid() -> None:
    for rule in HYPOTHESIS_EVALUATION_RULES.values():
        assert 0.0 <= rule.support_weight <= 1.0
        assert 0.0 <= rule.absence_penalty <= 1.0
        assert len(rule.fixes) > 0


def test_evidence_patterns_are_valid_regular_expressions() -> None:
    for rule in HYPOTHESIS_EVALUATION_RULES.values():
        re.compile(rule.pattern)


def test_every_category_has_fallback_fixes() -> None:
    expected_categories = set(CATEGORY_RULES)
    expected_categories.add(UNKNOWN)

    assert expected_categories.issubset(CATEGORY_FIXES)

    for fixes in CATEGORY_FIXES.values():
        assert len(fixes) > 0
