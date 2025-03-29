#!/bin/bash
lsblk
df -h
parted /dev/mmcblk0 resizepart 2 100%
partprobe
resize2fs /dev/mmcblk0p2
lsblk
df -h