# Module 4: Networking

## Overview

This module covers Oracle Cloud Infrastructure networking services, including Virtual Cloud Networks (VCN), load balancers, and network security.

## Learning Objectives

By the end of this module, you will be able to:
- Design and create Virtual Cloud Networks
- Configure subnets and route tables
- Implement network security using security lists and NSGs
- Set up load balancers
- Configure VPN and FastConnect
- Understand DNS and traffic management

## Topics Covered

### 4.1 Virtual Cloud Network (VCN) Fundamentals
- VCN architecture and components
- CIDR blocks and IP addressing
- Internet Gateway (IGW)
- NAT Gateway
- Service Gateway
- Dynamic Routing Gateway (DRG)

### 4.2 Subnets
- Public vs. Private subnets
- Subnet security
- Route tables
- DHCP options

### 4.3 Network Security
- Security Lists
- Network Security Groups (NSGs)
- Stateful vs. Stateless rules
- Best practices for network security

### 4.4 Load Balancing
- Load Balancer types (Public, Private)
- Backend sets and health checks
- SSL/TLS termination
- Session persistence

### 4.5 Hybrid Connectivity
- Site-to-Site VPN
- FastConnect
- VPN over FastConnect
- Network topology patterns

### 4.6 DNS and Traffic Management
- DNS service
- Traffic Management policies
- Health checks and failover

## Prerequisites

- Completion of Module 1
- Strong understanding of TCP/IP networking
- Knowledge of routing and subnetting
- Understanding of firewall concepts

## Hands-on Exercises

1. Creating a VCN with the VCN Wizard
2. Creating public and private subnets
3. Configuring route tables and gateways
4. Setting up security lists and NSGs
5. Creating a load balancer
6. Configuring a Site-to-Site VPN

## Code Examples

```bash
# Example: Creating a VCN using OCI CLI
oci network vcn create \
  --compartment-id <compartment-ocid> \
  --cidr-block 10.0.0.0/16 \
  --display-name my-vcn

# Example: Creating a subnet
oci network subnet create \
  --compartment-id <compartment-ocid> \
  --vcn-id <vcn-ocid> \
  --cidr-block 10.0.1.0/24 \
  --display-name public-subnet \
  --prohibit-public-ip-on-vnic false
```

## Network Architecture Patterns

### Pattern 1: Simple Web Application
- Public subnet for web tier
- Private subnet for application tier
- Private subnet for database tier

### Pattern 2: Hub and Spoke
- Central hub VCN for shared services
- Spoke VCNs for different environments/applications
- Local Peering Gateway for connectivity

## Additional Resources

- OCI Networking Documentation
- Network Architecture Patterns
- VCN Troubleshooting Guide
- Security Best Practices
