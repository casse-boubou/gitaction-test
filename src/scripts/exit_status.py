# exit_status.py - Determine the exit status code

import os
import sys


def dig_dataset(dataset):
    """Determine the status code if outdated are allowed or not"""
    distribution_found = {}
    for entry in dataset.items():
        for instruction in entry[1]:
            if instruction[0] in distribution_found:
                distribution_found[instruction[0]].append(instruction[1])
            else:
                distribution_found[instruction[0]] = []
                distribution_found[instruction[0]].append(instruction[1])
    return distribution_found


def determine_exit_code(dataset):
    """Determine the status code if outdated are allowed or not"""
    allow_outdated_for = (os.environ["ALLOW_OUTDATED_FOR"]) if os.environ.get("ALLOW_OUTDATED_FOR", "") else {}
    print(allow_outdated_for)
    disallow_outdated = not allow_outdated_for

    # Search for distribution with outdated package
    distribution_found = dig_dataset(dataset)

    # Compare distribution with outdated and allowed list
    for key, values in allow_outdated_for.items():
        for value in values:
            if str(key).lower() in str(distribution_found).lower() and str(value).lower() in str(distribution_found[key]).lower():
                distribution_found[key].remove(str(value).lower())
    for value in distribution_found.values():
        if value:
            disallow_outdated = True

    # Exit with statut 1 if outdated found and no deactivation
    if disallow_outdated:
        print("exit 1")
        sys.exit(1)
    else:
        print("exit 0")
        sys.exit(0)
