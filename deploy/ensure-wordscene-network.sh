#!/bin/sh
set -eu
if ! docker network inspect wordscene-edge >/dev/null 2>&1; then
    docker network create --subnet 172.30.80.0/24 wordscene-edge >/dev/null
fi
network_subnet="$(docker network inspect wordscene-edge --format '{{(index .IPAM.Config 0).Subnet}}')"
test "$network_subnet" = 172.30.80.0/24
