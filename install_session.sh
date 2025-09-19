#!/usr/bin/bash

set -euox pipefail

podman container start kde-dev
if ! podman container exec kde-dev test -f /usr/local/share/wayland-sessions/plasmawayland-dev6.desktop; then
  printf "The file '/usr/local/share/wayland-sessions/plasmawayland-dev6.desktop' does not exist in the KDE development container distrobox.\nYou will need to run ujust setup-kde-dev first.\n"
  exit 1
fi

printf "This will set up an overlayfs over /usr, making it temporarily mutable until the next reboot. This recipe will need to be run again on every reboot.\n"
sudo bootc usr-overlay

echo 'chown -f -R $USER:$USER /tmp/.X11-unix' | sudo tee /etc/profile.d/kde-dev-set_tmp_x11_permissions.sh > /dev/null

session_launch_script=/var/local/kde-dev/kde/start-plasma-dev-session
kde_dir=/var/local/kde-dev/kde

podman container cp kde-dev:/usr/local/share/wayland-sessions/plasmawayland-dev6.desktop /tmp
sed -i "s@^Exec=.*@Exec=${session_launch_script}@" /tmp/plasmawayland-dev6.desktop
sudo mv /tmp/plasmawayland-dev6.desktop /usr/share/wayland-sessions
echo "${kde_dir}/usr/lib64/libexec/kactivitymanagerd & disown
${kde_dir}/usr/lib64/libexec/plasma-dbus-run-session-if-needed ${kde_dir}/usr/lib64/libexec/startplasma-dev.sh -wayland" > ${session_launch_script}
chmod +x ${session_launch_script}
printf "Complete! Log out to see the Plasma development session in SDDM.\n"

