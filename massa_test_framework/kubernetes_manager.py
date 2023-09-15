# Description: This file contains the class KubernetesManager, which is responsible for managing the Kubernetes cluster.
import time
from kubernetes import client, config

class KubernetesManager:
    # Load Kubernetes configuration
    def __init__(self, config_file=None):
        if config_file:
            config.load_kube_config(config_file)
        else:
            config.load_incluster_config()
    
    # Function to create a namespace if it does not exist
    def create_namespace(self, namespace):
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
    def create_pods(self, namespace, pod_names, docker_image, authorized_keys, opened_ports):
        api_instance = client.CoreV1Api()

        for service_name in pod_names:
            env_var = client.V1EnvVar(name="AUTHORIZED_KEYS", value=authorized_keys)

            container_ports = [client.V1ContainerPort(container_port=22)] + [
                client.V1ContainerPort(container_port=port) for port in opened_ports
            ]

            container = client.V1Container(
                name=service_name,
                image=docker_image,
                ports=container_ports,
                env=[env_var],
            )

            pod = client.V1Pod(
                metadata=client.V1ObjectMeta(
                    name=service_name,
                    labels={"app": service_name}
                ),
                spec=client.V1PodSpec(containers=[container]),
            )

            try:
                api_instance.create_namespaced_pod(namespace, pod)
                print(f"Service {service_name} started successfully.")
            except Exception as e:
                print(f"Error starting service {service_name}: {e}")
    
    # Function to create a service from external access
    def create_services(self, namespace, service_name, external_ips, port, node_port):
        api_instance = client.CoreV1Api()

        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=service_name),
            spec=client.V1ServiceSpec(
                type="NodePort",
                selector={"app": service_name},
                ports=[
                    client.V1ServicePort(
                        port=port,
                        target_port=22,
                        node_port=node_port,
                    )
                ],
                external_i_ps=external_ips
            ),
        )

        try:
            api_instance.create_namespaced_service(namespace, service)
            print(f"Service {service_name} created successfully.")
        except Exception as e:
            print(f"Error creating Service {service_name}: {e}")

    def get_pods_info(self, namespace):
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
        api_instance = client.CoreV1Api()

        try:
            api_instance.delete_namespace(namespace, body=client.V1DeleteOptions(propagation_policy='Foreground'))
            print(f"Namespace {namespace} removed successfully.")
        except Exception as e:
            print(f"Error removing namespace {namespace}: {e}")

class PodConfig:
    def __init__(self, namespace, docker_image, pod_name, opened_ports, authorized_keys):
        self.namespace = namespace
        self.docker_image = docker_image
        self.pod_name = pod_name
        self.opened_ports = opened_ports
        self.authorized_keys = authorized_keys

class ServiceConfig:
    def __init__(self, namespace, pod_config, service_name, external_ips, port, node_port):
        self.namespace = namespace
        self.pod_config = pod_config
        self.service_name = service_name
        self.external_ips = external_ips
        self.port = port
        self.node_port = node_port

class DeployConfig:
    def __init__(self, namespace, pod_config, service_config):
        self.namespace = namespace
        self.pod_config = pod_config
        self.service_config = service_config
#TODO propagate the new config