import io
import xml.etree.ElementTree as ET
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from dateutil import tz

LOCAL_TZ = tz.gettz("America/New_York")


@st.cache_data
def parse_apple_export(xml_bytes: bytes) -> pd.DataFrame:
    """Parse Apple Health export.xml and extract body mass (weight) data."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        st.error(f"Error parsing XML: {e}")
        return pd.DataFrame()

    # Find all Record elements with type="HKQuantityTypeIdentifierBodyMass"
    records = []
    for record in root.findall('.//Record[@type="HKQuantityTypeIdentifierBodyMass"]'):
        records.append({
            'timestamp': record.get('startDate'),
            'value': float(record.get('value', 0)),
            'unit': record.get('unit', 'kg'),
            'source_name': record.get('sourceName', 'Unknown')
        })

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Convert timestamp to datetime and localize
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.tz_convert(LOCAL_TZ)
    df['date'] = df['timestamp'].dt.date
    df['time'] = df['timestamp'].dt.time
    df['year'] = df['timestamp'].dt.year
    df['month'] = df['timestamp'].dt.to_period('M').astype(str)
    df['week'] = df['timestamp'].dt.to_period('W').astype(str)
    df['weekday'] = df['timestamp'].dt.day_name()
    df['hour'] = df['timestamp'].dt.hour

    # Time-of-day bucket
    def bucket_hour(h):
        if 5 <= h < 11:
            return "Morning (5-11)"
        if 11 <= h < 17:
            return "Afternoon (11-17)"
        if 17 <= h < 22:
            return "Evening (17-22)"
        return "Night (22-5)"

    df['time_of_day'] = df['hour'].apply(bucket_hour)

    return df


@st.cache_data
def daily_latest_weight(df: pd.DataFrame) -> pd.DataFrame:
    """Get latest weight per day with rolling averages."""
    tmp = df.sort_values('timestamp').groupby('date').tail(1)
    tmp = tmp.sort_values('timestamp').reset_index(drop=True)
    tmp['delta_prev_day'] = tmp['value'].diff()
    tmp['rolling_7d'] = tmp['value'].rolling(7, min_periods=1).mean()
    return tmp


def main():
    st.set_page_config(
        page_title="Apple Weight Tracker",
        layout="wide",
    )

    st.title("🍎 Apple Health Weight Tracker")
    st.caption("Upload your Apple Health export.xml and analyze weight over time.")

    st.sidebar.header("📂 Upload Apple Health export")
    uploaded_file = st.sidebar.file_uploader(
        "export.xml from the Health app",
        type=["xml"],
        help="In the iOS Health app: Profile → Export All Health Data.",
    )

    if uploaded_file is None:
        st.info("📱 Upload your Apple Health `export.xml` to begin.")
        st.markdown("""
        ### How to export from Apple Health:
        1. Open the Health app on your iPhone
        2. Tap your profile picture (top right)
        3. Scroll down and tap **Export All Health Data**
        4. Wait for the export to complete
        5. Share/save the `export.zip` file
        6. Unzip it and upload the `export.xml` file here
        """)
        st.stop()

    with st.spinner("Parsing Apple Health export..."):
        df = parse_apple_export(uploaded_file.read())

    if df.empty:
        st.error("❌ No weight (body mass) data found in this export.")
        st.stop()

    st.success(f"✅ Loaded {len(df)} weight records from Apple Health.")

    # Sidebar filters
    min_date = df['date'].min()
    max_date = df['date'].max()
    date_range = st.sidebar.date_input(
        "📅 Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = min_date
        end_date = max_date

    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    df_filtered = df.loc[mask].copy()

    unit = df_filtered['unit'].mode().iat[0] if not df_filtered['unit'].empty else "kg"
    st.sidebar.markdown(f"**Unit:** {unit}")

    # Main layout
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🕐 Time of Day", "📊 Weekly/Monthly", "📋 Raw Data"])

    # === Overview tab ===
    with tab1:
        st.subheader("Daily weight trend")

        daily_df = daily_latest_weight(df_filtered)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Start weight", f"{daily_df['value'].iloc[0]:.1f} {unit}")
        with col2:
            st.metric("Current weight", f"{daily_df['value'].iloc[-1]:.1f} {unit}")
        with col3:
            delta_total = daily_df['value'].iloc[-1] - daily_df['value'].iloc[0]
            st.metric("Change over period", f"{delta_total:+.1f} {unit}")

        fig = px.line(
            daily_df,
            x='timestamp',
            y='value',
            title="Daily latest weight",
            labels={'timestamp': 'Date', 'value': f'Weight ({unit})'},
        )
        fig.add_scatter(
            x=daily_df['timestamp'],
            y=daily_df['rolling_7d'],
            mode='lines',
            name='7-day rolling avg',
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Daily table")
        display_df = daily_df[['timestamp', 'value', 'delta_prev_day', 'rolling_7d']].copy()
        display_df.columns = ['Date', f'Weight ({unit})', 'Daily Change', '7-Day Avg']
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # === Time-of-day tab ===
    with tab2:
        st.subheader("Time-of-day patterns")

        # Box plot by time of day bucket
        fig_tod = px.box(
            df_filtered,
            x='time_of_day',
            y='value',
            category_orders={
                'time_of_day': ["Morning (5-11)", "Afternoon (11-17)", "Evening (17-22)", "Night (22-5)"]
            },
            title="Weight distribution by time of day",
            labels={'time_of_day': 'Time of day', 'value': f'Weight ({unit})'},
        )
        st.plotly_chart(fig_tod, use_container_width=True)

        # Weekday vs weekend averages
        df_filtered['is_weekend'] = df_filtered['weekday'].isin(["Saturday", "Sunday"])
        agg = (
            df_filtered.groupby(['is_weekend', 'time_of_day'])['value']
            .mean()
            .reset_index()
        )
        agg['day_type'] = agg['is_weekend'].map({True: 'Weekend', False: 'Weekday'})

        fig_wd = px.bar(
            agg,
            x='time_of_day',
            y='value',
            color='day_type',
            barmode='group',
            title="Average weight: weekday vs weekend by time of day",
            labels={'time_of_day': 'Time of day', 'value': f'Weight ({unit})', 'day_type': 'Day type'},
        )
        st.plotly_chart(fig_wd, use_container_width=True)

    # === Weekly/Monthly tab ===
    with tab3:
        st.subheader("Weekly summary")
        weekly = df_filtered.groupby('week')['value'].agg(['mean', 'min', 'max', 'count']).reset_index()
        weekly.columns = ['Week', f'Avg Weight ({unit})', 'Min', 'Max', 'Measurements']
        st.dataframe(weekly, use_container_width=True, hide_index=True)

        st.subheader("Monthly summary")
        monthly = df_filtered.groupby('month')['value'].agg(['mean', 'min', 'max', 'count']).reset_index()
        monthly.columns = ['Month', f'Avg Weight ({unit})', 'Min', 'Max', 'Measurements']
        st.dataframe(monthly, use_container_width=True, hide_index=True)

    # === Raw data tab ===
    with tab4:
        st.subheader("Raw weight records")
        raw_df = df_filtered[
            ['timestamp', 'value', 'unit', 'source_name', 'weekday', 'time_of_day']
        ].sort_values('timestamp', ascending=False)
        raw_df.columns = ['Timestamp', 'Weight', 'Unit', 'Source', 'Weekday', 'Time of Day']
        st.dataframe(raw_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
