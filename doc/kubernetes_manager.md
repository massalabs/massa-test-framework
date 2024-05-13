# Kubernetes Manager Module

This module provides classes and functions for managing Kubernetes resources, including Pods and Services. It offers a convenient way to interact with Kubernetes clusters and perform common operations.

## Classes
- `KubernetesManager`: A class for managing Kubernetes resources in a cluster.
- `PodConfig`: Configuration for a Kubernetes Pod.
- `ServiceConfig`: Configuration for a Kubernetes Service.
- `ServicePortConfig`: Configuration for a Kubernetes Service Port.
- `DeployConfig`: Configuration for deploying a Kubernetes service and associated pod.
- `ContainerPortInfo`: Represents information about a container port.
- `PodInfo`: Represents information about a Kubernetes pod.
- `PortInfo`: Data class representing information about a service port.
- `ServiceInfo`: Data class representing information about a Kubernetes service.

## Dependencies
This module relies on the Kubernetes Python client library and other dependencies. Make sure to install the necessary packages before using this module.

## Usage

1. Import the required classes from this module.
2. Create a `KubernetesManager` instance with your cluster configuration.
3. Use the provided classes and methods to manage Pods and Services in your cluster.
