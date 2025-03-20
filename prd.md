# Sports Betting Model - Product Requirements Document (PRD)

## 1. Overview

This PRD describes the objectives, requirements, and scope of a Sports Betting Model that leverages data from a sportsbook API. The system will acquire betting odds, clean and analyze the data, calculate implied probabilities and expected values (EV), and optionally utilize a predictive model to compare probabilities with bookmaker odds.

---

## 2. Goals and Objectives

1. **Data Acquisition**  
   - Connect to an external odds API (sportsbook aggregator) to retrieve real-time odds for various sports and markets.
   - Retrieve odds from multiple bookmakers to compare lines and identify the best odds.
   - Store and parse the retrieved data in a structured, machine-readable format.

2. **Odds Analysis**  
   - Convert various odds formats (decimal, American, fractional) into a uniform representation (e.g., decimal).
   - Calculate implied probability and expected value (EV) for each outcome.
   - Provide insights for each event (i.e., identify potentially +EV bets).

3. **Model Development (Optional)**  
   - Integrate a predictive model using historical data to estimate win probabilities.
   - Compare model-derived probabilities to bookmaker-implied probabilities to determine potential betting edges.

4. **Data Visualization & Reporting**  
   - Present data in user-friendly tables, charts, or dashboards for quick insight.
   - Allow users to filter events by date, sport, or bookmaker.

---

## 3. Scope

- **In-Scope**  
  1. Pulling live or near real-time odds from an API.  
  2. Converting raw odds data into a standardized format (e.g., decimal).  
  3. Computing implied probabilities and expected values.  
  4. Storing data in a local `DataFrame` or a simple database.  
  5. Optional: Integrating or building basic machine learning models (like logistic regression).

- **Out-of-Scope**  
  1. Automated bet placement or integration with real bookmaker accounts.  
  2. Advanced analytics beyond basic EV and/or model-based edge detection (unless added in later phases).  
  3. Guaranteeing profitability—this is a tool to *assist* in making decisions, not a guaranteed profit engine.

---

## 4. Functional Requirements

1. **Odds Retrieval**  
   - The system shall allow specifying the sport, region, and league (where applicable) to retrieve odds.
   - The system shall retrieve data in JSON format from the sportsbook API.
   - The system shall handle authentication using API keys or tokens.

2. **Data Parsing & Normalization**  
   - The system shall parse the JSON response and convert it into a tabular structure (pandas DataFrame).
   - The system shall label the odds by team/event/bookmaker.
   - The system shall handle missing or partial data gracefully (e.g., skip events that lack critical data).

3. **Odds Conversion**  
   - The system shall support decimal and American odds.  
   - The system shall convert any American odds into decimal for uniform calculations.

4. **Implied Probability Calculation**  
   - The system shall calculate implied probability from decimal or American odds for each outcome.

5. **Expected Value Calculation**  
   - The system shall calculate EV for each potential bet based on the implied probability and the user’s stake.

6. **Comparison & Reporting**  
   - The system shall allow users to compare odds across different bookmakers for the same event.
   - The system shall identify the best odds for each event.
   - The system shall produce a summary of events with key metrics (e.g., implied probabilities, EV) to help identify value bets.

7. **Optional: Predictive Modeling**  
   - The system shall ingest historical data (external to this PRD) for training models.
   - The system shall output predicted win probabilities for each event.
   - The system shall compare predicted probabilities to bookmaker-implied probabilities to flag potential edges.

---

## 5. Non-Functional Requirements

1. **Performance**  
   - Data retrieval should complete quickly for reasonable sets of events (e.g., < 1 second for a typical API call, subject to external API performance).

2. **Scalability**  
   - The solution should be easily extensible to multiple sports, leagues, and hundreds of events without major refactoring.

3. **Reliability**  
   - The system should handle temporary API outages or timeouts gracefully (e.g., retry logic).

4. **Maintainability**  
   - The solution code should be modular, allowing for easy updates to the data parsing, model code, or additional analysis modules.

5. **Security**  
   - The API key or any sensitive credentials must be stored securely (environment variables, config files outside version control, etc.).

---

## 6. Data Requirements

1. **Data Source**  
   - Primary: Sportsbook aggregator API (requires paid subscription or key).
   - Optional: Historical data from sports stats providers for training predictive models.

2. **Data Content**  
   - Event details (team names, league, match time).
   - Bookmaker details (name, region).
   - Odds (American, decimal, or both).
   - Historical outcomes (for model training if used).

3. **Data Storage**  
   - In-memory `DataFrame` usage via pandas.
   - Optionally, local or cloud-based database to store historical logs.

---

## 7. User Stories

1. **As a user, I want** to retrieve odds from multiple sportsbooks for today’s soccer matches **so that** I can compare lines and find the most favorable odds.
2. **As a user, I want** to convert odds into implied probabilities and calculate EV **so that** I can quickly determine which bets might be profitable.
3. **As an analyst, I want** to integrate my own predictive model’s probabilities **so that** I can compare them to the market and potentially spot value bets.
4. **As a user, I want** to view a summary report/table of events with odds from different books **so that** I can quickly see the best lines.

---

## 8. Workflow Outline

1. **Environment Setup**  
   - Create a virtual environment and install necessary Python libraries (`requests`, `pandas`, `numpy`, `matplotlib`).

2. **Data Acquisition**  
   - Pull live odds via API using `requests` and store the raw JSON.
   - Parse JSON into a `pandas.DataFrame`.

3. **Data Cleaning & Transformation**  
   - Filter only relevant columns (teams, commence time, bookmaker, odds).
   - Convert American odds to decimal if needed.
   - Handle missing data.

4. **Odds & EV Calculation**  
   - For each outcome, calculate implied probability.
   - Compute EV using the user’s defined stake (e.g., 1 unit).

5. **Optional: Predictive Model**  
   - Integrate logistic regression or another model.
   - Compare model probabilities with bookmaker-implied probabilities.

6. **Reporting**  
   - Generate tables or basic charts showing EV distributions or best available lines across bookmakers.
   - Provide a summary of potential +EV opportunities.

7. **Refinement & Monitoring**  
   - Evaluate actual results of wagers.
   - Adjust the model, data sources, or parameters to improve performance over time.

---

## 9. Milestones & Timeline

1. **Milestone 1: Data Retrieval & Parsing**  
   - Estimated completion: 1 week  
   - Deliverable: Basic Python notebook that calls the API and returns a pandas DataFrame.

2. **Milestone 2: Odds Conversion & Implied Probability**  
   - Estimated completion: 1 week after Milestone 1  
   - Deliverable: Functions for converting odds formats and computing implied probabilities.

3. **Milestone 3: EV Calculation & Comparison**  
   - Estimated completion: 1 week after Milestone 2  
   - Deliverable: Fully functioning Jupyter Notebook that computes EV and highlights best odds across books.

4. **Milestone 4 (Optional): Predictive Model Integration**  
   - Estimated completion: 2–4 weeks  
   - Deliverable: A trained model with performance metrics (e.g., AUC) and code to compare predicted vs. implied probabilities.

5. **Milestone 5: Documentation & Final Review**  
   - Estimated completion: 1 week after Milestone 4  
   - Deliverable: Final notebook, documentation, and potential instructions for future enhancements.

---

## 10. Risks and Dependencies

1. **API Availability/Cost**  
   - Risk: The selected API might be expensive or have rate limits.
   - Mitigation: Cache data, or use smaller queries if usage is high.

2. **Data Quality**  
   - Risk: Inconsistent or incomplete odds data from certain books.
   - Mitigation: Validate data, fallback to alternative sources.

3. **Model Accuracy**  
   - Risk: Predictive model may not accurately estimate win probabilities if trained on limited or poor-quality data.
   - Mitigation: Acquire high-quality historical data and refine feature engineering.

4. **Market Dynamics**  
   - Risk: Odds change frequently, so stale data may lead to poor decisions.
   - Mitigation: Schedule frequent updates and track line movements over time.

---

## 11. Acceptance Criteria

1. **Odds Data**: Must be accurately retrieved, cleaned, and displayed in a DataFrame for at least one sport (e.g., soccer) from multiple bookmakers.
2. **Implied Probability & EV**: Calculations must be correct according to standard formulas and displayed for each team/event.
3. **Comparison**: System must allow for easy comparison of different bookmakers’ odds.
4. **Documentation**: Clear instructions for setup, usage, and extension in a Jupyter Notebook format.

---

**End of PRD**  