import os
import re
import subprocess
import json
import requests

# Slack webhook URL
slack_webhook_url = "https://hooks.slack.com/services/<webhook-key>"

# Getting the VM details for disk check
# Get the instance name from the hostname
instance_name = subprocess.check_output("hostname").decode("utf-8").strip()

# Get the zone info from vm's metadata agent
metadata = json.loads(subprocess.check_output("curl -H 'Metadata-Flavor: Google' "
                                              "http://metadata.google.internal/computeMetadata/v1/instance/?recursive"
                                              "=true", shell=True).decode("utf-8"))
zone = metadata['zone'].split('/')[-1]
threshold_percentage = 80
critical_percentage = 90

# Use the gcloud command to get the disk size
describe_command = "gcloud compute disks describe {} --zone={} --format=json".format(instance_name, zone)
disk_info = json.loads(subprocess.check_output(describe_command, shell=True).decode("utf-8"))

current_disk_gb = int(disk_info['sizeGb'])  # Use 'sizeGb' instead of 'sizeGB'

# Calculate the expand disk percent
expand_disk = int(current_disk_gb * 1.1)


def notify_before(message):
    payload = {
        "text": message
    }
    try:
        response = requests.post(slack_webhook_url, json=payload)
        if response.status_code == 200:
            print("Slack notification sent successfully.")
        else:
            print("Failed to send Slack notification.")
    except Exception as e:
        print("Error sending Slack notification:", str(e))


# Resize the disk
def resize_disk(instance_name, expand_disk, zone):
    try:
        resize_command = "gcloud compute disks resize {} --size={}GB --zone={}".format(instance_name, expand_disk, zone)
        subprocess.call(resize_command, shell=True)
        message = "Disk '{}' resized from {}GB to {}GB.".format(instance_name, current_disk_gb, expand_disk)
        notify_before(message)
        return "Disk '{}' resized from {}GB to {}GB.".format(instance_name, current_disk_gb, expand_disk)
    except subprocess.CalledProcessError as e:
        message = "Error resizing disk '{}': {}".format(instance_name, e)
        notify_before(message)
        return "Error resizing disk '{}': {}".format(instance_name, e)


def check_disk_usage(instance_name, zone, threshold_percentage, expand_disk):
    check_disk = "df -H | grep -vE '^Filesystem|tmpfs|cdrom|loop|udev|boot|overlay' | grep dev"
    output = subprocess.check_output(check_disk, shell=True).decode("utf-8")
    current_usage = int(re.search(r'(\d+)%', output).group(1))

    # Get a list of all mounted partitions
    df_command = subprocess.check_output("df -H | grep -vE '^Filesystem|tmpfs|cdrom|loop|udev|boot|overlay' | grep dev", shell=True).decode("utf-8")
    lines = df_command.split('\n')[1:]  # Skip the header line

    for line in lines:
        fields = line.split()
        if len(fields) >= 6:
            filesystem = fields[0]
            mount_point = fields[5]
            current_usage = int(fields[4].rstrip('%'))

            if current_usage > threshold_percentage:
                message = "Disk space on '{}' (Mount Point: '{}') is above {}%".format(filesystem, mount_point, threshold_percentage)
                notify_before(message)
            elif current_usage > critical_percentage:
                print(resize_disk(instance_name, expand_disk, zone))
            else:
                print("Disk usage of '{}' is at {}%, no resize needed.".format(mount_point, current_usage))


check_disk_usage(instance_name, zone, threshold_percentage, expand_disk)
