# NBA Player Props Guide

## Understanding the Best Props Today CSV Columns

This guide explains each column in the `best_props_today.csv` file to help you make informed betting decisions.

| Column | Description |
|--------|-------------|
| **player** | The NBA player's name |
| **prop_type** | The statistical category being bet on (points, rebounds, assists, or combinations) |
| **fair_line** | The line value our model thinks is accurate based on calculations |
| **book_line** | The line value offered by sportsbooks |
| **bet_type** | Whether to bet OVER or UNDER the line |
| **ev** | Expected Value - the percentage profit you can expect over time (higher is better) |
| **edge** | The difference between our model's probability and the implied probability from the odds (positive means value) |
| **score** | A combined rating that factors in both EV and edge (higher is better) |
| **implied_prob** | The probability of winning according to the sportsbook odds |
| **true_prob** | The probability of winning according to our model |
| **american_odds** | The odds in American format (e.g., -110 means bet $110 to win $100) |
| **bookmaker** | Which sportsbook offers these odds (showing the median bookmaker) |
| **total_bookmakers** | How many sportsbooks offer this prop bet |
| **game** | The matchup the player is participating in |

## Example Interpretation

For example, if you see a row like this:
```
Kelel Ware,assists,1.5,0.5,OVER,33.65%,6.90%,35.97,50.20%,57.10%,-101,median(fanatics),8,Hornets @ Heat
```

This means:
- **Player & Prop**: Kelel Ware's assists
- **Lines**: Our model thinks the fair line is 1.5, but bookmakers set it at 0.5
- **Recommendation**: Bet OVER with 33.65% expected value
- **Edge**: Our model gives a 6.90% edge over the bookmaker
- **Probabilities**: Bookmaker implies 50.20% chance, but our model calculates 57.10%
- **Odds**: -101 (bet $101 to win $100)
- **Availability**: Available at 8 bookmakers for the Hornets @ Heat game

## How to Use This Information

1. **Focus on high EV bets**: The higher the EV percentage, the better the long-term value
2. **Look for positive edge**: A positive edge means our model thinks the bet is more likely to win than the odds suggest
3. **Consider the score**: Higher scores represent the best combination of EV and edge
4. **Check multiple bookmakers**: The total_bookmakers column shows how widely available the prop is

The props in the CSV file are sorted by the "score" column, with the best betting opportunities at the top.

## Understanding American Odds

- **Negative odds** (e.g., -110): The amount you need to bet to win $100
- **Positive odds** (e.g., +150): The amount you win if you bet $100

## Why Most Value Bets Have Negative Odds

Our model typically finds more value in "favorite" bets (negative odds) where the true probability is even higher than what the odds suggest. While positive odds offer higher payouts, they often don't provide enough edge to generate high EV values in our analysis. 