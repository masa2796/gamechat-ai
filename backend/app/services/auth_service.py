import httpx
import logging
from fastapi import Request, Response
from typing import Optional, Any
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AuthService:
    async def verify_recaptcha(self, token: str) -> bool:
        """reCAPTCHA検証を実行"""
        # reCAPTCHA認証を完全にスキップする環境変数チェック（デバッグ用）
        if os.getenv("BACKEND_SKIP_RECAPTCHA") == "true":
            logger.info("reCAPTCHA verification skipped due to BACKEND_SKIP_RECAPTCHA=true")
            return True
            
        # テスト環境用のバイパス機能（本番環境でもtest tokenを一時的に許可）
        if token == "test":
            logger.info("reCAPTCHA bypass for test token")
            return True
            
        # 開発・テスト環境での完全バイパス
        if os.getenv("BACKEND_ENVIRONMENT") in ["development", "test"]:
            logger.info("reCAPTCHA bypass for test environment")
            return True
            
        # 環境に応じて適切なreCAPTCHA秘密鍵を選択
        environment = os.getenv("BACKEND_ENVIRONMENT", "development")
        if environment == "production":
            RECAPTCHA_SECRET = os.getenv("RECAPTCHA_SECRET_KEY")
        else:
            RECAPTCHA_SECRET = os.getenv("RECAPTCHA_SECRET_KEY_TEST")
            
        if not RECAPTCHA_SECRET:
            # reCAPTCHA秘密鍵が設定されていない場合、テスト環境では通す
            if os.getenv("BACKEND_ENVIRONMENT") in ["development", "test"]:
                logger.warning("reCAPTCHA secret not set, allowing in development mode")
                return True
            # 本番環境でも秘密キーが未設定の場合は一時的に許可（デバッグ用）
            logger.warning("reCAPTCHA secret not configured, allowing temporarily for debug")
            return True
            
        logger.info(f"Verifying reCAPTCHA token: {token[:10]}***")
        
        url = "https://www.google.com/recaptcha/api/siteverify"
        data = {
            "secret": RECAPTCHA_SECRET,
            "response": token,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, data=data, timeout=10)
                if resp.status_code != 200:
                    logger.error(f"reCAPTCHA API request failed with status {resp.status_code}")
                    return False
                    
                result: dict[str, Any] = resp.json()
                success: bool = result.get("success", False)
                score = result.get("score", 0.0)
                action = result.get("action", "")
                
                logger.info(f"reCAPTCHA verification result: success={success}, score={score}, action={action}")
                
                if not success:
                    error_codes = result.get("error-codes", [])
                    logger.warning(f"reCAPTCHA verification failed: {error_codes}")
                
                return success
                
        except Exception as e:
            logger.error(f"reCAPTCHA verification error: {str(e)}")
            # 本番環境ではreCAPTCHAサービス障害時は厳格に拒否
            if os.getenv("BACKEND_ENVIRONMENT") == "production":
                return False
            # 開発環境では通す
            return True

    def is_suspicious(self, request: Request, user_ip: str) -> bool:
        """疑わしいアクセスかどうかを判定"""
        # 現在は簡易実装。将来的にはより高度な検知ロジックを実装
        
        # 異常に短い間隔でのリクエストチェック
        user_agent = request.headers.get("user-agent", "").lower()
        
        # 明らかにボットと思われるケース
        suspicious_agents = ["bot", "crawler", "spider", "scraper", "curl", "wget"]
        if any(agent in user_agent for agent in suspicious_agents):
            logger.info(f"Suspicious user agent detected: {user_agent}")
            return True
            
        # TODO: より高度な検知ロジック
        # - IP ベースのレート制限
        # - リクエストパターン分析
        # - 地理的位置の異常検知
        
        return False

    async def verify_request(
        self, 
        request: Request, 
        response: Response, 
        recaptcha_token: Optional[str], 
        recaptcha_passed: Optional[str]
    ) -> bool:
        """統合認証検証フロー"""
        user_ip = request.client.host if request.client else "unknown"
        logger.info(f"Starting request verification for IP: {user_ip}")
        
        # 既にreCAPTCHA認証済みかチェック
        if recaptcha_passed:
            logger.info("reCAPTCHA already passed (cookie found)")
            
            # 疑わしいアクセスの場合は再検証を要求
            if self.is_suspicious(request, user_ip):
                logger.info("Suspicious activity detected, requiring re-verification")
                if not recaptcha_token:
                    logger.warning("Suspicious activity but no reCAPTCHA token provided")
                    return False
                    
                result = await self.verify_recaptcha(recaptcha_token)
                if result:
                    self._set_auth_cookie(response)
                    logger.info("Re-verification successful")
                    return True
                else:
                    logger.warning("Re-verification failed")
                    return False
            
            # 通常のケースでは認証済みとして扱う
            return True
        else:
            # 初回認証の場合
            logger.info("First-time authentication required")
            if not recaptcha_token:
                logger.warning("No reCAPTCHA token provided for first-time authentication")
                return False
                
            result = await self.verify_recaptcha(recaptcha_token)
            if result:
                self._set_auth_cookie(response)
                logger.info("First-time authentication successful")
                return True
            else:
                logger.warning("First-time authentication failed")
                return False
    
    def _set_auth_cookie(self, response: Response) -> None:
        """認証Cookieを設定"""
        response.set_cookie(
            key="recaptcha_passed",
            value="true",
            httponly=True,
            secure=True,
            samesite="none",
            max_age=60*60*24*7  # 7日間有効
        )
        logger.info("Authentication cookie set")