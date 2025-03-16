

# Push to ECR
aws ecr create-repository --repository-name fastapi-app --region us-east-1
docker build -t fastapi-app .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 339712985071.dkr.ecr.us-east-1.amazonaws.com
docker tag fastapi-app:latest 339712985071.dkr.ecr.us-east-1.amazonaws.com/fastapi-app:latest
docker push 339712985071.dkr.ecr.us-east-1.amazonaws.com/fastapi-app:latest

# Build the Infrastructure
cd terraform
terraform init
terraform apply