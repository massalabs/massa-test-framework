# Massa Cluster Manager Module

This module provides classes and functions for managing Massa Cluster deployments in Kubernetes. It offers a convenient way to interact with Massa Cluster configurations and perform common operations.

## Classes
- `MassaClusterConfig`: Data class representing configuration for a MassaCluster deployment.
- `MassaClusterManager`: A class for managing Massa Cluster deployments in Kubernetes.
- `LaunchInfo`: Represents information about a launched service and its associated pods.

## Usage

1. Import the required classes from this module.
2. Create a `MassaClusterConfig` instance with your Massa Cluster configuration.
3. Create a `MassaClusterManager` instance with your Kubernetes configuration.
4. Use the provided methods to initialize, manage, and terminate Massa Cluster deployments.
