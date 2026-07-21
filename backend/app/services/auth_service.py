import secrets

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import UTC, datetime, timedelta
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserUpdate
from app.utils.security import verify_password, get_password_hash, create_access_token

class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            premium_trial_ends_at=datetime.now(UTC) + timedelta(days=45),
            ingest_token=secrets.token_hex(8),
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    @staticmethod
    def update_user(db: Session, user: User, payload: UserUpdate) -> User:
        data = payload.model_dump(exclude_unset=True)
        if "avatar_url" in data:
            url = data["avatar_url"]
            if url is not None:
                url = url.strip() or None
            if url is not None:
                if not url.startswith("https://"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="avatar_url must be an https URL",
                    )
                if "readyplayer.me" not in url and "readyplayerme.com" not in url:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="avatar_url must be a Ready Player Me model URL",
                    )
            user.avatar_url = url
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin) -> str:
        """Authenticate user and return access token"""
        # Find user by email
        user = db.query(User).filter(User.email == login_data.email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )

        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})

        return access_token
