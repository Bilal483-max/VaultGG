from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from sqlalchemy import func

from app import db

from app.models.user import User
from app.models.game import Game

from app.models.listing import (
    Listing,
    ListingVerificationInfo
)

from app.models.review import SellerReview

from app.services.credential_service import encrypt_secret


seller_bp = Blueprint(
    "seller",
    __name__,
    url_prefix="/seller"
)


def get_logged_in_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return User.query.get(user_id)


def get_allowed_login_methods(game_slug):

    methods = {

        "blood-strike": {
            "google",
            "netease"
        },

        "call-of-duty": {
            "google",
            "activision"
        },

        "free-fire": set()

    }

    return methods.get(
        game_slug,
        set()
    )


def get_seller_rank(completed_sales):

    if completed_sales >= 30:
        return "Onyx"

    if completed_sales >= 10:
        return "Platinum"

    return "Bronze"


@seller_bp.route("/")
def dashboard():

    user = get_logged_in_user()

    if not user:
        return redirect(
            url_for("auth.login")
        )

    listings = (
        Listing.query
        .filter_by(
            seller_id=user.id
        )
        .order_by(
            Listing.created_at.desc()
        )
        .all()
    )

    active_count = sum(
        1
        for listing in listings
        if listing.status == "active"
    )

    sold_count = sum(
        1
        for listing in listings
        if listing.status == "sold"
    )

    pending_count = sum(
        1
        for listing in listings
        if listing.verification_status in (
            "pending",
            "pending_verification"
        )
    )

    return render_template(
        "seller_dashboard.html",
        user=user,
        listings=listings,
        active_count=active_count,
        sold_count=sold_count,
        pending_count=pending_count
    )


@seller_bp.route("/create", methods=["GET", "POST"])
def create_listing():

    user = get_logged_in_user()

    if not user:
        return redirect(
            url_for("auth.login")
        )

    if request.method == "GET":

        games = (
            Game.query
            .filter_by(
                active=True
            )
            .order_by(
                Game.name.asc()
            )
            .all()
        )

        return render_template(
            "create_listing.html",
            games=games
        )

    game_id = request.form.get(
        "game_id",
        ""
    ).strip()

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    price_raw = request.form.get(
        "price",
        ""
    ).strip()

    currency = request.form.get(
        "currency",
        "NGN"
    ).strip()

    negotiable_raw = request.form.get(
        "negotiable",
        "false"
    ).strip().lower()

    login_method = request.form.get(
        "login_method",
        ""
    ).strip().lower()

    login_identifier = request.form.get(
        "login_identifier",
        ""
    ).strip()

    if not login_identifier:

        login_identifier = request.form.get(
            "login_identifier_cod",
            ""
        ).strip()

    login_secret = request.form.get(
        "login_secret",
        ""
    )

    verification_notes = request.form.get(
        "verification_notes",
        ""
    ).strip()

    if not game_id:

        flash(
            "Please select a game.",
            "error"
        )

        return redirect(
            url_for("seller.create_listing")
        )

    if not title:

        flash(
            "Please enter a listing title.",
            "error"
        )

        return redirect(
            url_for("seller.create_listing")
        )

    if not description:

        flash(
            "Please enter a listing description.",
            "error"
        )

        return redirect(
            url_for("seller.create_listing")
        )

    if not price_raw:

        flash(
            "Please enter a price.",
            "error"
        )

        return redirect(
            url_for("seller.create_listing")
        )

    try:

        price = float(price_raw)

    except ValueError:

        flash(
            "Invalid price.",
            "error"
        )

        return redirect(
            url_for("seller.create_listing")
        )

    if price < 0:

        flash(
            "Price cannot be negative.",
            "error"
        )

        return redirect(
            url_for("seller.create_listing")
        )

    game = Game.query.get(game_id)

    if not game or not game.active:

        flash(
            "The selected game is unavailable.",
            "error"
        )

        return redirect(
            url_for("seller.create_listing")
        )

    allowed_methods = get_allowed_login_methods(
        game.slug
    )

    if not allowed_methods:

        flash(
            "Login methods for this game have not been configured yet.",
            "error"
        )

        return redirect(
            url_for("seller.create_listing")
        )

    if login_method not in allowed_methods:

        flash(
            "Invalid login method for the selected game.",
            "error"
        )

        return redirect(
            url_for("seller.create_listing")
        )

    if not login_identifier:

        flash(
            "Please enter the account identifier.",
            "error"
        )

        return redirect(
            url_for("seller.create_listing")
        )

    if not login_secret:

        flash(
            "Please enter the account verification secret.",
            "error"
        )

        return redirect(
            url_for("seller.create_listing")
        )

    negotiable = (
        negotiable_raw == "true"
    )

    listing = Listing(

        seller_id=user.id,

        game_id=game.id,

        title=title,

        description=description,

        price=price,

        currency=currency,

        negotiable=negotiable,

        status="draft",

        verification_status="pending"

    )

    db.session.add(listing)

    db.session.flush()

    verification_info = ListingVerificationInfo(

        listing_id=listing.id,

        login_identifier=login_identifier,

        login_method=login_method,

        encrypted_login_secret=encrypt_secret(
            login_secret
        ),

        verification_notes=verification_notes

    )

    db.session.add(
        verification_info
    )

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to create the listing. Please try again.",
            "error"
        )

        return redirect(
            url_for("seller.create_listing")
        )

    flash(
        "Listing submitted successfully and is awaiting verification.",
        "success"
    )

    return redirect(
        url_for("seller.dashboard")
    )


@seller_bp.route("/<int:seller_id>")
def seller_profile(seller_id):

    seller = User.query.get_or_404(
        seller_id
    )

    listings = (
        Listing.query
        .filter(
            Listing.seller_id == seller.id,
            Listing.status == "active",
            Listing.verification_status == "approved"
        )
        .order_by(
            Listing.created_at.desc()
        )
        .all()
    )

    completed_sales = Listing.query.filter(
        Listing.seller_id == seller.id,
        Listing.status == "sold"
    ).count()

    reviews = (
        SellerReview.query
        .filter(
            SellerReview.seller_id == seller.id,
            SellerReview.visible == True
        )
        .order_by(
            SellerReview.created_at.desc()
        )
        .all()
    )

    average_rating = 0

    if reviews:

        average_rating = round(
            sum(
                review.rating
                for review in reviews
            ) / len(reviews),
            1
        )

    rank = get_seller_rank(
        completed_sales
    )

    return render_template(
        "seller_profile.html",
        seller=seller,
        listings=listings,
        completed_sales=completed_sales,
        reviews=reviews,
        average_rating=average_rating,
        rank=rank
    )