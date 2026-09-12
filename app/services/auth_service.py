import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError
from sqlalchemy import or_

from app import db
from app.models.role import Role
from app.models.user import User


password_hasher = PasswordHasher()

OTP_EXPIRATION_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60

PASSWORD_RESET_MINUTES = 30

ACCOUNT_PENDING_VERIFICATION = "pending_verification"
ACCOUNT_ACTIVE = "active"


# ==========================================
# GENERAL HELPERS
# ==========================================

def normalize_email(email):
    if not email:
        return ""

    return email.strip().lower()


def normalize_username(username):
    if not username:
        return ""

    return username.strip()


def normalize_phone(phone_number):
    if not phone_number:
        return ""

    phone_number = phone_number.strip()

    phone_number = (
        phone_number
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    # Nigerian local format:
    # 08012345678 -> +2348012345678
    if phone_number.startswith("0"):
        phone_number = "+234" + phone_number[1:]

    return phone_number


def hash_password(password):
    return password_hasher.hash(password)


def verify_password(password_hash, password):
    try:
        return password_hasher.verify(
            password_hash,
            password
        )

    except (VerifyMismatchError, InvalidHash):
        return False


def hash_token(token):
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def generate_otp():
    """
    Generate a cryptographically secure 6-digit OTP.
    """
    return f"{secrets.randbelow(1_000_000):06d}"


def now_utc():
    return datetime.now(timezone.utc)


# ==========================================
# VALIDATION
# ==========================================

def validate_password(password):
    if not password:
        return False, "Password is required."

    if len(password) < 8:
        return False, "Password must be at least 8 characters."

    if len(password) > 128:
        return False, "Password is too long."

    return True, None


def validate_username(username):
    if not username:
        return False, "Username is required."

    if len(username) < 3:
        return False, "Username must be at least 3 characters."

    if len(username) > 50:
        return False, "Username must be 50 characters or fewer."

    allowed = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789_"
    )

    if any(
        character not in allowed
        for character in username
    ):
        return (
            False,
            "Username can only contain letters, numbers and underscores."
        )

    return True, None


def validate_email(email):
    if not email:
        return False, "Email is required."

    if len(email) > 255:
        return False, "Email is too long."

    if "@" not in email:
        return False, "Enter a valid email address."

    local, domain = email.rsplit("@", 1)

    if not local or not domain:
        return False, "Enter a valid email address."

    if "." not in domain:
        return False, "Enter a valid email address."

    return True, None


def validate_phone(phone_number):
    if not phone_number:
        return False, "Phone number is required."

    phone_number = normalize_phone(phone_number)

    if not phone_number.startswith("+"):
        return (
            False,
            "Enter your phone number with country code."
        )

    digits = phone_number[1:]

    if not digits.isdigit():
        return False, "Enter a valid phone number."

    if len(digits) < 8 or len(digits) > 15:
        return False, "Enter a valid phone number."

    return True, None


# ==========================================
# OTP HELPERS
# ==========================================

def can_resend_otp(last_sent_at):
    if last_sent_at is None:
        return True

    if last_sent_at.tzinfo is None:
        last_sent_at = last_sent_at.replace(
            tzinfo=timezone.utc
        )

    elapsed = (
        now_utc() - last_sent_at
    ).total_seconds()

    return elapsed >= OTP_RESEND_COOLDOWN_SECONDS


def seconds_until_resend(last_sent_at):
    if last_sent_at is None:
        return 0

    if last_sent_at.tzinfo is None:
        last_sent_at = last_sent_at.replace(
            tzinfo=timezone.utc
        )

    elapsed = (
        now_utc() - last_sent_at
    ).total_seconds()

    remaining = (
        OTP_RESEND_COOLDOWN_SECONDS
        - elapsed
    )

    return max(0, int(remaining))


def create_email_otp(user):
    """
    Generate and securely store a new email OTP.
    """

    otp = generate_otp()

    user.email_otp_hash = hash_token(otp)

    user.email_otp_expires_at = (
        now_utc()
        + timedelta(minutes=OTP_EXPIRATION_MINUTES)
    )

    user.email_otp_attempts = 0
    user.email_otp_last_sent_at = now_utc()

    return otp


def create_phone_otp(user):
    """
    Generate and securely store a new phone OTP.
    """

    otp = generate_otp()

    user.phone_otp_hash = hash_token(otp)

    user.phone_otp_expires_at = (
        now_utc()
        + timedelta(minutes=OTP_EXPIRATION_MINUTES)
    )

    user.phone_otp_attempts = 0
    user.phone_otp_last_sent_at = now_utc()

    return otp


# ==========================================
# VERIFY EMAIL OTP
# ==========================================

def verify_email_otp(user, otp):
    """
    Returns True when verification succeeds.

    Raises ValueError when verification fails.
    """

    if user.email_verified:
        return True

    if not user.email_otp_hash:
        raise ValueError(
            "No email verification code is active."
        )

    if not user.email_otp_expires_at:
        raise ValueError(
            "Your verification code has expired."
        )

    if user.email_otp_attempts >= OTP_MAX_ATTEMPTS:
        raise ValueError(
            "Too many incorrect attempts. "
            "Please request a new verification code."
        )

    expires_at = user.email_otp_expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    if now_utc() > expires_at:
        user.email_otp_hash = None
        user.email_otp_expires_at = None

        db.session.commit()

        raise ValueError(
            "Your verification code has expired. "
            "Please request a new one."
        )

    otp = (otp or "").strip()

    if len(otp) != 6 or not otp.isdigit():
        user.email_otp_attempts += 1

        db.session.commit()

        raise ValueError(
            "Enter the 6-digit verification code."
        )

    if hash_token(otp) != user.email_otp_hash:
        user.email_otp_attempts += 1

        db.session.commit()

        remaining = max(
            0,
            OTP_MAX_ATTEMPTS
            - user.email_otp_attempts
        )

        if remaining == 0:
            raise ValueError(
                "Too many incorrect attempts. "
                "Please request a new verification code."
            )

        raise ValueError(
            f"Incorrect verification code. "
            f"{remaining} attempt(s) remaining."
        )

    # Successful verification
    user.email_verified = True

    user.email_otp_hash = None
    user.email_otp_expires_at = None
    user.email_otp_attempts = 0
    user.email_otp_last_sent_at = None

    user.account_status = ACCOUNT_ACTIVE

    db.session.commit()

    return True


# ==========================================
# VERIFY PHONE OTP
# ==========================================

def verify_phone_otp(user, otp):
    """
    Returns True when verification succeeds.

    Raises ValueError when verification fails.
    """

    if user.phone_verified:
        return True

    if not user.phone_otp_hash:
        raise ValueError(
            "No phone verification code is active."
        )

    if not user.phone_otp_expires_at:
        raise ValueError(
            "Your verification code has expired."
        )

    if user.phone_otp_attempts >= OTP_MAX_ATTEMPTS:
        raise ValueError(
            "Too many incorrect attempts. "
            "Please request a new verification code."
        )

    expires_at = user.phone_otp_expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    if now_utc() > expires_at:
        user.phone_otp_hash = None
        user.phone_otp_expires_at = None

        db.session.commit()

        raise ValueError(
            "Your verification code has expired. "
            "Please request a new one."
        )

    otp = (otp or "").strip()

    if len(otp) != 6 or not otp.isdigit():
        user.phone_otp_attempts += 1

        db.session.commit()

        raise ValueError(
            "Enter the 6-digit verification code."
        )

    if hash_token(otp) != user.phone_otp_hash:
        user.phone_otp_attempts += 1

        db.session.commit()

        remaining = max(
            0,
            OTP_MAX_ATTEMPTS
            - user.phone_otp_attempts
        )

        if remaining == 0:
            raise ValueError(
                "Too many incorrect attempts. "
                "Please request a new verification code."
            )

        raise ValueError(
            f"Incorrect verification code. "
            f"{remaining} attempt(s) remaining."
        )

    # Successful verification
    user.phone_verified = True

    user.phone_otp_hash = None
    user.phone_otp_expires_at = None
    user.phone_otp_attempts = 0
    user.phone_otp_last_sent_at = None

    user.account_status = ACCOUNT_ACTIVE

    db.session.commit()

    return True


# ==========================================
# REGISTRATION
# ==========================================

def register_user(
    username,
    email,
    phone_number,
    password,
    verification_method="email"
):
    username = normalize_username(username)
    email = normalize_email(email)
    phone_number = normalize_phone(phone_number)

    verification_method = (
        verification_method.strip().lower()
        if verification_method
        else "email"
    )

    # ------------------------------------------
    # Validate username
    # ------------------------------------------

    valid, error = validate_username(username)

    if not valid:
        raise ValueError(error)

    # ------------------------------------------
    # Validate password
    # ------------------------------------------

    valid, error = validate_password(password)

    if not valid:
        raise ValueError(error)

    # ------------------------------------------
    # Validate verification method
    # ------------------------------------------

    if verification_method not in (
        "email",
        "phone"
    ):
        raise ValueError(
            "Invalid verification method."
        )

    # ------------------------------------------
    # Validate selected contact method
    # ------------------------------------------

    if verification_method == "email":

        valid, error = validate_email(email)

        if not valid:
            raise ValueError(error)

    else:

        valid, error = validate_phone(phone_number)

        if not valid:
            raise ValueError(error)

    # ------------------------------------------
    # Check username
    # ------------------------------------------

    existing_username = User.query.filter_by(
        username=username
    ).first()

    if existing_username:
        raise ValueError(
            "That username is already taken."
        )

    # ------------------------------------------
    # Check email
    # ------------------------------------------

    if email:

        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:
            raise ValueError(
                "An account with that email already exists."
            )

    # ------------------------------------------
    # Check phone
    # ------------------------------------------

    if phone_number:

        existing_phone = User.query.filter_by(
            phone_number=phone_number
        ).first()

        if existing_phone:
            raise ValueError(
                "An account with that phone number already exists."
            )

    # ------------------------------------------
    # Create user
    # ------------------------------------------

    user = User(
        username=username,
        email=email if email else None,
        phone_number=phone_number if phone_number else None,
        password_hash=hash_password(password),
        account_status=ACCOUNT_PENDING_VERIFICATION,
        email_verified=False,
        phone_verified=False,
        email_otp_attempts=0,
        phone_otp_attempts=0,
        failed_login_attempts=0
    )

    try:
        db.session.add(user)

        db.session.flush()

        # --------------------------------------
        # Assign Buyer role
        # --------------------------------------

        buyer_role = Role.query.filter_by(
            name="Buyer"
        ).first()

        if buyer_role is None:
            db.session.rollback()

            raise ValueError(
                "Buyer role is missing. "
                "Run seed_roles.py first."
            )

        user.roles.append(buyer_role)

        # --------------------------------------
        # Generate OTP
        # --------------------------------------

        if verification_method == "email":
            otp = create_email_otp(user)
        else:
            otp = create_phone_otp(user)

        db.session.commit()

        return user, otp

    except ValueError:
        db.session.rollback()
        raise

    except Exception:
        db.session.rollback()
        raise


# ==========================================
# RESEND EMAIL OTP
# ==========================================

def resend_email_otp(user):

    if user.email_verified:
        raise ValueError(
            "Your email is already verified."
        )

    if not user.email:
        raise ValueError(
            "No email address is connected to this account."
        )

    if not can_resend_otp(
        user.email_otp_last_sent_at
    ):
        seconds = seconds_until_resend(
            user.email_otp_last_sent_at
        )

        raise ValueError(
            f"Please wait {seconds} second(s) "
            f"before requesting another code."
        )

    otp = create_email_otp(user)

    db.session.commit()

    return otp


# ==========================================
# RESEND PHONE OTP
# ==========================================

def resend_phone_otp(user):

    if user.phone_verified:
        raise ValueError(
            "Your phone number is already verified."
        )

    if not user.phone_number:
        raise ValueError(
            "No phone number is connected to this account."
        )

    if not can_resend_otp(
        user.phone_otp_last_sent_at
    ):
        seconds = seconds_until_resend(
            user.phone_otp_last_sent_at
        )

        raise ValueError(
            f"Please wait {seconds} second(s) "
            f"before requesting another code."
        )

    otp = create_phone_otp(user)

    db.session.commit()

    return otp


# ==========================================
# PASSWORD RESET
# ==========================================

def create_password_reset_token(user):

    token = secrets.token_urlsafe(48)

    user.password_reset_token_hash = hash_token(
        token
    )

    user.password_reset_expires_at = (
        now_utc()
        + timedelta(minutes=PASSWORD_RESET_MINUTES)
    )

    return token


def verify_password_reset_token(user, token):

    if not user.password_reset_token_hash:
        return False

    if not user.password_reset_expires_at:
        return False

    expires_at = user.password_reset_expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    if now_utc() > expires_at:
        return False

    return (
        hash_token(token)
        == user.password_reset_token_hash
    )


def reset_password(
    user,
    token,
    new_password
):

    valid, error = validate_password(
        new_password
    )

    if not valid:
        return False, error

    if not verify_password_reset_token(
        user,
        token
    ):
        return (
            False,
            "Invalid or expired password reset token."
        )

    user.password_hash = hash_password(
        new_password
    )

    user.password_reset_token_hash = None
    user.password_reset_expires_at = None

    user.failed_login_attempts = 0
    user.locked_until = None

    db.session.commit()

    return True, None


# ==========================================
# LOGIN SECURITY
# ==========================================

def record_failed_login(user):

    user.failed_login_attempts += 1

    if user.failed_login_attempts >= 5:

        user.locked_until = (
            now_utc()
            + timedelta(minutes=15)
        )

        user.failed_login_attempts = 0


def record_successful_login(user):

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now_utc()


# ==========================================
# AUTHENTICATE USER
# ==========================================

def authenticate_user(
    identifier,
    password
):

    identifier = (identifier or "").strip()

    user = User.query.filter(
        or_(
            User.username == identifier,
            User.email == identifier.lower(),
            User.phone_number == normalize_phone(identifier)
        )
    ).first()

    if user is None:

        return (
            None,
            "Invalid username, email/phone or password."
        )

    if not user.is_active():

        return (
            None,
            "Please verify your email or phone number before logging in."
        )

    if user.is_locked():

        return (
            None,
            "Too many failed attempts. Please try again later."
        )

    if not verify_password(
        user.password_hash,
        password
    ):

        record_failed_login(user)

        db.session.commit()

        return (
            None,
            "Invalid username, email/phone or password."
        )

    record_successful_login(user)

    db.session.commit()

    return user, None