#!/bin/bash

set -eu
set -o pipefail

# Get the relative path of the folder in docs to write output
if [ -z "${INPUT_COLLECTION}" ]; then
    INPUT_COLLECTION="_events"
fi

# If the docs folder isn't created, do so.
if [ ! -d "/github/workspace/docs" ]; then
    printf "Creating docs folder for GitHub pages\n"
    cp -R /docs /github/workspace/docs
fi

# Cleanup old set of first issues
printf "Cleaning up previous events...\n"
rm -rf "/github/workspace/docs/${INPUT_COLLECTION}"
export INPUT_COLLECTION

# Generate Stanford Issues
python3 /generate-events.py
