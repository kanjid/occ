# Module 3: Storage Services

## Overview

This module explores Oracle Cloud Infrastructure storage services, including block volumes, file storage, object storage, and archive storage.

## Learning Objectives

By the end of this module, you will be able to:
- Understand different OCI storage options
- Create and manage block volumes
- Work with object storage buckets
- Implement file storage solutions
- Choose appropriate storage for different use cases

## Topics Covered

### 3.1 Block Volume Service
- Creating block volumes
- Attaching volumes to instances
- Volume performance levels
- Volume backups and clones
- Volume groups

### 3.2 Object Storage
- Buckets and objects
- Storage tiers (Standard, Infrequent Access, Archive)
- Pre-authenticated requests
- Object lifecycle policies
- Multipart uploads

### 3.3 File Storage Service
- Creating file systems
- Mount targets
- Export options
- Snapshots
- NFS protocol support

### 3.4 Boot Volumes
- Boot volume management
- Boot volume backups
- Detaching and reattaching boot volumes

### 3.5 Data Transfer Services
- Data Transfer Appliance
- Data Transfer Service
- Storage Gateway

## Prerequisites

- Completion of Module 1 and Module 2
- Understanding of storage concepts (block, file, object)
- Basic knowledge of file systems

## Hands-on Exercises

1. Creating and attaching block volumes
2. Creating object storage buckets
3. Uploading and managing objects
4. Setting up file storage
5. Configuring lifecycle policies
6. Creating volume backups

## Code Examples

```bash
# Example: Creating an object storage bucket using OCI CLI
oci os bucket create \
  --compartment-id <compartment-ocid> \
  --name my-bucket \
  --public-access-type NoPublicAccess

# Example: Uploading an object
oci os object put \
  --bucket-name my-bucket \
  --file /path/to/file \
  --name object-name
```

## Storage Decision Matrix

| Use Case | Recommended Storage |
|----------|-------------------|
| Database storage | Block Volumes |
| Application data | Block Volumes |
| Shared file system | File Storage |
| Backup and archive | Object Storage (Archive tier) |
| Static web content | Object Storage |
| Big data analytics | Object Storage |

## Additional Resources

- OCI Storage Documentation
- Storage Best Practices
- Performance Tuning Guide
