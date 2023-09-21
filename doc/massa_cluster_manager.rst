Massa Cluster Manager Module
=============================

This module provides classes and functions for managing Massa Cluster deployments in Kubernetes.
It offers a convenient way to interact with Massa Cluster configurations and perform common operations.

Classes
-------

- :class:`MassaClusterConfig`: Configuration data class for Massa Cluster deployment.
- :class:`MassaClusterManager`: A class for managing Massa Cluster deployments in Kubernetes.

Usage
-----

1. **Import the Required Classes:**

   Import the necessary classes from the module:

   ```python
   from massa_cluster_manager import MassaClusterConfig, MassaClusterManager
   ```

2. **Create a MassaClusterConfig Instance:**

   Create a `MassaClusterConfig` instance to define your Massa Cluster configuration. You need to provide values for the following attributes:

   - `namespace`: The namespace for the Massa Cluster.
   - `nodes_number`: The number of nodes in the cluster.
   - `external_ips`: A list of external IP addresses.
   - `authorized_keys`: The authorized SSH keys.
   - `startup_pods_timeout` (optional): The timeout for pod startup (default is 3 seconds).
   - `startup_services_timeout` (optional): The timeout for service startup (default is 3 seconds).

   Example:

   ```python
   external_ips = ["10.4.3.2"]
   authorized_keys = "ssh-ed25519 XXX_MY_SSH_KEY_XXX simulator@massa.net"
   cluster_config = MassaClusterConfig(
       authorized_keys=authorized_keys, external_ips=external_ips
   )
   ```

3. **Create a MassaClusterManager Instance:**

   Create a `MassaClusterManager` instance to interact with your Kubernetes cluster. You need to provide the path to your Kubernetes configuration file (kubeconfig.yml) as an argument.

   Example:

   ```python
   manager = MassaClusterManager(
       "PATH_TO/kubeconfig.yml"
   )
   ```

4. **Initialize the Massa Cluster:**

   Use the `init` method of the `MassaClusterManager` class to initialize the Massa Cluster. This method takes the `cluster_config` you created in step 2 as an argument. It will create and start all necessary pods and services.

   Example:

   ```python
   services_infos = manager.launch(cluster_config)
   ```

5. **Manage the Massa Cluster:**

   You can now interact with the Massa Cluster as needed. The `services_infos` variable contains information about the services that were created.

   Example:

   ```python
   for service_info in services_infos:
       print(service_info.name, external_ips[0], service_info.ports[0].port)
   ```

6. **Terminate the Massa Cluster:**

   When you're finished with the Massa Cluster, use the `terminate` method of the `MassaClusterManager` class to remove the cluster. This method takes the namespace of the cluster as an argument.

   Example:

   ```python
   print("Waiting terminating...")
   manager.terminate(cluster_config.namespace, 15)
   print(f"Namespace {cluster_config.namespace} terminated.")
   ```

   The `terminate` method will remove all pods and services associated with the Massa Cluster.

That's it! You can now use the Massa Cluster Manager module to easily manage your Massa Cluster deployments in Kubernetes.
