#!/usr/bin/env python3
"""
KDE Development Environment Setup Script

This script sets up a KDE development environment using distrobox.
"""

import argparse
import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and handle errors."""
    try:
        result = subprocess.run(cmd, check=check, 
                                capture_output=True, text=True, input=None)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        print(f"Exit code: {e.returncode}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)


def setup_directories():
    """Create and set up the required directories."""
    print("Setting up directories...")
    
    base_dir = Path("/var/local/kde-dev")
    home_dir = base_dir / "home"
    kde_dir = base_dir / "kde"
    
    run_command(["sudo", "mkdir", "-p", str(home_dir), str(kde_dir)])    
    user_id = os.getuid()
    run_command(["sudo", "chown", f"{user_id}:{user_id}", str(home_dir), str(kde_dir)])
    config_dir = home_dir / ".config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Created directories: {home_dir}, {kde_dir}")
    return home_dir, kde_dir


def copy_config(home_dir):

    kde_builder_config = Path("./kde-builder.yaml")
    if not kde_builder_config.exists():
        print(f"Error: {kde_builder_config} not found in current directory")
        sys.exit(1)

    target_config = home_dir / ".config" / "kde-builder.yaml"
    shutil.copy2(kde_builder_config, target_config)

    print(f"✓ Copied {kde_builder_config} to {target_config}")


def create_distrobox():
    """Create the distrobox container."""
    print("Creating distrobox container...")
    
    cmd = [
        "distrobox", "create",
        "--name", "kde-dev",
        "--home", "/var/local/kde-dev/home",
        "--init",
        "--additional-packages", "systemd",
        "--pull",
        "--image", "ghcr.io/ledif/ublue-kde-dev:latest"
    ]
    
    run_command(cmd)
    print("✓ Created distrobox container 'kde-dev'")


def build_kde_workspace():
    """Build the KDE workspace."""
    print("\nPlasma Desktop will now be built from master. This will take a while.\n")
    
    cache_dir = Path("/var/local/kde-dev/home/.cache")
    if cache_dir.exists():
        run_command(["sudo", "rm", "-rf", str(cache_dir)])
        print("✓ Cleared cache directory")

    cmd = f'yes | kde-builder workspace'
    run_command([
        "podman", "exec", "-it", "--user", str(os.getuid()), "kde-dev", 
        "bash", "-c", cmd
    ])

    print("✓ KDE build completed")


def init_command():
    """Initialize the KDE development environment."""
    print("KDE Development Environment Initialization")
    print("=" * 40)
    
    try:
        # Check if running as root
        if os.getuid() == 0:
            print("Error: This script should not be run as root")
            sys.exit(1)
        
        # Check if required commands exist
        required_commands = ["sudo", "distrobox", "podman"]
        for cmd in required_commands:
            if not shutil.which(cmd):
                print(f"Error: {cmd} not found. Please install it first.")
                sys.exit(1)
        
        # Setup process
        home_dir, kde_dir = setup_directories()
        copy_config(home_dir)
        create_distrobox()
        build_kde_workspace()
        
        print("\n" + "=" * 40)
        print("✓ KDE development environment setup completed!")
        print(f"✓ Container name: kde-dev")
        print(f"✓ Home directory: {home_dir}")
        print(f"✓ KDE directory: {kde_dir}")
        print("\nTo enter the development environment, run:")
        print("  distrobox enter kde-dev")
        
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def install_session_command():
    """Install a KDE session from the development environment."""
    print("KDE Session Installation")
    print("=" * 30)
    
    try:
        # Start the kde-dev container
        print("Starting kde-dev container...")
        run_command(["podman", "container", "start", "kde-dev"])
        
        # Check if the desktop file exists in the container
        desktop_file_path = "/usr/local/share/wayland-sessions/plasmawayland-dev6.desktop"
        print("Checking if desktop file exists in container...")
        
        result = run_command([
            "podman", "container", "exec", "kde-dev", 
            "test", "-f", desktop_file_path
        ], check=False)
        
        if result.returncode != 0:
            print(f"Error: The file '{desktop_file_path}' does not exist in the KDE development container.")
            print("You will need to run 'python ublue-kde-dev.py init' first.")
            sys.exit(1)
        
        print("✓ Desktop file found in container")
        
        # Set up overlayfs over /usr
        print("Setting up overlayfs over /usr (making it temporarily mutable until next reboot)...")
        print("This recipe will need to be run again on every reboot.")
        run_command(["sudo", "bootc", "usr-overlay"], False)
        print("✓ usr-overlay enabled")
        
        # Set up X11 permissions script
        print("Setting up X11 permissions...")
        x11_script_content = 'chown -f -R $USER:$USER /tmp/.X11-unix'
        x11_script_path = "/etc/profile.d/set_tmp_x11_permissions.sh"
        
        # Write the script using sudo tee
        proc = subprocess.Popen(
            ["sudo", "tee", x11_script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        proc.communicate(input=x11_script_content)
        print("✓ X11 permissions script created")
        
        # Copy desktop file from container to home directory
        print("Copying desktop file from container...")
        home_dir = Path.home()
        desktop_file_local = home_dir / "plasmawayland-dev6.desktop"
        
        run_command([
            "podman", "container", "cp", 
            f"kde-dev:{desktop_file_path}",
            str(desktop_file_local)
        ])
        print("✓ Desktop file copied to home directory")
        
        # Modify the desktop file's Exec line
        print("Modifying desktop file...")
        with open(desktop_file_local, 'r') as f:
            content = f.read()
        
        # Replace the Exec line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('Exec='):
                lines[i] = f"Exec={home_dir}/.local/bin/start-plasma-dev-session"
                break
        
        modified_content = '\n'.join(lines)
        with open(desktop_file_local, 'w') as f:
            f.write(modified_content)
        print("✓ Desktop file modified")
        
        # Move desktop file to system location
        print("Installing desktop file to system...")
        run_command([
            "sudo", "mv", str(desktop_file_local), 
            "/usr/share/wayland-sessions/"
        ])
        print("✓ Desktop file installed to /usr/share/wayland-sessions/")
        
        # Create the plasma dev session script
        print("Creating plasma development session script...")
        local_bin_dir = home_dir / ".local" / "bin"
        local_bin_dir.mkdir(parents=True, exist_ok=True)
        
        session_script_path = local_bin_dir / "start-plasma-dev-session"
        session_script_content = f"""{home_dir}/kde/usr/lib64/libexec/kactivitymanagerd & disown
{home_dir}/kde/usr/lib64/libexec/plasma-dbus-run-session-if-needed {home_dir}/kde/usr/lib64/libexec/startplasma-dev.sh -wayland"""
        
        with open(session_script_path, 'w') as f:
            f.write(session_script_content)
        
        # Make the script executable
        session_script_path.chmod(0o755)
        print("✓ Plasma development session script created and made executable")
        
        print("\n" + "=" * 30)
        print("✓ KDE session installation completed!")
        print("Log out to see the Plasma development session in SDDM.")
        
    except KeyboardInterrupt:
        print("\nInstallation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def main():
    """Main function to handle command-line arguments and dispatch to appropriate functions."""
    parser = argparse.ArgumentParser(
        description="KDE Development Environment Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s init                Initialize the development environment
  %(prog)s install-session     Install KDE session from development build
        """)
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize the KDE development environment')
    
    # Install-session command
    session_parser = subparsers.add_parser('install-session', help='Install KDE session from development build')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_command()
    elif args.command == 'install-session':
        install_session_command()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
