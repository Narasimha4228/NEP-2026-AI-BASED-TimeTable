from datetime import datetime, timedelta
from typing import Any, Union, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.models.user import User, UserCreate, UserRole
from app.db.mongodb import db
from bson import ObjectId

# -----------------------------
# PASSWORD HASHING
# -----------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -----------------------------
# OAUTH2 CONFIG
# -----------------------------
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# -----------------------------
# UTILS
# -----------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Always truncate before verifying
    safe_password = truncate_to_max_bytes(plain_password, 72)
    try:
        return pwd_context.verify(safe_password, hashed_password)
    except Exception as e:
        # Log and sanitize any passlib/bcrypt errors
        import logging
        logging.exception("Password verification error")
        return False


def get_password_hash(password: str) -> str:
    # Always truncate before hashing
    safe_password = truncate_to_max_bytes(password, 72)
    try:
        return pwd_context.hash(safe_password)
    except Exception as e:
            # Log and sanitize any passlib/bcrypt errors
            import logging, traceback
            logging.exception("Password hashing error")
            # Also write full traceback to a local file for diagnostics
            try:
                with open('backend/auth_errors.log', 'a', encoding='utf-8') as f:
                    f.write('--- Password hashing exception ---\n')
                    traceback.print_exc(file=f)
                    f.write('\n')
            except Exception:
                pass
            # Raise a generic error for the API layer to catch
            raise ValueError("Password could not be processed. Please use a shorter password.")


# Truncate a string to a maximum number of bytes when encoded as UTF-8.
# Bcrypt has a 72-byte limit for passwords; ensure we truncate consistently on the server.
def truncate_to_max_bytes(s: str, max_bytes: int = 72) -> str:
    if not isinstance(s, str):
        return s
    try:
        out_chars = []
        bytes_count = 0
        for ch in s:
            ch_bytes = len(ch.encode('utf-8'))
            if bytes_count + ch_bytes > max_bytes:
                break
            out_chars.append(ch)
            bytes_count += ch_bytes
        return ''.join(out_chars)
    except Exception:
        # Fallback: simple slice (may be incorrect for multibyte but safe)
        return s[:max_bytes]

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = (
        datetime.utcnow() + expires_delta
        if expires_delta
        else datetime.utcnow()
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

# -----------------------------
# AUTHENTICATION
# -----------------------------
async def authenticate_user(email: str, password: str) -> Optional[User]:
    user = await db.db.users.find_one({"email": email})
    if not user:
        return None

    # Truncate incoming password to bcrypt limit before verification
    safe_password = truncate_to_max_bytes(password, 72)

    if not verify_password(safe_password, user["hashed_password"]):
        return None

    user["id"] = str(user["_id"])
    user.pop("_id", None)
    return User(**user)

# -----------------------------
# CURRENT USER FROM TOKEN
# -----------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        user = await db.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise credentials_exception

        # Convert the document to User model
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        
        # Convert ObjectId fields to strings
        if "faculty_id" in user and user["faculty_id"]:
            user["faculty_id"] = str(user["faculty_id"]) if not isinstance(user["faculty_id"], str) else user["faculty_id"]
        if "group_id" in user and user["group_id"]:
            user["group_id"] = str(user["group_id"]) if not isinstance(user["group_id"], str) else user["group_id"]
        
        # Remove hashed_password from user data
        user_data = {k: v for k, v in user.items() if k != "hashed_password"}
        
        return User(**user_data)
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        traceback.print_exc()
        raise credentials_exception

# -----------------------------
# ACTIVE USER
# -----------------------------
async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user

# -----------------------------
# ADMIN USER (OPTIONAL DEPENDENCY)
# -----------------------------
async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user

# -----------------------------
# REGISTER USER
# -----------------------------
async def create_user_account(user_data: UserCreate) -> User:
    existing = await db.db.users.find_one({"email": user_data.email})
    if existing:
        raise ValueError("Email already registered")

    user_dict = user_data.model_dump(exclude={"password", "name"})
    # Truncate password to bcrypt limit before hashing (handled in get_password_hash)
    try:
        user_dict["hashed_password"] = get_password_hash(user_data.password)
    except ValueError as e:
        # Raise a ValueError with a user-friendly message
        raise ValueError(str(e))
    user_dict["created_at"] = datetime.utcnow()

    if not user_dict.get("full_name"):
        user_dict["full_name"] = user_data.name

    # Check if this is the first user - make them admin
    user_count = await db.db.users.count_documents({})
    if user_count == 0:
        user_dict["role"] = UserRole.admin
        print("🎉 First user registered - granting ADMIN role")
    else:
        user_dict["role"] = UserRole.student  # Default for all other users

    result = await db.db.users.insert_one(user_dict)
    user = await db.db.users.find_one({"_id": result.inserted_id})

    user["id"] = str(user["_id"])
    user.pop("_id", None)
    return User(**user)
