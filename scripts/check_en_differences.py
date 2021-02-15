#!/usr/bin/env python3

import argparse
import difflib
import os
import json
import re
import subprocess
import sys
from html.parser import HTMLParser

# Import libraries
try:
    from compare_locales import parser
except ImportError as e:
    print("FATAL: make sure that dependencies are installed")
    print(e)
    sys.exit(1)


class CheckStrings:
    def __init__(self, reference_path):
        """Initialize object"""

        # Set defaults
        self.supported_formats = [
            ".dtd",
            ".ftl",
            ".inc",
            ".ini",
            ".properties",
        ]

        # Extract reference strings
        self.reference_strings = {}
        self.extractStrings(reference_path, self.reference_strings)

    def extractFileList(self, repository_path):
        """Extract the list of supported files"""

        excluded_folders = [
            "calendar",
            "chat",
            "dom",
            "editor",
            "extensions",
            "mail",
            "mobile",
            "other-licenses",
            "security",
            "suite",
        ]

        file_list = []
        for root, dirs, files in os.walk(repository_path, followlinks=True):
            # Ignore excluded folders
            if root == repository_path:
                dirs[:] = [d for d in dirs if d not in excluded_folders]

            for f in files:
                for supported_format in self.supported_formats:
                    if f.endswith(supported_format):
                        file_list.append(os.path.join(root, f))
        file_list.sort()

        return file_list

    def extractStrings(self, repository_path, strings):
        """Extract strings in files"""

        # Create a list of files to analyze
        file_list = self.extractFileList(repository_path)

        for file_path in file_list:
            file_extension = os.path.splitext(file_path)[1]
            file_name = self.getRelativePath(file_path, repository_path)

            if file_name.endswith("region.properties"):
                continue

            file_parser = parser.getParser(file_extension)
            file_parser.readFile(file_path)
            try:
                entities = file_parser.parse()
                for entity in entities:
                    # Ignore Junk
                    if isinstance(entity, parser.Junk):
                        continue

                    string_id = "{}:{}".format(file_name, entity)
                    if file_extension == ".ftl":
                        if entity.raw_val != "":
                            strings[string_id] = entity.raw_val
                        # Store attributes
                        for attribute in entity.attributes:
                            attr_string_id = "{0}:{1}.{2}".format(
                                file_name, entity, attribute
                            )
                            strings[attr_string_id] = attribute.raw_val
                    else:
                        strings[string_id] = entity.raw_val
            except Exception as e:
                print("Error parsing file: {}".format(file_path))
                print(e)

    def getRelativePath(self, file_name, repository_path):
        """Get the relative path of a filename"""

        relative_path = file_name[len(repository_path) + 1 :]

        return relative_path

    def compareLocale(self, locale, repository_path, write, update):
        """Extract strings for locale, compare to reference strings"""

        # Update repo
        if update:
            subprocess.run(["hg", "-R", repository_path, "pull", "-u"])

        locale_strings = {}
        self.extractStrings(repository_path, locale_strings)

        ignored_strings = [
            "browser/browser/pageInfo.ftl:media-file-size",
            "browser/browser/pageInfo.ftl:properties-general-size.value",
            "browser/chrome/browser/browser.properties:safebrowsing.notAnAttackButton.accessKey",
            "browser/extensions/formautofill/formautofill.properties:zip",
            "browser/installer/override.properties:Kilo",
            "browser/pdfviewer/chrome.properties:open_with_different_viewer.accessKey",
            "browser/pdfviewer/viewer.properties:document_properties_kb",
            "devtools/client/netmonitor.properties:charts.sizeKB",
            "devtools/client/netmonitor.properties:charts.totalSize",
            "devtools/client/netmonitor.properties:charts.totalTransferredSize",
            "devtools/client/netmonitor.properties:charts.transferredSizeKB",
            "devtools/client/netmonitor.properties:networkMenu.sizeKB",
            "devtools/client/webconsole.properties:webconsole.cssFilterButton.inactive.tooltip",
            "devtools/shared/styleinspector.properties:styleinspector.contextmenu.copyColor.accessKey",
            "toolkit/chrome/mozapps/downloads/downloads.properties:kilobyte",
            "toolkit/toolkit/about/aboutPerformance.ftl:size-KB",
            "toolkit/toolkit/about/aboutProcesses.ftl:memory-unit-KB",
        ]

        spelling_changes = {
            "en-CA": {
                "behavior": "behaviour",
                "behaviors": "behaviours",
                "canceled": "cancelled",
                "center": "centre",
                "color": "colour",
                "colors": "colours",
                "colorful": "colourful",
                "counterclockwise": "anti-clockwise",
                "favorite": "favourite",
                "favorites": "favourites",
                "honors": "honours",
                "labeled": "labelled",
                "license": "licence",
                "licenses": "licences",
                "millimeters": "millimetres",
                "moveable": "movable",
                "neighborhood": "neighbourhood",
                "oxidized": "oxidise",
            }
        }

        spelling = spelling_changes.get(locale, {})

        translation_differences = []
        case_differences = []
        for id, translation in locale_strings.items():
            # Ignore obsolete strings
            if id not in self.reference_strings:
                continue

            # Ignore accesskey and shortcuts
            if id.endswith((".key", ".accesskey")):
                continue

            # Ignore other strings
            if id in ignored_strings:
                continue

            # Check differences
            if translation != self.reference_strings[id]:
                source = self.reference_strings[id]

                # Try cleaning up spaces (trailing, leading, multiple)
                translation = " ".join(translation.strip().split()).replace("\n", " ")
                source = " ".join(source.strip().split()).replace("\n", " ")
                if translation == source:
                    continue
                if translation.lower() == source.lower():
                    case_differences.append(id)
                else:
                    # Clean up translation differences due to spelling
                    source = source.lower()
                    translation = translation.lower()
                    for word, replacement in spelling.items():
                        source = re.sub(r"\b{}\b".format(word), replacement, source)

                    if source == translation:
                        continue

                    translation_differences.append(id)


        if case_differences:
            print("\nDifferent case:")
            for id in case_differences:
                print(f"\nID: {id}")
                print(f"Source: {self.reference_strings[id]}")
                print(f"Translation: {locale_strings[id]}")

        if write:
            # Organize them by file, to avoid opening the same file multiple times
            fixes = {}
            for id in case_differences:
                filename = id.split(":")[0]
                if filename not in fixes:
                    fixes[filename] = [id]
                else:
                    fixes[filename].append(id)

            for filename, ids in fixes.items():
                filename = os.path.join(repository_path, filename)
                with open(filename, "r") as f:
                    original_content = f.readlines()

                updated_content = []
                for index, line in enumerate(original_content):
                    for id in ids:
                        if locale_strings[id] in line:
                            string_id = id.split(":")[1]
                            if ".properties" in id:
                                # id = text
                                pattern = r"^{}(\s*)=(\s*){}(\s*$)".format(
                                    string_id, locale_strings[id]
                                )
                                replacement = r"{}\g<1>=\g<2>{}\g<3>".format(
                                    string_id, self.reference_strings[id]
                                )
                                line = re.sub(pattern, replacement, line)
                            elif ".dtd" in id:
                                # <!ENTITY id "text"> or <!ENTITY id 'text'>
                                pattern = r'{}(\s*)("|\'){}("|\')'.format(
                                    string_id, locale_strings[id]
                                )
                                replacement = r"{}\g<1>\g<2>{}\g<3>".format(
                                    string_id, self.reference_strings[id]
                                )
                                line = re.sub(pattern, replacement, line)
                                # line = line.replace(locale_strings[id], self.reference_strings[id])
                            elif ".ftl" in id:
                                if "." in string_id:
                                    # Attribute
                                    attribute = string_id.split(".")[1]
                                    pattern = r"^(\s*)\.{}(\s*)=(\s*){}(\s*$)".format(
                                        attribute, locale_strings[id]
                                    )
                                    replacement = r"\g<1>.{}\g<2>=\g<3>{}\g<4>".format(
                                        attribute, self.reference_strings[id]
                                    )
                                    line = re.sub(pattern, replacement, line)
                                else:
                                    # Value
                                    pattern = r"^{}(\s*)=(\s*){}(\s*$)".format(
                                        string_id, locale_strings[id]
                                    )
                                    replacement = r"{}\g<1>=\g<2>{}\g<3>".format(
                                        string_id, self.reference_strings[id]
                                    )
                                    line = re.sub(pattern, replacement, line)

                    updated_content.append(line)

                with open(filename, "w") as f:
                    f.writelines(updated_content)

        if translation_differences:
            print("\nDifferent translations:")
            for id in translation_differences:
                print(f"\nID: {id}")
                print(f"Original: {self.reference_strings[id]}")
                print(f"Translation: {locale_strings[id]}")

                output_list = [li for li in difflib.ndiff(
                    self.reference_strings[id], locale_strings[id]) if li[0] != ' ']
                print("Differences:")
                print(" ".join(output_list))


def main():
    script_path = os.path.abspath(os.path.dirname(__file__))

    p = argparse.ArgumentParser(
        description="Display and remove capitalization differences for English localizations"
    )
    p.add_argument(
        "--write",
        help="Write changes back to file",
        action="store_true",
        default=False,
    )
    p.add_argument(
        "--update",
        help="Pull from remote",
        action="store_true",
        default=False,
    )
    p.add_argument(
        "locale",
        help="Locale to check"
    )
    args = p.parse_args()

    l10n_repo_path = "/Users/flodolo/mozilla/mercurial/l10n_clones/locales"
    repo_path = f"{l10n_repo_path}/{args.locale}"
    if not os.path.isdir(repo_path):
        sys.exit(f"Path to repository {repo_path} does not exist.")

    check = CheckStrings("/Users/flodolo/mozilla/mercurial/gecko-strings-quarantine")
    print(f"Checking {args.locale}\n-------\n")
    check.compareLocale(args.locale, repo_path, args.write, args.update)


if __name__ == "__main__":
    main()
