# Streamlit Cloud Deployment Guide

Follow these steps to deploy the Sports Betting Model application to Streamlit Cloud.

## Prerequisites

1. Your code is pushed to a GitHub repository
2. You have deployed the FastAPI backend (using Render or another service)
3. You have your FastAPI backend URL

## Deployment Steps

1. Go to [Streamlit Cloud](https://streamlit.io/cloud) and sign in with GitHub

2. Click "New app" button in the dashboard

3. Select your repository, branch, and the main file:
   - Repository: Your GitHub repository
   - Branch: main (or your default branch)
   - Main file path: `streamlit_app.py`

4. Advanced Settings:
   - Click "Advanced settings"
   - Add secrets (these will be encrypted):
     - Key: `API_URL`
     - Value: `https://your-sports-betting-api.onrender.com` (replace with your actual API URL)

5. Click "Deploy!"

## Verification

After deployment completes:

1. Check that your app loads correctly
2. Verify that it connects to your API (it should display a connection status)
3. Test functionality by selecting a bookmaker and clicking "Get Fresh Props"

## Troubleshooting

If you encounter issues:

1. **API Connection Error**: Check that your API_URL is correct and the API is running
2. **Missing Dependencies**: Ensure all required packages are in your requirements.txt
3. **Memory Issues**: Streamlit Cloud has a 1GB RAM limit - be mindful of large dataframes

## Updating Your App

Any new commits to your GitHub repository will automatically trigger a redeployment of your Streamlit app. 