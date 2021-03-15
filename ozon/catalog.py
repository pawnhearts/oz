from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from aiohttp import ClientResponse, ClientSession
from loguru import logger


class Catalog:
    def __init__(self):
        self.accessToken = ""
        self.refreshToken = ""
        self.expiresIn = datetime.now()

    @logger.catch
    async def refresh_token(self):
        async with self.session.post(
            "https://api.ozon.ru/composer-api.bx/_action/initAuthRefresh",
            json={"refreshToken": self.refreshToken},
            headers={
                "Host": "api.ozon.ru",
                "accept": "application/json; charset=utf-8",
                "content-type": "application/json; charset=utf-8",
                "user-agent": "ozonapp_android/12.7+1444",
                "x-o3-app-name": "ozonapp_android",
                "x-o3-app-version": "12.7(1444)",
                "x-o3-device-type": "mobile",
            },
            cookies=await self.cookies()
        ) as resp:
            data = (await resp.json())["authToken"]
            self.accessToken = data["accessToken"]
            self.refreshToken = data["refreshToken"]
            self.expiresIn = datetime.now() + timedelta(seconds=data["expiresIn"])

    async def cookies(self):
        res = {
            "MOBILE_APP_TYPE": "ozonapp_android",
            "SessionID": "QSZo-2fORnWTaU1wQcrUsA",
            "__Secure-ab-group": "98",
            "__Secure-access-token": self.accessToken,
            "__Secure-refresh-token": self.refreshToken,
            "__Secure-user-id": "0",
            "abGroup": "98",
            "access_token": self.accessToken,
            "incap_ses_799_1285159": "JPWVKxW3LXt9lHd+jJ4WC4F9T2AAAAAAkjLeA1gCnAHM2PaNGs22xw==",
            "incap_ses_800_1285159": "zHzuLgZGHhDzC4R7DSwaC255T2AAAAAAzfDH34juNeA+E8QxuvvDRg==",
            "nlbi_1285159": "Bt+PSKhjAQ0T/YhNnIB5zwAAAAC5EoPpvQX65+x+CZ7iujel",
            "refresh_token": self.refreshToken,
            "token_expiration": self.expiresIn.isoformat(),
            "visid_incap_1285159": "XkToWduDRpaztXe6X/ZSRUN5T2AAAAAAQUIPAAAAAAAELRAlFIjQKrTENPDfbuYz",
        }
        res.update(dict(self.session.cookie_jar))
        return res

    async def headers(self):
        if datetime.now() > self.expiresIn:
            await self.refresh_token()
        return {
            "Host": "api.ozon.ru",
            "accept": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.accessToken}",
            "user-agent": "ozonapp_android/12.7+1444",
            "x-o3-app-name": "ozonapp_android",
            "x-o3-app-version": "12.7(1444)",
            "x-o3-device-type": "mobile",
        }

    async def __aenter__(self) -> "Catalog":
        self.session = ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.session.close()

    @logger.catch
    async def get(
        self, category: str, page: int = 1, sorting: str = "new"
    ) -> Optional[List]:
        response = await self.get_raw(category, page, sorting)
        if response.status == 200:
            logger.debug(f"Successfully got {response.url}")
            items = self.get_items(await response.json())
            if items is None:
                logger.warning(f"Nothing found on {response.url}")
            return items
        else:
            logger.warning(f"Non-200 http code on {response.url}")
            logger.debug(await response.text())
            return

    @logger.catch
    async def get_raw(
        self, category: str, page: int = 1, sorting: str = "new"
    ) -> ClientResponse:
        params = {
            "url": f"/category/{category}/?layout_container=default&layout_page_index=3&page={page}&sorting={sorting}"
        }
        headers = await self.headers()
        cookies = await self.cookies()
        response = await self.session.get(
            "https://api.ozon.ru/composer-api.bx/page/json/v1",
            params=params,
            headers=headers,
            cookies=cookies,
        )
        async with response:
            return response

    @staticmethod
    def get_items(data: Dict) -> Optional[List]:
        try:
            return next(iter(data["catalog"]["searchResultsV2"].values()))["items"]
        except (KeyError, StopIteration, TypeError):
            return None

    @staticmethod
    def item_to_product(data: Dict) -> Dict:
        data = data["cellTrackingInfo"]
        return {key: data[key] for key in ["id", "title", "price", "discount"]}
