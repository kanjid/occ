# Module 5: Security and Identity Management

## Overview

This module covers Oracle Cloud Infrastructure security and identity management services, including IAM, encryption, security zones, and compliance.

## Learning Objectives

By the end of this module, you will be able to:
- Understand OCI Identity and Access Management (IAM)
- Create and manage users, groups, and policies
- Implement authentication methods
- Configure encryption for data at rest and in transit
- Use security services like Cloud Guard and Security Zones
- Understand compliance and governance

## Topics Covered

### 5.1 Identity and Access Management (IAM)
- Users, Groups, and Policies
- Identity Domains
- Federation and SSO
- Multi-Factor Authentication (MFA)
- API keys and Auth tokens
- Resource principals

### 5.2 IAM Policies
- Policy syntax and structure
- Common policy examples
- Policy inheritance
- Policy debugging and troubleshooting

### 5.3 Compartment Strategy
- Compartment design best practices
- Resource organization
- Policy scope and compartment hierarchy

### 5.4 Data Encryption
- Encryption at rest
- Encryption in transit
- Vault service for key management
- Customer-managed encryption keys (CMEK)
- Secrets management

### 5.5 Security Services
- Cloud Guard
- Security Zones
- Vulnerability Scanning Service
- Web Application Firewall (WAF)
- Bastion Service

### 5.6 Monitoring and Auditing
- Audit logs
- Events service
- Logging service
- Security monitoring best practices

### 5.7 Compliance and Governance
- Compliance frameworks supported by OCI
- Data residency and sovereignty
- Security certifications

## Prerequisites

- Completion of Module 1
- Understanding of authentication and authorization concepts
- Basic knowledge of cryptography
- Familiarity with security best practices

## Hands-on Exercises

1. Creating users, groups, and compartments
2. Writing and testing IAM policies
3. Enabling MFA for users
4. Creating and using vault secrets
5. Configuring Cloud Guard
6. Setting up a Security Zone
7. Reviewing audit logs

## Code Examples

```bash
# Example: Creating a user using OCI CLI
oci iam user create \
  --name john.doe@example.com \
  --description "Application Developer"

# Example: Creating a group
oci iam group create \
  --compartment-id <tenancy-ocid> \
  --name developers \
  --description "Developer group"

# Example: Adding user to group
oci iam group add-user \
  --user-id <user-ocid> \
  --group-id <group-ocid>
```

## Common Policy Examples

### Allow group to manage all resources in a compartment
```
Allow group NetworkAdmins to manage virtual-network-family in compartment NetworkCompartment
```

### Allow group to launch instances
```
Allow group Developers to manage instance-family in compartment Development
Allow group Developers to use virtual-network-family in compartment Development
```

### Allow group to manage object storage
```
Allow group DataEngineers to manage object-family in compartment DataLake
```

## Security Best Practices

1. **Principle of Least Privilege**: Grant only necessary permissions
2. **Enable MFA**: Require MFA for all users, especially administrators
3. **Regular Access Reviews**: Periodically review and update user access
4. **Use Compartments**: Organize resources and apply policies at appropriate levels
5. **Enable Cloud Guard**: Automate security posture management
6. **Monitor Audit Logs**: Regularly review audit logs for suspicious activity
7. **Encrypt Sensitive Data**: Use Vault for managing encryption keys
8. **Use Service Limits**: Set and monitor service limits to prevent resource abuse

## Security Architecture Patterns

### Pattern 1: Multi-tier Application Security
- Separate compartments for different tiers
- Network security groups for micro-segmentation
- Bastion service for secure access
- WAF for application protection

### Pattern 2: Data Security
- Encryption at rest for all storage
- Customer-managed keys in Vault
- Private endpoints for data services
- Data classification and tagging

## Compliance Frameworks

OCI supports various compliance frameworks:
- SOC 1, SOC 2, SOC 3
- ISO 27001, 27017, 27018
- PCI DSS
- HIPAA
- GDPR
- FedRAMP

## Additional Resources

- OCI Security Documentation
- IAM Policy Reference
- Security Best Practices Guide
- Cloud Guard Documentation
- Compliance Documentation
