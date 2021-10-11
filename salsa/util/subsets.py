from typing import Dict, Any, List, Optional

from dataclasses import dataclass, field


@dataclass
class Diff:
    path: List[str]
    message: str
    mismatchs: List["Diff"] = field(default_factory=lambda: [])


def subset_diff(val1: Any, val2: Any) -> Optional[Diff]:
    """Returns a diff that causes val1 not to be a recursive subset of val2."""

    if type(val1) != type(val2):  # pylint: disable=unidiomatic-typecheck
        return Diff(
            path=[],
            message=f"'{val1}' ({type(val1)}) and '{val2}' {type(val2)} are different types.",
        )

    if isinstance(val1, list):
        return subset_diff_list(val1, val2)

    if isinstance(val1, dict):
        return subset_diff_dict(val1, val2)

    if val1 != val2:
        return Diff(path=[], message=f"{val1} != {val2}")

    return None


def subset_equals(val1: Any, val2: Any) -> bool:
    """Returns true if val1 is a subset of val2.

    For scalars, this returns true only if val1==val2.  For lists it returns
    true if val1 is a subsequence of val2.  For dictionaries it returns true if
    val1 is a recursive subset of val2."""
    return subset_diff(val1, val2) is None


def subset_diff_list(val1: List[Any], val2: List[Any]) -> Optional[Diff]:
    """Returns a diff that causes val1 not to be a recursive subset of val2."""

    large_index = 0
    for index, value in enumerate(val1):
        diffs: List[Diff] = []
        found = False
        while large_index < len(val2):
            diff = subset_diff(value, val2[large_index])
            large_index += 1
            if not diff:
                found = True
                diffs = []
                break
            diffs.append(
                Diff(path=[str(large_index)], message=diff.message, mismatchs=diff.mismatchs)
            )

        if large_index == len(val2) and not found:
            return Diff(
                path=[str(index)], message="Could not find match on right side.", mismatchs=diffs
            )

    return None


def is_list_subset(val1: List[Any], val2: List[Any]) -> bool:
    """Returns true if first argument is a subsequence of second argument.

    For checking the subsequence we use use subset equality for dictionaries.
    """
    return subset_diff_list(val1, val2) is None


def subset_diff_dict(val1: Dict, val2: Dict) -> Optional[Diff]:
    """Returns a diff that causes val1 not to be a recursive subset of val2."""

    smaller_keys = val1.keys()
    larger_keys = val2.keys()

    for key in smaller_keys:
        if key not in larger_keys:
            return Diff(path=[key], message="not present on right side")

        diff = subset_diff(val1[key], val2[key])
        if diff:
            return Diff(path=[key] + diff.path, message=diff.message, mismatchs=diff.mismatchs)

    return None


def is_dict_subset(val1: Dict, val2: Dict) -> bool:
    """Returns true if val1 is a recursive subset of val2."""
    return subset_diff_dict(val1, val2) is None
