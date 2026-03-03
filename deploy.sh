#!/bin/bash
set -e

# Google Cloud Run Deployment Script

# Ask for the Google Cloud Project ID if not set
if [ -z "$PROJECT_ID" ]; then
  read -p "Enter your Google Cloud Project ID: " PROJECT_ID
fi

REGION="us-central1" # You can change this to your preferred region

echo "Deploying to Project: $PROJECT_ID in Region: $REGION"

# 1. Provide permissions / enable services (Make sure you have run `gcloud auth login` first!)
echo "Enabling required Cloud APIs..."
gcloud services enable run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    --project $PROJECT_ID

# 2. Deploy Backend
echo "Deploying Backend..."
gcloud run deploy horoscope-backend \
    --source ./backend \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --project $PROJECT_ID \
    --format="value(status.url)" > backend_url.txt

BACKEND_URL=$(cat backend_url.txt)
echo "Backend deployed at: $BACKEND_URL"

# 3. Deploy Frontend
echo "Deploying Frontend..."
gcloud run deploy horoscope-frontend \
    --source ./frontend \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --project $PROJECT_ID \
    --set-env-vars NEXT_PUBLIC_API_URL=$BACKEND_URL,API_URL=$BACKEND_URL \
    --format="value(status.url)" > frontend_url.txt

FRONTEND_URL=$(cat frontend_url.txt)
echo "Frontend deployed at: $FRONTEND_URL"

echo ""
echo "🎉 Deployment Complete!"
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo "You can now visit $FRONTEND_URL to see your app live."
