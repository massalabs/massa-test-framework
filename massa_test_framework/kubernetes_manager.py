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
        ssh_existing_secret = "massa-credentials"
        opened_ports = [22, 33034, 33035, 33036, 33037, 33038, 31244, 31245]
        prefix = "m"
        suffix = "p"
        external_i_ps = [""10.4.3.2""]
        docker_image = "aoudiamoncef/ubuntu-sshd"  # Specify your Docker image
        ssh_authorized_keys = "ssh-ed25519 XXX_MY_SSH_KEY_XXX simulator@massa.net"
        env_variables = {
            "AUTHORIZED_KEYS": ssh_authorized_keys,
        }

        # Create a namespace
        manager.create_namespace(namespace)
        
        # Create a secret
        manager.create_secret(
            namespace, ssh_existing_secret, env_variables
        )

        # Create environment variables
        secret_env_variables = manager.create_secret_env_variables(
            ssh_existing_secret, env_variables
        )

        # Create pod port configurations
        pod_ports_config = manager.create_pod_port_configs(opened_ports, prefix, suffix)

        node_1_pod_config = PodConfig(namespace, "massa-node-1-container",
          docker_image, "massa-node-1-pod", pod_ports_config, secret_env_variables)
        node_2_pod_config = PodConfig(namespace, "massa-node-2-container",
          docker_image, "massa-node-2-pod", pod_ports_config, secret_env_variables)
        node_3_pod_config = PodConfig(namespace, "massa-node-3-container", 
        docker_image, "massa-node-3-pod", pod_ports_config, secret_env_variables)

        node_1_service_ports_config = manager.create_service_port_configs(opened_ports, 1, prefix, suffix)
        node_2_service_ports_config = manager.create_service_port_configs(opened_ports, 2, prefix, suffix)
        node_3_service_ports_config = manager.create_service_port_configs(opened_ports, 3, prefix, suffix)

        node_1_service_config = ServiceConfig(namespace, node_1_pod_config, 
        "massa-node-1-service", external_i_ps, node_1_service_ports_config)
        node_2_service_config = ServiceConfig(namespace, node_2_pod_config, 
        "massa-node-2-service", external_i_ps, node_2_service_ports_config)
        node_3_service_config = ServiceConfig(namespace, node_3_pod_config, 
        "massa-node-3-service", external_i_ps, node_3_service_ports_config)

        # Start services with the specified Docker image and authorized keys
        manager.create_pod(node_1_pod_config)
        manager.create_pod(node_2_pod_config)
        manager.create_pod(node_3_pod_config)

        # Wait for a moment to allow services to start
        time.sleep(3)

        # Get the informations of the pods
        pods_info = manager.get_pods_info(namespace)
        print("Available Pods:")    
        print(pods_info)
   
        # Create NodePort services with specified node ports
        manager.create_service(node_1_service_config)
        manager.create_service(node_2_service_config)
        manager.create_service(node_3_service_config)

        # Wait for a moment to allow services to start
        time.sleep(3)

        # Get the informations of the services
        services_info = manager.get_services_info(namespace)
        print("Available Services:")    
        print(services_info)

        # Wait for a moment before removing the namespace
        time.sleep(60)

        print("Removing namespace...")
        # Remove the namespace
        manager.remove_namespace(namespace)
"""

import base64
from dataclasses import dataclass
import os
from typing import Optional
from kubernetes import client, config as kube_config


@dataclass
class PodPortConfig:
    """
    Configuration for Kubernetes Pod Port which is a configuration element
    that defines the port number on which a Kubernetes Pod listens
    for incoming traffic.

    Attributes:
        name (str): The name of the port.
        container_port (int): The container_port number to expose.
    """

    name: str
    container_port: int


@dataclass
class PodConfig:
    """Configuration for a Kubernetes Pod.

    Attributes:
        namespace (str): The namespace in which the pod will be created.
        container_name (str): The name of the container within the pod.
        docker_image (str): The Docker image to be used for the container.
        name (str): The name of the pod.
        opened_ports (list[PodPortConfig]): A list of ports to be opened in the container.
        env_variables (list): Envirement variables to be added to the pod's environment.
    """

    namespace: str
    container_name: str
    docker_image: str
    name: str
    opened_ports: list[PodPortConfig]
    env_variables: list


@dataclass
class ServicePortConfig:
    """
    Configuration for Kubernetes Service Port which is a configuration element
    that defines the port number on which a Kubernetes Service listens
    for incoming traffic and specifies how that traffic should be forwarded
    to the Pods associated with the Service.

    Attributes:
        name (str): The name of the port.
        port (int): The port number to expose.
        target_port (int): The port to forward traffic to within the pod.
        node_port (int): The node port for external access.
    """

    name: str
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
        name (str): The name of the service.
        external_i_ps (list[str]): List of external IP addresses for the service.
        service_ports (list of ServicePortConfig): List of ServicePortConfig objects.
    """

    namespace: str
    pod_config: PodConfig
    name: str
    external_i_ps: list[str]
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


@dataclass
class ContainerPortInfo:
    """
    Represents information about a container port.

    Attributes:
        name (str): The name of the container port.
        container_port (int): The port number in the container.
        protocol (str): The protocol used by the port (e.g., "TCP" or "UDP").
    """

    name: str
    container_port: int
    protocol: str


@dataclass
class PodInfo:
    """
    Represents information about a Kubernetes pod.

    Attributes:
        name (str): The name of the pod.
        namespace (str): The namespace in which the pod is located.
        status (str): The status of the pod (e.g., "Running", "Pending", etc.).
        pod_i_ps (list[str]): The IP(s) address of the pod.
        container_ports (list[ContainerPortInfo]): A list of ContainerPortInfo objects representing
            the container ports of the pod.
    """

    name: str
    namespace: str
    status: str
    pod_i_ps: list[str]
    container_ports: list[ContainerPortInfo]


@dataclass
class PortInfo:
    """
    Data class representing information about a service port.

    Attributes:
        name (str): The port name.
        port (int): The port number.
        target_port (int): The target port number.
        node_port (int): The node port number.
    """

    name: str
    port: int
    target_port: int
    node_port: int


@dataclass
class ServiceInfo:
    """
    Data class representing information about a Kubernetes service.

    Attributes:
        name (str): The name of the service.
        namespace (str): The namespace in which the service is located.
        cluster_i_ps (list[str]): A list of cluster IP addresses associated with the service.
        external_i_ps (list[str]): A list of external IP addresses associated with the service.
        ports (list[PortInfo]): A list of PortInfo instances representing service ports.
    """

    name: str
    namespace: str
    cluster_i_ps: list[str]
    external_i_ps: list[str]
    ports: list[PortInfo]


class KubernetesManager:
    """
    Class for managing a Kubernetes cluster.
    """

    # Load Kubernetes configuration
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize a KubernetesManager object.

        Args:
            config_file (str, optional): Path to a Kubernetes configuration file.
            If None, in-cluster config is used.
        """
        if config_file:
            kube_config.load_kube_config(config_file)
        else:
            kube_config.load_incluster_config()

    # Function to create a namespace
    def create_namespace(self, namespace: str):
        """
        Create a Kubernetes namespace if it does not exist.

        Args:
            namespace (str): The name of the namespace to create.
        """
        api_instance = client.CoreV1Api()

        body = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))

        api_instance.create_namespace(body)

    # Function that creates envirement variables
    def create_env_variables(self, env_vars_map: dict):
        """
        Create a list of Kubernetes environment variables from a dictionary.

        Args:
            env_vars_map (dict): A dictionary where keys are environment variable names
                             and values are the corresponding values.

        Returns:
            list: A list of Kubernetes environment variable objects.
        """
        env_vars = []
        for name, value in env_vars_map.items():
            env_var = client.V1EnvVar(name=name)
            if isinstance(value, list):
                # Handle list values with a ConfigMapKeySelector
                env_var.value_from = client.V1EnvVarSource(
                    config_map_key_ref=client.V1ConfigMapKeySelector(
                        name=name,  # Use the same name for ConfigMap and key
                        key=name,
                    )
                )
            else:
                env_var.value = str(value)
            env_vars.append(env_var)
        return env_vars

    # Function to start a set of services with a specified Docker image and authorized keys
    def create_pod(self, pods_config: PodConfig):
        """
        Create a Kubernetes pod.

        Args:
            pods_config (PodConfig): The PodConfig object containing pod configuration.
        """
        api_instance = client.CoreV1Api()

        container_ports = [
            client.V1ContainerPort(
                name=port_config.name, container_port=port_config.container_port
            )
            for port_config in pods_config.opened_ports
        ]

        container = client.V1Container(
            name=pods_config.name,
            image=pods_config.docker_image,
            image_pull_policy="Always",
            ports=container_ports,
            env=pods_config.env_variables,
        )

        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=pods_config.name, labels={"app": pods_config.name}
            ),
            spec=client.V1PodSpec(containers=[container]),
        )

        api_instance.create_namespaced_pod(pods_config.namespace, pod)

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
                name=port_config.name,
                port=port_config.port,
                target_port=port_config.target_port,
                node_port=port_config.node_port,
            )
            ports.append(service_port)

        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=config.name),
            spec=client.V1ServiceSpec(
                type="NodePort",
                selector={"app": config.pod_config.name},
                ports=ports,
                external_i_ps=config.external_i_ps,
            ),
        )

        api_instance.create_namespaced_service(config.namespace, service)

    # Function to create a secret
    def create_secret(self, namespace: str, secret_name: str, data: dict):
        # Create a Kubernetes client
        api_client = client.CoreV1Api()

        # Base64 encode the data
        encoded_data = {
            key: base64.b64encode(value.encode("utf-8")).decode("utf-8")
            for key, value in data.items()
        }

        # Create the Secret object
        secret = client.V1Secret(
            metadata=client.V1ObjectMeta(name=secret_name),
            type="Opaque",
            data=encoded_data,
        )

        # Create the Secret in Kubernetes@
        api_client.create_namespaced_secret(namespace=namespace, body=secret)

    def create_secret_env_variables(self, secret_name, secret_data_map):
        # Create a list to store environment variables
        env_variables = []
        # Iterate through the secret_data_map and create V1EnvVar objects
        for env_name, _ in secret_data_map.items():
            env_var = client.V1EnvVar(
                name=env_name,
                value_from=client.V1EnvVarSource(
                    secret_key_ref=client.V1SecretKeySelector(
                        name=secret_name,
                        key=env_name,  # The key in the secret to reference
                    )
                ),
            )
            env_variables.append(env_var)

        # Set the environment variables in the current process
        for env_var in env_variables:
            os.environ[env_var.name] = env_var.value_from.secret_key_ref.key

        return env_variables

    # Create a set of pod port configurations
    def create_pod_port_configs(
        self, opened_ports: list[int], prefix: str, suffix: str
    ) -> list[PodPortConfig]:
        """
        Create PodPortConfig instances from a list of opened_ports
        with a given prefix and suffix for the name.

        Args:
            opened_ports (list[int]): A list of opened port numbers.
            prefix (str): A prefix to add to the port names.
            suffix (str): A suffix to add to the port names.

        Returns:
            list[PodPortConfig]: A list of PodPortConfig instances.
        """
        pod_port_configs = [
            PodPortConfig(name=f"{prefix}-{port}-{suffix}", container_port=port)
            for port in opened_ports
        ]

        return pod_port_configs

    # Create a set of service port configurations
    def create_service_port_configs(
        self, opened_ports: list[int], node_index: int, prefix: str, suffix: str
    ):
        """
        Create ServicePortConfig instances based on the opened_ports list.

        Args:
            opened_ports (list[int]): A list of opened port numbers.
            node_index (int): The node index.
            prefix (str): A prefix to add to the port names.
            suffix (str): A suffix to add to the port names.

        Returns:
            list[ServicePortConfig]: A list of ServicePortConfig instances.
        """
        num_ports_per_node = len(opened_ports)
        service_ports_config = []

        for port_index, port in enumerate(opened_ports, start=1):
            service_port_config = ServicePortConfig(
                f"{prefix}-{port}-{suffix}",
                20000 + (node_index * num_ports_per_node) + port_index,
                port,
                30000 + (node_index * num_ports_per_node) + port_index,
            )
            service_ports_config.append(service_port_config)

        return service_ports_config

    # Function to get the informations of pods
    def get_pods_info(self, namespace: str) -> list[PodInfo]:
        """
        Get information about pods in a Kubernetes namespace.

        Args:
            namespace (str): The namespace to query.

        Returns:
            list: A list of PodInfo objects containing pod information.
        """
        api_instance = client.CoreV1Api()
        pods_info = []

        # List Pods in the specified namespace
        pods = api_instance.list_namespaced_pod(namespace)

        for pod in pods.items:
            container_ports = []
            # Extract and add the container ports to the container_ports list
            for container in pod.spec.containers:
                for port in container.ports:
                    container_port_info = ContainerPortInfo(
                        name=port.name,
                        container_port=port.container_port,
                        protocol=port.protocol,
                    )
                    container_ports.append(container_port_info)

            # Create a PodInfo object for the pod
            pod_info = PodInfo(
                name=pod.metadata.name,
                namespace=namespace,
                status=pod.status.phase,
                pod_i_ps=pod.status.pod_i_ps,
                container_ports=container_ports,
            )

            pods_info.append(pod_info)

        return pods_info

    # Function to get the informations of services
    def get_services_info(self, namespace: str) -> list[ServiceInfo]:
        """
        Get information about services in a Kubernetes namespace.

        Args:
            namespace (str): The namespace to query.

        Returns:
            list: A list of dictionaries containing service information.
        """
        api_instance = client.CoreV1Api()

        services_info = []
        services = api_instance.list_namespaced_service(namespace)

        for service in services.items:
            port_infos = []

            for port in service.spec.ports:
                port_info = PortInfo(
                    name=port.name,
                    port=port.port,
                    target_port=port.target_port,
                    node_port=port.node_port,
                )
                port_infos.append(port_info)

            service_info = ServiceInfo(
                name=service.metadata.name,
                namespace=service.metadata.namespace,
                cluster_i_ps=service.spec.cluster_i_ps,
                external_i_ps=service.spec.external_i_ps,
                ports=port_infos,
            )

            services_info.append(service_info)

        return services_info

    # Function to get the status of a namespace
    def get_namespace_status(self, namespace: str):
        """
        Get the status of a Kubernetes namespace.

        Args:
            namespace_name (str): The name of the namespace to check.

        Returns:
            str: The status of the namespace.
                Returns None if the namespace does not exist.
        """
        # Create an instance of the CoreV1Api
        api_instance = client.CoreV1Api()

        try:
            # Attempt to read the namespace
            namespace_info = api_instance.read_namespace(namespace)

            # Get the phase/status of the namespace
            namespace_status = namespace_info.status

            return namespace_status
        except client.rest.ApiException as e:
            if e.status == 404:
                return None
            else:
                raise

    # Function to remove a set of services
    def remove_services(self, namespace: str, names: Optional[list[str]] = None):
        """
        Remove services from a Kubernetes namespace.

        Args:
            namespace (str): The namespace from which to remove services.
            names (list, optional): List of service names to remove.
            If None, all services in the namespace are removed.
        """
        api_instance = client.CoreV1Api()

        if names:
            for name in names:
                api_instance.delete_namespaced_service(name, namespace)
        else:
            pods = api_instance.list_namespaced_service(namespace)
            for pod in pods.items:
                api_instance.delete_namespaced_service(pod.metadata.name, namespace)

    # Function to remove a namespace
    def remove_namespace(self, namespace: str):
        """
        Remove a Kubernetes namespace.

        Args:
            namespace (str): The namespace to remove.
        """
        api_instance = client.CoreV1Api()
        api_instance.delete_namespace(
            namespace, body=client.V1DeleteOptions(propagation_policy="Foreground")
        )
