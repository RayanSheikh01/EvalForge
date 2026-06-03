import pytest

from generator.categories import all_categories



def test_categories():
    categories = all_categories()
    assert len(categories) > 0, "There should be at least one category"
    assert len(categories) == 5, "There should be exactly five categories"
    from generator.categories import CATEGORIES
    for category in categories:
        assert category.key in CATEGORIES, f"Category key {category.key} should be in CATEGORIES dict"