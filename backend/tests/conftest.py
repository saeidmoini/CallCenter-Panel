import os

# Minimal settings so Pydantic config resolves during imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DIALER_TOKEN", "test-token")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
os.environ.setdefault("DEFAULT_BATCH_SIZE", "100")
os.environ.setdefault("TIMEZONE", "Asia/Tehran")
