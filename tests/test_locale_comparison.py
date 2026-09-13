import json
import shutil
import tempfile
import unittest

from pathlib import Path

from check_en_differences import CheckStrings


class TestLocaleComparison(unittest.TestCase):
    def setUp(self):
        self.testfiles_path = Path(__file__).parent / "testfiles"

        # compareLocale rewrites the exclusions and output files, so work on a
        # copy of the data folders
        self.tmp_dir = tempfile.mkdtemp()
        self.root_path = Path(self.tmp_dir) / "root"
        shutil.copytree(self.testfiles_path / "root", self.root_path)

        check = CheckStrings(str(self.testfiles_path / "reference"))
        check.compareLocale(
            "en-XX",
            str(self.testfiles_path),
            write=False,
            update=False,
            root_path=str(self.root_path),
        )

        with open(self.root_path / "output" / "en-XX.json") as f:
            self.differences = json.load(f)
        with open(self.root_path / "exclusions" / "en-XX.json") as f:
            self.used_exceptions = json.load(f)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def testCaseDifferences(self):
        self.assertEqual(self.differences["case"], ["test.ftl:case-difference"])

    def testSpellingDifferences(self):
        self.assertEqual(self.differences["spelling"], ["test.ftl:spelling-difference"])

    def testExpectedSpellingChangesAreIgnored(self):
        # Known spelling variations are not reported as differences
        all_differences = self.differences["case"] + self.differences["spelling"]

        for string_id in (
            "test.ftl:identical-string",
            "test.ftl:spelling-change",
            "test.ftl:value-and-attributes",
            "test.ftl:value-and-attributes.tooltiptext",
            "test.ftl:empty-value.label",
            "test.dtd:simple.label",
            "test.properties:simpleString",
            "test.ini:simpleString",
            "test.inc:simpleString",
            "folder/nested.ftl:nested-string",
            # The capitalized variant is generated from the lowercase entry
            "test.ftl:capitalized-word",
            "test.ftl:lowercase-word",
            # Asymmetric entries are defined explicitly for both cases
            "test.ftl:asymmetric-lowercase",
            "test.ftl:asymmetric-capitalized",
        ):
            self.assertNotIn(string_id, all_differences)

    def testAccesskeysAreCaseInsensitive(self):
        # Accesskeys and shortcuts are compared in lowercase
        all_differences = self.differences["case"] + self.differences["spelling"]

        self.assertNotIn("test.ftl:accesskey-string.accesskey", all_differences)
        self.assertNotIn("test.dtd:simple.accesskey", all_differences)

    def testUsedExceptionsAreStored(self):
        # Exceptions that matched a difference are written back to file
        self.assertEqual(self.used_exceptions["case"], ["test.ftl:case-exception"])
        self.assertEqual(
            self.used_exceptions["spelling"], ["test.ftl:spelling-exception"]
        )


if __name__ == "__main__":
    unittest.main()
