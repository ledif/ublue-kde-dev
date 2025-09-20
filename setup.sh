#!/bin/bash
#
# Should be run on host

set -exuo pipefail

sudo mkdir -p /var/local/kde-dev/{home,kde}
sudo chown $(id -u):$(id -u) /var/local/kde-dev/{home,kde}

mkdir -p /var/local/kde-dev/home/.config
cp ./kde-builder.yaml /var/local/kde-dev/home/.config

distrobox create \
	--name kde-dev \
	--home /var/local/kde-dev/home \
	--volume /var/local/kde-dev/kde:/var/local/kde-dev/kde:Z \
	--init \
	--additional-packages "systemd" \
	--pull \
	--image ghcr.io/ledif/ublue-kde-dev:latest

