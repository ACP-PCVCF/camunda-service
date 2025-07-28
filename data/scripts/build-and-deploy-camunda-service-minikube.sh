#!/bin/bash

# Simple build and deploy script for existing Minikube cluster
set -e

echo "🔨 Building Docker image with updated files..."

# Set Docker environment to use Minikube's Docker daemon
eval $(minikube docker-env)

# Build the image with a new tag to force update
IMAGE_TAG="v$(date +%s)"
docker build -t camunda-service:${IMAGE_TAG} .

echo "✅ Image built: camunda-service:${IMAGE_TAG}"

# Update the deployment to use the new image
echo "🚀 Updating deployment..."
kubectl set image deployment/camunda-service camunda-service=camunda-service:${IMAGE_TAG} -n proving-system

# Wait for rollout to complete
echo "⏳ Waiting for rollout to complete..."
kubectl rollout status deployment/camunda-service -n proving-system

echo "✅ Deployment updated successfully!"
echo "📋 Pod status:"
kubectl get pods -n proving-system -l app=camunda-service
