import os

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


load_dotenv()


db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "development-secret-key"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False

    if not app.config["SQLALCHEMY_DATABASE_URI"]:
        raise RuntimeError(
            "DATABASE_URL is not set in the .env file."
        )

    db.init_app(app)
    migrate.init_app(app, db)

    # ==========================
    # DATABASE MODELS
    # ==========================

    from app.models.user import User

    from app.models.game import (
        Game,
        GameAttribute
    )

    from app.models.listing import (
        Listing,
        ListingAttributeValue,
        ListingMedia,
        Favorite,
        ListingVerificationInfo
    )

    from app.models.role import (
        Role,
        Permission,
        RolePermission,
        UserRole
    )

    from app.models.review import SellerReview  
    _ = (   
        User,
        Game,
        GameAttribute,
        Listing,
        ListingAttributeValue,
        ListingMedia,
        Favorite,
        ListingVerificationInfo,
        Role,
        Permission,
        RolePermission,
        UserRole
    )

    # ==========================
    # AUTHENTICATION
    # ==========================

    from app.routes.auth import auth_bp

    app.register_blueprint(auth_bp)

    # ==========================
    # MARKETPLACE
    # ==========================

    from app.routes.marketplace import marketplace_bp

    app.register_blueprint(marketplace_bp)

    # ==========================
    # LISTING DETAILS
    # ==========================

    from app.routes.listings import listings_bp

    app.register_blueprint(listings_bp)

    # ==========================
    # SELLER CENTER
    # ==========================

    from app.routes.seller import seller_bp

    app.register_blueprint(seller_bp)

    # ==========================
    # USER DASHBOARD
    # ==========================

    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(dashboard_bp)

    # ==========================
    # PUBLIC HOMEPAGE
    # ==========================

    @app.route("/")
    def home():
        return render_template("home.html")

    return app