from datetime import datetime, timezone

from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=True,
        index=True
    )

    phone_number = db.Column(
        db.String(30),
        unique=True,
        nullable=True,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    account_status = db.Column(
        db.String(30),
        nullable=False,
        default="pending_verification",
        index=True
    )

    # ==========================================
    # EMAIL VERIFICATION
    # ==========================================

    email_verified = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    email_otp_hash = db.Column(
        db.String(255),
        nullable=True
    )

    email_otp_expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    email_otp_attempts = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    email_otp_last_sent_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    # ==========================================
    # PHONE VERIFICATION
    # ==========================================

    phone_verified = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    phone_otp_hash = db.Column(
        db.String(255),
        nullable=True
    )

    phone_otp_expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    phone_otp_attempts = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    phone_otp_last_sent_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    # ==========================================
    # OLD EMAIL VERIFICATION FIELDS
    # ==========================================

    email_verification_token_hash = db.Column(
        db.String(255),
        nullable=True
    )

    email_verification_expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    # ==========================================
    # PASSWORD RESET
    # ==========================================

    password_reset_token_hash = db.Column(
        db.String(255),
        nullable=True
    )

    password_reset_expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    # ==========================================
    # LOGIN SECURITY
    # ==========================================

    failed_login_attempts = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    locked_until = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    last_login_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    # ==========================================
    # ACCOUNT TIMESTAMPS
    # ==========================================

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # ==========================================
    # ROLES
    # ==========================================

    roles = db.relationship(
        "Role",
        secondary="user_roles",
        backref=db.backref(
            "users",
            lazy=True
        )
    )

    # ==========================================
    # ROLE HELPERS
    # ==========================================

    def has_role(self, role_name):
        return any(
            role.name == role_name
            for role in self.roles
        )

    def has_permission(self, permission_name):
        return any(
            permission.name == permission_name
            for role in self.roles
            for permission in role.permissions
        )

    # ==========================================
    # VERIFICATION HELPERS
    # ==========================================

    def is_fully_verified(self):
        return (
            self.email_verified
            or self.phone_verified
        )

    def can_use_marketplace(self):
        return (
            self.account_status == "active"
            and self.is_fully_verified()
        )

    # ==========================================
    # ACCOUNT HELPERS
    # ==========================================

    def is_active(self):
        return self.account_status == "active"

    def is_locked(self):
        if self.locked_until is None:
            return False

        return (
            datetime.now(timezone.utc)
            < self.locked_until
        )

    def __repr__(self):
        return f"<User {self.username}>"