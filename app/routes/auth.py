from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from app.services.auth_service import (
    register_user,
    verify_email_otp,
    verify_phone_otp,
    resend_email_otp,
    resend_phone_otp,
    authenticate_user
)

from app.models.user import User


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


# =========================================================
# REGISTER
# =========================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone_number = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        verification_method = request.form.get(
            "verification_method",
            "email"
        ).strip().lower()

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template(
                "register.html"
            )

        if verification_method not in [
            "email",
            "phone"
        ]:

            flash(
                "Invalid verification method.",
                "error"
            )

            return render_template(
                "register.html"
            )

        try:

            user, otp = register_user(
                username=username,
                email=email,
                phone_number=phone_number,
                password=password,
                verification_method=verification_method
            )

        except ValueError as error:

            flash(
                str(error),
                "error"
            )

            return render_template(
                "register.html"
            )

        session["pending_verification_user_id"] = user.id

        session["pending_verification_method"] = (
            verification_method
        )

        # Development only.
        # Later we will connect a real email/SMS provider.

        print("")
        print("=" * 50)
        print("VAULTGG DEVELOPMENT OTP")
        print("=" * 50)
        print(f"Username: {user.username}")
        print(f"Method: {verification_method}")
        print(f"OTP: {otp}")
        print("=" * 50)
        print("")

        return redirect(
            url_for("auth.verify")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# VERIFY OTP
# =========================================================

@auth_bp.route("/verify", methods=["GET", "POST"])
def verify():

    user_id = session.get(
        "pending_verification_user_id"
    )

    method = session.get(
        "pending_verification_method"
    )

    if not user_id or not method:

        flash(
            "No verification session was found.",
            "error"
        )

        return redirect(
            url_for("auth.register")
        )

    user = User.query.get(user_id)

    if user is None:

        session.pop(
            "pending_verification_user_id",
            None
        )

        session.pop(
            "pending_verification_method",
            None
        )

        flash(
            "Account could not be found.",
            "error"
        )

        return redirect(
            url_for("auth.register")
        )

    if user.is_fully_verified():

        session.pop(
            "pending_verification_user_id",
            None
        )

        session.pop(
            "pending_verification_method",
            None
        )

        return redirect(
            url_for("auth.login")
        )

    if request.method == "POST":

        otp = request.form.get(
            "otp",
            ""
        ).strip()

        try:

            if method == "phone":

                verified = verify_phone_otp(
                    user,
                    otp
                )

            else:

                verified = verify_email_otp(
                    user,
                    otp
                )

        except ValueError as error:

            flash(
                str(error),
                "error"
            )

            return render_template(
                "verify_email.html",
                method=method,
                user=user
            )

        if verified:

            session.pop(
                "pending_verification_user_id",
                None
            )

            session.pop(
                "pending_verification_method",
                None
            )

            flash(
                "Your account has been verified. You can now log in.",
                "success"
            )

            return redirect(
                url_for("auth.login")
            )

        flash(
            "Invalid or expired verification code.",
            "error"
        )

    return render_template(
        "verify_email.html",
        method=method,
        user=user
    )


# =========================================================
# RESEND VERIFICATION
# =========================================================

@auth_bp.route(
    "/resend-verification",
    methods=["POST"]
)
def resend_verification():

    user_id = session.get(
        "pending_verification_user_id"
    )

    method = session.get(
        "pending_verification_method"
    )

    if not user_id or not method:

        flash(
            "No verification session was found.",
            "error"
        )

        return redirect(
            url_for("auth.register")
        )

    user = User.query.get(user_id)

    if user is None:

        flash(
            "Account could not be found.",
            "error"
        )

        return redirect(
            url_for("auth.register")
        )

    try:

        if method == "phone":

            otp = resend_phone_otp(user)

        else:

            otp = resend_email_otp(user)

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for("auth.verify")
        )

    # Development only.

    print("")
    print("=" * 50)
    print("VAULTGG DEVELOPMENT OTP RESENT")
    print("=" * 50)
    print(f"Username: {user.username}")
    print(f"Method: {method}")
    print(f"OTP: {otp}")
    print("=" * 50)
    print("")

    flash(
        "A new verification code has been sent.",
        "success"
    )

    return redirect(
        url_for("auth.verify")
    )


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        identifier = request.form.get(
            "identifier",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not identifier or not password:

            flash(
                "Please enter your login details.",
                "error"
            )

            return render_template(
                "login.html"
            )

        try:

            result = authenticate_user(
                identifier,
                password
            )

            # authenticate_user() returns a tuple.
            # The first item is the User object.

            if isinstance(result, tuple):

                user = result[0]

            else:

                user = result

        except ValueError as error:

            flash(
                str(error),
                "error"
            )

            return render_template(
                "login.html"
            )

        if user is None:

            flash(
                "Invalid username/email/phone or password.",
                "error"
            )

            return render_template(
                "login.html"
            )

        # Clear any previous session.
        session.clear()

        # Create the authenticated session.
        session["user_id"] = user.id
        session["username"] = user.username

        flash(
            f"Welcome back, {user.username}!",
            "success"
        )

        return redirect(
            url_for("dashboard.dashboard")
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@auth_bp.route(
    "/logout",
    methods=["POST", "GET"]
)
def logout():

    username = session.get(
        "username"
    )

    session.clear()

    if username:

        flash(
            "You have been logged out successfully.",
            "success"
        )

    else:

        flash(
            "You are not currently logged in.",
            "error"
        )

    return redirect(
        url_for("home")
    )