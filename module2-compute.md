# Module 2: Compute Services

## Overview

This module covers Oracle Cloud Infrastructure Compute services, including virtual machines, bare metal instances, and container services.

## Learning Objectives

By the end of this module, you will be able to:
- Create and manage compute instances
- Understand different instance types and shapes
- Configure instance networking
- Manage instance lifecycle
- Work with custom images

## Topics Covered

### 2.1 Compute Instance Types
- Virtual Machines (VM)
- Bare Metal Instances
- Dedicated Virtual Machine Hosts

### 2.2 Instance Shapes
- Standard Shapes
- Dense I/O Shapes
- GPU Shapes
- High Performance Computing (HPC) Shapes
- Flexible Shapes

### 2.3 Creating and Managing Instances
- Launching an instance
- Connecting to instances (SSH, RDP)
- Instance metadata
- Instance lifecycle management (start, stop, reboot, terminate)

### 2.4 Custom Images
- Creating custom images
- Importing and exporting images
- Image management and versioning

### 2.5 Instance Configuration
- Boot volumes
- Block volumes attachment
- Network configuration
- Security lists and network security groups

## Prerequisites

- Completion of Module 1
- Understanding of Linux/Windows server administration
- SSH/RDP client software

## Hands-on Exercises

1. Creating a Linux compute instance
2. Creating a Windows compute instance
3. Configuring instance networking
4. Creating and using custom images
5. Managing instance lifecycle

## Code Examples

```bash
# Example: Using OCI CLI to launch an instance
oci compute instance launch \
  --availability-domain <AD> \
  --compartment-id <compartment-ocid> \
  --shape VM.Standard2.1 \
  --subnet-id <subnet-ocid> \
  --image-id <image-ocid>
```

## Additional Resources

- OCI Compute Documentation
- Instance Shape Specifications
- Best Practices for Compute Instances
