from app import create_app, db
from app.models.role import Role, Permission


ROLES = {
    "Buyer": {
        "description": "User who purchases gaming accounts.",
        "permissions": [
            "browse_listings",
            "favorite_listings",
            "send_messages",
            "make_offers",
            "purchase_accounts",
            "open_disputes",
            "leave_reviews",
            "create_buyer_requests",
        ],
    },
    "Seller": {
        "description": "User who lists and sells gaming accounts.",
        "permissions": [
            "browse_listings",
            "favorite_listings",
            "send_messages",
            "make_offers",
            "create_listings",
            "edit_own_listings",
            "submit_listings_for_verification",
            "view_own_sales",
            "view_own_analytics",
            "view_own_wallet",
            "request_payouts",
            "respond_to_disputes",
        ],
    },
    "Verification Staff": {
        "description": "Staff member responsible for reviewing and verifying listings.",
        "permissions": [
            "view_verification_queue",
            "review_listings",
            "approve_listings",
            "reject_listings",
            "request_listing_evidence",
            "view_listing_media",
            "add_verification_notes",
        ],
    },
    "Support Staff": {
        "description": "Staff member responsible for customer support.",
        "permissions": [
            "view_users",
            "view_orders",
            "view_disputes",
            "respond_to_support_requests",
            "view_conversations",
            "report_suspicious_activity",
        ],
    },
    "Super Admin": {
        "description": "Full VaultGG administrator.",
        "permissions": [
            "manage_users",
            "manage_roles",
            "manage_permissions",
            "manage_staff",
            "view_all_listings",
            "manage_listings",
            "verify_listings",
            "manage_games",
            "manage_game_attributes",
            "view_all_orders",
            "manage_orders",
            "view_payments",
            "manage_payments",
            "manage_payouts",
            "manage_disputes",
            "manage_reviews",
            "view_analytics",
            "manage_platform_settings",
            "view_audit_logs",
            "view_security_events",
            "manage_security",
        ],
    },
}


def get_or_create_permission(name):
    permission = Permission.query.filter_by(name=name).first()

    if permission is None:
        permission = Permission(
            name=name,
            description=name.replace("_", " ").capitalize()
        )
        db.session.add(permission)
        db.session.flush()

    return permission


def get_or_create_role(name, description):
    role = Role.query.filter_by(name=name).first()

    if role is None:
        role = Role(
            name=name,
            description=description
        )
        db.session.add(role)
        db.session.flush()

    return role


def seed_roles():
    app = create_app()

    with app.app_context():
        for role_name, role_data in ROLES.items():

            role = get_or_create_role(
                role_name,
                role_data["description"]
            )

            for permission_name in role_data["permissions"]:
                permission = get_or_create_permission(
                    permission_name
                )

                if permission not in role.permissions:
                    role.permissions.append(permission)

        db.session.commit()

        print()
        print("===================================")
        print("VaultGG roles and permissions seeded")
        print("===================================")

        for role_name in ROLES:
            role = Role.query.filter_by(
                name=role_name
            ).first()

            print(
                f"{role.name}: "
                f"{len(role.permissions)} permissions"
            )

        print()
        print("Seed completed successfully.")


if __name__ == "__main__":
    seed_roles()