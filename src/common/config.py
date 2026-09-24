"""Central configuration loaded from environment variables / .env.

Using pydantic-settings gives us validation and one place to see every
setting the project depends on.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str = "hpw"
    postgres_password: str = "changeme"
    postgres_db: str = "hospital_pricing"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    cms_inpatient_dataset_id: str = ""
    cms_hospital_info_dataset_id: str = ""

    aws_region: str = "us-east-1"
    s3_bucket: str = ""

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
