# Simple blockchain in Python

This project aims to learn the basics operations that a blockchain is composed of, as well as deploying a raw application with Docker and Kubernetes locally.

### Cluster node creation and app deployment commands:
    1. Start minikube: `minikube start --nodes 2 -p <cluster-name>`
    2. Make deployment: `kubectl apply -f deployment.yaml`
    3. Run LoadBalancer service: `kubectl apply -f blockchain_service.yaml`
    4. Apply rbac.yaml file to run kubernetes API on python `kubectl apply -f rbac.yaml`
    5. On a separate terminal run `minikube tunnel`
    6. Execute a shell inside a pod: `kubectl exec --stdin --tty <pod-name> -- sh`

If you want to see some metrics enable the dashboard addon, and the metrics addon. Then just get the url to the dashboard with the command `minikube dashboard --url -p <cluster-name>`

More information on the **why** of step 4 [here](https://github.com/kubernetes-client/python/blob/master/examples/in_cluster_config.py)

## Serving the blockchain with Kubernetes

This diagrams gives a visual representation of how Kubernetes is running the blockchain.

<p align="center">
<img src="https://github.com/jucamohedano/simple-blockchain/blob/main/overview.png?raw=true" width="600" height="500" class="center">
</p>
