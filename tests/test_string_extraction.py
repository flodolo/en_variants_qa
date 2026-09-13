import unittest

from pathlib import Path

from check_en_differences import CheckStrings


class TestStringExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testfiles_path = Path(__file__).parent / "testfiles"
        cls.check = CheckStrings(str(cls.testfiles_path / "reference"))

    def testReferenceStrings(self):
        strings = self.check.reference_strings

        self.assertEqual(len(strings), 23)
        self.assertEqual(strings["test.ftl:identical-string"], "Settings")
        self.assertEqual(strings["test.dtd:simple.label"], "Color")
        self.assertEqual(strings["test.properties:simpleString"], "Color")
        self.assertEqual(strings["test.inc:simpleString"], "Color")
        self.assertEqual(strings["folder/nested.ftl:nested-string"], "Center")

    def testUnicodeIsNotEscaped(self):
        self.assertEqual(
            self.check.reference_strings["test.properties:unicodeString"], "Café"
        )

    def testIniSectionIsIgnoredInID(self):
        # For .ini files the section name is not part of the string ID
        strings = self.check.reference_strings

        self.assertIn("test.ini:simpleString", strings)
        self.assertNotIn("test.ini:Strings.simpleString", strings)

    def testFluentAttributes(self):
        strings = self.check.reference_strings

        # Both the value and the attributes are extracted
        self.assertEqual(strings["test.ftl:value-and-attributes"], "Behavior")
        self.assertEqual(
            strings["test.ftl:value-and-attributes.tooltiptext"],
            "Customize the dialog",
        )

        # An empty value is not stored, the attribute is
        self.assertNotIn("test.ftl:empty-value", strings)
        self.assertEqual(strings["test.ftl:empty-value.label"], "Favorites")

    def testDatetimeOptionsAreNormalized(self):
        # moz.l10n serializes DATETIME options in a canonical order, so a
        # different order in the localization is not reported as a difference
        locale_strings = {}
        self.check.extractStrings(str(self.testfiles_path / "en-XX"), locale_strings)

        self.assertEqual(
            self.check.reference_strings["test.ftl:datetime-options"],
            locale_strings["test.ftl:datetime-options"],
        )

    def testExcludedFilesAndFolders(self):
        strings = self.check.reference_strings

        # region.properties is ignored
        self.assertNotIn("region.properties:ignoredString", strings)
        # The dom folder is ignored
        self.assertNotIn("dom/excluded.ftl:excluded-string", strings)


if __name__ == "__main__":
    unittest.main()
