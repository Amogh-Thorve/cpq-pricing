import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.auth.models import Role, Permission
from backend.app.domains.auth.permissions import ROLE_PERMISSION_MAPPINGS

logger = logging.getLogger(__name__)

async def seed_roles_and_permissions(db: AsyncSession) -> None:
    """
    Seeds default roles and permissions in the database and configures their relationships.
    """
    # 1. Gather all unique permissions across mappings
    all_perm_names = set()
    for perms in ROLE_PERMISSION_MAPPINGS.values():
        all_perm_names.update(perms)

    # 2. Fetch existing permissions
    existing_perms_result = await db.execute(select(Permission))
    existing_perms = {p.name: p for p in existing_perms_result.scalars().all()}

    # 3. Create missing permissions
    for perm_name in all_perm_names:
        if perm_name not in existing_perms:
            logger.info(f"Seeding permission: {perm_name}")
            new_perm = Permission(name=perm_name, description=f"Permission for {perm_name}")
            db.add(new_perm)
            existing_perms[perm_name] = new_perm
    
    await db.flush()

    # 4. Fetch existing roles
    from sqlalchemy.orm import selectinload
    existing_roles_result = await db.execute(select(Role).options(selectinload(Role.permissions)))
    existing_roles = {r.name: r for r in existing_roles_result.scalars().all()}

    # 5. Create missing roles & setup relationships
    for role_name, perm_names in ROLE_PERMISSION_MAPPINGS.items():
        if role_name not in existing_roles:
            logger.info(f"Seeding role: {role_name}")
            new_role = Role(name=role_name, description=f"Default role {role_name}")
            db.add(new_role)
            existing_roles[role_name] = new_role

        role_obj = existing_roles[role_name]

        # Resolve permission entities to associate with role
        target_permissions = [existing_perms[p_name] for p_name in perm_names]
        
        # Link permissions
        role_obj.permissions = target_permissions
        db.add(role_obj)

    await db.flush()
    logger.info("Roles and permissions seeding completed successfully.")
