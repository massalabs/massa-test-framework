"""
Massa Cluster Manager Module

This module provides classes and functions for managing Massa Cluster deployments in Kubernetes.
It offers a convenient way to interact with Massa Cluster configurations and perform common operations.

Classes:
    MassaClusterConfig: Configuration data class for Massa Cluster deployment.
    MassaClusterManager: A class for managing Massa Cluster deployments in Kubernetes.

Usage:
    1. Import the required classes from this module.
    2. Create a `MassaClusterConfig` instance with your cluster configuration.
    3. Create a `MassaClusterManager` instance with your Kubernetes configuration.
    4. Use the provided methods to initialize, manage, and terminate Massa Cluster deployments.

Example:
    from massa_cluster_manager import MassaClusterConfig, MassaClusterManager

    if __name__ == "__main__":
        # Example usage:
        external_i_ps = ["10.4.3.2"]
        
        ssh_authorized_keys = "ssh-ed25519 XXX_MY_SSH_KEY_XXX simulator@massa.net"

        cluster_config = MassaClusterConfig(
            ssh_authorized_keys=ssh_authorized_keys, external_i_ps=external_i_ps
        )

        manager = MassaClusterManager(
            "PATH_TO/kubeconfig.yml"
        )

        print("Initializing...")
        launch_infos = manager.launch(cluster_config)
        # Iterate through the LaunchInfo objects
        for launch_info in launch_infos:
            print(f"Service Name: {launch_info.service_info.name}, 
            Cluster IP: {launch_info.service_info.cluster_i_ps[0]}")
            print(f"Service Namespace: {launch_info.service_info.namespace}, 
            External IP: {launch_info.service_info.external_i_ps[0]}")

            # Iterate through the ports of the service and print their details
            for port in launch_info.service_info.ports:
                print(f"Port Name: {port.name}, Port Number: {port.port}")

            # Print pod information
            print(f"Pod Name: {launch_info.pod_info.name}, Pod IP: {launch_info.pod_info.pod_i_ps[0]}")
            print(f"Namespace: {launch_info.pod_info.namespace}, Status: {launch_info.pod_info.status}")

            # Print container ports
            for container_port in launch_info.pod_info.container_ports:
                print(f"Container Port Name: {container_port.name}, 
                Container Port Number: {container_port.container_port}")
                print(f"Protocol: {container_port.protocol}")

            print("\n")  # Add a newline for separation between LaunchInfos

        print("Waiting terminating...")
        manager.terminate(cluster_config.namespace, 55)
        print(f"Namespace {cluster_config.namespace} terminated.")
"""

import os
import time
from typing import Optional

from .kubernetes_manager import (
    KubernetesManager,
    PodConfig,
    PodInfo,
    ServiceInfo,
    ServiceConfig,
)

from dataclasses import dataclass, field


@dataclass
class MassaClusterConfig:
    """
    Data class representing configuration for a MassaCluster.

    Attributes:
        namespace (str): The namespace for the MassaCluster.
        nodes_number (int): The number of nodes in the cluster.
        external_i_ps (list[str]): A list of external IP addresses.
        ssh_authorized_keys (str): The authorized SSH keys.
        existing_secret (str): The name of an existing secret to use.
        startup_pods_timeout (int): The timeout for pod startup (default is 3 seconds).
        startup_services_timeout (int): The timeout for service startup (default is 3 seconds).
    """

    namespace: str = os.environ.get("MASSA_TEST_FRAMEWORK_NAMESPACE", "massa-simulator")
    nodes_number: int = int(os.environ.get("MASSA_TEST_FRAMEWORK_NODES_NUMBER", "3"))
    external_i_ps: list[str] = field(
        default_factory=lambda: os.environ.get(
            "MASSA_TEST_FRAMEWORK_EXTERNAL_I_PS", ""
        ).split(",")
    )
    ssh_username: str = os.environ.get("MASSA_TEST_FRAMEWORK_SSH_USERNAME", "simulator")
    ssh_password: str = os.environ.get("MASSA_TEST_FRAMEWORK_SSH_PASSWORD", "")
    ssh_authorized_keys: str = os.environ.get(
        "MASSA_TEST_FRAMEWORK_SSH_AUTHORIZED_KEYS", ""
    )
    ssh_existing_secret: str = os.environ.get(
        "MASSA_TEST_FRAMEWORK_SSH_EXISTING_SECRET", "massa-credentials"
    )
    startup_pods_timeout: int = int(
        os.environ.get("MASSA_TEST_FRAMEWORK_STARTUP_PODS_TIMEOUT", "3")
    )
    startup_services_timeout: int = int(
        os.environ.get("MASSA_TEST_FRAMEWORK_STARTUP_SERVICES_TIMEOUT", "3")
    )

    def __post_init__(self):
        if not self.external_i_ps:
            raise ValueError("external_i_ps is required")
        if not self.ssh_password and not self.ssh_authorized_keys:
            raise ValueError(
                "Either ssh_password or ssh_authorized_keys is required, but not both"
            )


@dataclass
class LaunchInfo:
    """
    Represents information about a launched service and its associated pods.

    Attributes:
        pod_info (PodInfo): Information about the pods associated with the service.
        service_info (ServiceInfo): Information about the service itself.
    """

    pod_info: PodInfo
    service_info: ServiceInfo


class MassaClusterManager:
    def __init__(self, kube_config_path: Optional[str] = None):
        self.manager = KubernetesManager(kube_config_path)

    # Function to launch a Massa cluster
    def launch(self, cluster_config: MassaClusterConfig) -> list[LaunchInfo]:
        opened_ports = [22, 33034, 33035, 33036, 33037, 33038, 31244, 31245]
        prefix = "m"
        suffix = "p"
        docker_image = "aoudiamoncef/ubuntu-sshd"

        self.manager.create_namespace(cluster_config.namespace)

        env_variables = {
            "SSH_USERNAME": cluster_config.ssh_username,
            "PASSWORD": cluster_config.ssh_password,
            "AUTHORIZED_KEYS": cluster_config.ssh_authorized_keys,
        }

        self.manager.create_secret(
            cluster_config.namespace, cluster_config.ssh_existing_secret, env_variables
        )

        secret_env_variables = self.manager.create_secret_env_variables(
            cluster_config.ssh_existing_secret, env_variables
        )

        # Create and start all pods
        pod_configs = []
        for node_index in range(1, cluster_config.nodes_number + 1):
            pod_ports_config = self.manager.create_pod_port_configs(
                opened_ports, prefix, suffix
            )
            pod_config = PodConfig(
                cluster_config.namespace,
                f"massa-node-{node_index}-container",
                docker_image,
                f"massa-node-{node_index}-pod",
                pod_ports_config,
                secret_env_variables,
            )
            self.manager.create_pod(pod_config)
            pod_configs.append(pod_config)

        # Wait for pods to start
        time.sleep(cluster_config.startup_pods_timeout)

        # Create all services after pods have started
        for node_index, pod_config in enumerate(pod_configs, start=1):
            service_ports_config = (
                service_ports_config
            ) = self.manager.create_service_port_configs(
                opened_ports, node_index, prefix, suffix
            )

            service_config = ServiceConfig(
                cluster_config.namespace,
                pod_config,
                f"massa-node-{node_index}-service",
                cluster_config.external_i_ps,
                service_ports_config,
            )
            self.manager.create_service(service_config)

        # Wait for services to start
        time.sleep(cluster_config.startup_services_timeout)

        # Assuming you have already imported the LaunchInfo class

        # Get pod and service information
        pods_infos = sorted(
            self.manager.get_pods_info(cluster_config.namespace),
            key=lambda p: p.name)
        services_infos = sorted(
            self.manager.get_services_info(cluster_config.namespace),
            key=lambda s: s.name)

        # Create LaunchInfo objects for each pair of pod and service information
        launch_infos = [
            LaunchInfo(pod_info, service_info)
            for pod_info, service_info in zip(pods_infos, services_infos)
        ]

        return launch_infos

    # Function to terminate a Massa cluster
    def terminate(
        self, namespace: str, terminating_timeout: int = 60, waiting_interval: int = 5
    ):
        self.manager.remove_namespace(namespace)
        start_time = time.time()

        while True:
            namespace_status = self.manager.get_namespace_status(
                namespace
            )  # Pass the namespace as an argument here

            if namespace_status is None or namespace_status.phase != "Terminating":
                break

            if time.time() - start_time >= terminating_timeout:
                break

            time.sleep(waiting_interval)
