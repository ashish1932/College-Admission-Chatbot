import streamlit as st
from datetime import datetime, timedelta
import json

class NotificationSystem:
    def __init__(self):
        self.notifications = self._load_notifications()
    
    def _load_notifications(self):
        """Load notifications from JSON"""
        try:
            with open('notifications.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_notifications()
    
    def _create_default_notifications(self):
        """Create default notifications"""
        return [
            {
                "id": 1,
                "type": "urgent",
                "title": "🚨 Last Week for Applications",
                "message": "Only 7 days left to submit your application for the August batch!",
                "action_url": "#apply",
                "expires": (datetime.now() + timedelta(days=7)).isoformat(),
                "priority": "high"
            },
            {
                "id": 2,
                "type": "info",
                "title": "🎓 New Scholarship Program",
                "message": "Merit-based scholarships up to 75% now available. Apply before March 20th!",
                "action_url": "#scholarship",
                "expires": (datetime.now() + timedelta(days=30)).isoformat(),
                "priority": "medium"
            }
        ]
    
    def show_notifications(self):
        """Display active notifications"""
        active_notifications = self._get_active_notifications()
        
        if not active_notifications:
            return
        
        st.markdown("### 🔔 Important Updates")
        
        for notification in active_notifications:
            self._render_notification(notification)
    
    def _render_notification(self, notification):
        """Render individual notification"""
        
        # Determine styling based on type
        if notification['priority'] == 'high':
            alert_type = "error"
            icon = "🚨"
        elif notification['priority'] == 'medium':
            alert_type = "warning"
            icon = "⚠️"
        else:
            alert_type = "info"
            icon = "ℹ️"
        
        with st.container():
            st.markdown(f"""
            <div style="
                padding: 1rem;
                border-radius: 10px;
                margin: 0.5rem 0;
                background: {'#fee' if notification['priority'] == 'high' else '#fef7e0' if notification['priority'] == 'medium' else '#e7f3ff'};
                border-left: 4px solid {'#dc3545' if notification['priority'] == 'high' else '#ffc107' if notification['priority'] == 'medium' else '#0dcaf0'};
            ">
                <h4>{icon} {notification['title']}</h4>
                <p>{notification['message']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if notification.get('action_url'):
                if st.button(f"Learn More", key=f"notif_{notification['id']}"):
                    st.info("Redirecting to more information...")
    
    def _get_active_notifications(self):
        """Get currently active notifications"""
        now = datetime.now()
        active = []
        
        for notification in self.notifications:
            expires = datetime.fromisoformat(notification['expires'])
            if expires > now:
                active.append(notification)
        
        return sorted(active, key=lambda x: x['priority'] == 'high', reverse=True)