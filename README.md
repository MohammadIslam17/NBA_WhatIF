# NBA What If Simulator

An **AI-powered trading mentor** that helps beginners learn safe stock trading practices.  
By combining real market data with **Large Language Models (LLMs)**, the system generates simple strategies, explains the reasoning behind them, and teaches users how to manage risk like a coach with “training wheels.”  

---

## 🚀 Project Overview  

Most trading platforms overwhelm beginners with jargon and complex charts. **Stock Trading Mentor** bridges that gap by:  
- Generating **plain-language trading strategies**.  
- Backtesting ideas on historical data to check if they actually work.  
- Explaining concepts with analogies, charts, and Q&A.  
- Teaching risk management and portfolio diversification.  

**Our goal**: Make stock trading a learning experience, not just a guessing game.  

---

## 🛠️ Core Features  

### 📑 Strategy Generator (LLM-Powered)  
- Takes stock data, user preferences, and sentiment signals.  
- Produces **clear entry/exit rules, stop-losses, and position sizing**.  
- Explains the reasoning in simple terms.  

### 📊 Simulation & Backtesting  
- Uses **historical data** (via yFinance, Alpaca, Polygon.io).  
- Runs strategies through engines like Backtrader/Zipline.  
- Outputs performance metrics (Win Rate, Sharpe Ratio, Max Drawdown).  
- Provides beginner-friendly explanations and equity charts.  

### 📰 Sentiment & News Integration  
- Analyzes news headlines, Reddit, and Twitter for bullish/bearish signals.  
- Converts raw sentiment into **plain English summaries** and trend charts.  

### 🎓 Beginner-Friendly Education  
- Plain-language lessons, glossary, and analogies.  
- Interactive Q&A with adjustable explanation depth (“Explain like I’m 12”).  
- Visual education: highlights, arrows, charts, flashcards.  

### 🛡️ Risk & Portfolio Guidance  
- Teaches stop-loss and take-profit rules.  
- Recommends diversification and safe position sizing.  
- Assigns risk scores (Green = safe, Red = high risk).  

### 🤖 Interactive Q&A  
- Users can ask: *“What does RSI mean?”*, *“Is Tesla a good buy this week?”*.  
- Context-aware answers with charts, analogies, and multiple levels of detail.  

### 🎮 Gamification / Practice Mode *(Future)*  
- Paper trading mode to practice strategies without risking real money.  
- Badges and achievements for mastering key trading lessons.  

---

## ⚙️ Tech Stack  

- **Frontend:** Web-based dashboard (charts, visualizations, user input).  
- **Backend:** Python (Pandas, Backtrader, Zipline).  
- **APIs:** yFinance, Polygon.io, Reddit API, Twitter API, News API.  
- **AI:** LLMs for strategy generation, FinBERT/VADER for sentiment analysis.  

---

## 📅 Project Roadmap  

**Phase 1:** Connect stock data, build initial LLM, basic dashboard.  
**Phase 2:** Add sentiment analysis, beginner education, and risk guidance.  
**Phase 3:** Implement backtesting engine and interactive charts.  
**Phase 4:** Paper trading mode, performance explanations.  
**Phase 5:** Final polish, testing, and deployment.  

---

## 👥 Team  

- Conor Long  
- Josh Wufsus  
- Mohammad Islam  

---

## 📌 Disclaimer  
This project is for **educational purposes only**. It is not financial advice. Users should consult a licensed professional before making real investment decisions.  
