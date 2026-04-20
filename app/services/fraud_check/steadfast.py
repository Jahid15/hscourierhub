import httpx
from bs4 import BeautifulSoup
import urllib.parse
from app.database import db
from datetime import datetime, timedelta

# Global Dictionary: { email: {"cookies": dict, "headers": dict, "expires_at": datetime} }
SESSION_CACHE = {}

class SteadfastChecker:
    def __init__(self):
        self.base_url = "https://steadfast.com.bd"

    async def _try_login(self, client: httpx.AsyncClient, account: dict) -> bool:
        email = account['email']
        
        # 1. Attempt to bypass login entirely via Memory Cache
        if email in SESSION_CACHE:
            cached = SESSION_CACHE[email]
            if datetime.utcnow() < cached["expires_at"]:
                client.cookies.update(cached["cookies"])
                client.headers.update(cached["headers"])
                return True
            else:
                del SESSION_CACHE[email] # Expired cache

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        try:
            # 2. Get login page
            resp = await client.get(f"{self.base_url}/login", headers=headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            token_elem = soup.find('input', {'name': '_token'})
            if not token_elem:
                return False
                
            login_data = {
                "_token": token_elem['value'],
                "email": account['email'],
                "password": account['password'],
                "remember": "on"
            }
            
            # 2. Submit login
            post_resp = await client.post(
                f"{self.base_url}/login", 
                data=login_data, 
                headers={**headers, "Content-Type": "application/x-www-form-urlencoded"}, 
                follow_redirects=True
            )
            
            if "login" not in post_resp.url.path and (post_resp.status_code == 200 or "dashboard" in post_resp.url.path):
                # 3. Extract tokens
                soup = BeautifulSoup(post_resp.text, 'html.parser')
                meta_csrf = soup.find('meta', {'name': 'csrf-token'})
                csrf_token = meta_csrf['content'] if meta_csrf else None
                
                xsrf_cookie = client.cookies.get('XSRF-TOKEN')
                xsrf_token = urllib.parse.unquote(xsrf_cookie) if xsrf_cookie else ""
                
                if csrf_token:
                    auth_headers = {
                        "X-CSRF-TOKEN": csrf_token,
                        "X-XSRF-TOKEN": xsrf_token,
                        "User-Agent": headers["User-Agent"],
                        "X-Requested-With": "XMLHttpRequest"
                    }
                    client.headers.update(auth_headers)
                    
                    # Store session globally natively
                    try:
                        settings = await db.app_settings.find_one({"_id": "cache_settings"})
                        skip_mins = int(settings.get("steadfast_login_skip_minutes", 60)) if settings else 60
                    except:
                        skip_mins = 60
                        
                    SESSION_CACHE[email] = {
                        "cookies": dict(client.cookies),
                        "headers": auth_headers,
                        "expires_at": datetime.utcnow() + timedelta(minutes=skip_mins)
                    }
                    
                    return True
            return False
            
        except Exception as e:
            print(f"Error logging in {account['email']}: {e}")
            return False

    async def _handle_rate_limit(self, account: dict, data: dict, limit_key: str, current_key: str, status_key: str):
        try:
            limit_val = int(data.get("limit", account.get(limit_key, 10)))
        except (ValueError, TypeError):
            limit_val = account.get(limit_key, 10)
            
        await db.steadfast_check_accounts.update_one(
            {"_id": account["_id"]},
            {"$set": {
                limit_key: limit_val,
                current_key: limit_val,
                status_key: f"limit {limit_val}"
            }}
        )

    async def _try_api(self, client: httpx.AsyncClient, account: dict, phone: str, api_type: str) -> tuple[bool, dict]:
        if api_type == 'fraud':
            url = f"{self.base_url}/user/frauds/check/{phone}"
            limit_key = "fraud_limit"
            current_key = "fraud_current"
            status_key = "status_fraud"
        else:
            url = f"{self.base_url}/user/consignment/getbyphone/{phone}"
            limit_key = "consignment_limit"
            current_key = "consignment_current"
            status_key = "status_consignment"

        resp = await client.get(url)
        
        # Dead Token / 401 Catch Block
        if resp.status_code in [401, 403, 302] or "login" in str(resp.url).lower() or "<html" in resp.text.lower():
            if account['email'] in SESSION_CACHE:
                del SESSION_CACHE[account['email']]
            return False, {"error": "Authentication dropped explicitly by Steadfast gateway", "auth_failed": True}
        
        try:
            data = resp.json()
        except:
            data = {"error": "Invalid API JSON"}

        if resp.status_code == 429 or "limit exceeded" in str(data.get("error", "")).lower() or "maximum allowed" in str(data.get("error", "")).lower():
            await self._handle_rate_limit(account, data, limit_key, current_key, status_key)
            return False, {"error": "Rate limit", "limit_hit": True}

        if "not active" in str(data.get("error", "")).lower():
            await db.steadfast_check_accounts.update_one({"_id": account["_id"]}, {"$set": {status_key: "inactive"}})
            return False, data

        if resp.status_code == 200 and "error" not in data:
            await db.steadfast_check_accounts.update_one(
                {"_id": account["_id"]}, 
                {"$inc": {current_key: 1}, "$set": {"last_used": datetime.utcnow().isoformat()}}
            )
            return True, data
            
        return False, data

    async def check(self, phone: str) -> dict:
        result = {"data": None, "errors": []}
        
        try:
            accounts = await db.steadfast_check_accounts.find({"status_login": {"$ne": "failed"}}).to_list(None)
        except Exception as e:
            result["errors"].append(f"DB Error: {str(e)}")
            return result

        for acc in accounts:
            fraud_available = acc.get("fraud_current", 0) < acc.get("fraud_limit", 5)
            consignment_available = acc.get("consignment_current", 0) < acc.get("consignment_limit", 10)
            
            if not fraud_available and not consignment_available:
                continue
                
            async with httpx.AsyncClient() as client:
                if not await self._try_login(client, acc):
                    if acc['email'] in SESSION_CACHE:
                        del SESSION_CACHE[acc['email']]
                        
                    client.cookies.clear()
                    client.headers.clear()
                    
                    if not await self._try_login(client, acc):
                        await db.steadfast_check_accounts.update_one({"_id": acc["_id"]}, {"$set": {"status_login": "failed"}})
                        result["errors"].append(f"Login failed on {acc['email']}")
                        continue
                
                # Check Endpoint 1 (Method 1: fraud_search_ui)
                if fraud_available:
                    success, data = await self._try_api(client, acc, phone, 'fraud')
                    
                    if success:
                        result["data"] = data
                        result["errors"] = []
                        break # Found data successfully natively
                        
                    # Identify Global Auth/Ban Errors that implicitly kill Method 2 as well
                    elif data.get("auth_failed"):
                        result["errors"].append(f"Cached Authentication Rejected [{acc['email']}]")
                        continue # Instant Account Rotation!
                        
                    elif "not active" in str(data.get("error", "")).lower():
                        result["errors"].append(f"Banned Account Automatically Bypassed [{acc['email']}]")
                        continue # Instant Account Rotation! Method 2 will be categorically dead here anyway
                        
                    elif data.get("limit_hit"):
                        # Graceful fallback, Account is structurally still alive! 
                        pass # proceed natively to check Consignment endpoint exactly below
                        
                    else:
                        result["errors"].append(f"Fraud fail [{acc['email']}]: {data.get('error', data)}")
                        pass # proceed natively to check Consignment
                
                # Check Endpoint 2 (Method 2: add_parcel_fraud_search)
                if consignment_available:
                    success, data = await self._try_api(client, acc, phone, 'consignment')
                    
                    if success:
                        result["data"] = data
                        result["errors"] = []
                        break # Found data successfully natively via fallback
                        
                    else:
                        result["errors"].append(f"Consignment fallback fetch fail on {acc['email']} - {data.get('error', '')}")
                        continue # End of the line for this Account. Rotate to the next.

        return result
