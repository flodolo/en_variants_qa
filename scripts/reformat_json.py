#!/usr/bin/env python3

import glob
import json
import os


def main():
    root_path = os.path.abspath(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), os.path.pardir)
    )

    file_list = glob.glob(os.path.join(root_path, "**/*.json"))
    for filename in file_list:
        with open(filename, "r") as f:
            json_data = json.load(f)
        with open(filename, "w") as f:
            json.dump(json_data, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
