from __future__ import annotations

import unittest

from app.services.validation_engine import validate_required_inputs


class ValidationEngineTests(unittest.TestCase):
    def test_validate_required_inputs_returns_sorted_missing_fields(self) -> None:
        missing = validate_required_inputs(
            {
                "EPAZAR_OPERATOR_ID": "",
                "EPAZAR_CATALOG_ITEM": "item-1",
                "EPAZAR_PROCUREMENT_REF": "  ",
            },
            ["EPAZAR_OPERATOR_ID", "EPAZAR_CATALOG_ITEM", "EPAZAR_PROCUREMENT_REF"],
        )
        self.assertEqual(missing, ["EPAZAR_OPERATOR_ID", "EPAZAR_PROCUREMENT_REF"])

    def test_validate_required_inputs_returns_empty_when_complete(self) -> None:
        missing = validate_required_inputs(
            {
                "EPAZAR_OPERATOR_ID": "OP-1",
                "EPAZAR_CATALOG_ITEM": "item-1",
                "EPAZAR_PROCUREMENT_REF": "REF-1",
            },
            ["EPAZAR_OPERATOR_ID", "EPAZAR_CATALOG_ITEM", "EPAZAR_PROCUREMENT_REF"],
        )
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()

