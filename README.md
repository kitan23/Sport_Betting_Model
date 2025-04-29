# Sports Betting Model

A professional web application for analyzing sports betting odds and identifying value plays across different bookmakers.

## Overview

This application identifies betting opportunities by comparing odds across multiple bookmakers to find positive expected value (EV) propositions. The system focuses on NBA player props, analyzing line differences and odds discrepancies to highlight potential value plays.

## Features

- **Real-time Data**: Fetches upcoming NBA games and player props for the next 24 hours
- **Multi-bookmaker Analysis**: Compares odds across FanDuel, DraftKings, Fanatics, and other major sportsbooks
- **Value Play Detection**: Calculates edge percentages and EV to identify profitable betting opportunities
- **Intuitive Interface**: Clean, responsive web UI for effortless navigation and analysis
- **Export Functionality**: Download value plays as CSV for further analysis

## Technology Stack

### Backend
- **FastAPI**: High-performance API framework for the backend
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing for statistical analysis
- **Sports Game Odds API**: Real-time sports and betting data across major leagues

### Frontend
- **Streamlit**: Interactive web application framework
- **Requests**: HTTP library for API communication
- **Pandas**: Data manipulation and visualization

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sport-betting-model.git
   cd sport-betting-model
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the backend:
   ```bash
   python app.py
   ```

4. Run the frontend in a new terminal:
   ```bash
   streamlit run streamlit_app.py
   ```

## Usage

1. Select a bookmaker from the dropdown menu
2. Set your minimum edge threshold using the slider
3. Click "Get Props" to analyze current betting opportunities
4. Review value plays sorted by expected value (EV)
5. Download results as CSV if desired

## API Integration

This project uses the Sports Game Odds API for data sourcing:

> "Welcome to the Sports Game Odds API! Our API provides real-time sports and betting data across dozens of sports and leagues. Whether you're developing a sports app, a betting platform, or a model to beat the betting platforms, we have the data you need to succeed."

More information about the API can be found on their website.

## Future Enhancements

- Support for additional sports leagues
- Custom date range selection
- Enhanced statistical analysis
- User authentication and personalized tracking

## License

MIT

---

*Note: This application is designed for educational and research purposes. Please use responsibly and in accordance with all applicable laws regarding sports betting in your jurisdiction.*

## Deployment Instructions

### Deploying the FastAPI Backend

Before deploying the Streamlit frontend, you need to deploy the FastAPI backend:

1. Deploy the FastAPI app (app.py) to a platform like Heroku, Railway, Render, or similar service
2. Make sure all dependencies are included in the requirements.txt for the backend
3. Note the URL where your API is deployed (e.g., `https://your-sports-betting-api.herokuapp.com`)

### Deploying to Streamlit Cloud

1. Push your code to a GitHub repository
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Click "New app"
4. Connect to your GitHub repository
5. For the main file path, enter: `streamlit_app.py`
6. Under "Advanced settings", add the following secrets:
   - `API_URL`: Your deployed FastAPI URL (e.g., `https://your-sports-betting-api.herokuapp.com`)
7. Click "Deploy"

### Local Development

To run the app locally:

1. Start the FastAPI backend:
   ```
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

2. Set `LOCAL_DEV_MODE = True` in streamlit_app.py

3. Run the Streamlit app:
   ```
   streamlit run streamlit_app.py
   ```

## Important Notes

- This app uses Streamlit's session state for data persistence in cloud environments
- The API URL must be properly configured for the app to function
- Refresh rate limits are in place to prevent excessive API calls 