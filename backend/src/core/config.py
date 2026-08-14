import os


JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "development-only-change-this-secret",
)

JWT_ALGORITHM = "HS256"

JWT_EXPIRE_MINUTES = 15