# Description: This file contains the class KubernetesManager, which is responsible for managing the Kubernetes cluster.
import time
from kubernetes import client, config

class PodConfig:
    """Configuration for a Kubernetes Pod."""
    def __init__(self, namespace, container_name, docker_image, pod_name, opened_ports, authorized_keys):
        """
        Initialize a PodConfig object.

        Args:
            namespace (str): The namespace in which the pod will be created.
            container_name (str): The name of the container within the pod.
            docker_image (str): The Docker image to be used for the container.
            pod_name (str): The name of the pod.
            opened_ports (list): A list of ports to be opened in the container.
            authorized_keys (str): Authorized SSH keys to be added to the pod's environment.
        """
        self.namespace = namespace
        self.container_name = container_name
        self.docker_image = docker_image
        self.pod_name = pod_name
        self.opened_ports = opened_ports
        self.authorized_keys = authorized_keys

class ServicePortConfig:
    """Configuration for a Kubernetes Service Port."""
    def __init__(self, port, target_port, node_port):
        """
        Initialize a ServicePortConfig object.

        Args:
            port (int): The port number to expose.
            target_port (int): The port to forward traffic to within the pod.
            node_port (int): The node port for external access.
        """
        self.port = port
        self.target_port = target_port
        self.node_port = node_port

class ServiceConfig:
    """Configuration for a Kubernetes Service."""
    def __init__(self, namespace, pod_config, service_name, external_ips, service_ports: [ServicePortConfig]):
        """
        Initialize a ServiceConfig object.

        Args:
            namespace (str): The namespace in which the service will be created.
            pod_config (PodConfig): The PodConfig object associated with this service.
            service_name (str): The name of the service.
            external_ips (list): List of external IP addresses for the service.
            service_ports (list of ServicePortConfig): List of ServicePortConfig objects.
        """
        self.namespace = namespace
        self.pod_config = pod_config
        self.service_name = service_name
        self.external_ips = external_ips
        self.service_ports = service_ports

class DeployConfig:
    """Configuration for deploying a Kubernetes service and associated pod."""
    def __init__(self, namespace, pod_config, service_config):
        """
        Initialize a DeployConfig object.

        Args:
            namespace (str): The namespace in which the service and pod will be created.
            pod_config (PodConfig): The PodConfig object associated with this deployment.
            service_config (ServiceConfig): The ServiceConfig object associated with this deployment.
        """
        self.namespace = namespace
        self.pod_config = pod_config
        self.service_config = service_config

class KubernetesManager:
    """
    Class for managing a Kubernetes cluster.
    """
    # Load Kubernetes configuration
    def __init__(self, config_file=None):
        """
        Initialize a KubernetesManager object.

        Args:
            config_file (str, optional): Path to a Kubernetes configuration file. If None, in-cluster config is used.
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

        env_var = client.V1EnvVar(name="AUTHORIZED_KEYS", value=pods_config.authorized_keys)
        container_ports = [
            client.V1ContainerPort(container_port=port) for port in pods_config.opened_ports
        ]

        container = client.V1Container(
            name=pods_config.pod_name,
            image=pods_config.docker_image,
            ports=container_ports,
            env=[env_var],
        )

        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=pods_config.pod_name,
                labels={"app": pods_config.pod_name}
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
                external_i_ps=config.external_ips
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
                    "container_ports": []
                }

                # Extract and add the container ports to the pod_info dictionary
                for container in pod.spec.containers:
                    for port in container.ports:
                        container_port_info = {
                            "name": port.name,
                            "container_port": port.container_port,
                            "protocol": port.protocol
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
                service_info = {
                    "name": service.metadata.name,
                    "ports": []
                }

                for port in service.spec.ports:
                    service_info["ports"].append({
                        "name": port.name,
                        "port": port.port,
                        "target_port": port.target_port,
                        "node_port": port.node_port
                    })

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
            service_names (list, optional): List of service names to remove. If None, all services in the namespace are removed.
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
            api_instance.delete_namespace(namespace, body=client.V1DeleteOptions(propagation_policy='Foreground'))
            print(f"Namespace {namespace} removed successfully.")
        except Exception as e:
            print(f"Error removing namespace {namespace}: {e}")
