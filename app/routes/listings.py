from flask import Blueprint, render_template, abort

from app.models.listing import Listing


listings_bp = Blueprint(
    "listings",
    __name__,
    url_prefix="/listing"
)


@listings_bp.route("/<int:listing_id>")
def listing_detail(listing_id):
    listing = (
        Listing.query
        .filter(
            Listing.id == listing_id,
            Listing.status == "active",
            Listing.verification_status == "approved"
        )
        .first()
    )

    if listing is None:
        abort(404)

    return render_template(
        "listing_detail.html",
        listing=listing
    )