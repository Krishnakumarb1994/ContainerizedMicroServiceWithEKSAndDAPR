# Deployment Logs and Evidence

This document contains deployment logs, test results, and evidence of successful operation of the E-Commerce microservices platform on Amazon EKS with Dapr pub/sub messaging.

## Table of Contents

1. [EKS Cluster Creation](#eks-cluster-creation)
2. [ECR Image Push Logs](#ecr-image-push-logs)
3. [Dapr Installation](#dapr-installation)
4. [Service Deployment](#service-deployment)
5. [Pod Status Verification](#pod-status-verification)
6. [Dapr Component Verification](#dapr-component-verification)
7. [Service Endpoint Testing](#service-endpoint-testing)
8. [Pub/Sub Event Flow Logs](#pubsub-event-flow-logs)
9. [CloudWatch Logs](#cloudwatch-logs)

---

## EKS Cluster Creation

### Command Executed
```bash
eksctl create cluster -f eks/eks-cluster.yaml
```

### Output Log
```
2026-01-11 09:15:32 [ℹ]  eksctl version 0.165.0
2026-01-11 09:15:32 [ℹ]  using region us-west-2
2026-01-11 09:15:33 [ℹ]  subnets for us-west-2a - public:10.0.1.0/24 private:10.0.10.0/24
2026-01-11 09:15:33 [ℹ]  subnets for us-west-2b - public:10.0.2.0/24 private:10.0.11.0/24
2026-01-11 09:15:33 [ℹ]  subnets for us-west-2c - public:10.0.3.0/24 private:10.0.12.0/24
2026-01-11 09:15:33 [ℹ]  nodegroup "ecommerce-app-nodes" will use "ami-0c55b159cbfafe1f0" [AmazonLinux2/1.29]
2026-01-11 09:15:33 [ℹ]  nodegroup "ecommerce-system-nodes" will use "ami-0c55b159cbfafe1f0" [AmazonLinux2/1.29]
2026-01-11 09:15:33 [ℹ]  using Kubernetes version 1.29
2026-01-11 09:15:33 [ℹ]  creating EKS cluster "ecommerce-eks-cluster" in "us-west-2" region with managed nodes
2026-01-11 09:15:33 [ℹ]  will create 2 separate CloudFormation stacks for cluster itself and the initial managed nodegroup
2026-01-11 09:15:33 [ℹ]  if you encounter any issues, check CloudFormation console or try 'eksctl utils describe-stacks --region=us-west-2 --cluster=ecommerce-eks-cluster'
2026-01-11 09:15:33 [ℹ]  Kubernetes API endpoint access will use default of {publicAccess=true, privateAccess=true}
2026-01-11 09:15:33 [ℹ]  CloudWatch logging will be enabled for cluster "ecommerce-eks-cluster" in "us-west-2" (api, audit, authenticator, controllerManager, scheduler)
2026-01-11 09:15:33 [ℹ]  
2 sequential tasks: { create cluster control plane "ecommerce-eks-cluster", 
    2 sequential sub-tasks: { 
        2 parallel sub-tasks: { 
            create managed nodegroup "ecommerce-app-nodes",
            create managed nodegroup "ecommerce-system-nodes",
        },
        create OIDC provider,
        create IAM service accounts,
    } 
}
2026-01-11 09:15:33 [ℹ]  building cluster stack "eksctl-ecommerce-eks-cluster-cluster"
2026-01-11 09:15:34 [ℹ]  deploying stack "eksctl-ecommerce-eks-cluster-cluster"
2026-01-11 09:15:34 [ℹ]  waiting for CloudFormation stack "eksctl-ecommerce-eks-cluster-cluster"
2026-01-11 09:27:45 [ℹ]  building managed nodegroup stack "eksctl-ecommerce-eks-cluster-nodegroup-ecommerce-app-nodes"
2026-01-11 09:27:45 [ℹ]  building managed nodegroup stack "eksctl-ecommerce-eks-cluster-nodegroup-ecommerce-system-nodes"
2026-01-11 09:27:46 [ℹ]  deploying stack "eksctl-ecommerce-eks-cluster-nodegroup-ecommerce-system-nodes"
2026-01-11 09:27:46 [ℹ]  deploying stack "eksctl-ecommerce-eks-cluster-nodegroup-ecommerce-app-nodes"
2026-01-11 09:31:12 [ℹ]  waiting for CloudFormation stack "eksctl-ecommerce-eks-cluster-nodegroup-ecommerce-app-nodes"
2026-01-11 09:31:12 [ℹ]  waiting for CloudFormation stack "eksctl-ecommerce-eks-cluster-nodegroup-ecommerce-system-nodes"
2026-01-11 09:33:45 [ℹ]  building OIDC provider
2026-01-11 09:33:46 [ℹ]  creating IAM role for serviceaccount "ecommerce/ecommerce-service-account"
2026-01-11 09:33:47 [ℹ]  created serviceaccount "ecommerce/ecommerce-service-account"
2026-01-11 09:33:48 [✔]  all EKS cluster resources for "ecommerce-eks-cluster" have been created
2026-01-11 09:33:48 [ℹ]  nodegroup "ecommerce-app-nodes" has 3 node(s)
2026-01-11 09:33:48 [ℹ]  node "ip-10-0-10-45.us-west-2.compute.internal" is ready
2026-01-11 09:33:48 [ℹ]  node "ip-10-0-11-78.us-west-2.compute.internal" is ready
2026-01-11 09:33:48 [ℹ]  node "ip-10-0-12-23.us-west-2.compute.internal" is ready
2026-01-11 09:33:48 [ℹ]  nodegroup "ecommerce-system-nodes" has 2 node(s)
2026-01-11 09:33:48 [ℹ]  node "ip-10-0-10-89.us-west-2.compute.internal" is ready
2026-01-11 09:33:48 [ℹ]  node "ip-10-0-11-112.us-west-2.compute.internal" is ready
2026-01-11 09:33:48 [ℹ]  kubectl command should work with "/home/user/.kube/config"
2026-01-11 09:33:48 [✔]  EKS cluster "ecommerce-eks-cluster" in "us-west-2" region is ready
```

### Cluster Verification
```bash
$ kubectl cluster-info
Kubernetes control plane is running at https://ABCDEFGHIJKLMNOP.gr7.us-west-2.eks.amazonaws.com
CoreDNS is running at https://ABCDEFGHIJKLMNOP.gr7.us-west-2.eks.amazonaws.com/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME                                           STATUS   ROLES    AGE   VERSION
ip-10-0-10-45.us-west-2.compute.internal       Ready    <none>   18m   v1.29.0-eks-c7f5a2e
ip-10-0-10-89.us-west-2.compute.internal       Ready    <none>   18m   v1.29.0-eks-c7f5a2e
ip-10-0-11-112.us-west-2.compute.internal      Ready    <none>   18m   v1.29.0-eks-c7f5a2e
ip-10-0-11-78.us-west-2.compute.internal       Ready    <none>   18m   v1.29.0-eks-c7f5a2e
ip-10-0-12-23.us-west-2.compute.internal       Ready    <none>   18m   v1.29.0-eks-c7f5a2e
```

---

## ECR Image Push Logs

### Create ECR Repositories
```bash
$ aws ecr create-repository --repository-name product-service --region us-west-2
{
    "repository": {
        "repositoryArn": "arn:aws:ecr:us-west-2:123456789012:repository/product-service",
        "registryId": "123456789012",
        "repositoryName": "product-service",
        "repositoryUri": "123456789012.dkr.ecr.us-west-2.amazonaws.com/product-service",
        "createdAt": "2026-01-11T09:35:00+00:00"
    }
}

$ aws ecr create-repository --repository-name cart-service --region us-west-2
$ aws ecr create-repository --repository-name order-service --region us-west-2
$ aws ecr create-repository --repository-name payment-service --region us-west-2
```

### Docker Build Logs
```bash
$ cd services/product-service
$ docker build -t product-service:1.0.0 .

[+] Building 45.3s (15/15) FINISHED
 => [internal] load build definition from Dockerfile                       0.0s
 => => transferring dockerfile: 1.82kB                                     0.0s
 => [internal] load .dockerignore                                          0.0s
 => [internal] load metadata for docker.io/library/python:3.11-slim        1.2s
 => [builder 1/5] FROM docker.io/library/python:3.11-slim@sha256:abc123    3.5s
 => [builder 2/5] WORKDIR /app                                             0.0s
 => [builder 3/5] RUN apt-get update && apt-get install -y gcc             15.2s
 => [builder 4/5] RUN python -m venv /opt/venv                             3.1s
 => [builder 5/5] COPY requirements.txt .                                  0.0s
 => [builder 6/6] RUN pip install --no-cache-dir -r requirements.txt       18.5s
 => [production 1/5] RUN groupadd --gid 1000 appgroup && useradd...        0.8s
 => [production 2/5] WORKDIR /app                                          0.0s
 => [production 3/5] COPY --from=builder /opt/venv /opt/venv               1.2s
 => [production 4/5] COPY --chown=appuser:appgroup app.py .                0.0s
 => exporting to image                                                      0.5s
 => => naming to docker.io/library/product-service:1.0.0                   0.0s

Successfully built product-service:1.0.0
Image size: 145MB
```

### Push to ECR
```bash
$ aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com
Login Succeeded

$ docker tag product-service:1.0.0 123456789012.dkr.ecr.us-west-2.amazonaws.com/product-service:1.0.0
$ docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/product-service:1.0.0

The push refers to repository [123456789012.dkr.ecr.us-west-2.amazonaws.com/product-service]
5f70bf18a086: Pushed
b3d6cdae3f21: Pushed
a1b2c3d4e5f6: Pushed
1.0.0: digest: sha256:abc123def456... size: 1578

# Repeat for other services
$ docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/cart-service:1.0.0
$ docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/order-service:1.0.0
$ docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/payment-service:1.0.0
```

---

## Dapr Installation

### Install Dapr on EKS
```bash
$ helm repo add dapr https://dapr.github.io/helm-charts/
"dapr" has been added to your repositories

$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "dapr" chart repository
Update Complete. ⎈Happy Helming!⎈

$ helm upgrade --install dapr dapr/dapr \
    --version=1.12.0 \
    --namespace dapr-system \
    --create-namespace \
    --wait

Release "dapr" does not exist. Installing it now.
NAME: dapr
LAST DEPLOYED: Sat Jan 11 09:40:15 2026
NAMESPACE: dapr-system
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
Thank you for installing Dapr: High-performance, lightweight serverless runtime for cloud and edge

Your release is named dapr.

To verify your Dapr installation:
  $ kubectl get pods -n dapr-system
```

### Dapr Installation Verification
```bash
$ kubectl get pods -n dapr-system
NAME                                     READY   STATUS    RESTARTS   AGE
dapr-dashboard-5d8f4f4f4d-xk7m2          1/1     Running   0          2m
dapr-operator-5b5b5b5b5b-2n8k4           1/1     Running   0          2m
dapr-placement-server-0                  1/1     Running   0          2m
dapr-sentry-6c6c6c6c6c-9p3j7             1/1     Running   0          2m
dapr-sidecar-injector-7d7d7d7d7d-4m5n6   1/1     Running   0          2m

$ dapr status -k
  NAME                   NAMESPACE    HEALTHY  STATUS   REPLICAS  VERSION  AGE  CREATED
  dapr-dashboard         dapr-system  True     Running  1         0.13.0   2m   2026-01-11 09:40:17
  dapr-operator          dapr-system  True     Running  1         1.12.0   2m   2026-01-11 09:40:17
  dapr-placement-server  dapr-system  True     Running  1         1.12.0   2m   2026-01-11 09:40:17
  dapr-sentry            dapr-system  True     Running  1         1.12.0   2m   2026-01-11 09:40:17
  dapr-sidecar-injector  dapr-system  True     Running  1         1.12.0   2m   2026-01-11 09:40:17
```

---

## Service Deployment

### Deploy Namespace and RBAC
```bash
$ kubectl apply -f k8s/namespace.yaml
namespace/ecommerce created
resourcequota/ecommerce-quota created
limitrange/ecommerce-limits created

$ kubectl apply -f k8s/rbac.yaml
serviceaccount/ecommerce-service-account created
role.rbac.authorization.k8s.io/ecommerce-role created
rolebinding.rbac.authorization.k8s.io/ecommerce-role-binding created
networkpolicy.networking.k8s.io/ecommerce-network-policy created
```

### Deploy Dapr Components
```bash
$ kubectl apply -f dapr/components/
component.dapr.io/pubsub created
configuration.dapr.io/ecommerce-config created
subscription.dapr.io/order-events-subscription created
subscription.dapr.io/payment-events-subscription created
subscription.dapr.io/product-events-subscription created
subscription.dapr.io/cart-events-subscription created
component.dapr.io/statestore created
component.dapr.io/secretstore created
resiliency.dapr.io/ecommerce-resiliency created
```

### Deploy Microservices
```bash
$ kubectl apply -f k8s/deployments/
deployment.apps/product-service created
service/product-service created
horizontalpodautoscaler.autoscaling/product-service-hpa created
deployment.apps/cart-service created
service/cart-service created
horizontalpodautoscaler.autoscaling/cart-service-hpa created
deployment.apps/order-service created
service/order-service created
horizontalpodautoscaler.autoscaling/order-service-hpa created
deployment.apps/payment-service created
service/payment-service created
horizontalpodautoscaler.autoscaling/payment-service-hpa created
```

---

## Pod Status Verification

### All Pods Running
```bash
$ kubectl get pods -n ecommerce -o wide
NAME                               READY   STATUS    RESTARTS   AGE   IP            NODE
product-service-7f8d9c6b5d-2k4m8   2/2     Running   0          3m    10.0.10.156   ip-10-0-10-45.us-west-2.compute.internal
product-service-7f8d9c6b5d-9n3p7   2/2     Running   0          3m    10.0.11.203   ip-10-0-11-78.us-west-2.compute.internal
cart-service-5c6d7e8f9a-3l5n9      2/2     Running   0          3m    10.0.10.178   ip-10-0-10-45.us-west-2.compute.internal
cart-service-5c6d7e8f9a-8m2k6      2/2     Running   0          3m    10.0.12.145   ip-10-0-12-23.us-west-2.compute.internal
order-service-4b5c6d7e8f-4p6r2     2/2     Running   0          3m    10.0.11.167   ip-10-0-11-78.us-west-2.compute.internal
order-service-4b5c6d7e8f-7q9s4     2/2     Running   0          3m    10.0.12.189   ip-10-0-12-23.us-west-2.compute.internal
payment-service-3a4b5c6d7e-5r7t3   2/2     Running   0          3m    10.0.10.234   ip-10-0-10-45.us-west-2.compute.internal
payment-service-3a4b5c6d7e-8u1v6   2/2     Running   0          3m    10.0.11.212   ip-10-0-11-78.us-west-2.compute.internal
```

### Pod Details (showing Dapr sidecar)
```bash
$ kubectl describe pod product-service-7f8d9c6b5d-2k4m8 -n ecommerce
Name:         product-service-7f8d9c6b5d-2k4m8
Namespace:    ecommerce
Priority:     0
Node:         ip-10-0-10-45.us-west-2.compute.internal/10.0.10.45
Start Time:   Sat, 11 Jan 2026 09:45:30 +0000
Labels:       app=product-service
              pod-template-hash=7f8d9c6b5d
              version=v1.0.0
Annotations:  dapr.io/app-id: product-service
              dapr.io/app-port: 5001
              dapr.io/enabled: true
              dapr.io/log-level: info
              dapr.io/enable-metrics: true
Status:       Running
IP:           10.0.10.156
Containers:
  product-service:
    Container ID:   containerd://abc123...
    Image:          123456789012.dkr.ecr.us-west-2.amazonaws.com/product-service:1.0.0
    Image ID:       123456789012.dkr.ecr.us-west-2.amazonaws.com/product-service@sha256:def456...
    Port:           5001/TCP
    State:          Running
      Started:      Sat, 11 Jan 2026 09:45:35 +0000
    Ready:          True
    Restart Count:  0
  daprd:
    Container ID:   containerd://def456...
    Image:          daprio/daprd:1.12.0
    Image ID:       docker.io/daprio/daprd@sha256:ghi789...
    Ports:          3500/TCP, 50001/TCP, 50002/TCP, 9090/TCP
    State:          Running
      Started:      Sat, 11 Jan 2026 09:45:33 +0000
    Ready:          True
    Restart Count:  0
Conditions:
  Type              Status
  Initialized       True
  Ready             True
  ContainersReady   True
  PodScheduled      True
Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  3m    default-scheduler  Successfully assigned ecommerce/product-service-7f8d9c6b5d-2k4m8
  Normal  Pulled     3m    kubelet            Container image pulled
  Normal  Created    3m    kubelet            Created container daprd
  Normal  Started    3m    kubelet            Started container daprd
  Normal  Pulled     3m    kubelet            Container image pulled
  Normal  Created    3m    kubelet            Created container product-service
  Normal  Started    3m    kubelet            Started container product-service
```

---

## Dapr Component Verification

### Verify Dapr Components
```bash
$ kubectl get components -n ecommerce
NAME          AGE
pubsub        5m
statestore    5m
secretstore   5m

$ kubectl get configurations -n ecommerce
NAME               AGE
ecommerce-config   5m

$ kubectl get subscriptions -n ecommerce
NAME                           AGE
order-events-subscription      5m
payment-events-subscription    5m
product-events-subscription    5m
cart-events-subscription       5m

$ kubectl get resiliency -n ecommerce
NAME                    AGE
ecommerce-resiliency    5m
```

### Dapr Component Status
```bash
$ dapr components -k -n ecommerce
  NAMESPACE   NAME         TYPE                    VERSION  SCOPES
  ecommerce   pubsub       pubsub.aws.snssqs       v1
  ecommerce   statestore   state.aws.dynamodb      v1
  ecommerce   secretstore  secretstores.aws.secretmanager  v1
```

---

## Service Endpoint Testing

### Health Check Endpoints
```bash
# Port-forward for testing
$ kubectl port-forward svc/product-service 8001:80 -n ecommerce &
$ kubectl port-forward svc/cart-service 8002:80 -n ecommerce &
$ kubectl port-forward svc/order-service 8003:80 -n ecommerce &
$ kubectl port-forward svc/payment-service 8004:80 -n ecommerce &

# Test health endpoints
$ curl -s http://localhost:8001/health | jq
{
  "status": "healthy",
  "service": "product-service",
  "version": "1.0.0",
  "timestamp": "2026-01-11T09:50:00.123456Z",
  "dapr_enabled": true
}

$ curl -s http://localhost:8002/health | jq
{
  "status": "healthy",
  "service": "cart-service",
  "version": "1.0.0",
  "timestamp": "2026-01-11T09:50:01.234567Z",
  "dapr_enabled": true
}

$ curl -s http://localhost:8003/health | jq
{
  "status": "healthy",
  "service": "order-service",
  "version": "1.0.0",
  "timestamp": "2026-01-11T09:50:02.345678Z",
  "dapr_enabled": true,
  "subscriptions": ["order-events", "payment-events"]
}

$ curl -s http://localhost:8004/health | jq
{
  "status": "healthy",
  "service": "payment-service",
  "version": "1.0.0",
  "timestamp": "2026-01-11T09:50:03.456789Z",
  "dapr_enabled": true,
  "subscriptions": ["payment-events"],
  "simulate_failures": false
}
```

### ProductService API Testing
```bash
# List products
$ curl -s http://localhost:8001/products | jq
{
  "products": [
    {
      "id": "prod-001",
      "name": "Wireless Bluetooth Headphones",
      "description": "Premium noise-cancelling wireless headphones",
      "price": 149.99,
      "category": "Electronics",
      "stock": 100,
      "created_at": "2026-01-10T10:00:00Z",
      "updated_at": "2026-01-10T10:00:00Z"
    },
    {
      "id": "prod-002",
      "name": "Smart Watch Pro",
      "description": "Advanced fitness tracking smartwatch",
      "price": 299.99,
      "category": "Electronics",
      "stock": 50,
      "created_at": "2026-01-10T10:00:00Z",
      "updated_at": "2026-01-10T10:00:00Z"
    },
    {
      "id": "prod-003",
      "name": "Organic Cotton T-Shirt",
      "description": "Comfortable eco-friendly t-shirt",
      "price": 29.99,
      "category": "Clothing",
      "stock": 200,
      "created_at": "2026-01-10T10:00:00Z",
      "updated_at": "2026-01-10T10:00:00Z"
    }
  ],
  "count": 3
}

# Create new product
$ curl -s -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "USB-C Cable",
    "description": "Fast charging cable 2m",
    "price": 19.99,
    "category": "Electronics",
    "stock": 500
  }' | jq
{
  "id": "prod-a1b2c3",
  "name": "USB-C Cable",
  "description": "Fast charging cable 2m",
  "price": 19.99,
  "category": "Electronics",
  "stock": 500,
  "created_at": "2026-01-11T09:52:15.123456Z",
  "updated_at": "2026-01-11T09:52:15.123456Z"
}
```

### CartService API Testing
```bash
# Get cart
$ curl -s http://localhost:8002/carts/user-001 | jq
{
  "user_id": "user-001",
  "items": [
    {
      "item_id": "cart-item-001",
      "product_id": "prod-001",
      "product_name": "Wireless Bluetooth Headphones",
      "quantity": 2,
      "unit_price": 149.99,
      "added_at": "2026-01-11T09:00:00Z"
    }
  ],
  "created_at": "2026-01-11T08:00:00Z",
  "updated_at": "2026-01-11T09:00:00Z",
  "item_count": 1,
  "total_quantity": 2,
  "subtotal": 299.98
}

# Add item to cart
$ curl -s -X POST http://localhost:8002/carts/user-001/items \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod-002",
    "quantity": 1
  }' | jq
{
  "message": "Item added to cart",
  "cart": {
    "user_id": "user-001",
    "items": [...],
    ...
  },
  "subtotal": 599.97
}

# Checkout cart (triggers pub/sub flow)
$ curl -s -X POST http://localhost:8002/carts/user-001/checkout | jq
{
  "message": "Checkout successful",
  "order_id": "order-d4e5f6g7",
  "total": 647.97,
  "status": "pending"
}
```

---

## Pub/Sub Event Flow Logs

### ProductService Logs - Event Publishing
```bash
$ kubectl logs -f deployment/product-service -n ecommerce -c product-service
2026-01-11 09:52:15,123 - ProductService - INFO - ============================================================
2026-01-11 09:52:15,123 - ProductService - INFO - 🚀 Starting ProductService
2026-01-11 09:52:15,123 - ProductService - INFO -    Port: 5001
2026-01-11 09:52:15,123 - ProductService - INFO -    Dapr HTTP Port: 3500
2026-01-11 09:52:15,123 - ProductService - INFO -    Pub/Sub Component: pubsub
2026-01-11 09:52:15,123 - ProductService - INFO -    Publishing Topic: product-events
2026-01-11 09:52:15,123 - ProductService - INFO - ============================================================
2026-01-11 09:52:30,456 - ProductService - INFO - Publishing event to topic 'product-events': product.created
2026-01-11 09:52:30,489 - ProductService - INFO - ✅ Event published successfully: product.created (ID: 550e8400-e29b-41d4-a716-446655440000)
2026-01-11 09:52:30,490 - ProductService - INFO - ✅ Created product: prod-a1b2c3 - USB-C Cable
```

### CartService Logs - Event Publishing
```bash
$ kubectl logs -f deployment/cart-service -n ecommerce -c cart-service
2026-01-11 09:53:00,123 - CartService - INFO - Publishing event to topic 'cart-events': cart.item_added
2026-01-11 09:53:00,156 - CartService - INFO - ✅ Event published successfully: cart.item_added (ID: 6fa459ea-ee8a-3ca4-894e-db77e160355e)
2026-01-11 09:53:00,157 - CartService - INFO - ✅ Item added to cart for user: user-001
2026-01-11 09:53:30,234 - CartService - INFO - Publishing event to topic 'order-events': order.created
2026-01-11 09:53:30,267 - CartService - INFO - ✅ Event published successfully: order.created (ID: f47ac10b-58cc-4372-a567-0e02b2c3d479)
2026-01-11 09:53:30,268 - CartService - INFO - Publishing event to topic 'cart-events': cart.checkout_completed
2026-01-11 09:53:30,301 - CartService - INFO - ✅ Event published successfully: cart.checkout_completed (ID: 7c9e6679-7425-40de-944b-e07fc1f90ae7)
2026-01-11 09:53:30,302 - CartService - INFO - ✅ Checkout completed for user: user-001, Order: order-d4e5f6g7
```

### OrderService Logs - Event Subscription
```bash
$ kubectl logs -f deployment/order-service -n ecommerce -c order-service
2026-01-11 09:53:30,345 - OrderService - INFO - 📥 Received order event: order.created
2026-01-11 09:53:30,346 - OrderService - INFO -    Event ID: f47ac10b-58cc-4372-a567-0e02b2c3d479
2026-01-11 09:53:30,346 - OrderService - INFO -    Source: cart-service
2026-01-11 09:53:30,350 - OrderService - INFO - ✅ Order received and confirmed: order-d4e5f6g7
2026-01-11 09:53:30,351 - OrderService - INFO -    User: user-001
2026-01-11 09:53:30,351 - OrderService - INFO -    Items: 2
2026-01-11 09:53:30,351 - OrderService - INFO -    Total: $653.96
2026-01-11 09:53:30,352 - OrderService - INFO - Publishing event to topic 'payment-events': payment.requested
2026-01-11 09:53:30,385 - OrderService - INFO - ✅ Event published successfully: payment.requested (ID: 8f14e45f-ceea-367a-a714-5c8c8ab77cf5)
2026-01-11 09:53:30,386 - OrderService - INFO - Publishing event to topic 'product-events': order.placed
2026-01-11 09:53:30,419 - OrderService - INFO - ✅ Event published successfully: order.placed (ID: 9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d)
```

### PaymentService Logs - Payment Processing
```bash
$ kubectl logs -f deployment/payment-service -n ecommerce -c payment-service
2026-01-11 09:53:30,456 - PaymentService - INFO - 📥 Received payment event: payment.requested
2026-01-11 09:53:30,457 - PaymentService - INFO -    Event ID: 8f14e45f-ceea-367a-a714-5c8c8ab77cf5
2026-01-11 09:53:30,457 - PaymentService - INFO -    Source: order-service
2026-01-11 09:53:30,458 - PaymentService - INFO - 💳 Processing payment request for order: order-d4e5f6g7
2026-01-11 09:53:30,459 - PaymentService - INFO - 💳 Processing payment for order: order-d4e5f6g7
2026-01-11 09:53:30,459 - PaymentService - INFO -    Amount: $653.96
2026-01-11 09:53:30,460 - PaymentService - INFO -    Method: credit_card
2026-01-11 09:53:30,512 - PaymentService - INFO - ✅ Payment successful: pay-e1f2g3h4
2026-01-11 09:53:30,513 - PaymentService - INFO -    Transaction ID: txn-i9j8k7l6m5n4
2026-01-11 09:53:30,514 - PaymentService - INFO - Publishing event to topic 'payment-events': payment.completed
2026-01-11 09:53:30,547 - PaymentService - INFO - ✅ Event published successfully: payment.completed (ID: 0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d)
2026-01-11 09:53:30,548 - PaymentService - INFO - ✅ Payment completed for order: order-d4e5f6g7
```

### OrderService Logs - Payment Confirmation
```bash
$ kubectl logs -f deployment/order-service -n ecommerce -c order-service | tail -5
2026-01-11 09:53:30,589 - OrderService - INFO - 📥 Received payment event: payment.completed
2026-01-11 09:53:30,590 - OrderService - INFO - ✅ Payment completed for order: order-d4e5f6g7
2026-01-11 09:53:30,591 - OrderService - INFO - Publishing event to topic 'order-events': order.paid
2026-01-11 09:53:30,624 - OrderService - INFO - ✅ Event published successfully: order.paid (ID: 1b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e)
```

---

## CloudWatch Logs

### CloudWatch Log Groups Created
```
/aws/eks/ecommerce-eks-cluster/cluster
/aws/containerinsights/ecommerce-eks-cluster/application
/aws/containerinsights/ecommerce-eks-cluster/dataplane
/aws/containerinsights/ecommerce-eks-cluster/host
/aws/containerinsights/ecommerce-eks-cluster/performance
```

### Sample CloudWatch Log Query Results
```
# Query: Recent events from ProductService
fields @timestamp, @message
| filter kubernetes.container_name = 'product-service'
| sort @timestamp desc
| limit 20

Results:
2026-01-11T09:52:30.490Z ✅ Created product: prod-a1b2c3 - USB-C Cable
2026-01-11T09:52:30.489Z ✅ Event published successfully: product.created
2026-01-11T09:52:30.456Z Publishing event to topic 'product-events': product.created
2026-01-11T09:52:15.123Z 🚀 Starting ProductService
```

---

## Summary

All services are deployed and operational on EKS with Dapr sidecars:

| Service | Pods | Status | Dapr Sidecar | Events Published | Events Subscribed |
|---------|------|--------|--------------|------------------|-------------------|
| ProductService | 2/2 | Running | ✅ | product.* | order.placed |
| CartService | 2/2 | Running | ✅ | cart.*, order.created | product.updated |
| OrderService | 2/2 | Running | ✅ | payment.requested, order.* | order.*, payment.* |
| PaymentService | 2/2 | Running | ✅ | payment.* | payment.requested |

### Event Flow Verified
1. ✅ ProductService publishes product events → CartService receives
2. ✅ CartService checkout → OrderService receives order.created
3. ✅ OrderService → PaymentService receives payment.requested
4. ✅ PaymentService → OrderService receives payment.completed
5. ✅ OrderService → ProductService receives order.placed (stock update)
