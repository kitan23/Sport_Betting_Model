# Understanding the NBA Player Props Enhanced Statistics CSV

This guide explains each column in the enhanced stats CSV file and how you can use this information to make informed betting decisions.

## Column Explanations

1. **player**: The NBA player's name.

2. **prop_type**: The type of statistical category being bet on (points, rebounds, assists, blocks, steals, three-pointers made, etc.).

3. **fair_line**: The calculated "true" line value based on either:
   - The fair line provided by the API (if available)
   - The median line across all bookmakers (if no fair line is available)
   This represents what the over/under line should theoretically be without bookmaker margin.

4. **book_line**: The actual line offered by bookmakers for this prop.

5. **total_bookmakers**: The total number of bookmakers offering this prop bet.

6. **over_bookmakers**: The number of bookmakers specifically offering the "over" side of this prop. This may be different from the total number of bookmakers if some only offer one side of the bet.

7. **under_bookmakers**: The number of bookmakers specifically offering the "under" side of this prop. This may be different from the total number of bookmakers if some only offer one side of the bet.

8. **best_over_odds**: The best American odds available for the "over" bet across all bookmakers.

9. **best_over_bookmaker**: The bookmaker offering the best odds for the "over" bet.

10. **best_under_odds**: The best American odds available for the "under" bet across all bookmakers.

11. **best_under_bookmaker**: The bookmaker offering the best odds for the "under" bet.

12. **no_vig_over_odds**: The calculated American odds for the "over" bet after removing the bookmaker's margin (vig).

13. **no_vig_under_odds**: The calculated American odds for the "under" bet after removing the bookmaker's margin (vig).

14. **over_implied_prob**: The implied probability of the "over" bet based on the best available odds.
    - For example, +150 odds implies a 40% probability (1/2.5)
    - -150 odds implies a 60% probability (1.5/2.5)

15. **under_implied_prob**: The implied probability of the "under" bet based on the best available odds.

16. **no_vig_over_prob**: The true probability of the "over" bet after removing the bookmaker's margin.

17. **no_vig_under_prob**: The true probability of the "under" bet after removing the bookmaker's margin.

18. **game**: The matchup information (e.g., "Nets @ Hornets").

19. **home_team**: The home team for this game.

20. **away_team**: The away team for this game.

21. **event_id**: The unique identifier for this game.

22. **over_ev**: The Expected Value (EV) percentage for the "over" bet.
    - Calculated using the fair line as the reference point for true probability
    - Positive values indicate potentially profitable bets
    - Higher values indicate better betting opportunities
    - When the fair line is higher than the book line, the over bet tends to have positive EV

23. **under_ev**: The Expected Value (EV) percentage for the "under" bet.
    - Calculated using the fair line as the reference point for true probability
    - Positive values indicate potentially profitable bets
    - Higher values indicate better betting opportunities
    - When the fair line is lower than the book line, the under bet tends to have positive EV

## How to Use This Information for Betting Decisions

### 1. Focus on Expected Value (EV)

The most important columns for making betting decisions are **over_ev** and **under_ev**:

- **Positive EV**: Look for bets with positive EV (the higher, the better). These represent situations where the odds offered by bookmakers are more favorable than the true probability suggests.
  
- **EV Threshold**: Consider setting a minimum EV threshold (e.g., 5% or higher) to focus on the most valuable opportunities.

### 2. Compare Fair Line vs. Book Line

- If the **fair_line** is higher than the **book_line**, this suggests value on the "over" bet.
- If the **fair_line** is lower than the **book_line**, this suggests value on the "under" bet.

### 3. Bookmaker Coverage

- **total_bookmakers**: Higher numbers indicate more market consensus and potentially more reliable odds.
- Be cautious with props that have very few bookmakers offering them, as these markets might be less efficient.

### 4. Implied Probabilities vs. No-Vig Probabilities

- Compare **over_implied_prob** with **no_vig_over_prob** (and the same for under):
  - If the no-vig probability is higher than the implied probability, this suggests value.

### 5. Best Odds Shopping

- Always bet with the bookmaker offering the best odds (**best_over_bookmaker** or **best_under_bookmaker**).
- The difference between average odds and best odds can significantly impact your long-term profitability.

### 6. Practical Decision-Making Process

1. **Sort by EV**: Sort the CSV by either over_ev or under_ev in descending order to find the highest value bets.

2. **Apply Filters**:
   - Minimum EV threshold (e.g., >5%)
   - Minimum number of bookmakers (e.g., >3)
   - Specific prop types you're comfortable with

3. **Cross-Reference Information**:
   - Check if the player has any recent news (injuries, role changes)
   - Look at recent performance trends
   - Consider matchup factors

4. **Manage Your Bankroll**:
   - Bet sizes should be proportional to the edge (higher EV = larger bet, within reason)
   - Never bet more than 1-5% of your bankroll on a single prop
   - Track your bets to evaluate performance over time

### 7. Example Analysis

Let's analyze a hypothetical entry from your CSV:

```
Player: Josh Green
Prop Type: threePointersMade
Fair Line: 2.0
Book Line: 1.5
Best Over Odds: +136 (Fanduel)
Best Under Odds: -150 (Bet365)
No-Vig Over Odds: +142
No-Vig Under Odds: -142
Over EV: -2.32%
Under EV: -2.31%
```

Analysis:
- The fair line (2.0) is higher than the book line (1.5), suggesting potential value on the over.
- However, both over_ev and under_ev are negative, indicating neither bet offers positive expected value.
- This would not be a recommended bet despite the line discrepancy.

### 8. Red Flags to Watch For

- **Extremely High EV**: Be cautious of props showing extremely high EV (e.g., >50%). These could indicate:
  - Data quality issues in the source data
  - Large discrepancies between fair line and book line
  - Unusual market conditions or breaking news
  - Calculation artifacts due to the simplified probability adjustment model
  
  The system now caps EV values at 100% and warns about large line differences, but you should still manually verify any prop with EV > 50% before placing a bet.

- **Large Line Discrepancies**: If the fair line and book line are very different (>4 points), this could indicate:
  - Stale data from one or more sources
  - Recent injury news not yet reflected in all bookmaker lines
  - Errors in the fair line calculation or data entry
  - Different scoring systems or prop definitions
  
  The system now caps line differences at 4 points to prevent unrealistic probability adjustments, but you should investigate the cause of any large discrepancy.

- **Limited Bookmaker Coverage**: Props with only 1-2 bookmakers might have less reliable odds and could indicate a less efficient market. These markets may offer value but carry higher risk due to limited price discovery.

## Understanding the Math Behind the Columns

### American Odds to Decimal Odds Conversion

- For positive American odds (e.g., +150):
  - Decimal Odds = (American Odds / 100) + 1
  - Example: +150 → (150/100) + 1 = 2.5

- For negative American odds (e.g., -150):
  - Decimal Odds = (100 / |American Odds|) + 1
  - Example: -150 → (100/150) + 1 = 1.67

### Implied Probability Calculation

- Implied Probability = 1 / Decimal Odds
  - Example: Decimal Odds of 2.5 → 1/2.5 = 0.4 or 40%
  - Example: Decimal Odds of 1.67 → 1/1.67 = 0.6 or 60%

### No-Vig Probability Calculation

1. Calculate implied probabilities for both over and under
2. Sum the probabilities (this will be >100% due to the vig)
3. Normalize each probability by dividing by the sum

Example:
- Over implied probability: 0.55
- Under implied probability: 0.60
- Sum: 1.15 (represents a 15% vig)
- No-vig over probability: 0.55/1.15 = 0.478 or 47.8%
- No-vig under probability: 0.60/1.15 = 0.522 or 52.2%

### Expected Value (EV) Calculation

The EV calculation takes into account both the odds offered by the bookmaker and the true probability of the outcome:

EV = (Probability of Winning × Potential Profit) - (Probability of Losing × Stake)

For a $100 stake:
- EV% = ((True Probability × Potential Profit) - ((1 - True Probability) × 100)) / 100

The key to accurate EV calculation is determining the true probability. In our model:

1. We start with the no-vig probabilities derived from the market odds
2. We adjust these probabilities based on the difference between the fair line and the book line:
   - For over bets: If fair_line > book_line, we increase the true probability
   - For under bets: If fair_line < book_line, we increase the true probability
   - The adjustment is proportional to the difference between the lines (10% per point)
   - Line differences are capped at 4 points to prevent unrealistic adjustments
   - Final probabilities are clamped between 5% and 95% to avoid extreme values

Example:
- Book line: 22.5 points
- Fair line: 24.5 points
- No-vig over probability from market: 45%
- Line difference: +2.0 points
- Probability adjustment: +20% (10% per point)
- Adjusted true over probability: 65%
- With decimal odds of 2.0 (+100 American):
  - EV = (0.65 × $100) - (0.35 × $100) = $65 - $35 = $30
  - EV% = $30/$100 = 30%

This approach ensures that over and under EV values are properly complementary - when one side has positive EV, the other typically has negative EV. The system also caps extreme EV values at ±100% to prevent unrealistic expectations.

## Conclusion

This enhanced stats CSV provides a comprehensive framework for identifying value in NBA player props. By focusing on expected value, comparing fair lines to book lines, and shopping for the best odds, you can make more informed betting decisions.

Remember that successful sports betting is about finding value over the long term. No single bet is guaranteed to win, but consistently betting with positive expected value should lead to profitability over a large sample size.

## Additional Tips for Long-Term Success

1. **Keep Records**: Track all your bets, including the closing lines. If you're consistently beating the closing line, you're likely making +EV bets.

2. **Specialize**: Focus on specific teams, players, or prop types that you understand well.

3. **Be Disciplined**: Stick to your bankroll management strategy and don't chase losses.

4. **Stay Informed**: Player injuries, lineup changes, and coaching decisions can significantly impact prop performance.

5. **Consider Correlations**: Some props may be correlated (e.g., points and minutes played). This can inform your betting strategy.

6. **Timing Matters**: Lines often move as game time approaches. Understanding when to bet is as important as what to bet on.

7. **Avoid Parlays**: While tempting, parlay bets typically have higher vig and lower expected value than individual bets.

8. **Emotional Control**: Don't let recent wins or losses affect your decision-making process. Stick to the numbers and the value.