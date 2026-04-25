from datetime import datetime
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash


def init_user_model(db):
    """Initialize User model"""

    class User(db.Model):
        __tablename__ = 'user'

        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=True)
        password_hash = db.Column(db.String(200), nullable=False)
        first_name = db.Column(db.String(50), nullable=True)
        last_name = db.Column(db.String(50), nullable=True)
        phone = db.Column(db.String(20), nullable=True)
        profile_picture = db.Column(db.String(120), nullable=True)
        gender = db.Column(db.String(10), nullable=True)
        date_of_birth = db.Column(db.Date, nullable=True)
        bio = db.Column(db.String(500), nullable=True)
        address = db.Column(db.String(255), nullable=True)
        city = db.Column(db.String(50), nullable=True)
        state = db.Column(db.String(50), nullable=True)
        zip_code = db.Column(db.String(20), nullable=True)
        country = db.Column(db.String(50), nullable=True)
        role = db.Column(db.String(40), nullable=False, default='staff')
        is_active = db.Column(db.Boolean, nullable=False, default=True)
        email_verified = db.Column(db.Boolean, default=False)
        phone_verified = db.Column(db.Boolean, default=False)
        newsletter_subscribed = db.Column(db.Boolean, default=False)
        last_login = db.Column(db.DateTime, nullable=True)
        create_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
        updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
        deleted_at = db.Column(db.DateTime, nullable=True)

        def set_password(self, password):
            self.password_hash = generate_password_hash(password)

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)

        def __repr__(self):
            return f'<User {self.username}>'

    return User