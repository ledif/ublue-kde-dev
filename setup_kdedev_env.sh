#!/bin/bash

set -exuo pipefail

### 🔧 KDE Build Dependencies
echo "Installing KDE build dependencies..."
sudo dnf5 install -y --skip-broken --skip-unavailable --allowerasing \
    git python3-dbus python3-pyyaml python3-setproctitle python3-wheel clang-devel libfyaml-devel rust cargo

### Get KDE dependencies list
echo "Fetching KDE dependency list..."
kde_deps=$(curl -s 'https://invent.kde.org/sysadmin/repo-metadata/-/raw/master/distro-dependencies/fedora.ini' |
    sed '1d' | grep -vE '^\s*#|^\s*$')

if [[ -z "$kde_deps" ]]; then
    echo "Failed to fetch KDE dependencies list"
 else
    echo "Installing KDE dependencies..."
    echo "$kde_deps" | xargs sudo dnf5 install -y --skip-broken --skip-unavailable --allowerasing
fi

## 🎮 Development Tools
 echo "Installing additional dev tools..."
 dev_tools=(neovim zsh flatpak-builder kdevelop kdevelop-devel kdevelop-libs)
 for tool in "${dev_tools[@]}"; do
     sudo dnf5 install -y --skip-broken --skip-unavailable --allowerasing "$tool"
 done

## 🛠 Install kde-builder (manual clone + symlinks)
echo "Installing kde-builder..."
tmpdir=$(mktemp -d)
pushd "$tmpdir" >/dev/null

git clone https://invent.kde.org/sdk/kde-builder.git
cd kde-builder

sudo mkdir -p /usr/share/kde-builder
sudo cp -r ./* /usr/share/kde-builder

sudo mkdir -p /usr/bin
sudo ln -sf /usr/share/kde-builder/kde-builder /usr/bin/kde-builder

sudo mkdir -p /usr/share/zsh/site-functions
sudo ln -sf /usr/share/kde-builder/data/completions/zsh/_kde-builder \
     /usr/share/zsh/site-functions/_kde-builder
sudo ln -sf /usr/share/kde-builder/data/completions/zsh/_kde-builder_projects_and_groups \
     /usr/share/zsh/site-functions/_kde-builder_projects_and_groups

rm -rf "$tmpdir"

## Build KDE
sudo rm -rf "$HOME"/.cache
yes | kde-builder workspace

