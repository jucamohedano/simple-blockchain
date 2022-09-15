Simple blockchain in Python.

Some useful commands:

    Start minikube: minikube start --nodes 2 -p <cluster-name>

    Make deployment: kubectl apply -f deployment.yaml
    
    Run LoadBalancer service: kubectl apply -f blockchain_service.yaml

    Apply rbac.yaml file to run kubernetes API on python (read more: https://github.com/kubernetes-client/python/blob/master/examples/in_cluster_config.py)

    On a separate terminal: minikube tunnel

    Execute a shell inside a pod: kubectl exec --stdin --tty <pod-name> -- sh

    If you want to see some metrics enable the dashboard addon, and the metrics addon. Then just get the url to the dashboard with command: minikube dashboard --url -p <cluster-name>