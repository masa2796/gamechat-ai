import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    RECAPTCHA_SECRET: str = os.getenv("RECAPTCHA_SECRET_TEST")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    UPSTASH_VECTOR_REST_URL: str = os.getenv("UPSTASH_VECTOR_REST_URL")
    UPSTASH_VECTOR_REST_TOKEN: str = os.getenv("UPSTASH_VECTOR_REST_TOKEN")

settings = Settings()