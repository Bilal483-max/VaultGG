from datetime import datetime, timezone

from app import db


class SellerReview(db.Model):
    __tablename__ = "seller_reviews"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    buyer_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    listing_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "listings.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    rating = db.Column(
        db.Integer,
        nullable=False
    )

    comment = db.Column(
        db.Text,
        nullable=True
    )

    visible = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

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

    seller = db.relationship(
        "User",
        foreign_keys=[seller_id],
        backref=db.backref(
            "seller_reviews",
            lazy=True
        )
    )

    buyer = db.relationship(
        "User",
        foreign_keys=[buyer_id],
        backref=db.backref(
            "buyer_reviews",
            lazy=True
        )
    )

    listing = db.relationship(
        "Listing",
        foreign_keys=[listing_id],
        backref=db.backref(
            "seller_reviews",
            lazy=True
        )
    )

    def __repr__(self):
        return (
            f"<SellerReview "
            f"{self.id} seller={self.seller_id} "
            f"rating={self.rating}>"
        )