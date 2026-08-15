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
    # Customer Management
    "customers.read",
    "customers.create",
    "customers.update",
    "customers.archive",
    "contacts.read",
    "contacts.create",
    "contacts.update",
    "contacts.delete",
    "addresses.read",
    "addresses.create",
    "addresses.update",
    "addresses.delete",
    # Catalog
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
        "customers.read",
        "customers.create",
        "customers.update",
        "customers.archive",
        "contacts.read",
        "contacts.create",
        "contacts.update",
        "contacts.delete",
        "addresses.read",
        "addresses.create",
        "addresses.update",
        "addresses.delete",
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
        "customers.read",
        "customers.create",
        "customers.update",
        "contacts.read",
        "contacts.create",
        "contacts.update",
        "addresses.read",
        "addresses.create",
        "addresses.update",
        "catalog.read",
        "pricing.read",
        "quotes.read",
        "quotes.create",
        "quotes.update",
        "approval.read"
    ],
    "Viewer": [
        "customers.read",
        "contacts.read",
        "addresses.read",
        "catalog.read",
        "pricing.read",
        "quotes.read",
        "approval.read"
    ]
}
