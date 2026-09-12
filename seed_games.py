from app import create_app, db
from app.models.game import Game, GameAttribute


app = create_app()


GAMES = [
    {
        "name": "Blood Strike",
        "slug": "blood-strike",
        "description": "Battle royale and tactical shooter.",
        "attributes": [
            {
                "name": "Evo Guns",
                "slug": "evo-guns",
                "data_type": "number",
                "required": False,
                "filterable": True,
                "sort_order": 1
            },
            {
                "name": "Evo Melee",
                "slug": "evo-melee",
                "data_type": "number",
                "required": False,
                "filterable": True,
                "sort_order": 2
            },
            {
                "name": "Eternal Guns",
                "slug": "eternal-guns",
                "data_type": "number",
                "required": False,
                "filterable": True,
                "sort_order": 3
            },
            {
                "name": "Ultra Guns",
                "slug": "ultra-guns",
                "data_type": "number",
                "required": False,
                "filterable": True,
                "sort_order": 4
            },
            {
                "name": "Ultra Melee",
                "slug": "ultra-melee",
                "data_type": "number",
                "required": False,
                "filterable": True,
                "sort_order": 5
            }
        ]
    },

    {
        "name": "Free Fire",
        "slug": "free-fire",
        "description": "Free Fire gaming accounts.",
        "attributes": [
            {
                "name": "Character Level",
                "slug": "character-level",
                "data_type": "number",
                "required": False,
                "filterable": True,
                "sort_order": 1
            },
            {
                "name": "Weapon Skins",
                "slug": "weapon-skins",
                "data_type": "number",
                "required": False,
                "filterable": True,
                "sort_order": 2
            },
            {
                "name": "Rare Items",
                "slug": "rare-items",
                "data_type": "number",
                "required": False,
                "filterable": True,
                "sort_order": 3
            }
        ]
    },

    {
        "name": "Call of Duty",
        "slug": "call-of-duty",
        "description": "Call of Duty gaming accounts.",
        "attributes": [
            {
                "name": "Account Level",
                "slug": "account-level",
                "data_type": "number",
                "required": False,
                "filterable": True,
                "sort_order": 1
            },
            {
                "name": "Weapon Blueprints",
                "slug": "weapon-blueprints",
                "data_type": "number",
                "required": False,
                "filterable": True,
                "sort_order": 2
            },
            {
                "name": "Mythic Weapons",
                "slug": "mythic-weapons",
                "data_type": "number",
                "required": False,
                "filterable": True,
                "sort_order": 3
            },
            {
                "name": "Legendary Weapons",
                "slug": "legendary-weapons",
                "data_type": "number",
                "required": False,
                "filterable": True,
                "sort_order": 4
            }
        ]
    }
]


def seed_games():

    with app.app_context():

        print()
        print("================================")
        print(" VaultGG Game Seeder")
        print("================================")
        print()

        for game_data in GAMES:

            game = (
                Game.query
                .filter_by(
                    slug=game_data["slug"]
                )
                .first()
            )

            if game is None:

                game = Game(
                    name=game_data["name"],
                    slug=game_data["slug"],
                    description=game_data["description"],
                    active=True
                )

                db.session.add(game)

                db.session.flush()

                print(
                    f"Added game: {game.name}"
                )

            else:

                game.name = game_data["name"]
                game.description = game_data["description"]
                game.active = True

                print(
                    f"Game already exists: {game.name}"
                )


            for attribute_data in game_data["attributes"]:

                attribute = (
                    GameAttribute.query
                    .filter_by(
                        game_id=game.id,
                        slug=attribute_data["slug"]
                    )
                    .first()
                )

                if attribute is None:

                    attribute = GameAttribute(
                        game_id=game.id,
                        name=attribute_data["name"],
                        slug=attribute_data["slug"],
                        data_type=attribute_data["data_type"],
                        required=attribute_data["required"],
                        filterable=attribute_data["filterable"],
                        sort_order=attribute_data["sort_order"],
                        active=True
                    )

                    db.session.add(attribute)

                    print(
                        f"  + Added attribute: "
                        f"{attribute_data['name']}"
                    )

                else:

                    attribute.name = attribute_data["name"]
                    attribute.data_type = attribute_data["data_type"]
                    attribute.required = attribute_data["required"]
                    attribute.filterable = attribute_data["filterable"]
                    attribute.sort_order = attribute_data["sort_order"]
                    attribute.active = True

        db.session.commit()

        print()
        print("================================")
        print(" Games seeded successfully!")
        print("================================")
        print()

        games = (
            Game.query
            .filter_by(active=True)
            .order_by(Game.name.asc())
            .all()
        )

        print("Available games:")

        for game in games:

            print(
                f"- {game.name}"
            )

        print()


if __name__ == "__main__":
    seed_games()