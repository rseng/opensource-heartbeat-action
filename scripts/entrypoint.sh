#!/bin/bash

set -eu
set -o pipefail

# Get the relative path of the folder in docs to write output
if [ -z "${INPUT_COLLECTION}" ]; then
    INPUT_COLLECTION="_events"
fi

# If a query is defined, update the users file
if [ ! -z "${INPUT_QUERY}" ]; then
    printf "Updating users using query: ${INPUT_QUERY}\n"
    python3 /update-users.py --user-query "${INPUT_QUERY}";
fi

# If the docs folder isn't created, do so.
if [ ! -d "/github/workspace/docs" ]; then
    printf "Creating docs folder for GitHub pages\n"
    cp -R /docs /github/workspace/docs
fi

# Cleanup old set of first issues
if [ ! -z "${INPUT_CLEANUP}" ]; then
    printf "Cleaning up previous events...\n"
    rm -rf "/github/workspace/docs/${INPUT_COLLECTION}"
fi
export INPUT_COLLECTION

# Generate Stanford Issues
python3 /generate-events.py
