#!/usr/bin/env bash

# Maintainer = devops@comapany.in
#
# Test only on Ubuntu
#
# Purpose - Auto expand the disk space by 10%

set -e

# ENVS

THRESHOLD=80
CRITICAL=85

# Root-only run

if [[ $EUID -ne 0 ]]; then
    echo "This script should be run using sudo or as the root user"
    exit 1
fi

# Get disk usage information

disk_usage=$(df -H | grep -vE '^Filesystem|tmpfs|cdrom|loop|udev|boot' | awk '{ print $5 " " $1 }')
vm_name=$(uname -n)

# Check disk space and take action

df -H | grep -vE '^Filesystem|tmpfs|cdrom|loop|udev|boot|overlay' | awk '{ print $5 " " $1 }' | while read -r output; do
    echo "$output"
    used_percentage=$(echo "$output" | awk '{ print $1}' | cut -d'%' -f1 )
    partition=$(echo "$output" | awk '{ print $2 }' )
    if [ $used_percentage -ge $CRITICAL ]; then
        echo "Running out of space \"$partition ($used_percentage%)\" on $(hostname) as expanding 10%"
        # Uncomment and modify the following line to expand disk space if needed.
        # gcloud compute disks resize DISK_NAME --size DISK_SIZE
    elif [ $used_percentage -ge $THRESHOLD ]; then
        echo "Running out of space \"$partition ($used_percentage%)\" on $(hostname) as on $(date)"
        # Implement Slack notification or other alert mechanism here if needed.
    fi
done

# Additional notes or commands can be added below
check_and_resize_disk(instance_name, zone, threshold_percentage, new_size_gb)
