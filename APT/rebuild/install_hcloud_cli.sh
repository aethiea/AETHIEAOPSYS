#!/usr/bin/env bash
set -euo pipefail

echo "Installing Hetzner hcloud CLI..."
sudo apt update
sudo apt install -y hcloud-cli

echo
echo "hcloud path:"
command -v hcloud

echo
echo "hcloud version:"
hcloud version
