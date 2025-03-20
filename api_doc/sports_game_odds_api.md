Skip to content

SportsGameOdds API
Main Navigation
Website
Guides
Explorer
Reference

v2

Sidebar Navigation
Reference

Data Explorer

Basics
Introduction

Getting Started

Rate Limiting

Guides
Getting Data in Batches

Handling Odds

Fetching Teams

Improving Response Times

More Examples

Data Types
Markets

Bookmakers (bookmakerID)

Sports (sportID)

Leagues (leagueID)

Stats (statID)

Stat Entity (statEntityID)

Periods (periodID)

Bet Types & Sides (betTypeID & sideID)

Putting it Together (oddID)

Other Info
Consensus Odds

Upgrading to v2

FAQ

Get Help

Website

On this page
Requests & Responses
Getting Help
Features
Introduction
Welcome to the Sports Game Odds API! Our API provides real-time sports and betting data across dozens of sports and leagues. Whether you’re developing a sports app, a betting platform, or a model to beat the betting platforms, we have the data you need to succeed.

More info about the API can be found on our website.

Requests & Responses
The API includes a number of endpoints that allow you to access different types of data. Each endpoint has a specific URL and accepts different parameters. A full list of endpoints, including their request options, response formats, example responses, and code samples can be found in our API Reference.

Requests are made to the API via HTTPS URLs and responses are returned in JSON format. For more information on JSON, check out JSON.org or this MDN Web Docs Guide.

All requests must include your unique API key in the request headers. The header key should be x-api-key and the value should be your API key. You can obtain an API key by signing up for a plan here.

Getting Help
If at any time you have a question, need advice, want to request a new feature or data type, or anything else just reach out and we’ll get on it ASAP.

Features
55+ Leagues Across 25+ Sports
Pre-Match and Live Odds on spreads, over-unders, and moneylines
Player Props, Game Props, and Futures Odds
Sub-Minute Update Frequency for real-time data
Historical Data Availability
Scores & Stats Coupled with 100% of Odds
Results Data for All Odds Provided
Partial Game Odds (e.g., halves, quarters, periods, rounds, sets)
Live In-Game Odds for dynamic betting
Comprehensive Player, Team, League, and Tournament Data
Extensive Support for Major and Minor Sports
Detailed Documentation for easy integration
Free Support and Consulting for All Subscribers
Pager
Previous page
Data Explorer
Next page
Getting Started


Getting Started
1. Get an API Key
Head over to our pricing page and sign up for a free account here. You’ll receive an API key that will grant you access to the API.

After creating an account you will receive an email with your API key. You will then use this key to authenticate your requests to the API.

2. Make Your First Request
Now that you have your API key, you can start making requests to the Sports Game Odds API. You’ll want to add your API key into the ‘X-API-Key’ header for each request you make.

Manually - With a Browser Extension
You can use a browser extension like Postman Interceptor or Restlet Client to manually send requests to the API.

Install the extension.
Open the extension and create a new request.
Set the request type to GET.
Enter the API endpoint URL, e.g., https://api.sportsgameodds.com/v2/sports/.
Add a new header with the key X-API-Key and the value as your API key.
Send the request and view the response.
Manually - With an App Like Postman
Postman is a powerful tool for testing and interacting with APIs.

Download and install Postman.
Open Postman and create a new request.
Set the request type to GET.
Enter the API endpoint URL, e.g., https://api.sportsgameodds.com/v2/sports/.
Go to the Headers tab and add a new header with the key X-API-Key and the value as your API key.
Click Send to make the request and view the response.
Manually - From the Reference Docs
You can also make requests directly from our API Reference page. Each endpoint has an interactive section where you can input your API key and parameters to see the response.

With Code

Javascript

Python

Ruby

PHP

Java

// This example uses fetch() but you can use any HTTP library
const requestOptions = {
    method: 'GET',
    headers: { 'X-Api-Key': 'YOUR_API_KEY' }
};
const requestUrl = 'https://api.sportsgameodds.com/v2/sports/'; 
fetch(requestUrl, requestOptions) 
  .then(response => response.json()) 
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
Head over to our detailed API reference here to see all the available endpoints and parameters that the Sports Game Odds API has to offer.

API Reference

Pager
Previous page
Introduction
Next page
Rate Limiting



Rate Limiting
Based on the package you chose, your API key will be limited to a certain number of requests made and/or objects returned during a given time interval. If you exceed this limit, you will receive a 429 status code and will be unable to make further requests until the limit resets.

While we do make changes to our standard rate limits, these changes usually won’t affect existing subscribers, so unless you receive an email, your rate limit will remain the same as it was when you signed up. Therefore, the limits posted in this guide may be different from those your API key is subject to.

Request Limits
Each request you make to the Sports Game Odds API server will count towards your request rate limit.

Amateur plan: 10 requests per minute
Rookie plan: 60 requests per minute
Pro plan: 1,000 requests per minute
Object Limits
Each request you make to the Sports Game Odds API server may return multiple objects in the response. Each object returned will count towards your object rate limit over a given time interval. Each response counts as a minimum of 1 object.

Amateur plan: 1,000 objects per month
Rookie plan: 5M objects per month
Pro plan: Unlimited objects per month
Default Limits
In order to protect our servers and ensure maximum uptime, the following default limits apply to all API keys. In general you shouldn’t ever hit these limits regardless of your plan, but if you do, feel free to reach out to us and we can find a solution for removing or increasing these default limits

50k requests per hour
300k objects per hour
7M objects per day
Strategies to Avoid Rate Limiting
To protect your application from rate limiting, you can use the following strategies:

Avoid a high frequency of calls to endpoints serving data that doesn’t change frequently (e.g., Teams, Players, Stats).
Cache this data locally to avoid making unnecessary requests.
Make use of available query params at each endpoint to focus on only the data you need.
You can always fetch data about your current rate limit usage using the /account/usage endpoint.
Checking Your Rate Limit Usage
You can use the /account/usage endpoint to get information on your rate limits. This endpoint provides details about your current usage and remaining limits.

A sample API call to the endpoint is below:


fetch('https://api.sportsgameodds.com/v2/account/usage', {
  headers: {
    'X-Api-Key': 'YOUR_TOKEN'
  }
})
A sample response is below


{
    "success": true,
    "data": {
        "keyID": "abc123xyz456",
        "customerID": "cus_987xyz321abc",
        "isActive": true,
        "rateLimits": {
            "per-second": {
                "maxRequestsPerInterval": "unlimited",
                "maxEntitiesPerInterval": "unlimited",
                "currentIntervalRequests": "n/a",
                "currentIntervalEntities": "n/a",
                "currentIntervalEndTime": "n/a"
            },
            "per-minute": {
                "maxRequestsPerInterval": 1000,
                "maxEntitiesPerInterval": "unlimited",
                "currentIntervalRequests": 1,
                "currentIntervalEntities": "n/a",
                "currentIntervalEndTime": "2024-01-01T00:01:00.000Z"
            },
            "per-hour": {
                "maxRequestsPerInterval": "unlimited",
                "maxEntitiesPerInterval": "unlimited",
                "currentIntervalRequests": "n/a",
                "currentIntervalEntities": "n/a",
                "currentIntervalEndTime": "n/a"
            },
            "per-day": {
                "maxRequestsPerInterval": "unlimited",
                "maxEntitiesPerInterval": "unlimited",
                "currentIntervalRequests": "n/a",
                "currentIntervalEntities": "n/a",
                "currentIntervalEndTime": "n/a"
            },
            "per-month": {
                "maxRequestsPerInterval": "unlimited",
                "maxEntitiesPerInterval": 1000000,
                "currentIntervalRequests": "n/a",
                "currentIntervalEntities": 100,
                "currentIntervalEndTime": "2024-01-31T00:01:00.000Z"
            }
        }
    }
}
Pager
Previous page
Getting Started
Next page
Getting Data in Batches



Getting Data in Batches
This following information only applies to the /teams, /events, and /odds endpoints.

Most endpoints will always return all results which match your query. However, since the /teams, /events, and /odds endpoints can potentially return hundreds or even thousands of results, the resulting objects are paginated/limited and must be fetched in batches.

The number of items by each request to these endpoints is determined by the limit parameter. This parameter currently has a default value of 10 but can be overridden up to a max value of 100.

In some cases you may want to fetch all of the results from these endpoints. To do this, you can feed the nextCursor in the resonse as the cursor parameter in your next request to pick up where you left off. When the response does not contain a nextCursor property, you have reached the end of the results.

Let’s take the following example, where we want to grab all finalized NBA events:


Javascript

Python

Ruby

PHP

java

let nextCursor = null;
let eventData = [];
do {
  try {
    const response = await axios.get('/v2/events', {
      params: {
        leagueID: 'NBA',
        startsAfter: '2024-04-01',
        startsBefore: '2024-04-08',
        limit: 50,
        cursor: nextCursor
      }
    });

    // response.data will contain the 30 events for this request
    const data = response.data;

    eventData = eventData.concat(data.data);

    nextCursor = data?.nextCursor;

  } catch (error) {
    console.error('Error fetching events:', error);
    break;
  }
} while (nextCursor);

// Once you have this data, you could feed it to your betting model, display it in your sportsbook application, etc.
eventData.forEach((event) => {
  const odds = event.odds;
  Object.values(odds).forEach((oddObject) => {
    console.log(`Odd ID: ${oddObject.oddID}`);
    console.log(`Odd Value: ${oddObject.closeOdds}`);
  });
});
Pager
Previous page
Rate Limiting
Next page
Handling Odds


Handling Odds
Overview
The Sports Game Odds API comes complete with odds and result data for every event.

This guide will show you how you can easily fetch and parse the odds for a specific event or group of events!

Example
In our previous example you saw how you would fetch upcoming NBA events from the API using our cursor pattern, let’s take that a step further!

Now, assuming the NBA week has passed, we will fetch all finalized NBA events from that week, then parse the odds results for each event, so we can grade them.


let nextCursor = null;
let eventData = [];
do {
  try {
    const response = await axios.get('/v2/events', {
      params: {
        leagueID: 'NBA',
        startsAfter: '2024-04-01',
        startsBefore: '2024-04-08',
        finalized: true,
        cursor: nextCursor
      }
    });

    const data = response.data;

    eventData = eventData.concat(data.data);

    nextCursor = data?.nextCursor;

  } catch (error) {
    console.error('Error fetching events:', error);
    break;
  }
} while (nextCursor);

// Now that we have the events, let's parse the odd results!
// Based on the bet type, compare score to the odds and grade the odds, for this example assume the odds are over/under
eventData.forEach((event) => {
  const odds = event.odds;
  Object.values(odds).forEach((oddObject) => {
    const oddID = oddObject.oddID;
    const score = parseFloat(oddObject.score);

    const closeOverUnder = parseFloat(oddObject.closeOverUnder);
    if (score > closeOverUnder)
        console.log(`Odd ID: ${oddID} - Over Wins`);
    else if (score === closeOverUnder)
        console.log(`Odd ID: ${oddID} - Push`);
    else
        console.log(`Odd ID: ${oddID} - Under Wins`);
  });
});
Pager
Previous page
Getting Data in Batches
Next page
Fetching Teams


Fetching Teams
Overview
The Sports Game Odds API provides the ability to fetch a list of teams or a specific team’s details.

You can use a sportID or leagueID to get a list of associated teams and their details. You can also pass a teamID to just get a single team’s details. Note that when specifying a teamID, it will still return as an array, just with a single object in it.

Fetching by Team
Let’s take the following example, where we want to fetch the details of a specific NBA team:


Javascript

Python

Ruby

PHP

Java

await axios.get("/v2/teams", {
  params: {
    teamID: "LOS_ANGELES_LAKERS_NBA",
  },
});
This will return a response that looks something like this:


{
  "success": true,
  "data": [
    {
      "sportID": "BASKETBALL",
      "names": {
        "short": "LAL",
        "medium": "Lakers",
        "long": "Los Angeles Lakers"
      },
      "leagueID": "NBA",
      "teamID": "LOS_ANGELES_LAKERS_NBA"
    }
  ]
}
Fetching by league
If you wanted to fetch a list of all the teams in the NBA, your request would look something like this:


Javascript

Python

Ruby

PHP

Java

await axios.get("/v2/teams", {
  params: {
    leagueID: "NBA",
  },
});
This will return a response that looks something like this:


{
  "nextCursor": "MILWAUKEE_BUCKS_NBA",
  "success": true,
  "data": [
    {
      "sportID": "BASKETBALL",
      "names": {
        "short": "LAL",
        "medium": "Lakers",
        "long": "Los Angeles Lakers"
      },
      "leagueID": "NBA",
      "teamID": "LAKERS_NBA",
      "colors": {
        "secondary": "#FFFFFF",
        "primaryContrast": "#000000",
        "secondaryContrast": "#552583",
        "primary": "#552583"
      }
    },
    {
      "sportID": "BASKETBALL",
      "names": {
        "short": "BOS",
        "medium": "Celtics",
        "long": "Boston Celtics"
      },
      "leagueID": "NBA",
      "teamID": "CELTICS_NBA",
      "colors": {
        "secondary": "#FFFFFF",
        "primaryContrast": "#000000",
        "secondaryContrast": "#007A33",
        "primary": "#007A33"
      }
    },
    // ...
    // Up to 30 objects may be returned in this object. If there are more available
    // then you'll see a nextCursor property you can use to fetch the next
    // page of related objects.
  ]
}
Fetching by sport
If you wanted to fetch a list of all basketball teams across all of our supported leagues, your request would look something like this:


Javascript

Python

Ruby

PHP

Java

await axios.get("/v2/teams", {
  params: {
    sportID: "BASKETBALL",
  },
});
This will return a response that looks something like this:


{
  "nextCursor": "BELMONT_NCAAB",
  "success": true,
  "data": [
    {
      "sportID": "BASKETBALL",
      "names": {
        "short": "LAL",
        "medium": "Lakers",
        "long": "Los Angeles Lakers"
      },
      "leagueID": "NBA",
      "teamID": "LAKERS_NBA"
    },
    {
      "sportID": "BASKETBALL",
      "names": {
        "short": "BOS",
        "medium": "Celtics",
        "long": "Boston Celtics"
      },
      "leagueID": "NBA",
      "teamID": "CELTICS_NBA"
    },
    {
      "sportID": "BASKETBALL",
      "names": {
        "short": "GSW",
        "medium": "Warriors",
        "long": "Golden State Warriors"
      },
      "leagueID": "NBA",
      "teamID": "WARRIORS_NBA"
    },
    // ...
    // Up to 30 objects may be returned in this object. If there are more available
    // then you'll see a nextCursor property you can use to fetch the next
    // page of related objects.
  ]
}
Pager
Previous page
Handling Odds
Next page
Improving Response Times


Improving Response Speed
Note

We’re in the process of adding additional request params which are designed to allow you to more efficiently fetch only the data you need. We also plan on releasing a GraphQL API in the future. Check back here for updates.

We’re committed to finding balance between making as much data available to you as possible while also ensuring that you can fetch that data quickly and efficiently. This guide is designed to help you understand how to optimize your requests to reduce response times/latency.

Use the oddIDs parameter
The most common cause of high response times is fetching a large number of odds at once. This can be especially problematic when fetching odds for a large number of Events.
To reduce this, you can use the oddIDs parameter to fetch only the odds you need.
The oddIDs parameter can be included in the /events
It accepts a comma-separated list of oddID values (See the Markets guide for a list of supported oddID values)
You can also set the parameter includeOpposingOddIDs to true to also include the opposing side of all oddIDs provided
You can also replace the playerID portion of any oddID with PLAYER_ID to fetch that oddID across all players
Example
Consider the oddID batting_strikeouts-CODY_BELLINGER_1_MLB-game-ou-under which represents the under odds for Cody Bellinger’s strikeouts in a game
If you wanted to fetch all player strikeouts odds for this game you would set the following params
oddIDs=batting_strikeouts-PLAYER_ID-game-ou-under
includeOpposingOddIDs=true
That would give you both over and under odds for all player strikeouts odds markets for all Events/Odds returned
Pager
Previous page
Fetching Teams
Next page
More Examples

Leagues
Each bookmakerID corresponds to a sportbook, daily fantasy site, or betting platform. In cases where odds cannot be attributed to a single specific bookmaker, the bookmakerID will be unknown.

Below is a list of bookmakerIDs. More bookmakers (including ones not shown here) can be added upon request through a custom plan.

Name	bookmakerID
1xBet	1xbet
888 Sport	888sport
Bally Bet	ballybet
Barstool	barstool
Bet Victor	betvictor
Bet365	bet365
BetAnySports	betanysports
BetClic	betclic
Betfair Exchange	betfairexchange
Betfair Sportsbook	betfairsportsbook
Betfred	betfred
BetMGM	betmgm
BetOnline	betonline
BetPARX	betparx
Betr Sportsbook	betrsportsbook
BetRivers	betrivers
Betsafe	betsafe
Betsson	betsson
BetUS	betus
Betway	betway
BlueBet	bluebet
Bodog	bodog
Bookmaker.eu	bookmakereu
BoomBet	boombet
Bovada	bovada
BoyleSports	boylesports
Caesars	caesars
Casumo	casumo
Circa	circa
Coolbet	coolbet
Coral	coral
Draft Kings	draftkings
ESPN BET	espnbet
Everygame	everygame
Fanatics	fanatics
FanDuel	fanduel
Fliff	fliff
FourWinds	fourwinds
FOX Bet	foxbet
Grosvenor	grosvenor
GTbets	gtbets
Hard Rock Bet	hardrockbet
HotStreak	hotstreak
Ladbrokes	ladbrokes
LeoVegas	leovegas
LiveScore Bet	livescorebet
LowVig	lowvig
Marathon Bet	marathonbet
Matchbook	matchbook
Mr Green	mrgreen
MyBookie	mybookie
Neds	neds
NordicBet	nordicbet
NorthStar Bets	northstarbets
Paddy Power	paddypower
ParlayPlay	parlayplay
Pinnacle	pinnacle
PlayUp	playup
PointsBet	pointsbet
Prime Sports	primesports
PrizePicks	prizepicks
Prophet Exchange	prophetexchange
SI Sportsbook	si
Sky Bet	skybet
Sleeper	sleeper
SportsBet	sportsbet
SportsBetting.ag	sportsbetting_ag
Sporttrade	sporttrade
Stake	stake
Superbook	superbook
Suprabets	suprabets
TAB	tab
TABtouch	tabtouch
theScore Bet	thescorebet
Tipico	tipico
TopSport	topsport
Underdog	underdog
Unibet	unibet
Unknown	unknown
Virgin Bet	virginbet
William Hill	williamhill
Wind Creek (Betfred PA)	windcreek
WynnBet	wynnbet
Pager
Previous page
Markets