# Prediction With Custom Trained Model

This application provides a frontend for getting predictions from a custom
trained mode in Vertex AI.

![LLM Text demo](images/fe.png)

## Deploying to GKE

### Setup Service Account

Compute service account is used by default. However, it's recommended to
use a separate service account for minimum permissions.

1. Enable required API

```bash
gcloud services enable compute.googleapis.com \
    container.googleapis.com
```

2. Set the environment vars based on your environment

```bash
export PROJECT_ID=<YOUR_PROJECT_ID>
export REGION=<YOUR_GCP_REGION_NAME>
```

3. Set up the cluster 

```shell
gcloud container clusters create demo-gke-cluster --zone $REGION --num-nodes 1 --project $PROJECT_ID

gcloud container clusters get-credentials demo-gke-cluster --zone $REGION --project $PROJECT_ID

export PROJECT_NUMBER=`gcloud projects describe $PROJECT_ID --format="value(projectNumber)"`

# Enable Workload Identity Federation. Note that, for GKE Autopilot clusters Workload Identity Federation is already enabled by default.
gcloud container clusters update demo-gke-cluster \
    --zone=$REGION \
    --workload-pool=$PROJECT_ID.svc.id.goog

gcloud container node-pools update default-pool \
    --cluster=demo-gke-cluster \
    --zone=$REGION \
    --workload-metadata=GKE_METADATA
```

4. Create and Authorize a Kubernetes ServiceAccount

```shell
kubectl create serviceaccount prediction-app-k8s-sa

# Add `aiplatform.user` role    
gcloud projects add-iam-policy-binding projects/$PROJECT_ID \
    --role=roles/aiplatform.user \
    --member=principal://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$PROJECT_ID.svc.id.goog/subject/ns/default/sa/prediction-app-k8s-sa \
    --condition=None    

# Add `logging.logWriter` role
gcloud projects add-iam-policy-binding projects/$PROJECT_ID \
    --role=roles/logging.logWriter \
    --member=principal://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$PROJECT_ID.svc.id.goog/subject/ns/default/sa/prediction-app-k8s-sa \
    --condition=None    
```

### Build

Build the docker image with Cloud Build and upload the image to Artifact
Registry.

```shell
export AR_REPO=$PROJECT_ID-app-ar
export SERVICE_NAME=$PROJECT_ID-app-prediction
export APP_IMAGE=$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/$SERVICE_NAME

gcloud artifacts repositories create ${AR_REPO} \
    --location=$REGION \
    --repository-format=Docker

gcloud builds submit app --tag $APP_IMAGE
```

### Deploy

Get Vertex AI model endpoint.

```shell
export MODEL_DISPLAY_NAME=<your model display name>
export MODEL_ENDPOINT=`gcloud ai endpoints list \
--project="$PROJECT_ID" \
--region="$REGION" \
--filter="DISPLAY_NAME: $MODEL_DISPLAY_NAME" \
--sort-by=~creationTimestamp \
--limit=1 \
--format="flattened(name)" \
| awk '{print $2}' | tr -d '\n'`
```

Deploy `prediction-app` to the `demo-gke-cluster` GKE cluster.

```shell
cat <<EOF > app/pod.yaml 
apiVersion: v1
kind: Pod
metadata:
  name: prediction-app
  namespace: default
spec:
  containers:
  - name: prediction-app
    image: ${APP_IMAGE}:latest
    imagePullPolicy: Always
    args:
    - python
    - "app.py"
    - "--project-id=${PROJECT_ID}"
    - "--location=${REGION}"
    - "--endpoint=${MODEL_ENDPOINT}"
    ports:
    - containerPort: 7860 # Or the port on which your web app listens
  serviceAccountName: prediction-app-k8s-sa
  nodeSelector:
    iam.gke.io/gke-metadata-server-enabled: "true"
EOF

kubectl apply -f app/pod.yaml
```

### Test

Use Port Forwarding to Access Applications in a Cluster

```shell
kubectl port-forward prediction-app 7860:7860
```

Open the below link in your browser

http://127.0.0.1:7860
