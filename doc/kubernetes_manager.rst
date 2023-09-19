```rst
Kubernetes Manager
==================

This tutorial provides an overview of how to use the `KubernetesManager` class from the `kubernetes_manager.py` script to manage a Kubernetes cluster. The `KubernetesManager` class allows you to create namespaces, pods, services, and perform other Kubernetes-related operations.

.. note::
   Ensure you have the Kubernetes Python client library (`kubernetes`) installed before proceeding with this tutorial.

Getting Started
---------------

Before you begin, make sure you have the necessary Python environment set up.

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
