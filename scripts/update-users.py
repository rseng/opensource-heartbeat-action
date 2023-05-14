#!/usr/bin/env python

"""

Copyright (C) 2020-2022 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""

import argparse
import json
import os
import requests
import sys

here = os.path.dirname(os.path.abspath(__file__))
print("Present working directory is %s" % here)


def get_parser():
    parser = argparse.ArgumentParser(description="Open Source Heartbeat")

    parser.add_argument(
        "--version",
        dest="version",
        help="suppress additional output.",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--users-file",
        dest="users_file",
        help="The users.txt file with GitHub usernames on lines.",
        default=None,
    )

    parser.add_argument(
        "--exclude-users-file",
        dest="exclude_users_file",
        help="A list of users to never add (that might still be discovered).",
        default=None,
    )

    parser.add_argument(
        "--user-query",
        dest="user_query",
        help="The string portion of a user query, generate with https://github.com/search/advanced.",
        default=None,
    )

    parser.add_argument(
        "--org-users-file",
        dest="org_users_file",
        help="A filename with organization names to get public users from",
        default=None,
    )

    return parser


def get_headers():
    """Get headers with an authentication token if one is found in the
    environment
    """
    # Add token to increase API limits
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers = {"Authorization": f"token {token}"}
    return headers


def get_org_users(orgs):
    """
    Given a list of orgs, retrieve public users
    """
    users = []
    for org in orgs:
        org = org.strip()
        if not org:
            continue
        res = requests.get(f"https://api.github.com/orgs/{org}/members")
        if res.status_code != 200:
            sys.exit(f"{res.status_code}: {res.reason}")
        users += [x["login"] for x in res.json()]
    return users


def search_users(query, search_type="users"):
    """
    Return a subset of users that match a particular query (up to 1000)
    The example here searches for location Stanford
    """

    url = "https://api.github.com/search/%s?q=%s" % (search_type, query)
    response = requests.get(url, headers=get_headers())

    # Exit early if issue with request
    if response.status_code != 200:
        sys.exit(f"{response.status_code}: {response.reason}")

    return [item["login"] for item in response.json().get("items", [])]


def read_file(filename):
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def write_file(content, filename):
    with open(filename, "w") as fd:
        fd.writelines(content)


def main():
    parser = get_parser()
    args, extra = parser.parse_known_args()

    # GitHub Workflow - we get variables from environment
    USERS_FILE = args.users_file or os.environ.get("INPUT_USERS_FILE", "users.txt")
    SKIP_USERS_FILE = args.exclude_users_file or os.environ.get(
        "INPUT_EXCLUDE_USERS_FILE", "exclude-users.txt"
    )
    USERS_FROM_ORGS_FILE = args.org_users_file or os.environ.get(
        "INPUT_USERS_FROM_ORGS_FILE", "org-users.txt"
    )

    # Debugging for the user
    print(f"users file: {USERS_FILE}")
    print(f"skips file: {SKIP_USERS_FILE}")
    print(f"users from orgs file {USERS_FROM_ORGS_FILE}")

    # Update users to file (so they can remove later)
    SEARCH_QUERY = os.environ.get("INPUT_QUERY", args.user_query)

    users = []
    if os.path.exists(USERS_FILE):
        users = [u for u in read_file(USERS_FILE).split("\n") if u]

    # Get public users for an org
    if os.path.exists(USERS_FROM_ORGS_FILE):
        users += get_org_users(read_file(USERS_FROM_ORGS_FILE).split("\n"))

    # Unique
    users = list(set(users))

    # If skip users is defined
    skip_users = []
    if os.path.exists(SKIP_USERS_FILE):
        skip_users = [u for u in read_file(USERS_FILE).split("\n") if u]

    # To we want to further filter?
    new_users = []
    if SEARCH_QUERY:
        new_users = search_users(SEARCH_QUERY)

    users = users + new_users

    # Update users
    users = [user for user in users if user not in skip_users]
    print(f"Found {len(new_users)} users!")
    write_file("\n".join(users), USERS_FILE)


if __name__ == "__main__":
    main()
