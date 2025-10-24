SETUP INSTRUCTION FOR THE BITCOIN KEY GENERATOR PROJECT:
1.	Create a new project:
In the current example I would use: bitcoin-generator-1 as project name and ID
2.	Open the cloud shell making sure bitcoin-generator-1 is default or run the following command:
gcloud config set project bitcoin-generator-1 (change it as per project ID )
3.	Create a firewall to allow public HTTP access (port 80)
It can be done console or the following command:
gcloud compute firewall-rules create allow-http \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server
4.	Enable kubernet and Artifact registry: using the following command
gcloud services enable \
artifactregistry.googleapis.com \
container.googleapis.com

5.	Create kubernet cluster
It can be done console or the following command:
gcloud container clusters create btc-keygen-cluster \
--zone us-central1-b \
--num-nodes 3 \
--machine-type n1-standard-2 \
--image-type UBUNTU_CONTAINERD \
--disk-type pd-balanced \
--disk-size 20 \
--release-channel regular
To interact with kubernet cluster run: 
gcloud container clusters get-credentials btc-keygen-cluster --zone us-central1-b
6.	Create artifact repository using the following command:

gcloud artifacts repositories create keygen-repo \
--repository-format=docker \
--location=us-central1 \
--description="Docker repo for Bitcoin Keygen project"

7.	Build docker images for backend and frontend:
To build docker images run the following command,
You need to replace “bitcoin-generator-1” if your project id is different

cd ~/BTC-Keygen/backend
docker build -t us-central1-docker.pkg.dev/bitcoin-generator-1($Project_ID)/keygen-repo/backend:latest .
docker push us-central1-docker.pkg.dev/bitcoin-generator-1($Project_ID)/keygen-repo/backend:latest

cd ~/BTC-Keygen/frontend
docker build -t us-central1-docker.pkg.dev/bitcoin-generator-1($Project_ID)/keygen-repo/frontend:latest .
docker push us-central1-docker.pkg.dev/bitcoin-generator-1($Project_ID)/keygen-repo/frontend:latest

8.	Update image references as in YAML files :

image: us-central1-docker.pkg.dev/bitcoin-generator-1($Project_ID)/keygen-repo/backend:latest
image: us-central1-docker.pkg.dev/bitcoin-generator-1($Project_ID)/keygen-repo/frontend:latest

9.	Run kubernet:
kubectl create namespace keygen
kubectl apply -f ~/BTC-Keygen/k8s/ -n keygen
kubectl get pods -n keygen
kubectl get svc -n keygen
