#!/usr/bin/env python

"""

Copyright (C) 2020 Vanessa Sochat.

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

# Headers are required!
token = os.environ.get("GITHUB_TOKEN")
if not token:
    sys.exit("Please export GITHUB_TOKEN")

headers = {"Authorization": f"token {token}"}


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

    return parser


def read_file(filename):
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def get_users(users_file):
    """Given a users file, load it and return a list of users
    """
    users = []
    if os.path.exists(users_file):
        users = [u for u in read_file(USERS_FILE).split("\n") if u]
    return users

def get_events(users):

    # We will lookup public events
    api_base = "https://api.github.com/users/{username}/events/public"

    events = {}
    for user in users:
        print("Looking up events for user %s" % user)
        url = api_base.format(username=user)
        response = requests.get(url, headers=headers)

        # Cut out early if non-200 response
        if response.status_code != 200:
           sys.exit("Error with response %s: %s" % (response.status_code, response.reason))
 
        events[user] = response.json()

    return events
 

def generate_content(event, user, seen):

    # Get shared metadata
    repo_name = event['repo']['name']
    repo = "https://github.com/%s" % repo_name
    event_type = event['type']
    avatar = event['actor']['avatar_url']

    if user not in seen:
        seen[user] = {"PushEvent": False, "IssueCommentEvent": False}

    # Only allow one push event, comment event, per repository
    for _type in ['PushEvent', "IssueCommentEvent"]:
        if seen[user][_type] is True:
           return None
        seen[user][_type] = True

    # Content for description on the kind of event
    if event_type == "PushEvent":
        commit_url = "%s/commit/%s" %(repo, event['payload']['commits'][-1]['sha'])
        message = event['payload']['commits'][-1]['message']
        description = "<a href='https://github.com/%s' target='_blank'>%s</a> pushed to <a href='%s' target='_blank'>%s</a>\n\n<small>%s</small>\n\n<a href='%s' target='_blank'>View Commit</a>" %(user, user, repo, repo_name, message, commit_url)
        url = commit_url

    elif event_type == "PullRequestEvent":
        action = event['payload']['action'] if event['payload']['pull_request']['merged'] is False else 'merged'
        url = event['payload']['pull_request']['html_url']      
        description = "<a href='https://github.com/%s' target='_blank'>%s</a> %s a pull request to <a href='%s' target='_blank'>%s</a>\n\n<a href='%s' target='_blank'>View Pull Request</a>" %(user, user, action, repo, repo_name, url)

    elif event_type == "CreateEvent":
        created = event['payload']['ref_type']
        branch = repo_name if created == "repository" else event['payload']['ref']
        description = "<a href='https://github.com/%s' target='_blank'>%s</a> created a new %s, %s at <a href='%s' target='_blank'>%s</a>\n\n<a href='%s' target='_blank'>View Repository</a>" %(user, user, created, branch, repo, repo_name, repo)
        url = repo

    elif event_type == "IssueCommentEvent":
        issue_url = event['payload']['issue']['html_url']
        issue_number = issue_url.split('/')[-1]
        comment = event['payload']['comment']['body'].split('\n')[0] + "..."
        description = "<a href='https://github.com/%s' target='_blank'>%s</a> commented on issue <a href='%s' target='_blank'>%s#%s</a>.\n\n<small>%s</small>\n\n<a href='%s' target='_blank'>View Comment</a>" %(user, user, issue_url, repo_name, issue_number, comment, issue_url)
        url = issue_url

    elif event_type == "ReleaseEvent":
        url = event['payload']['release']['html_url']
        comment = event['payload']['release']['body']
        tag = event['payload']['release']['tag_name']
        description = "<a href='https://github.com/%s' target='_blank'>%s</a> released <a href='%s' target='_blank'>%s</a>.\n\n<small>%s</small><a href='%s' target='_blank'>View Comment</a>" %(user, user, url, tag, comment, url)

    elif event_type == "IssuesEvent":
        issue_url = event['payload']['issue']['html_url']
        issue_number = issue_url.split('/')[-1]
        issue_state = event['payload']['issue']['state']
        issue_title = event['payload']['issue']['title']
        issue_body = event['payload']['issue']['body'].split('\n')[0] + "..."
        description = "<a href='https://github.com/%s' target='_blank'>%s</a> %s issue <a href='%s' target='_blank'>%s#%s</a>.\n\n<p>%s</p><small>%s</small><a href='%s' target='_blank'>View Comment</a>" %(user, user, issue_state, issue_url, repo_name, issue_number, issue_title, issue_body, issue_url)
        url = issue_url

    elif event_type == "PublicEvent":
        action = "public" if event['public'] else "private"
        description = "<a href='https://github.com/%s' target='_blank'>%s</a> has made <a href='%s' target='_blank'>%s</a> %s.<a href='%s' target='_blank'>View Repository</a>" %(user, user, repo, repo_name, action, repo)
        url = repo

    elif event_type == "PullRequestReviewCommentEvent":
        comment = event['payload']['comment']['body']
        comment_url = event['payload']['comment']['html_url']
        description = "<a href='https://github.com/%s' target='_blank'>%s</a> <a href='%s' target='_blank'>commented</a> on <a href='%s' target='_blank'>%s</a>\n\n<a href='%s' target='_blank'>View Comment</a>" %(user, user, comment_url, repo, repo_name, comment_url)
        url = comment_url

    # Include front end matter for jekyll
    content = "---\n"

    # Title must have quotes escaped
    content += "event_type: %s\n" % event_type
    content += 'avatar: "%s"\n' % avatar
    content += "user: %s\n" % user
    content += "date: %s\n" % date
    content += "repo_name: %s\n" % repo_name
    content += "html_url: %s\n" % url
    content += "repo_url: %s\n" % repo
    content += "---\n\n"
    content += description
    return content


def write_events(events, output_dir):
    """Given a listing of events (associated with users) write them to markdown
       files in the _events folder.
    """
    # We will only allow one PushEvent per user
    seen = {}
    for user, eventlist in events.items():
        for event in eventlist:

            # We don't care about watching, forking, etc.
            # https://docs.github.com/en/developers/webhooks-and-events/github-event-types
            if event["type"] in ["WatchEvent", "ForkEvent", "MemberEvent", "DeleteEvent"]:
                continue

            
            # Generate content for the event depending on type
            content = generate_content(event, user, seen)

            # If content is None, don't generate
            if not content:
                continue

            # Write to file
            repo_name = event['repo']['name']
            date = event["created_at"].split("T")[0]
            basename = "%s-%s-%s-%s.md" % (date, repo_name.replace("/", "-"), event_type , event["id"])
            filename = os.path.join(output_dir, basename)
            
            # Output to ../docs/_issues
            print(f"Writing {filename}")
            with open(filename, "w") as filey:
                filey.writelines(content)



def main():

    parser = get_parser()
    args, extra = parser.parse_known_args()

    # GitHub Workflow - we get variables from environment
    USERS_FILE = args.users_file or os.environ.get("INPUT_USERS_FILE", "users.txt")
    SKIP_USERS_FILE = args.exclude_users_file or os.environ.get("INPUT_EXCLUDE_USERS_FILE", "exclude-users.txt")
    COLLECTION_FOLDER = os.environ.get("INPUT_COLLECTION", "_events")

    # Debugging for the user
    print(f"users file: {USERS_FILE}")
    print(f"users file: {SKIP_USERS_FILE}")

    if not os.path.exists(USERS_FILE):
        sys.exit(f"{USERS_FILE} does not exist.")

    # Documentation base is located at docs
    output_dir = "/github/workspace/docs/%s" % COLLECTION_FOLDER
    print("Collection output folder: %s" % output_dir)

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # Get events, organized by type to write tomarkdown
    users = get_users(USERS_FILE)
    events = get_events(users)
    write_events(events, output_dir)


if __name__ == "__main__":
    main()
