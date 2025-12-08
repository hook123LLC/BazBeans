# BazBeans Deployment Guide

> **Note:** This deployment guide has been expanded and improved. Please see the [Agent Deployment Guide](AGENT-DEPLOYMENT.md) for comprehensive deployment instructions.

## Quick Links

- **For Agent Deployment:** [Agent Deployment Guide](AGENT-DEPLOYMENT.md) - Complete deployment process
- **For CLI Setup:** [CLI Setup Guide](SETUP-CLI.md) - Install the management interface
- **For System Architecture:** [Architecture Guide](ARCHITECTURE.md) - Understand the system design

## Deployment Overview

BazBeans deployment typically involves:

1. **Setting up Redis** as the shared state backend
2. **Deploying Node Agents** on each server you want to manage
3. **Installing the CLI** for administrative control
4. **Configuring Load Balancer** integration (optional)

## Getting Started

### For Production Deployment

See the [Agent Deployment Guide](AGENT-DEPLOYMENT.md) for:
- System prerequisites
- Step-by-step deployment process
- Production configuration
- Security considerations
- Monitoring and troubleshooting

### For Development/Testing

1. Start with [CLI Setup Guide](SETUP-CLI.md) to install the management tools
2. See [Examples](examples/) for integration patterns
3. Review [Architecture Guide](ARCHITECTURE.md) for system understanding

## Need Help?

- Check the [Troubleshooting Guide](TROUBLESHOOTING.md) for common deployment issues
- Review the [Agent Deployment Guide](AGENT-DEPLOYMENT.md) for detailed instructions
- See the [README.md](README.md) for an overview of capabilities