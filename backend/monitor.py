import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "monitoring", "logs.db")

st.set_page_config(page_title="GDPR RAG Monitor", layout="wide")

st.title("GDPR RAG Assistant - Monitoring Dashboard")
st.markdown("Phase 7: Monitor production queries and user feedback.")

def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM queries", conn)
    # Convert timestamp to datetime
    if not df.empty:
        df['created_at'] = pd.to_datetime(df['created_at'], unit='s')
    return df

df = load_data()

if df.empty:
    st.warning("No logs found yet. Ask some questions in the Next.js UI first!")
else:
    # 1. High Level Metrics
    total_queries = len(df)
    avg_latency = df['latency_ms'].mean()
    positive_feedback = len(df[df['feedback'] == 1])
    negative_feedback = len(df[df['feedback'] == -1])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Queries", total_queries)
    col2.metric("Avg Latency (ms)", f"{avg_latency:.0f}")
    col3.metric("👍 Thumbs Up", positive_feedback)
    col4.metric("👎 Thumbs Down", negative_feedback)
    

    st.markdown("---")
    
    st.subheader("System Performance & Analytics")
    
    # 5 Charts required by DataTalks.Club rubric
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Chart 1: Queries by Retrieval Mode
        mode_counts = df['retrieval_mode'].value_counts().reset_index()
        mode_counts.columns = ['Mode', 'Count']
        fig1 = px.bar(mode_counts, x='Mode', y='Count', title='Queries by Retrieval Mode', color='Mode')
        st.plotly_chart(fig1, use_container_width=True)
        
        # Chart 3: Latency Distribution
        fig3 = px.histogram(df, x='latency_ms', nbins=20, title='Latency Distribution (ms)', color_discrete_sequence=['#b08d57'])
        st.plotly_chart(fig3, use_container_width=True)

    with chart_col2:
        # Chart 2: User Feedback Pie Chart
        feedback_labels = df['feedback'].map({1: 'Positive (👍)', -1: 'Negative (👎)', None: 'No Feedback'}).fillna("No Feedback")
        feedback_counts = feedback_labels.value_counts().reset_index()
        feedback_counts.columns = ['Feedback', 'Count']
        fig2 = px.pie(feedback_counts, values='Count', names='Feedback', title='User Feedback Breakdown', hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Chart 4: Queries Over Time (Aggregated by Minute)
        time_df = df.copy()
        time_df['Time (Minute)'] = time_df['created_at'].dt.floor('Min')
        volume_df = time_df.groupby('Time (Minute)').size().reset_index(name='Queries')
        fig4 = px.line(volume_df, x='Time (Minute)', y='Queries', title='Query Volume Over Time', markers=True)
        st.plotly_chart(fig4, use_container_width=True)
        
    # Chart 5: Average Latency Over Time (Full width)
    lat_df = time_df.groupby('Time (Minute)')['latency_ms'].mean().reset_index()
    fig5 = px.line(lat_df, x='Time (Minute)', y='latency_ms', title='Average Latency Over Time (ms)', markers=True, color_discrete_sequence=['#c4645a'])
    st.plotly_chart(fig5, use_container_width=True)
    
    st.markdown("---")
    
    # 2. Query History Table
    st.subheader("Recent Queries")
    # Clean up the table for display
    display_df = df.copy()
    display_df = display_df.sort_values(by="created_at", ascending=False)
    display_df['Feedback'] = display_df['feedback'].map({1: '👍', -1: '👎', None: 'None'})
    
    st.dataframe(
        display_df[['created_at', 'question', 'retrieval_mode', 'latency_ms', 'Feedback']],
        use_container_width=True,
        hide_index=True
    )
    
    # 3. Deep Dive
    st.subheader("Explore Answers")
    selected_query_id = st.selectbox(
        "Select a question to see the LLM's answer:", 
        options=display_df['id'].tolist(),
        format_func=lambda x: display_df[display_df['id'] == x]['question'].values[0]
    )
    
    if selected_query_id:
        row = df[df['id'] == selected_query_id].iloc[0]
        st.markdown(f"**Answer:**")
        st.info(row['answer'])
        st.markdown(f"**Retrieved Articles:** `{row['retrieved_articles']}`")
