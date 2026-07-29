# List of default permissions as requested
DEFAULT_PERMISSIONS = [
    "users.create",
    "users.read",
    "users.update",
    "users.delete",
    "roles.create",
    "roles.read",
    "roles.update",
    "roles.delete",
    "permissions.read",
    "catalog.read",
    "catalog.create",
    "catalog.update",
    "catalog.delete",
    "pricing.read",
    "pricing.manage",
    "quotes.read",
    "quotes.create",
    "quotes.update",
    "quotes.delete",
    "quotes.approve",
    "quotes.export",
    "approval.read",
    "approval.manage",
    "system.admin"
]

# List of default roles
DEFAULT_ROLES = [
    "Administrator",
    "Sales Manager",
    "Sales Representative",
    "Viewer"
]

# Default role to permission mappings for seeding
ROLE_PERMISSION_MAPPINGS = {
    "Administrator": DEFAULT_PERMISSIONS,
    "Sales Manager": [
        "users.read",
        "roles.read",
        "permissions.read",
        "catalog.read",
        "pricing.read",
        "quotes.read",
        "quotes.create",
        "quotes.update",
        "quotes.approve",
        "quotes.export",
        "approval.read",
        "approval.manage"
    ],
    "Sales Representative": [
        "catalog.read",
        "pricing.read",
        "quotes.read",
        "quotes.create",
        "quotes.update",
        "approval.read"
    ],
    "Viewer": [
        "catalog.read",
        "pricing.read",
        "quotes.read",
        "approval.read"
    ]
}
