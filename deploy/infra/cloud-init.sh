#!/bin/sh
# First-boot setup of the Lightsail instance, run once as root.
# Progress: ssh in and run `cloud-init status --wait` or read /var/log/cloud-init-output.log.
#
# POSIX sh only: Lightsail prepends its own #!/bin/sh launch script to user_data,
# so this runs under dash whatever the shebang says (no pipefail, no bashisms).
set -eu

# 2GB swap: the stack needs a bit more than the 1GB plan's RAM at peaks.
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
echo 'vm.swappiness=10' > /etc/sysctl.d/99-swap.conf
sysctl --system

# Docker Engine with the compose plugin.
# Downloaded first: without pipefail a failed curl piped into sh would pass.
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sh /tmp/get-docker.sh
usermod -aG docker ubuntu

# Where CI puts compose.yaml, Caddyfile, init-mongo.js and .env.
mkdir -p /opt/agent-demo
chown ubuntu:ubuntu /opt/agent-demo
chmod 700 /opt/agent-demo
