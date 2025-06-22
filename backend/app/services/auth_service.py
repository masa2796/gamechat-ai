import httpx
from fastapi import Request, Response
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class AuthService:
    async def verify_recaptcha(self, token: str) -> bool:
        RECAPTCHA_SECRET = os.getenv("RECAPTCHA_SECRET_TEST")
        url = "https://www.google.com/recaptcha/api/siteverify"
        data = {
            "secret": RECAPTCHA_SECRET,
            "response": token,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=data, timeout=5)
            if resp.status_code != 200:
                return False
            result: dict = resp.json()
            success: bool = result.get("success", False)
            return success

    def is_suspicious(self, request: Request, user_ip: str) -> bool:
        return False

    async def verify_request(
        self, 
        request: Request, 
        response: Response, 
        recaptcha_token: Optional[str], 
        recaptcha_passed: Optional[str]
    ) -> bool:
        user_ip = request.client.host if request.client else "unknown"
        
        if not recaptcha_passed:
            if not recaptcha_token:
                return False
            result = await self.verify_recaptcha(recaptcha_token)
            if result:
                self._set_auth_cookie(response)
                return True
            return False
        else:
            if self.is_suspicious(request, user_ip):
                if not recaptcha_token:
                    return False
                result = await self.verify_recaptcha(recaptcha_token)
                if result:
                    self._set_auth_cookie(response)
                    return True
                return False
            return True
    
    def _set_auth_cookie(self, response: Response) -> None:
        response.set_cookie(
            key="recaptcha_passed",
            value="true",
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=60*60*24*7
        )