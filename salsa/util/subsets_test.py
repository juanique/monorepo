from typing import Dict, Any
import unittest
from salsa.util.subsets import is_dict_subset, is_list_subset, subset_diff_list, subset_diff


class TestSubsets(unittest.TestCase):
    def test_is_subset_recursive_empty(self) -> None:
        dict1: Dict[Any, Any] = {}
        dict2: Dict[Any, Any] = {}
        self.assertTrue(is_dict_subset(dict1, dict2))
        self.assertTrue(is_dict_subset(dict2, dict1))

    def test_is_subset_recursive_small(self) -> None:
        dict1: Dict[Any, Any] = {}
        dict2 = {"key": "value"}
        self.assertTrue(is_dict_subset(dict1, dict2))
        self.assertFalse(is_dict_subset(dict2, dict1))

    def test_is_subset_recursive_nested(self) -> None:
        dict1: Dict[Any, Any] = {"nested": {}}
        dict2 = {"key": "value", "nested": {"another_key": 1}}
        self.assertTrue(is_dict_subset(dict1, dict2))
        self.assertFalse(is_dict_subset(dict2, dict1))

    def test_is_subset_recursive_nested_2(self) -> None:
        dict1 = {"key": "value", "nested": {}}
        dict2 = {"key": "value", "nested": {"another_key": 1}}
        self.assertTrue(is_dict_subset(dict1, dict2))
        self.assertFalse(is_dict_subset(dict2, dict1))

    def test_is_subset_recursive_nested_3(self) -> None:
        dict1 = {"nested": {"another_key": 1}}
        dict2 = {"key": "value", "nested": {"another_key": 1}}
        self.assertTrue(is_dict_subset(dict1, dict2))
        self.assertFalse(is_dict_subset(dict2, dict1))

    def test_lists_value(self) -> None:
        dict1 = {"a": ["a", {"e": "f"}]}
        dict2 = {"a": ["a", "b", {"c": "d", "e": "f"}]}
        self.assertTrue(is_dict_subset(dict1, dict2))
        self.assertFalse(is_dict_subset(dict2, dict1))

    def test_lists_with_dicts(self) -> None:
        """Works with list that have dicts inside."""

        list1 = ["a", {"e": "f"}]
        list2 = ["a", "b", {"c": "d", "e": "f"}]

        d1 = subset_diff_list(list1, list2)
        d2 = subset_diff_list(list2, list1)

        self.assertIsNone(d1)
        self.assertIsNotNone(d2)

        self.assertTrue(is_list_subset(list1, list2))
        self.assertFalse(is_list_subset(list2, list1))

    def test_lists(self) -> None:
        """Can compare scalar lists."""

        list1 = ["a"]
        list2 = ["a", "b"]

        d1 = subset_diff_list(list1, list2)
        d2 = subset_diff_list(list2, list1)

        self.assertIsNone(d1)
        self.assertIsNotNone(d2)

        self.assertTrue(is_list_subset(list1, list2))
        self.assertFalse(is_list_subset(list2, list1))

    def test_mismatch(self) -> None:
        dict1 = {"x": "y", "a": [1]}
        dict2 = {"x": "y", "a": [2]}

        diff = subset_diff(dict1, dict2)
        self.assertNotEqual(diff and diff.mismatchs, [])


if __name__ == "__main__":
    unittest.main()
