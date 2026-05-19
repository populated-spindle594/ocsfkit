from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring


def mapping_results_to_junit(results: list[dict[str, Any]]) -> str:
    failures = sum(1 for result in results if not result["passed"])
    suite = Element(
        "testsuite",
        {
            "name": "ocsfkit.mapping",
            "tests": str(len(results)),
            "failures": str(failures),
        },
    )
    for result in results:
        case = SubElement(
            suite,
            "testcase",
            {
                "classname": "ocsfkit.mapping",
                "name": str(result["spec"]),
            },
        )
        if not result["passed"]:
            failure = SubElement(
                case,
                "failure",
                {
                    "message": f"{len(result['changes'])} semantic differences",
                    "type": "ocsfkit.mapping.diff",
                },
            )
            failure.text = "\n".join(
                f"{change['kind']} {change['path']}: {change.get('before')!r} -> "
                f"{change.get('after')!r}"
                for change in result["changes"]
            )
    return tostring(suite, encoding="unicode")
