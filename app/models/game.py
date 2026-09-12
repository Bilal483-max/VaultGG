from datetime import datetime, timezone

from app import db


class Game(db.Model):
    __tablename__ = "games"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    slug = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    icon_url = db.Column(
        db.String(500),
        nullable=True
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    attributes = db.relationship(
        "GameAttribute",
        back_populates="game",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Game {self.name}>"


class GameAttribute(db.Model):
    __tablename__ = "game_attributes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    game_id = db.Column(
        db.Integer,
        db.ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    slug = db.Column(
        db.String(100),
        nullable=False
    )

    data_type = db.Column(
        db.String(30),
        nullable=False,
        default="number"
    )

    required = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    filterable = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    sort_order = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    game = db.relationship(
        "Game",
        back_populates="attributes"
    )

    def __repr__(self):
        return f"<GameAttribute {self.name}>"