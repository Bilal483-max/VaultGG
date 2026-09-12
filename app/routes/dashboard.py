from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    flash
)

from app import db
from app.models.user import User
from app.models.listing import Listing
from app.models.listing import Favorite


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard"
)


def get_logged_in_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return User.query.get(user_id)


@dashboard_bp.route("/")
def dashboard():

    user = get_logged_in_user()

    if user is None:

        flash(
            "Please log in to access your dashboard.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    listings = (
        Listing.query
        .filter_by(seller_id=user.id)
        .order_by(Listing.created_at.desc())
        .all()
    )

    active_listings = sum(
        1
        for listing in listings
        if listing.status == "active"
    )

    sold_listings = sum(
        1
        for listing in listings
        if listing.status == "sold"
    )

    pending_listings = sum(
        1
        for listing in listings
        if listing.status in [
            "draft",
            "pending",
            "pending_verification"
        ]
    )

    favorites_count = (
        Favorite.query
        .filter_by(user_id=user.id)
        .count()
    )

    return render_template(
        "dashboard.html",
        user=user,
        listings=listings,
        active_listings=active_listings,
        sold_listings=sold_listings,
        pending_listings=pending_listings,
        favorites_count=favorites_count
    )


@dashboard_bp.route("/favorites")
def favorites():

    user = get_logged_in_user()

    if user is None:

        flash(
            "Please log in to view your favorites.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    favorites = (
        Favorite.query
        .filter_by(user_id=user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )

    return render_template(
        "favorites.html",
        user=user,
        favorites=favorites
    )


@dashboard_bp.route(
    "/favorite/<int:listing_id>",
    methods=["POST"]
)
def add_favorite(listing_id):

    user = get_logged_in_user()

    if user is None:

        flash(
            "Please log in to save listings.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )

    listing = Listing.query.get(listing_id)

    if listing is None:

        flash(
            "Listing not found.",
            "error"
        )

        return redirect(
            url_for("marketplace.marketplace")
        )

    if listing.status != "active":

        flash(
            "This listing is no longer available.",
            "error"
        )

        return redirect(
            url_for(
                "listings.listing_detail",
                listing_id=listing.id
            )
        )

    existing = (
        Favorite.query
        .filter_by(
            user_id=user.id,
            listing_id=listing.id
        )
        .first()
    )

    if existing:

        db.session.delete(existing)

        db.session.commit()

        flash(
            "Listing removed from favorites.",
            "success"
        )

    else:

        favorite = Favorite(
            user_id=user.id,
            listing_id=listing.id
        )

        db.session.add(favorite)

        db.session.commit()

        flash(
            "Listing saved to favorites.",
            "success"
        )

    return redirect(
        request_referrer_or_marketplace()
    )


def request_referrer_or_marketplace():
    from flask import request

    referrer = request.referrer

    if referrer:
        return referrer

    return url_for(
        "marketplace.marketplace"
    )