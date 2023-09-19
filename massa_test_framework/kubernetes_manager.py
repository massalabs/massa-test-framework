"""
Kubernetes Manager Module

This module provides classes and functions for managing Kubernetes resources, including Pods and Services.
It offers a convenient way to interact with Kubernetes clusters and perform common operations.

Classes:
    KubernetesManager: A class for managing Kubernetes resources in a cluster.
    PodConfig: Configuration for a Kubernetes Pod.
    ServiceConfig: Configuration for a Kubernetes Service.
    ServicePortConfig: Configuration for a Kubernetes Service Port.

Dependencies:
    This module relies on the Kubernetes Python client library and other dependencies.
    Make sure to install the necessary packages before using this module.

Usage:
    1. Import the required classes from this module.
    2. Create a KubernetesManager instance with your cluster configuration.
    3. Use the provided classes and methods to manage Pods and Services in your cluster.

Example:
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
"""

from dataclasses import dataclass
from kubernetes import client, config


@dataclass
class PodConfig:
    """Configuration for a Kubernetes Pod.

    Attributes:
        namespace (str): The namespace in which the pod will be created.
        container_name (str): The name of the container within the pod.
        docker_image (str): The Docker image to be used for the container.
        pod_name (str): The name of the pod.
        opened_ports (list[int]): A list of port numbers to be opened in the container.
        authorized_keys (str): Authorized SSH keys to be added to the pod's environment.
    """

    namespace: str
    container_name: str
    docker_image: str
    pod_name: str
    opened_ports: list[int]
    authorized_keys: str

@dataclass
class ServicePortConfig:
    """
    Configuration for a Kubernetes Service Port.

    Attributes:
        port (int): The port number to expose.
        target_port (int): The port to forward traffic to within the pod.
        node_port (int): The node port for external access.
    """

    port: int
    target_port: int
    node_port: int

@dataclass
class ServiceConfig:
    """
    Configuration for a Kubernetes Service.

    Attributes:
        namespace (str): The namespace in which the service will be created.
        pod_config (PodConfig): The PodConfig object associated with this service.
        service_name (str): The name of the service.
        external_ips (list[str]): List of external IP addresses for the service.
        service_ports (list of ServicePortConfig): List of ServicePortConfig objects.
    """

    namespace: str
    pod_config: PodConfig
    service_name: str
    external_ips: list[str]
    service_ports: list[ServicePortConfig]

@dataclass
class DeployConfig:
    """
    Configuration for deploying a Kubernetes service and associated pod.

    Attributes:
        namespace (str): The namespace in which the service and pod will be created.
        pod_config (PodConfig): The PodConfig object associated with this deployment.
        service_config (ServiceConfig): The ServiceConfig object associated with this deployment.
    """

    namespace: str
    pod_config: PodConfig
    service_config: ServiceConfig

class KubernetesManager:
    """
    Class for managing a Kubernetes cluster.
    """

    # Load Kubernetes configuration
    def __init__(self, config_file=None):
        """
        Initialize a KubernetesManager object.

        Args:
            config_file (str, optional): Path to a Kubernetes configuration file.
            If None, in-cluster config is used.
        """
        if config_file:
            config.load_kube_config(config_file)
        else:
            config.load_incluster_config()

    # Function to create a namespace if it does not exist
    def create_namespace(self, namespace):
        """
        Create a Kubernetes namespace if it does not exist.

        Args:
            namespace (str): The name of the namespace to create.
        """
        api_instance = client.CoreV1Api()

        try:
            api_instance.read_namespace(namespace)
            print(f"Namespace {namespace} already exists.")
        except client.rest.ApiException as e:
            if e.status == 404:
                body = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))
                api_instance.create_namespace(body)
                print(f"Namespace {namespace} created successfully.")
            else:
                print(f"Error checking namespace {namespace}: {e}")
        except Exception as e:
            print(f"Error creating namespace {namespace}: {e}")

    # Function to start a set of services with a specified Docker image and authorized keys
    def create_pod(self, pods_config: PodConfig):
        """
        Create a Kubernetes pod.

        Args:
            pods_config (PodConfig): The PodConfig object containing pod configuration.
        """
        api_instance = client.CoreV1Api()

        env_var = client.V1EnvVar(
            name="AUTHORIZED_KEYS", value=pods_config.authorized_keys
        )
        container_ports = [
            client.V1ContainerPort(container_port=port)
            for port in pods_config.opened_ports
        ]

        container = client.V1Container(
            name=pods_config.pod_name,
            image=pods_config.docker_image,
            ports=container_ports,
            env=[env_var],
        )

        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=pods_config.pod_name, labels={"app": pods_config.pod_name}
            ),
            spec=client.V1PodSpec(containers=[container]),
        )

        try:
            api_instance.create_namespaced_pod(pods_config.namespace, pod)
            print(f"Pod {pods_config.pod_name} started successfully.")
        except Exception as e:
            print(f"Error starting pod {pods_config.pod_name}: {e}")

    # Function to create a service from external access
    def create_service(self, config: ServiceConfig):
        """
        Create a Kubernetes service for external access.

        Args:
            config (ServiceConfig): The ServiceConfig object containing service configuration.
        """
        api_instance = client.CoreV1Api()
        ports = []
        for port_config in config.service_ports:
            service_port = client.V1ServicePort(
                port=port_config.port,
                target_port=port_config.target_port,
                node_port=port_config.node_port,
            )
            ports.append(service_port)

        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=config.service_name),
            spec=client.V1ServiceSpec(
                type="NodePort",
                selector={"app": config.service_name},
                ports=ports,
                external_i_ps=config.external_ips,
            ),
        )

        try:
            api_instance.create_namespaced_service(config.namespace, service)
            print(f"Service {config.service_name} created successfully.")
        except Exception as e:
            print(f"Error creating Service {config.service_name}: {e}")

    def get_pods_info(self, namespace):
        """
        Get information about pods in a Kubernetes namespace.

        Args:
            namespace (str): The namespace to query.

        Returns:
            list: A list of dictionaries containing pod information.
        """
        api_instance = client.CoreV1Api()
        pods_info = []

        try:
            # List Pods in the specified namespace
            pods = api_instance.list_namespaced_pod(namespace)

            for pod in pods.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "namespace": namespace,
                    "status": pod.status.phase,
                    "container_ports": [],
                }

                # Extract and add the container ports to the pod_info dictionary
                for container in pod.spec.containers:
                    for port in container.ports:
                        container_port_info = {
                            "name": port.name,
                            "container_port": port.container_port,
                            "protocol": port.protocol,
                        }
                        pod_info["container_ports"].append(container_port_info)

                pods_info.append(pod_info)

        except Exception as e:
            print(f"Error getting pods in namespace {namespace}: {e}")

        return pods_info

    # Function to get the informations of a service
    def get_services_info(self, namespace):
        """
        Get information about services in a Kubernetes namespace.

        Args:
            namespace (str): The namespace to query.

        Returns:
            list: A list of dictionaries containing service information.
        """
        api_instance = client.CoreV1Api()
        services_info = []

        try:
            services = api_instance.list_namespaced_service(namespace)

            for service in services.items:
                service_info = {"name": service.metadata.name, "ports": []}

                for port in service.spec.ports:
                    service_info["ports"].append(
                        {
                            "name": port.name,
                            "port": port.port,
                            "target_port": port.target_port,
                            "node_port": port.node_port,
                        }
                    )

                services_info.append(service_info)

        except Exception as e:
            print(f"Error getting services in namespace {namespace}: {e}")

        return services_info

    # Function to remove a set of services
    def remove_services(self, namespace, service_names=None):
        """
        Remove services from a Kubernetes namespace.

        Args:
            namespace (str): The namespace from which to remove services.
            service_names (list, optional): List of service names to remove.
            If None, all services in the namespace are removed.
        """
        api_instance = client.CoreV1Api()

        try:
            if service_names:
                for service_name in service_names:
                    api_instance.delete_namespaced_pod(service_name, namespace)
                    print(f"Service {service_name} killed successfully.")
            else:
                pods = api_instance.list_namespaced_pod(namespace)
                for pod in pods.items:
                    api_instance.delete_namespaced_pod(pod.metadata.name, namespace)
                    print(f"Service {pod.metadata.name} killed successfully.")
        except Exception as e:
            print(f"Error killing services in namespace {namespace}: {e}")

    # Function to remove a namespace
    def remove_namespace(self, namespace):
        """
        Remove a Kubernetes namespace.

        Args:
            namespace (str): The namespace to remove.
        """
        api_instance = client.CoreV1Api()

        try:
            api_instance.delete_namespace(
                namespace, body=client.V1DeleteOptions(propagation_policy="Foreground")
            )
            print(f"Namespace {namespace} removed successfully.")
        except Exception as e:
            print(f"Error removing namespace {namespace}: {e}")
