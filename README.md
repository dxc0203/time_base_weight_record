# 🍎 Apple Health Weight Tracker

A Streamlit web app to analyze your Apple Health weight data with time-based insights.

## ✨ Features

- **Daily Trends**: View your weight over time with 7-day rolling averages
- **Time-of-Day Analysis**: See how your weight varies by morning, afternoon, evening, and night
- **Weekday vs Weekend**: Compare weight patterns between weekdays and weekends
- **Weekly & Monthly Summaries**: Aggregate statistics to track long-term progress
- **Interactive Charts**: Built with Plotly for rich, interactive visualizations
- **Date Filtering**: Focus on specific time periods
- **Auto Timezone**: Converts Apple Health UTC timestamps to US Eastern time

## 🚀 Quick Start

### 1. Export your Apple Health data

1. Open the **Health** app on your iPhone
2. Tap your **profile picture** (top right)
3. Scroll down and tap **Export All Health Data**
4. Wait for the export to complete (may take a few minutes)
5. Share/save the `export.zip` file to your computer
6. **Unzip** the file to get `export.xml`

### 2. Run the app locally

```bash
git clone https://github.com/dxc0203/time_base_weight_record.git
cd time_base_weight_record
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL (usually `http://localhost:8501`) in your browser.

### 3. Upload and analyze

1. Click **Browse files** in the sidebar
2. Select your `export.xml` file
3. Wait for parsing (large files may take 10-30 seconds)
4. Explore the tabs:
   - **📈 Overview**: Daily weight trend and rolling averages
   - **🕐 Time of Day**: Weight patterns by time buckets
   - **📊 Weekly/Monthly**: Aggregate summaries
   - **📋 Raw Data**: All records with timestamps and sources

## 📊 What You'll See

### Overview Tab
- Start weight, current weight, and total change metrics
- Interactive line chart of daily weight with 7-day rolling average
- Daily table showing weight, daily change, and rolling average

### Time of Day Tab
- Box plot showing weight distribution across time periods
- Weekday vs weekend comparison by time of day

### Weekly/Monthly Tab
- Weekly summary: average, min, max, measurement count
- Monthly summary: same stats aggregated by month

### Raw Data Tab
- Every weight measurement with timestamp, source (iPhone, Apple Watch, scale), weekday, and time bucket

## 🛠 Tech Stack

- **Python 3.8+**
- **Streamlit** – web framework
- **Pandas** – data processing
- **Plotly** – interactive charts
- **lxml** – XML parsing
- **python-dateutil** – timezone handling

## 🔒 Privacy

- **100% local**: Your health data never leaves your computer
- No data is uploaded to any server
- All processing happens in your browser session
- Cache is cleared when you close the browser

## 📝 Notes

- The app uses **US Eastern timezone** by default. Edit `LOCAL_TZ` in `app.py` to change.
- If you have multiple weight entries per day, the app uses the **latest** measurement for daily trends.
- Weight unit (kg or lb) is auto-detected from your Apple Health export.

## 🤝 Contributing

Pull requests welcome! Ideas for future features:
- Goal tracking with alerts
- Correlation with steps, calories, sleep data
- Export charts as PDF/PNG
- Multi-user support

## 📜 License

MIT License – feel free to use and modify.

---

Built with ❤️ using Streamlit
