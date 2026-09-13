import unittest

from pathlib import Path

from check_en_differences import CheckStrings


class TestSpellingRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        testfiles_path = Path(__file__).parent / "testfiles"
        cls.check = CheckStrings(str(testfiles_path / "reference"))

    def buildRules(self, spelling):
        """Return the generated rules as a {pattern: replacements} dictionary"""

        return {
            pattern.pattern: replacements
            for pattern, replacements in self.check.buildSpellingRules(spelling)
        }

    def testBothCasesAreGenerated(self):
        rules = self.buildRules({"color": "colour"})

        self.assertEqual(rules[r"\b(?<![$-])color\b"], ["colour"])
        self.assertEqual(rules[r"\b(?<![$-])Color\b"], ["Colour"])

    def testCapitalizedEntryGeneratesLowercase(self):
        rules = self.buildRules({"Soccer": "Football"})

        self.assertEqual(rules[r"\b(?<![$-])Soccer\b"], ["Football"])
        self.assertEqual(rules[r"\b(?<![$-])soccer\b"], ["football"])

    def testStringAndListReplacementsAreEquivalent(self):
        # A single replacement is normalized to a list
        self.assertEqual(
            self.buildRules({"sync": "synchronise"}),
            self.buildRules({"sync": ["synchronise"]}),
        )

    def testListReplacementsKeepAllValues(self):
        rules = self.buildRules({"webpage": ["web page", "web site"]})

        self.assertEqual(rules[r"\b(?<![$-])webpage\b"], ["web page", "web site"])
        self.assertEqual(rules[r"\b(?<![$-])Webpage\b"], ["Web page", "Web site"])

    def testExplicitEntryIsNotOverridden(self):
        # An explicit entry wins over the generated one, so asymmetric
        # replacements stay possible
        rules = self.buildRules(
            {
                "counterclockwise": "anti-clockwise",
                "Counterclockwise": "Anti-Clockwise",
            }
        )

        self.assertEqual(rules[r"\b(?<![$-])counterclockwise\b"], ["anti-clockwise"])
        self.assertEqual(rules[r"\b(?<![$-])Counterclockwise\b"], ["Anti-Clockwise"])

    def testNonAlphabeticEntriesAreNotDuplicated(self):
        # Nothing to swap, so only one rule is generated
        rules = self.check.buildSpellingRules({", and": " and"})

        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0][1], [" and"])


if __name__ == "__main__":
    unittest.main()
