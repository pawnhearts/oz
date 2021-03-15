from typing import Dict, List, Optional, Tuple

from aiohttp import ClientResponse, ClientSession
from loguru import logger


class Catalog:
    async def cookies(self):
        return {
            "MOBILE_APP_TYPE": "ozonapp_android",
            "SessionID": "QSZo-2fORnWTaU1wQcrUsA",
            "__Secure-ab-group": "98",
            "__Secure-access-token": "3.0.QSZo-2fORnWTaU1wQcrUsA.98.l8cMBQAAAABgT3lEK_W2QqphbmRyb2lkYXBwoDmAkKA..20210315171204.fgh0n_f0GAcKGKc5xWmFPxRtk5zb6ONYdKlZ82EWFas",
            "__Secure-refresh-token": "3.0.QSZo-2fORnWTaU1wQcrUsA.98.l8cMBQAAAABgT3lEK_W2QqphbmRyb2lkYXBwoDmAkKA..20210315171204.RhOVLaS7PShHGhN9H9RMBjNySSMVmyOeGvCThhw3UDQ",
            "__Secure-user-id": "0",
            "abGroup": "98",
            "access_token": "3.0.QSZo-2fORnWTaU1wQcrUsA.98.l8cMBQAAAABgT3lEK_W2QqphbmRyb2lkYXBwoDmAkKA..20210315171204.fgh0n_f0GAcKGKc5xWmFPxRtk5zb6ONYdKlZ82EWFas",
            "incap_ses_799_1285159": "JPWVKxW3LXt9lHd+jJ4WC4F9T2AAAAAAkjLeA1gCnAHM2PaNGs22xw==",
            "incap_ses_800_1285159": "zHzuLgZGHhDzC4R7DSwaC255T2AAAAAAzfDH34juNeA+E8QxuvvDRg==",
            "nlbi_1285159": "Bt+PSKhjAQ0T/YhNnIB5zwAAAAC5EoPpvQX65+x+CZ7iujel",
            "refresh_token": "3.0.QSZo-2fORnWTaU1wQcrUsA.98.l8cMBQAAAABgT3lEK_W2QqphbmRyb2lkYXBwoDmAkKA..20210315171204.RhOVLaS7PShHGhN9H9RMBjNySSMVmyOeGvCThhw3UDQ",
            "token_expiration": "2021-03-15T20:12:04+03:00",
            "visid_incap_1285159": "XkToWduDRpaztXe6X/ZSRUN5T2AAAAAAQUIPAAAAAAAELRAlFIjQKrTENPDfbuYz",
        }

    async def headers(self):
        return {
            "Host": "api.ozon.ru",
            "accept": "application/json; charset=utf-8",
            "authorization": "Bearer 3.0.QSZo-2fORnWTaU1wQcrUsA.98.l8cMBQAAAABgT3lEK_W2QqphbmRyb2lkYXBwoDmAkKA..20210315171204.fgh0n_f0GAcKGKc5xWmFPxRtk5zb6ONYdKlZ82EWFas",
            "user-agent": "ozonapp_android/12.7+1444",
            "x-o3-app-name": "ozonapp_android",
            "x-o3-app-version": "12.7(1444)",
            "x-o3-device-type": "mobile",
        }

    async def __aenter__(self) -> 'Catalog':
        self.session = ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.session.close()

    @logger.catch
    async def get(self, category: str, page: int = 1, sorting: str = 'new') -> Optional[List]:
        response = await self.get_raw(category, page, sorting)
        if response.status == 200:
            logger.debug(f'Successfully got {response.url}')
            items = self.get_items(await response.json())
            if items is None:
                logger.warning(f'Nothing found on {response.url}')
            return items
        else:
            logger.warning(f'Non-200 http code on {response.url}')
            logger.debug(await response.text())
            return

    @logger.catch
    async def get_raw(self, category: str, page: int = 1, sorting: str = 'new') -> ClientResponse:
        params = {'url': f'/category/{category}/?layout_container=default&layout_page_index=3&page={page}&sorting={sorting}'}
        headers = await self.headers()
        cookies = await self.cookies()
        response = await self.session.get('https://api.ozon.ru/composer-api.bx/page/json/v1', params=params, headers=headers, cookies=cookies)
        async with response:
            return response

    @staticmethod
    def get_items(data: Dict) -> Optional[List]:
        try:
            return next(iter(data['catalog']['searchResultsV2'].values()))['items']
        except (KeyError, StopIteration):
            return None

    @staticmethod
    def item_to_product(data: Dict) -> Dict:
        data = data['cellTrackingInfo']
        return {key: data[key] for key in ['id', 'title', 'price', 'discount']}

