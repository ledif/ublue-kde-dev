#!/bin/bash
#
# Should be run on host

set -euo pipefail

sudo mkdir -p /var/local/kde-dev/{home,kde}
sudo chown $(id -u):$(id -u) /var/local/kde-dev/{home,kde}

mkdir -p /var/local/kde-dev/home/.config
cp ./kde-builder.yaml /var/local/kde-dev/home/.config

distrobox create --name kde-dev --home /var/local/kde-dev/home --init --additional-packages "systemd" --pull --image ghcr.io/ublue-os/fedora-toolbox:latest

