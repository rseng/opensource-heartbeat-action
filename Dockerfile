FROM ubuntu:18.04
# docker build -t stanford-issues .
RUN apt-get update && apt-get install -y git wget python3 python3-pip wget
RUN pip3 install requests
ENV GITHUB_PAGES=/github/workspace/docs
COPY ./scripts/entrypoint.sh /entrypoint.sh
COPY ./scripts/generate-events.py /generate-events.py
COPY ./docs /docs
RUN rm -rf /docs/_events && ls /docs
WORKDIR /github/workspace
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
