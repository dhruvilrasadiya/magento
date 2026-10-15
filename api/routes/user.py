import os
from uuid import uuid4
from dotenv import load_dotenv
from database.user import User
from mongoengine import DoesNotExist
from .authentication import get_current_admin
from utils import hash_password, is_valid_password
from fastapi import APIRouter, HTTPException, Query, Depends
from email_validator import validate_email, EmailNotValidError
from schemas.user_schema import UserIn, UserOut, PaginatedUserResponse, UserUpdate, DeleteUserRequest

load_dotenv()

FORGOT_PASSWORD_SECRET = os.getenv("FORGOT_PASSWORD_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
FRONTEND_URL = os.getenv("FRONTEND_URL")


user_router = APIRouter()


def initialize_default_admin():
    if not User.objects(role="superadmin").first():
        admin_email = os.getenv("DEFAULT_ADMIN_EMAIL")
        admin_username = os.getenv("DEFAULT_ADMIN_USERNAME")
        admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")

        if not all([admin_email, admin_username, admin_password]):
            raise RuntimeError("Missing default admin credentials in .env file")

        if User.objects(email=admin_email).first():
            return  # Prevent duplicate emails if role is different

        hashed_pwd = hash_password(admin_password)
        user = User(
            id=str(uuid4()),
            email=admin_email,
            username=admin_username,
            password=hashed_pwd,
            role="superadmin",
        )
        user.save()


@user_router.post("/", response_model=UserOut)
async def create_user(user: UserIn, current_user: User = Depends(get_current_admin)):
    if User.objects(username=user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check email uniqueness
    if User.objects(email=user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    def email_validator_address(email):
        try:
            valid = validate_email(email, check_deliverability=False)
            return True, valid.email
        except EmailNotValidError as e:
            return False, str(e)

    is_valid, cleaned_email = email_validator_address(user.email)

    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid email: {cleaned_email}")

    if not is_valid_password(user.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long, and include at least one uppercase letter, one special character, and one number.",
        )

    hashed_pwd = hash_password(user.password)

    user_doc = User(
        id=str(uuid4()),
        email=cleaned_email,
        username=user.username,
        password=hashed_pwd,
        role=user.role,
    )
    user_doc.save()
    return user_doc.to_dict()


@user_router.get("/", response_model=PaginatedUserResponse)
async def list_users(
    role: str = None,
    page: int = Query(1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
):

    page = page + 1

    offset = (page - 1) * limit
    query = {}

    if role:
        query["role"] = role

    query["role__ne"] = "superadmin"
    
    # Role-based filtering
    if current_user.role == "supervisor":
        query["role"] = "supervisor"
    elif current_user.role == "admin":
        query["role__in"] = ["admin", "supervisor"]
    
    total = User.objects(**query).count()
    users = User.objects(**query).skip(offset).limit(limit)

    user_list = [user.to_dict() for user in users]
    return {
        "total": total,
        "users": user_list,
    }


@user_router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str, current_user: User = Depends(get_current_admin)):
    try:
        user = User.objects.get(id=user_id)
        return user.to_dict()
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")


@user_router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin),
):
    user = User.objects(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate and update email if provided
    if user_update.email and user_update.email != user.email:
        if User.objects(email=user_update.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        try:
            valid = validate_email(user_update.email, check_deliverability=False)
            user.email = valid.email
        except EmailNotValidError as e:
            raise HTTPException(status_code=400, detail=f"Invalid email: {str(e)}")

    # Validate and update username if provided
    if user_update.username and user_update.username != user.username:
        if User.objects(username=user_update.username).first():
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = user_update.username

    # Update role if provided
    if user_update.role:
        user.role = user_update.role

    user.save()
    return user.to_dict()

@user_router.delete("/delete-all", summary="Delete multiple users")
async def delete_multiple_users(request: DeleteUserRequest, current_user: User = Depends(get_current_admin)):
    
    user_ids = request.user_ids
    print("Hello there", user_ids)

    if not user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")

    result = User.objects(id__in=user_ids).delete()

    if result == 0:
        raise HTTPException(status_code=404, detail="No users found or all users are superadmins")

    return {"detail": f"{result} users deleted successfully"}


@user_router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_admin)):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return {"detail": "User deleted successfully"}
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")