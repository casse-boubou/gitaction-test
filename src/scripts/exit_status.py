# exit_status.py - Computes the action's final exit code.

import os
import sys
from ast import literal_eval


def collect_distro_versions(outdated_by_line):
    """Build a {distribution_name: [version, ...]} map listing, for every
    stage in the outdated_by_line"""
    distribution_found = {}
    for stage_entry in outdated_by_line.values():
        if not stage_entry[2]:
            continue
        if stage_entry[0] in distribution_found:
            distribution_found[stage_entry[0]].append(stage_entry[1])
        else:
            distribution_found[stage_entry[0]] = []
            distribution_found[stage_entry[0]].append(stage_entry[1])
    return distribution_found


def determine_exit_code(outdated_by_line):
    """Compute and apply the action's final exit code."""
    allow_outdated_for_raw = (os.environ["ALLOW_OUTDATED_FOR"]) if os.environ.get("ALLOW_OUTDATED_FOR", "") else "{}"
    allow_outdated_for = literal_eval(allow_outdated_for_raw)
    should_fail = False

    # List every distribution/version referenced by a pinned package
    distribution_found = collect_distro_versions(outdated_by_line)

    # Remove whitelisted distribution/version pairs, so only non-whitelisted ones remain
    for whitelisted_distro, whitelisted_versions in allow_outdated_for.items():
        for white_version in whitelisted_versions:
            if str(whitelisted_distro).lower() in str(distribution_found).lower() and str(white_version).lower() in str(distribution_found[whitelisted_distro]).lower():
                distribution_found[whitelisted_distro].remove(str(white_version).lower())
    for remaining_versions in distribution_found.values():
        if remaining_versions:
            should_fail = True

    # Exit 1 unless every referenced distribution/version is covered by the whitelist
    if should_fail:
        print("exit 1")
        sys.exit(1)
    else:
        print("exit 0")
        sys.exit(0)
