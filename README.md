# E-Commerce Microservices Platform on AWS EKS with Dapr

[![AWS](https://img.shields.io/badge/AWS-EKS-orange?logo=amazon-aws)](https://aws.amazon.com/eks/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.29-blue?logo=kubernetes)](https://kubernetes.io/)
[![Dapr](https://img.shields.io/badge/Dapr-1.12.0-blueviolet)](https://dapr.io/)
[![Python](https://img.shields.io/badge/Python-3.11-green?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A production-ready e-commerce microservices platform deployed on Amazon EKS with Dapr sidecars for pub/sub messaging using AWS SNS/SQS.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Detailed Setup Guide](#detailed-setup-guide)
- [Microservices](#microservices)
- [API Reference](#api-reference)
- [Dapr Configuration](#dapr-configuration)
- [Testing](#testing)
- [Monitoring & Observability](#monitoring--observability)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🎯 Overview

This project demonstrates the deployment of a containerized microservices architecture on Amazon EKS with Dapr (Distributed Application Runtime) sidecars implementing pub/sub messaging patterns for real-time event-driven interactions.

### Key Features

- **4 Microservices**: Product, Cart, Order, and Payment services
- **Event-Driven Architecture**: Using Dapr pub/sub with AWS SNS/SQS
- **Cloud-Native**: Fully containerized and Kubernetes-native
- **Resilient**: Built-in retry policies and circuit breakers
- **Observable**: Integrated with CloudWatch and distributed tracing
- **Scalable**: Horizontal Pod Autoscaler configured for each service

### Technology Stack

| Component | Technology |
|-----------|------------|
| Container Orchestration | Amazon EKS (Kubernetes 1.29) |
| Container Runtime | Docker / containerd |
| Service Mesh | Dapr 1.12.0 |
| Message Broker | AWS SNS/SQS |
| Programming Language | Python 3.11 |
| Web Framework | Flask |
| Container Registry | Amazon ECR |
| Infrastructure as Code | eksctl, CloudFormation |
| Observability | CloudWatch, X-Ray |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Amazon EKS Cluster                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Namespace: ecommerce                          │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │   │
│  │  │ProductService │  │  CartService  │  │ OrderService  │        │   │
│  │  │  + Dapr       │  │  + Dapr       │  │  + Dapr       │        │   │
│  │  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘        │   │
│  │          │                  │                  │                 │   │
│  │  ┌───────────────┐          │                  │                 │   │
│  │  │PaymentService │          │                  │                 │   │
│  │  │  + Dapr       │          │                  │                 │   │
│  │  └───────┬───────┘          │                  │                 │   │
│  └──────────┼──────────────────┼──────────────────┼─────────────────┘   │
│             │                  │                  │                     │
│             └──────────────────┼──────────────────┘                     │
│                                │                                        │
│                      ┌─────────┴─────────┐                              │
│                      │   Dapr Pub/Sub    │                              │
│                      │  (AWS SNS/SQS)    │                              │
│                      └───────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Event Flow

1. **Product Events**: ProductService → SNS → SQS → CartService, OrderService
2. **Cart Events**: CartService → SNS → SQS → OrderService
3. **Order Events**: CartService/OrderService → SNS → SQS → PaymentService, OrderService
4. **Payment Events**: PaymentService → SNS → SQS → OrderService

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed diagrams.

### 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Detailed architecture diagrams and component descriptions |
| [DEPLOYMENT_LOGS.md](docs/DEPLOYMENT_LOGS.md) | EKS cluster creation and deployment evidence |
| [ECR_IMAGE_PUSH_LOGS.md](docs/ECR_IMAGE_PUSH_LOGS.md) | Container image build and ECR push logs |
| [PRODUCTSERVICE_ORDERSERVICE_FLOW.md](docs/PRODUCTSERVICE_ORDERSERVICE_FLOW.md) | Detailed pub/sub event flow logs and screenshots |
| [BEDROCK_INSIGHTS.md](docs/BEDROCK_INSIGHTS.md) | AI-generated recommendations for improvements |

## ✅ Prerequisites

### Required Tools

| Tool | Version | Description |
|------|---------|-------------|
| AWS CLI | 2.x | AWS command-line interface |
| kubectl | 1.29+ | Kubernetes CLI |
| eksctl | 0.165.0+ | EKS cluster management |
| Helm | 3.x | Kubernetes package manager |
| Docker | 24.x | Container runtime |
| Python | 3.11 | For local development |

### AWS Permissions

Required IAM permissions:
- EKS: Full access
- ECR: Full access
- SNS/SQS: Full access
- IAM: Role creation
- CloudWatch: Logs access
- VPC: Network management

### Installation Commands

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Install kubectl
curl -LO "https://dl.k8s.io/release/v1.29.0/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install Dapr CLI
curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash
```

## 📁 Project Structure

```
ecommerce-eks-dapr/
├── services/                    # Microservices source code
│   ├── product-service/
│   │   ├── app.py              # ProductService application
│   │   ├── requirements.txt    # Python dependencies
│   │   └── Dockerfile          # Multi-stage Dockerfile
│   ├── cart-service/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── order-service/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── payment-service/
│       ├── app.py
│       ├── requirements.txt
│       └── Dockerfile
├── k8s/                         # Kubernetes manifests
│   ├── namespace.yaml          # Namespace and quotas
│   ├── rbac.yaml              # Service accounts and RBAC
│   └── deployments/
│       ├── product-service.yaml
│       ├── cart-service.yaml
│       ├── order-service.yaml
│       └── payment-service.yaml
├── dapr/                        # Dapr configurations
│   └── components/
│       ├── pubsub.yaml         # SNS/SQS pub/sub component
│       └── statestore.yaml     # DynamoDB state store
├── eks/                         # EKS cluster configuration
│   └── eks-cluster.yaml        # eksctl cluster spec
├── aws/                         # AWS infrastructure
│   └── cloudformation/
│       └── sns-sqs-infrastructure.yaml
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT_LOGS.md
└── README.md                    # This file
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Krishnakumarb1994/ContainerizedMicroServiceWithEKSAndDAPR
cd ecommerce-eks-dapr
```

### 2. Configure AWS

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, Region (us-west-2)
```

### 3. Create EKS Cluster

```bash
eksctl create cluster -f eks/eks-cluster.yaml
```

### 4. Install Dapr

```bash
helm repo add dapr https://dapr.github.io/helm-charts/
helm repo update
helm install dapr dapr/dapr --namespace dapr-system --create-namespace --wait
```

### 5. Build and Push Images

```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com

# Build and push each service
for service in product cart order payment; do
  cd services/${service}-service
  docker build -t ${service}-service:1.0.0 .
  docker tag ${service}-service:1.0.0 <ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/${service}-service:1.0.0
  docker push <ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/${service}-service:1.0.0
  cd ../..
done
```

### 6. Deploy Services

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f dapr/components/
kubectl apply -f k8s/deployments/
```

### 7. Verify Deployment

```bash
kubectl get pods -n ecommerce
# All pods should show 2/2 READY (app container + Dapr sidecar)
```

## 📖 Detailed Setup Guide

### Step 1: Create ECR Repositories

```bash
aws ecr create-repository --repository-name product-service --region us-west-2
aws ecr create-repository --repository-name cart-service --region us-west-2
aws ecr create-repository --repository-name order-service --region us-west-2
aws ecr create-repository --repository-name payment-service --region us-west-2
```

### Step 2: Deploy AWS Infrastructure

```bash
aws cloudformation create-stack \
  --stack-name ecommerce-messaging \
  --template-body file://aws/cloudformation/sns-sqs-infrastructure.yaml \
  --capabilities CAPABILITY_IAM
```

### Step 3: Create EKS Cluster

```bash
# Create cluster (takes ~15-20 minutes)
eksctl create cluster -f eks/eks-cluster.yaml

# Verify cluster
kubectl cluster-info
kubectl get nodes
```

### Step 4: Install Dapr on EKS

```bash
# Add Dapr Helm repo
helm repo add dapr https://dapr.github.io/helm-charts/
helm repo update

# Install Dapr runtime
helm upgrade --install dapr dapr/dapr \
  --version=1.12.0 \
  --namespace dapr-system \
  --create-namespace \
  --wait

# Verify installation
kubectl get pods -n dapr-system
dapr status -k
```

### Step 5: Build Docker Images

```bash
# Update image URIs in k8s manifests with your AWS Account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
sed -i "s/123456789012/${AWS_ACCOUNT_ID}/g" k8s/deployments/*.yaml

# Build and push images
./scripts/build-push.sh  # Or manually as shown in Quick Start
```

### Step 6: Deploy Application

```bash
# Create namespace and RBAC
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml

# Deploy Dapr components
kubectl apply -f dapr/components/

# Deploy microservices
kubectl apply -f k8s/deployments/

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=product-service -n ecommerce --timeout=120s
kubectl wait --for=condition=ready pod -l app=cart-service -n ecommerce --timeout=120s
kubectl wait --for=condition=ready pod -l app=order-service -n ecommerce --timeout=120s
kubectl wait --for=condition=ready pod -l app=payment-service -n ecommerce --timeout=120s
```

## 🔧 Microservices

### ProductService (Port 5001)

Manages the product catalog with CRUD operations and publishes product events.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/products` | GET | List all products |
| `/products/<id>` | GET | Get product by ID |
| `/products` | POST | Create product |
| `/products/<id>` | PUT | Update product |
| `/products/<id>` | DELETE | Delete product |
| `/products/<id>/stock` | PATCH | Update stock |

**Events Published:**
- `product.created` - New product created
- `product.updated` - Product modified
- `product.deleted` - Product removed
- `product.stock_updated` - Stock level changed

### CartService (Port 5002)

Manages shopping carts and handles checkout process.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/carts/<user_id>` | GET | Get user's cart |
| `/carts/<user_id>/items` | POST | Add item to cart |
| `/carts/<user_id>/items/<item_id>` | PUT | Update cart item |
| `/carts/<user_id>/items/<item_id>` | DELETE | Remove from cart |
| `/carts/<user_id>` | DELETE | Clear cart |
| `/carts/<user_id>/checkout` | POST | Checkout cart |

**Events Published:**
- `cart.item_added` - Item added to cart
- `cart.item_updated` - Cart item quantity changed
- `cart.item_removed` - Item removed from cart
- `cart.cleared` - Cart emptied
- `cart.checkout_completed` - Checkout successful
- `order.created` - Order created from checkout

### OrderService (Port 5003)

Processes orders and manages order lifecycle.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/orders` | GET | List all orders |
| `/orders/<id>` | GET | Get order by ID |
| `/orders/user/<user_id>` | GET | Get user's orders |
| `/orders/<id>/status` | PUT | Update order status |
| `/orders` | POST | Create order |

**Events Subscribed:**
- `order.created` - From CartService
- `payment.completed` - From PaymentService
- `payment.failed` - From PaymentService

**Events Published:**
- `payment.requested` - Request payment processing
- `order.confirmed` - Order confirmed
- `order.paid` - Payment received
- `order.placed` - Stock reduction needed

### PaymentService (Port 5004)

Processes payments and manages payment records.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/payments` | GET | List all payments |
| `/payments/<id>` | GET | Get payment by ID |
| `/payments/order/<order_id>` | GET | Get payment for order |
| `/payments/process` | POST | Process payment |
| `/payments/<id>/refund` | POST | Refund payment |

**Events Subscribed:**
- `payment.requested` - From OrderService

**Events Published:**
- `payment.completed` - Payment successful
- `payment.failed` - Payment failed
- `payment.refunded` - Payment refunded

## 📡 API Reference

### Create Product Example

```bash
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Mouse",
    "description": "Ergonomic wireless mouse",
    "price": 29.99,
    "category": "Electronics",
    "stock": 100
  }'
```

### Add to Cart Example

```bash
curl -X POST http://localhost:8002/carts/user-001/items \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod-001",
    "quantity": 2
  }'
```

### Checkout Example

```bash
curl -X POST http://localhost:8002/carts/user-001/checkout
```

## ⚙️ Dapr Configuration

### Pub/Sub Component (AWS SNS/SQS)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
  namespace: ecommerce
spec:
  type: pubsub.aws.snssqs
  version: v1
  metadata:
    - name: region
      value: "us-west-2"
    - name: messageVisibilityTimeout
      value: "30"
    - name: messageWaitTimeSeconds
      value: "20"
```

### Topics and Subscriptions

| Topic | Publishers | Subscribers |
|-------|-----------|-------------|
| `product-events` | ProductService | CartService, OrderService |
| `cart-events` | CartService | OrderService |
| `order-events` | CartService, OrderService | OrderService, ProductService |
| `payment-events` | PaymentService, OrderService | PaymentService, OrderService |

## 🧪 Testing

### Port Forwarding for Local Testing

```bash
# Forward all services
kubectl port-forward svc/product-service 8001:80 -n ecommerce &
kubectl port-forward svc/cart-service 8002:80 -n ecommerce &
kubectl port-forward svc/order-service 8003:80 -n ecommerce &
kubectl port-forward svc/payment-service 8004:80 -n ecommerce &
```

### Health Check Tests

```bash
# Test all services
for port in 8001 8002 8003 8004; do
  echo "Testing port $port:"
  curl -s http://localhost:$port/health | jq
done
```

### End-to-End Flow Test

```bash
# 1. Create a product
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Product","description":"Test","price":10.00,"category":"Test","stock":100}'

# 2. Add to cart
curl -X POST http://localhost:8002/carts/test-user/items \
  -H "Content-Type: application/json" \
  -d '{"product_id":"prod-001","quantity":1}'

# 3. Checkout
curl -X POST http://localhost:8002/carts/test-user/checkout

# 4. Check order
curl http://localhost:8003/orders

# 5. Check payment
curl http://localhost:8004/payments
```

### View Logs

```bash
# View all service logs
kubectl logs -f -l app=product-service -n ecommerce -c product-service
kubectl logs -f -l app=order-service -n ecommerce -c order-service

# View Dapr sidecar logs
kubectl logs -f -l app=product-service -n ecommerce -c daprd
```

## 📊 Monitoring & Observability

### CloudWatch Logs

Logs are automatically sent to CloudWatch:
- `/aws/eks/ecommerce-eks-cluster/cluster`
- `/aws/containerinsights/ecommerce-eks-cluster/application`

### Metrics

Dapr metrics available at port 9090 on each pod:
```bash
kubectl port-forward pod/<pod-name> 9090:9090 -n ecommerce
curl http://localhost:9090/metrics
```

### View HPA Status

```bash
kubectl get hpa -n ecommerce
```

## 🔧 Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n ecommerce

# Check events
kubectl get events -n ecommerce --sort-by='.lastTimestamp'
```

### Dapr Issues

```bash
# Check Dapr system status
kubectl get pods -n dapr-system
dapr status -k

# Check Dapr sidecar logs
kubectl logs <pod-name> -n ecommerce -c daprd
```

### Pub/Sub Not Working

```bash
# Verify components
kubectl get components -n ecommerce
kubectl describe component pubsub -n ecommerce

# Check SNS/SQS in AWS Console
aws sns list-topics
aws sqs list-queues
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Pods stuck in Pending | Check node capacity, resource quotas |
| ImagePullBackOff | Verify ECR permissions, image tags |
| CrashLoopBackOff | Check application logs, health endpoints |
| Dapr sidecar not injecting | Verify annotations, namespace labels |

## 🧹 Cleanup

```bash
# Delete application
kubectl delete -f k8s/deployments/
kubectl delete -f dapr/components/
kubectl delete -f k8s/rbac.yaml
kubectl delete -f k8s/namespace.yaml

# Uninstall Dapr
helm uninstall dapr -n dapr-system

# Delete EKS cluster
eksctl delete cluster -f eks/eks-cluster.yaml

# Delete AWS resources
aws cloudformation delete-stack --stack-name ecommerce-messaging

# Delete ECR repositories
for repo in product-service cart-service order-service payment-service; do
  aws ecr delete-repository --repository-name $repo --force
done
```

## 📚 References

- [Amazon EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Dapr Documentation](https://docs.dapr.io/)
- [Dapr AWS SNS/SQS Component](https://docs.dapr.io/reference/components-reference/supported-pubsub/setup-aws-snssqs/)
- [eksctl Documentation](https://eksctl.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Author**: Cloud Native Architecture Team  
**Last Updated**: January 11, 2026  
**Version**: 1.0.0
