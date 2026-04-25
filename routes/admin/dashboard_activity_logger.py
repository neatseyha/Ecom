"""
Admin Activity Logger & Dashboard Integration
Track admin actions and integrate all dashboard features
"""

from flask import current_app, session
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

# ============ ACTIVITY LOG MODEL ============
def init_activity_log_model(db):
    """Create Admin Activity Log model"""
    
    class AdminActivityLog(db.Model):
        __tablename__ = 'admin_activity_log'
        
        id = Column(Integer, primary_key=True)
        admin_id = Column(Integer, nullable=False)
        action = Column(String(100), nullable=False)  # create, update, delete, login, logout
        entity_type = Column(String(50), nullable=False)  # product, order, user, coupon, etc
        entity_id = Column(Integer, nullable=True)
        description = Column(Text, nullable=True)
        details = Column(Text, nullable=True)  # JSON serialized details
        ip_address = Column(String(45), nullable=True)
        timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
        
        def __repr__(self):
            return f'<AdminActivityLog {self.action} on {self.entity_type}>'
    
    return AdminActivityLog

# ============ LOGGING FUNCTIONS ============
def log_admin_activity(admin_id, action, entity_type, entity_id=None, description=None, details=None, ip_address=None):
    """Log an admin activity"""
    try:
        from flask import request
        db = current_app.extensions['sqlalchemy']
        
        # Get the ActivityLog model
        activity_log = None
        for model in db.Model.registry.mappers:
            if hasattr(model.class_, '__tablename__') and model.class_.__tablename__ == 'admin_activity_log':
                activity_log = model.class_
                break
        
        if not activity_log:
            # Create the model if it doesn't exist
            ActivityLog = init_activity_log_model(db)
        else:
            ActivityLog = activity_log
        
        # Get IP address
        if not ip_address:
            ip_address = request.remote_addr if request else None
        
        # Create log entry
        log = ActivityLog(
            admin_id=admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            details=details,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(log)
        db.session.commit()
        
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        return False

# ============ GET ACTIVITY LOGS ============
def get_admin_activity_logs(limit=50, entity_type=None):
    """Get admin activity logs"""
    try:
        db = current_app.extensions['sqlalchemy']
        
        # Find the ActivityLog model
        ActivityLog = None
        for model in db.Model.registry.mappers:
            if hasattr(model.class_, '__tablename__') and model.class_.__tablename__ == 'admin_activity_log':
                ActivityLog = model.class_
                break
        
        if not ActivityLog:
            return []
        
        query = db.session.query(ActivityLog)
        
        if entity_type:
            query = query.filter_by(entity_type=entity_type)
        
        logs = query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
        
        return [{
            'id': log.id,
            'admin_id': log.admin_id,
            'action': log.action,
            'entity_type': log.entity_type,
            'entity_id': log.entity_id,
            'description': log.description,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else None,
            'ip_address': log.ip_address
        } for log in logs]
    except Exception as e:
        print(f"Error getting activity logs: {e}")
        return []

# ============ ACTIVITY STATISTICS ============
def get_activity_statistics(days=30):
    """Get admin activity statistics"""
    try:
        from datetime import timedelta
        db = current_app.extensions['sqlalchemy']
        
        # Find the ActivityLog model
        ActivityLog = None
        for model in db.Model.registry.mappers:
            if hasattr(model.class_, '__tablename__') and model.class_.__tablename__ == 'admin_activity_log':
                ActivityLog = model.class_
                break
        
        if not ActivityLog:
            return {}
        
        from sqlalchemy import func
        
        date_from = datetime.utcnow() - timedelta(days=days)
        
        # Activity count by action
        by_action = db.session.query(
            ActivityLog.action,
            func.count(ActivityLog.id).label('count')
        ).filter(ActivityLog.timestamp >= date_from).group_by(ActivityLog.action).all()
        
        # Activity count by entity type
        by_entity = db.session.query(
            ActivityLog.entity_type,
            func.count(ActivityLog.id).label('count')
        ).filter(ActivityLog.timestamp >= date_from).group_by(ActivityLog.entity_type).all()
        
        # Most active admins
        by_admin = db.session.query(
            ActivityLog.admin_id,
            func.count(ActivityLog.id).label('count')
        ).filter(ActivityLog.timestamp >= date_from).group_by(ActivityLog.admin_id).order_by(
            func.count(ActivityLog.id).desc()
        ).limit(5).all()
        
        return {
            'by_action': {a.action: a.count for a in by_action},
            'by_entity': {e.entity_type: e.count for e in by_entity},
            'top_admins': [{'admin_id': a.admin_id, 'activity_count': a.count} for a in by_admin]
        }
    except Exception as e:
        print(f"Error getting activity statistics: {e}")
        return {}
