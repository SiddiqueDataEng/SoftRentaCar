#!/bin/bash
# Soft Rent a Car — AWS ECS Fargate Deployment Script
# Prerequisites: aws cli, docker configured
# Run: chmod +x deploy/aws/deploy.sh && ./deploy/aws/deploy.sh

set -e

# ── Configuration ──────────────────────────────────────────────────────
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="softrentacar"
ECS_CLUSTER="soft-rentacar-cluster"
ECS_SERVICE="soft-rentacar-service"
ECS_TASK="soft-rentacar-task"
S3_BUCKET="softrentacar-data-${AWS_ACCOUNT_ID}"

echo "🚗 Deploying Soft Rent a Car to AWS..."
echo "Account: $AWS_ACCOUNT_ID | Region: $AWS_REGION"

# ── S3 Buckets ─────────────────────────────────────────────────────────
echo "→ Creating S3 buckets..."
aws s3 mb s3://$S3_BUCKET --region $AWS_REGION 2>/dev/null || true
aws s3 mb s3://${S3_BUCKET}-processed --region $AWS_REGION 2>/dev/null || true

# ── ECR Repository ─────────────────────────────────────────────────────
echo "→ Creating ECR repository..."
aws ecr create-repository \
    --repository-name $ECR_REPO \
    --region $AWS_REGION \
    --output none 2>/dev/null || true

ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO"

# ── Build & Push Docker Image ──────────────────────────────────────────
echo "→ Building Docker image..."
docker build -t $ECR_REPO:latest .

echo "→ Pushing to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
docker tag $ECR_REPO:latest $ECR_URI:latest
docker push $ECR_URI:latest

# ── Secrets Manager ────────────────────────────────────────────────────
echo "→ Storing secrets in AWS Secrets Manager..."
aws secretsmanager create-secret \
    --name "softrentacar/openai-key" \
    --secret-string "${OPENAI_API_KEY:-placeholder}" \
    --region $AWS_REGION --output none 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id "softrentacar/openai-key" \
    --secret-string "${OPENAI_API_KEY:-placeholder}" \
    --region $AWS_REGION --output none

aws secretsmanager create-secret \
    --name "softrentacar/carto-key" \
    --secret-string "${CARTO_API_KEY:-placeholder}" \
    --region $AWS_REGION --output none 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id "softrentacar/carto-key" \
    --secret-string "${CARTO_API_KEY:-placeholder}" \
    --region $AWS_REGION --output none

OPENAI_SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id "softrentacar/openai-key" --query ARN --output text)
CARTO_SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id "softrentacar/carto-key" --query ARN --output text)

# ── IAM Role for ECS Task ──────────────────────────────────────────────
echo "→ Creating ECS task execution role..."
aws iam create-role \
    --role-name ecsTaskExecutionRole-SoftRentaCar \
    --assume-role-policy-document '{
        "Version":"2012-10-17",
        "Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},
        "Action":"sts:AssumeRole"}]}' \
    --output none 2>/dev/null || true

aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole-SoftRentaCar \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
    --output none 2>/dev/null || true

TASK_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole-SoftRentaCar"

# ── CloudWatch Log Group ───────────────────────────────────────────────
aws logs create-log-group --log-group-name /ecs/soft-rentacar \
    --region $AWS_REGION --output none 2>/dev/null || true

# ── ECS Cluster ────────────────────────────────────────────────────────
echo "→ Creating ECS cluster..."
aws ecs create-cluster --cluster-name $ECS_CLUSTER --output none 2>/dev/null || true

# ── Task Definition ────────────────────────────────────────────────────
echo "→ Registering task definition..."
TASK_DEF=$(cat <<EOF
{
  "family": "$ECS_TASK",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "$TASK_ROLE_ARN",
  "containerDefinitions": [{
    "name": "soft-rentacar",
    "image": "$ECR_URI:latest",
    "essential": true,
    "portMappings": [{"containerPort": 8501, "protocol": "tcp"}],
    "secrets": [
      {"name": "OPENAI_API_KEY", "valueFrom": "$OPENAI_SECRET_ARN"},
      {"name": "CARTO_API_KEY",  "valueFrom": "$CARTO_SECRET_ARN"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/soft-rentacar",
        "awslogs-region": "$AWS_REGION",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "healthCheck": {
      "command": ["CMD-SHELL","curl -f http://localhost:8501/_stcore/health || exit 1"],
      "interval": 30, "timeout": 10, "retries": 3, "startPeriod": 60
    }
  }]
}
EOF
)

aws ecs register-task-definition \
    --cli-input-json "$TASK_DEF" \
    --region $AWS_REGION --output none

# ── ECS Service (requires VPC subnet — use default) ────────────────────
DEFAULT_VPC=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true \
    --query 'Vpcs[0].VpcId' --output text)
DEFAULT_SUBNET=$(aws ec2 describe-subnets \
    --filters Name=vpc-id,Values=$DEFAULT_VPC Name=defaultForAz,Values=true \
    --query 'Subnets[0].SubnetId' --output text)
DEFAULT_SG=$(aws ec2 describe-security-groups \
    --filters Name=vpc-id,Values=$DEFAULT_VPC Name=group-name,Values=default \
    --query 'SecurityGroups[0].GroupId' --output text)

echo "→ Creating ECS service..."
aws ecs create-service \
    --cluster $ECS_CLUSTER \
    --service-name $ECS_SERVICE \
    --task-definition $ECS_TASK \
    --launch-type FARGATE \
    --desired-count 1 \
    --network-configuration "awsvpcConfiguration={subnets=[$DEFAULT_SUBNET],securityGroups=[$DEFAULT_SG],assignPublicIp=ENABLED}" \
    --region $AWS_REGION \
    --output none 2>/dev/null || \
aws ecs update-service \
    --cluster $ECS_CLUSTER \
    --service $ECS_SERVICE \
    --force-new-deployment \
    --region $AWS_REGION --output none

echo ""
echo "✅ AWS Deployment complete!"
echo "📋 Check status: aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE"
echo "📊 Logs: aws logs tail /ecs/soft-rentacar --follow"
echo ""
echo "💡 To get the public IP:"
echo "   aws ecs list-tasks --cluster $ECS_CLUSTER --service-name $ECS_SERVICE"
echo "   aws ecs describe-tasks --cluster $ECS_CLUSTER --tasks <TASK_ARN>"
