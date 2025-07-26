import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import json

class AnalyticsDashboard:
    def __init__(self, db):
        self.db = db
    
    def show_dashboard(self):
        """Display comprehensive analytics dashboard"""
        
        st.markdown("## 📊 Chatbot Analytics Dashboard")
        
        # Get analytics data
        analytics = self.db.get_analytics()
        
        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Conversations", 
                analytics['total_conversations'],
                delta=self._get_daily_change('conversations')
            )
        
        with col2:
            st.metric(
                "Unique Users", 
                self._get_unique_users(),
                delta=self._get_daily_change('users')
            )
        
        with col3:
            avg_session = self._get_avg_session_length()
            st.metric(
                "Avg Session Length", 
                f"{avg_session:.1f} questions",
                delta=self._get_session_change()
            )
        
        with col4:
            satisfaction = self._get_satisfaction_score()
            st.metric(
                "Satisfaction Score", 
                f"{satisfaction:.1f}%",
                delta=self._get_satisfaction_change()
            )
        
        # Charts Row 1
        col1, col2 = st.columns(2)
        
        with col1:
            # Intent Distribution
            if not analytics['intent_data'].empty:
                fig_intent = px.pie(
                    analytics['intent_data'], 
                    values='count', 
                    names='intent',
                    title="📈 Questions by Intent"
                )
                fig_intent.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_intent, use_container_width=True)
        
        with col2:
            # Language Distribution
            if not analytics['language_data'].empty:
                fig_lang = px.bar(
                    analytics['language_data'], 
                    x='language', 
                    y='count',
                    title="🌐 Usage by Language",
                    color='count',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig_lang, use_container_width=True)
        
        # Daily Activity Chart
        if not analytics['daily_data'].empty:
            fig_daily = px.line(
                analytics['daily_data'], 
                x='date', 
                y='count',
                title="📅 Daily Activity Trend",
                markers=True
            )
            fig_daily.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Questions"
            )
            st.plotly_chart(fig_daily, use_container_width=True)
        
        # Hourly Heatmap
        hourly_data = self._get_hourly_data()
        if not hourly_data.empty:
            fig_heatmap = px.density_heatmap(
                hourly_data, 
                x='hour', 
                y='day_of_week',
                z='count',
                title="🕐 Usage Heatmap (Hour vs Day)",
                labels={'hour': 'Hour of Day', 'day_of_week': 'Day of Week'}
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Recent Activity
        st.markdown("### 🕒 Recent Activity")
        recent_conversations = self.db.get_recent_conversations(limit=10)
        if not recent_conversations.empty:
            st.dataframe(
                recent_conversations[['timestamp', 'question', 'intent', 'language']],
                use_container_width=True
            )
        
        # Export Options
        st.markdown("### 📥 Export Data")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export Analytics"):
                self._export_analytics()
        
        with col2:
            if st.button("💬 Export Conversations"):
                self._export_conversations()
        
        with col3:
            if st.button("📧 Export Email Logs"):
                self._export_email_logs()
    
    def _get_daily_change(self, metric_type):
        """Calculate daily change for metrics"""
        # Implementation for daily change calculation
        return "+5"  # Placeholder
    
    def _export_analytics(self):
        """Export analytics data"""
        analytics = self.db.get_analytics()
        
        # Create comprehensive report
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_conversations': analytics['total_conversations'],
            'intent_distribution': analytics['intent_data'].to_dict('records'),
            'language_distribution': analytics['language_data'].to_dict('records'),
            'daily_activity': analytics['daily_data'].to_dict('records')
        }
        
        st.download_button(
            "📥 Download Analytics Report",
            json.dumps(report, indent=2),
            "analytics_report.json",
            "application/json"
        )