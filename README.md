# 🏀 NBA Daily Scoreboard & Win Probability Analyzer

An interactive NBA dashboard that combines live game data, team analytics, injury reports, and AI-style “what-if” scenario analysis into a beginner-friendly basketball analytics platform.

Built with Streamlit and powered by live APIs, the app allows users to track NBA games in real time, compare team performance, and simulate hypothetical game situations to better understand how different factors influence win probability. 

---

## 🚀 Project Overview

Most sports scoreboards only show scores and schedules. This project goes further by turning NBA data into an interactive analytics experience.

The NBA Daily Scoreboard:

Displays live and scheduled NBA games.
- Calculates pre-game and live win probabilities.
- Factors in team performance and injuries.
- Lets users test hypothetical scenarios like:
- “What if the home team scores 8 more points?”
- “What if Giannis is ruled out?”
- Presents team statistics in a clean visual dashboard.

Goal: Make basketball analytics accessible, interactive, and easy to understand for casual fans and beginners.

---

## 🛠️ Core Features  

### 📅 Daily NBA Scoreboard
- Fetches NBA games for a selected date using the BallDontLie API.
- Displays:
  - Home & away teams
  - Team logos
  - Live scores
  - Game status (Final, Halftime, Quarter, Not Started)
- Optional auto-refresh every 30 seconds for live tracking.

### 📊 Win Probability Engine
- Generates:
  - Pre-game win probabilities
  - Live in-game win probabilities
- Uses:
  - Team season performance
  - Win/loss records
  - Points per game
  - Home-court advantage
  - Live score margin
- Displays probabilities visually with dynamic progress bars.

### 🏥 Injury Impact Analysis
- Pulls live injury data from FantasyNerds API.
- Automatically adjusts team strength ratings based on:
  - Out
  - Doubtful
  - Questionable
  - Day-to-day statuses
- Shows which injuries were factored into calculations. 

### 🧠 What-If Scenario Simulator

Users can simulate custom scenarios using natural language input.

Examples:

- “Home team +5 points”
- “Away scores 8 points”
- “Steph Curry is out”

The system:

- Parses the text input
- Adjusts score or team ratings
- Recalculates win probabilities instantly
- Explains what changes were applied

### 📈 Team Analytics Dashboard

Displays season averages using NBA.com statistics via nba_api:

- Points per game
- Rebounds per game
- Assists per game
- 2PT shooting percentage
- 3PT shooting percentage
- Win/loss records
- Games played

Each team is shown in visually styled stat cards with logos and summaries.

### 🔄 Live Updating Interface
- Built with Streamlit for a fast interactive dashboard.
- Supports:
  - Sidebar controls
  - Date selection
  - Auto-refresh
  - Responsive layouts
  - Dynamic game detail pages 

---

## ⚙️ Tech Stack  

Frontend
- Streamlit
- Plotly
- Custom HTML/CSS styling
  
Backend
- Python
- Pandas
- Requests
  
APIs & Data Sources
- BallDontLie API (live games/scores)
- NBA API / NBA.com stats
- FantasyNerds API (injuries)
  
Analytics
- Custom logistic win probability model
- Scenario simulation engine
- Injury-adjusted team rating system  

---

## 📅 Project Roadmap  

Phase 1
- Connect NBA game data APIs
- Build scoreboard UI
- Add team logos and live score updates
  
Phase 2
- Implement season analytics dashboard
- Add win probability calculations
- Build game detail pages
  
Phase 3
- Add injury integration and rating adjustments
- Develop what-if scenario parser
  
Phase 4
- Improve probability modeling
- Add probability history charts and visual analytics
  
Phase 5
- Advanced simulations
- Player-level statistical impacts
- Deployment and production optimization

---

## 📌 Disclaimer  
This project is for educational and analytical purposes only.
Win probabilities and simulations are estimates based on statistical models and do not guarantee actual game outcomes.  
