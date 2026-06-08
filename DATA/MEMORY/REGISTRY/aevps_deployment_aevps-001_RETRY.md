# AEVPS DEPLOYMENT RETRY

Timestamp: 2026-06-08T19:09:36Z
Host Surface: RUBIII
Operator: d_ny5u5
Authority Body: /mnt/h/AETHIEAOPSYS

## Corrected Target
Name: aevps-001
Type: cpx22
Image: ubuntu-24.04
Location: ash
SSH Key: RUBIII-d_ny5u5
Firewall: aevps-fw-001
Firewall ID: 11106105

## Prior Failures
cx22: invalid server type name
cx23: unsupported location for server type in ash

## Current Status Before Retry
AEVPS: NOT DEPLOYED
Server: NOT CREATED
Firewall: CREATED
Firewall SSH Rule: FIXED
Private Network: NONE

## Doctrine
Host executes.
AEUSB carries.
HCLOUD hosts only after successful server creation.
AEVPS is not born until server describe and server ip succeed.
DON'T MINGLE.
