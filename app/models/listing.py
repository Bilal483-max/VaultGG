from datetime import datetime, timezone

from app import db


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    game_id = db.Column(
        db.Integer,
        db.ForeignKey("games.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    price = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    currency = db.Column(
        db.String(10),
        nullable=False,
        default="NGN"
    )

    negotiable = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="draft",
        index=True
    )

    verification_status = db.Column(
        db.String(30),
        nullable=False,
        default="pending",
        index=True
    )

    views = db.Column(
        db.Integer,
        nullable=False,
        default=0
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

    published_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    sold_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    seller = db.relationship(
        "User",
        backref=db.backref(
            "listings",
            lazy=True
        )
    )

    game = db.relationship(
        "Game",
        backref=db.backref(
            "listings",
            lazy=True
        )
    )

    attribute_values = db.relationship(
        "ListingAttributeValue",
        back_populates="listing",
        cascade="all, delete-orphan"
    )

    media = db.relationship(
        "ListingMedia",
        back_populates="listing",
        cascade="all, delete-orphan"
    )

    favorites = db.relationship(
        "Favorite",
        back_populates="listing",
        cascade="all, delete-orphan"
    )

    verification_info = db.relationship(
        "ListingVerificationInfo",
        back_populates="listing",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Listing {self.title}>"


class ListingAttributeValue(db.Model):
    __tablename__ = "listing_attribute_values"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    listing_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "listings.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    attribute_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "game_attributes.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    value = db.Column(
        db.Text,
        nullable=False
    )

    listing = db.relationship(
        "Listing",
        back_populates="attribute_values"
    )

    attribute = db.relationship(
        "GameAttribute",
        backref=db.backref(
            "listing_values",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<ListingAttributeValue {self.id}>"


class ListingMedia(db.Model):
    __tablename__ = "listing_media"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    listing_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "listings.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    media_type = db.Column(
        db.String(20),
        nullable=False
    )

    storage_key = db.Column(
        db.String(500),
        nullable=False
    )

    original_filename = db.Column(
        db.String(255),
        nullable=True
    )

    mime_type = db.Column(
        db.String(100),
        nullable=True
    )

    file_size = db.Column(
        db.BigInteger,
        nullable=True
    )

    sort_order = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    listing = db.relationship(
        "Listing",
        back_populates="media"
    )

    def __repr__(self):
        return f"<ListingMedia {self.id}>"


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
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
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "favorites",
            lazy=True
        )
    )

    listing = db.relationship(
        "Listing",
        back_populates="favorites"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "listing_id",
            name="uq_favorite_user_listing"
        ),
    )

    def __repr__(self):
        return (
            f"<Favorite "
            f"user={self.user_id} "
            f"listing={self.listing_id}>"
        )


class ListingVerificationInfo(db.Model):
    __tablename__ = "listing_verification_info"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    listing_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "listings.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True,
        index=True
    )

    login_identifier = db.Column(
        db.Text,
        nullable=True
    )

    login_method = db.Column(
        db.String(50),
        nullable=True
    )

    encrypted_login_secret = db.Column(
        db.Text,
        nullable=True
    )

    verification_notes = db.Column(
        db.Text,
        nullable=True
    )

    submitted_at = db.Column(
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

    listing = db.relationship(
        "Listing",
        back_populates="verification_info"
    )

    def __repr__(self):
        return (
            f"<ListingVerificationInfo "
            f"listing={self.listing_id}>"
        )