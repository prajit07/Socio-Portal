from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Reads from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    DATABASE_URL: str = (
        "postgresql://placeholder:placeholder@ep-placeholder.region.aws.neon.tech/neondb?sslmode=require"
    )
    JWT_SECRET: str = "local-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:5173"

    # AI / LLM (pluggable). Leave CLOUDFLARE_* empty to use the built-in heuristic engine.
    CLOUDFLARE_ACCOUNT_ID: str = ""
    CLOUDFLARE_AI_API_KEY: str = ""
    CLOUDFLARE_AI_MODEL: str = "@cf/meta/llama-3.1-8b-instruct"
    DUPLICATE_THRESHOLD: float = 0.6

    # Email OTP (Google SMTP). Paste your sender address + app password below to
    # enable real email sending. When EMAIL_USER/EMAIL_PASS are empty, OTP codes are
    # printed to the server console (dev mode) so the flow is testable without creds.
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USER: str = ""  # sender Gmail address, e.g. you@gmail.com
    EMAIL_PASS: str = ""  # Gmail app password (NOT your normal password)
    EMAIL_FROM_NAME: str = "Socio Connect"
    OTP_TTL_SECONDS: int = 300
    OTP_LENGTH: int = 6
    EMAIL_VERIFICATION_REQUIRED: bool = False

    # Evidence file storage: "local" writes to backend/uploads/ (served at
    # /uploads/...), "s3" uploads to any S3-compatible bucket — AWS S3,
    # Cloudflare R2, Backblaze B2, Supabase Storage, or self-hosted MinIO.
    STORAGE_BACKEND: str = "local"
    S3_ENDPOINT_URL: str = ""  # empty = AWS S3; e.g. https://<acct>.r2.cloudflarestorage.com for R2
    S3_REGION: str = "auto"  # "auto" works for R2/MinIO; e.g. us-east-1 for AWS
    S3_BUCKET: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_PUBLIC_BASE_URL: str = ""  # e.g. https://pub-<id>.r2.dev or your CDN; empty = auto AWS URL

    @property
    def ai_enabled(self) -> bool:
        return bool(self.CLOUDFLARE_ACCOUNT_ID and self.CLOUDFLARE_AI_API_KEY)

    @property
    def email_configured(self) -> bool:
        return bool(self.EMAIL_USER and self.EMAIL_PASS)

    @property
    def storage_is_s3(self) -> bool:
        return self.STORAGE_BACKEND.strip().lower() == "s3"

    @property
    def s3_configured(self) -> bool:
        return bool(self.S3_BUCKET and self.S3_ACCESS_KEY and self.S3_SECRET_KEY)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
