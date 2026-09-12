from flask import Blueprint, render_template, session

from app.models.listing import Listing, Favorite


marketplace_bp = Blueprint(
    "marketplace",
    __name__,
    url_prefix="/marketplace"
)


@marketplace_bp.route("/")
def marketplace():

    listings = (
        Listing.query
        .filter(
            Listing.status == "active",
            Listing.verification_status == "approved"
        )
        .order_by(
            Listing.created_at.desc()
        )
        .all()
    )

    user_id = session.get("user_id")

    favorite_ids = set()

    if user_id:

        favorites = (
            Favorite.query
            .filter_by(user_id=user_id)
            .all()
        )

        favorite_ids = {
            favorite.listing_id
            for favorite in favorites
        }

    return render_template(
        "marketplace.html",
        listings=listings,
        favorite_ids=favorite_ids,
        logged_in=bool(user_id)
    )