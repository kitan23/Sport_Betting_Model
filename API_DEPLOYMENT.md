# API Deployment Guide

This document provides instructions for deploying the Sports Betting Model API with proper environment variable configuration.

## Environment Variables

The application requires the following environment variables:

| Variable | Description | Required |
| --- | --- | --- |
| `SPORTSGAMEODDS_API_KEY` | API key for Sports Game Odds API | Yes |
| `SPORTSGAMEODDS_BASE_URL` | Base URL for the API (default: https://api.sportsgameodds.com/v2) | No |
| `CSV_STORAGE_PATH` | Path for storing CSV files (default: ./data) | No |

## Deploying on Render

1. Create an account on [Render](https://render.com) if you don't have one
2. Connect your GitHub repository to Render
3. Create a new Web Service pointing to your repository
4. During setup, Render will use the `render.yaml` configuration
5. For the `SPORTSGAMEODDS_API_KEY` variable, you'll be prompted to enter the value during deployment
6. Click "Create Web Service" to start the deployment

## Using environment variables locally

For local development:

1. Create a `.env` file in the root directory with the following content:
```
SPORTSGAMEODDS_API_KEY=your_actual_api_key
SPORTSGAMEODDS_BASE_URL=https://api.sportsgameodds.com/v2
CSV_STORAGE_PATH=./data
```

2. Install the python-dotenv package:
```
pip install python-dotenv
```

3. Make sure to not commit the `.env` file to your repository

## Considerations for file storage

The free tier of Render has an ephemeral filesystem, which means:

1. Any files created will be lost when the service restarts
2. Consider using a persistent database or storage service for long-term data storage

If you need persistent file storage:

1. Create a directory in your repo for data (e.g., `data/`)
2. Make sure your app reads/writes CSV files to the path from `CSV_STORAGE_PATH` environment variable
3. For a production environment, consider using Amazon S3, Google Cloud Storage, or a database 