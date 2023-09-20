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
        external_ips = ["10.4.3.2"]
        authorized_keys = "ssh-ed25519 XXX_MY_SSH_KEY_XXX simulator@massa.net"
        cluster_config = MassaClusterConfig(
            authorized_keys=authorized_keys, external_ips=external_ips
        )
        manager = MassaClusterManager(
            "PATH_TO/kubeconfig.yml"
        )
        services_infos = manager.init(cluster_config)
        for service_info in services_infos:
            print(service_info.name, external_ips[0], service_info.ports[0].port)
        print("Waiting terminating...")
        manager.terminate(cluster_config.namespace, 15)
        print(f"Namespace {cluster_config.namespace} terminated.")
"""

import time
from typing import Optional
from kubernetes_manager import (
    KubernetesManager,
    PodConfig,
    ServiceConfig,
    ServicePortConfig,
)
from dataclasses import dataclass, field

from massa_test_framework.kubernetes_manager import ServiceInfo


@dataclass
class MassaClusterConfig:
    """
    Data class representing configuration for a MassaCluster.

    Attributes:
        namespace (str): The namespace for the MassaCluster.
        nodes_number (int): The number of nodes in the cluster.
        external_ips (list[str]): A list of external IP addresses.
        authorized_keys (str): The authorized SSH keys.
        startup_pods_timeout (int): The timeout for pod startup (default is 3 seconds).
        startup_services_timeout (int): The timeout for service startup (default is 3 seconds).
    """

    namespace: str = "massa-simulator"
    nodes_number: int = 3
    external_ips: list[str] = field(default_factory=list)
    authorized_keys: str = field(default="")
    startup_pods_timeout: int = 3
    startup_services_timeout: int = 3

    def __post_init__(self):
        if not self.external_ips:
            raise ValueError("external_ips is required")
        if not self.authorized_keys:
            raise ValueError("authorized_keys is required")


class MassaClusterManager:
    def __init__(self, kube_config_path: Optional[str] = None):
        self.manager = KubernetesManager(kube_config_path)

    def init(self, cluster_config: MassaClusterConfig) -> list[ServiceInfo]:
        opened_ports = [22, 33034, 33035, 33036, 33037, 33038, 31244, 31245]
        docker_image = "aoudiamoncef/ubuntu-sshd"
        env_variables = {"AUTHORIZED_KEYS": cluster_config.authorized_keys}
        self.manager.create_namespace(cluster_config.namespace)
        # Create and start all pods
        pod_configs = []
        for node_index in range(1, cluster_config.nodes_number + 1):
            pod_config = PodConfig(
                cluster_config.namespace,
                f"massa-node-{node_index}-container",
                docker_image,
                f"massa-node-{node_index}-pod",
                opened_ports,
                env_variables,
            )
            self.manager.create_pod(pod_config)
            pod_configs.append(pod_config)

        # Wait for pods to start
        time.sleep(cluster_config.startup_pods_timeout)

        # Create all services after pods have started
        for node_index, pod_config in enumerate(pod_configs, start = 1):
            service_port_config = ServicePortConfig(
                20000 + node_index, 22, 30000 + node_index
            )
            service_config = ServiceConfig(
                cluster_config.namespace,
                pod_config,
                f"massa-node-{node_index}-service",
                cluster_config.external_ips,
                [service_port_config],
            )
            self.manager.create_service(service_config)

        # Wait for services to start
        time.sleep(cluster_config.startup_services_timeout)

        return self.manager.get_services_info(cluster_config.namespace)

    def terminate(self, namespace: str, terminating_timeout: int = 5):
        self.manager.remove_namespace(namespace)
        time.sleep(terminating_timeout)
