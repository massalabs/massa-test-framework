```rst
Kubernetes Manager
==================

This tutorial provides an overview of how to use the `KubernetesManager` class from the `kubernetes_manager.py` script to manage a Kubernetes cluster. The `KubernetesManager` class allows you to create namespaces, pods, services, and perform other Kubernetes-related operations.

.. note::
   Ensure you have the Kubernetes Python client library (`kubernetes`) installed before proceeding with this tutorial.

Getting Started
---------------

Before you begin, make sure you have the necessary Python environment set up with the `kubernetes` library installed. You can install it using `pip`:

```bash
pip install kubernetes
```

Once you have the library installed, you can use the `KubernetesManager` class to interact with your Kubernetes cluster.

Import the `KubernetesManager` class in your Python script:

```python
from kubernetes_manager import KubernetesManager
```

Creating a Kubernetes Namespace
-------------------------------

To create a new Kubernetes namespace using the `KubernetesManager` class, follow these steps:

1. Create an instance of `KubernetesManager`:

```python
k8s_manager = KubernetesManager()
```

2. Use the `create_namespace` method to create a namespace. Replace `my_namespace` with your desired namespace name:

```python
namespace_name = "my_namespace"
k8s_manager.create_namespace(namespace_name)
```

Creating a Kubernetes Pod
-------------------------

To create a new Kubernetes pod using the `KubernetesManager` class, follow these steps:

1. Define the configuration for the pod using a `PodConfig` object:

```python
from kubernetes_manager import PodConfig

pod_config = PodConfig(
    namespace="my_namespace",
    container_name="my-container",
    docker_image="my-docker-image",
    pod_name="my-pod",
    opened_ports=[80, 443],
    authorized_keys="ssh-rsa my-public-key"
)
```

2. Create an instance of `KubernetesManager`:

```python
k8s_manager = KubernetesManager()
```

3. Use the `create_pod` method to start the pod:

```python
k8s_manager.create_pod(pod_config)
```

Creating a Kubernetes Service
-------------------------------

To create a Kubernetes service for external access using the `KubernetesManager` class, follow these steps:

1. Define the configuration for the service using a `ServiceConfig` object:

```python
from kubernetes_manager import ServiceConfig, ServicePortConfig

service_ports = [ServicePortConfig(port=80, target_port=8080, node_port=30000)]

service_config = ServiceConfig(
    namespace="my_namespace",
    pod_config=pod_config,
    service_name="my-service",
    external_ips=["1.2.3.4"],
    service_ports=service_ports
)
```

2. Create an instance of `KubernetesManager`:

```python
k8s_manager = KubernetesManager()
```

3. Use the `create_service` method to create the service:

```python
k8s_manager.create_service(service_config)
```

Viewing Kubernetes Cluster Information
--------------------------------------

You can also use the following methods to view information about your Kubernetes cluster:

- `get_pods_info`: Retrieve information about pods in a specific namespace.
- `get_services_info`: Retrieve information about services in a specific namespace.

For example:

```python
pod_info = k8s_manager.get_pods_info("my_namespace")
service_info = k8s_manager.get_services_info("my_namespace")
```

Cleaning Up Resources
---------------------

To remove Kubernetes resources such as pods, services, or namespaces, you can use the `remove_services` and `remove_namespace` methods of the `KubernetesManager` class.

For example, to remove a specific service:

```python
k8s_manager.remove_services("my_namespace", service_names=["my-service"])
```

To remove an entire namespace:

```python
k8s_manager.remove_namespace("my_namespace")
```

Massa Simulator Example
-----------------------

```python
from kubernetes_manager import KubernetesManager, PodConfig, ServiceConfig, ServicePortConfig

if __name__ == "__main__":

    # Create a KubernetesManager instance
    manager = KubernetesManager("PATH_TO/kubeconfig.yml")

    # Example usage:
    namespace = "massa-simulator"
    opened_ports = [22, 33034, 33035, 33036, 33037, 33038, 31244, 31245] # SSH PORT 22 + MASSA PORTS
    external_ips = ["10.4.3.2"]
    docker_image = "aoudiamoncef/ubuntu-sshd"  # Specify your Docker image
    authorized_keys = "ssh-ed25519 XXX_MY_SSH_KEY_XXX simulator@massa.net"

    node_1_pod_config = PodConfig(namespace, "massa-node-1-container", docker_image, "massa-node-1-pod", opened_ports, authorized_keys)
    node_2_pod_config = PodConfig(namespace, "massa-node-2-container", docker_image, "massa-node-2-pod", opened_ports, authorized_keys)
    node_3_pod_config = PodConfig(namespace, "massa-node-3-container", docker_image, "massa-node-3-pod", opened_ports, authorized_keys)

    node_1_service_port_config = ServicePortConfig(20001, 22, 30001)
    node_2_service_port_config = ServicePortConfig(20002, 22, 30002)
    node_3_service_port_config = ServicePortConfig(20003, 22, 30003)

    node_1_service_config = ServiceConfig(namespace, node_1_pod_config, "massa-node-1-service", external_ips, [node_1_service_port_config])
    node_2_service_config = ServiceConfig(namespace, node_2_pod_config, "massa-node-2-service", external_ips, [node_2_service_port_config])
    node_3_service_config = ServiceConfig(namespace, node_3_pod_config, "massa-node-3-service", external_ips, [node_3_service_port_config])

    # Create a namespace if it does not exist
    manager.create_namespace(namespace)

    # Start services with the specified Docker image and authorized keys
    manager.create_pod(node_1_pod_config)
    manager.create_pod(node_2_pod_config)
    manager.create_pod(node_3_pod_config)

    # Wait for a moment to allow services to start
    time.sleep(3)
    
    # Get the informations of the pods
    pods_info = manager.get_pods_info(namespace)
    # Print the obtained information
    for pod_info in pods_info:
        print(f"Pod Name: {pod_info['name']}")
        print(f"Status: {pod_info['status']}")
        print("Container Ports:")
        for container_port_info in pod_info['container_ports']:
            print(f"Container Port: {container_port_info['container_port']}")
            print(f"Protocol: {container_port_info['protocol']}")

    # Create NodePort services with specified node ports
    manager.create_service(node_1_service_config)
    manager.create_service(node_2_service_config)
    manager.create_service(node_3_service_config)

    # Wait for a moment to allow services to start
    time.sleep(3)

    # Get the informations of the services
    services_info = manager.get_services_info(namespace)
    print("Available Services:")
    for service_info in services_info:
        print(f"Service Name: {service_info['name']}")
        print("Ports:")
        for port_info in service_info['ports']:
            print(f"  Port: {port_info['port']}, Target Port: {port_info['target_port']}, Node Port: {port_info['node_port']}")
        print("\n")

    # Wait for a moment before removing the namespace
    time.sleep(60)

    # Remove the namespace
    manager.remove_namespace(namespace)
```
