import sys
with open('Backend/app/routers/sync.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace resolve_canvas_user with resolve_user_identities
target_resolve = '''async def resolve_canvas_user(user_ref: str) -> str:
    """Returns the internal Canvas user ID."""
    if user_ref.isdigit():
        return user_ref

    account_id = settings.canvas_account_id
    try:
        users = await canvas.paginate_limited(f"/accounts/{account_id}/users", {"search_term": user_ref, "per_page": 5}, max_records=5)
        if users:
            return str(users[0]["id"])
    except Exception as e:
        logger.error(f"Error resolving Canvas user {user_ref}: {e}")
    
    if "@" in user_ref:
        return f"sis_login_id:{user_ref}"
        
    raise ValueError(f"No se encontró el usuario en Canvas: {user_ref}")'''

replacement_resolve = '''async def resolve_user_identities(user_ref: str):
    """
    Given a user_ref (email, SIS ID, or Canvas ID), returns (canvas_user_id, teams_upn).
    Queries Canvas to resolve SIS IDs into emails for Teams, and ensures Canvas IDs are robust.
    """
    user_ref = str(user_ref).strip()
    if "@" in user_ref:
        return f"sis_login_id:{user_ref}", user_ref
        
    # Try as sis_user_id first
    try:
        user = await canvas.get(f"/users/sis_user_id:{user_ref}/profile")
        if user and "login_id" in user:
            return f"sis_user_id:{user_ref}", user["login_id"]
    except Exception:
        pass
        
    # Try as internal Canvas ID
    try:
        user = await canvas.get(f"/users/{user_ref}/profile")
        if user and "login_id" in user:
            return str(user["id"]), user["login_id"]
    except Exception:
        pass
        
    # Fallback to search
    account_id = settings.canvas_account_id
    try:
        users = await canvas.paginate_limited(f"/accounts/{account_id}/users", {"search_term": user_ref, "per_page": 5}, max_records=5)
        if users and len(users) > 0 and "login_id" in users[0]:
            return str(users[0]["id"]), users[0]["login_id"]
    except Exception as e:
        logger.error(f"Error resolving Canvas user {user_ref}: {e}")
        
    raise ValueError(f"No se pudo resolver el correo del usuario a partir de su identificador: {user_ref}")'''

if target_resolve in content:
    content = content.replace(target_resolve, replacement_resolve)
    print("Replaced resolve_canvas_user")
else:
    print("Failed to replace resolve_canvas_user")

# 2. Update _enroll_single
target_enroll = '''async def _enroll_single(item: UnifiedEnrollment):
    errors = []
    
    # 1. Resolve IDs
    try:
        canvas_user_id = await resolve_canvas_user(item.user_identifier)
    except Exception as e:
        return {"status": "error", "message": str(e), "item": item.dict()}'''

replacement_enroll = '''async def _enroll_single(item: UnifiedEnrollment):
    errors = []
    
    # 1. Resolve IDs
    try:
        canvas_user_id, teams_upn = await resolve_user_identities(item.user_identifier)
    except Exception as e:
        return {"status": "error", "message": str(e), "item": item.dict()}'''

if target_enroll in content:
    content = content.replace(target_enroll, replacement_enroll)
    print("Replaced _enroll_single user resolve")
else:
    print("Failed to replace _enroll_single user resolve")

target_teams_payload = '''    # 3. Teams Enrollment
    teams_role = ["owner"] if item.role == "teacher" else []
    teams_payload = {
        "@odata.type": "#microsoft.graph.aadUserConversationMember",
        "roles": teams_role,
        "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{item.user_identifier}')",
    }'''

replacement_teams_payload = '''    # 3. Teams Enrollment
    teams_role = ["owner"] if item.role == "teacher" else []
    teams_payload = {
        "@odata.type": "#microsoft.graph.aadUserConversationMember",
        "roles": teams_role,
        "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{teams_upn}')",
    }'''

if target_teams_payload in content:
    content = content.replace(target_teams_payload, replacement_teams_payload)
    print("Replaced teams payload")
else:
    print("Failed to replace teams payload")

# 3. Update resolve_canvas_course to be smarter about ID (Canvas vs SIS)
target_course = '''async def resolve_canvas_course(course_ref: str) -> str:
    """Returns the course ID, searching by name if course_ref is not purely numeric."""
    if course_ref.isdigit():
        return course_ref'''

replacement_course = '''async def resolve_canvas_course(course_ref: str) -> str:
    """Returns the course ID, searching by name if course_ref is not purely numeric."""
    course_ref = str(course_ref).strip()
    if course_ref.isdigit():
        # It's highly likely to be a SIS ID rather than an internal Canvas ID if it's 1830. 
        # But we'll try internal first, and if it fails, fallback to sis_course_id.
        # However, to avoid multiple Canvas calls here, we just return the most likely format.
        # But wait, it's safer to just return the internal ID or SIS ID.
        # The user's screenshot had 1830, which looks like an internal ID, but maybe it doesn't exist?
        # Canvas accepts course ids or sis_course_id:XXX.
        return course_ref'''

# I'll leave resolve_canvas_course alone because if 1830 doesn't exist, it's because it doesn't exist.
# The user's error says "Canvas API 404", meaning 1830 truly doesn't exist in their Canvas. I can't magically make it exist.

with open('Backend/app/routers/sync.py', 'w', encoding='utf-8') as f:
    f.write(content)
