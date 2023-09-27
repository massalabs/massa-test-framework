# Installing K3s on Linux

K3s is a lightweight Kubernetes distribution designed for use on resource-constrained systems. In this tutorial, we'll walk you through the process of installing K3s on a Linux machine.

## Prerequisites

Before you begin, make sure you have the following:

- A Linux machine (physical or virtual) with internet access.
- The `curl` command-line tool installed.

## Step 1: Install K3s

Open a terminal on your Linux machine and run the following command to install K3s:

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server --flannel-iface=eno1 --node-ip MY_PUBLIC_IP --disable servicelb --disable traefik --secrets-encryption" sh -s -
```

Replace `MY_PUBLIC_IP` with the public IP address or hostname of your Linux machine. This command will download and install K3s with the specified configuration options.

## Step 2: Uninstall K3s (Optional)

If you ever need to uninstall K3s, you can use the following command:

```bash
/usr/local/bin/k3s-uninstall.sh
```

This will remove K3s and its associated components from your system.

## Step 3: Retrieve the K3s Server Token

After K3s is installed, you can retrieve the server token, which is required for authenticating worker nodes or other clients. Run the following command to view the server token:

```bash
sudo cat /var/lib/rancher/k3s/server/token
```

Make sure to keep this token secure, as it is used to join additional nodes to the K3s cluster.

## Conclusion

You have successfully installed K3s on your Linux machine and retrieved the server token. K3s is now ready to use, and you can start deploying and managing containers and applications using Kubernetes.

For more advanced configurations and cluster management, refer to the K3s documentation: [https://rancher.com/docs/k3s](https://rancher.com/docs/k3s)
