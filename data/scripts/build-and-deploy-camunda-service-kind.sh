#!/bin/bash

# Build and deploy script for kind cluster
set -e

# Configuration
KIND_CLUSTER_NAME="trace"
NAMESPACE="proving-system"
SERVICE_NAME="camunda-service"

echo "🔨 Building Docker image with updated files..."

IMAGE_TAG="v$(date +%s)"
IMAGE_NAME="${SERVICE_NAME}:${IMAGE_TAG}"

docker build -t ${IMAGE_NAME} .

echo "✅ Image built: ${IMAGE_NAME}"

echo "📦 Loading image into kind cluster..."
kind load docker-image ${IMAGE_NAME} --name ${KIND_CLUSTER_NAME}

echo "✅ Image loaded into kind cluster"

echo "🔍 Checking namespace..."
if ! kubectl get namespace ${NAMESPACE} >/dev/null 2>&1; then
    echo "📝 Creating namespace ${NAMESPACE}..."
    kubectl create namespace ${NAMESPACE}
else
    echo "✅ Namespace ${NAMESPACE} already exists"
fi

echo "🚀 Updating deployment..."
kubectl set image deployment/${SERVICE_NAME} ${SERVICE_NAME}=${IMAGE_NAME} -n ${NAMESPACE}

echo "⏳ Waiting for rollout to complete..."
kubectl rollout status deployment/${SERVICE_NAME} -n ${NAMESPACE} --timeout=300s

echo "✅ Deployment updated successfully!"
echo "📋 Pod status:"
kubectl get pods -n ${NAMESPACE} -l app=${SERVICE_NAME}

echo ""
echo "🎉 Deployment complete!"
echo "📊 To check logs, run:"
echo "   kubectl logs -f deployment/${SERVICE_NAME} -n ${NAMESPACE}"
echo ""
echo "🔍 To check service status, run:"
echo "   kubectl get svc -n ${NAMESPACE}"
echo ""
echo "🌐 To port-forward and access the service locally, run:"
echo "   kubectl port-forward svc/${SERVICE_NAME} 8000:8000 -n ${NAMESPACE}"
