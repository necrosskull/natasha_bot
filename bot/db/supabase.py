import httpx
import bot.config as config
from typing import Optional, Dict, Any, List
import logging


class Supabase:
    def __init__(self) -> None:
        self.api_key: str = config.SUPABASE_KEY
        self.authorization: str = config.SUPABASE_KEY
        self.url: str = f'{config.SUPABASE_URL}/rest/v1'
        self.table_name: Optional[str] = None
        self.select_columns: Optional[str] = None
        self.order_by_columns: Optional[str] = None
        self.limit_value: Optional[int] = None
        self.insert_data: Optional[Dict[str, Any]] = None
        self.update_data: Optional[Dict[str, Any]] = None
        self.eq_column: Optional[str] = None
        self.eq_value: Optional[str] = None

    def table(self, table_name: str) -> "Supabase":
        self.table_name = table_name
        return self

    def select(self, *columns: str) -> "Supabase":
        self.select_columns = ', '.join(columns)
        return self

    def order_by(self, *columns: str) -> "Supabase":
        self.order_by_columns = ', '.join(columns)
        return self

    def limit(self, value: int) -> "Supabase":
        self.limit_value = value
        return self

    def insert(self, data: Dict[str, Any]) -> "Supabase":
        self.insert_data = data
        return self

    def update(self, data: Dict[str, Any]) -> "Supabase":
        self.update_data = data
        return self

    def eq(self, column: str, value: str or int) -> "Supabase":
        self.eq_column = column
        self.eq_value = value
        return self

    async def execute(self) -> List[Dict[str, Any]] or Dict[str, Any] or str:

        url = f'{self.url}/{self.table_name}'
        headers = {
            'apikey': self.api_key,
            'Authorization': f'Bearer {self.authorization}',
            'Content-Type': 'application/json',
        }
        params = {}

        if self.select_columns:
            params['select'] = self.select_columns

        if self.order_by_columns:
            params['order'] = self.order_by_columns

        if self.limit_value:
            params['limit'] = self.limit_value

        if self.eq_column and self.eq_value:
            params[self.eq_column] = f'eq.{self.eq_value}'

        async with httpx.AsyncClient() as client:
            if self.insert_data:
                response = await client.post(url, headers=headers, json=self.insert_data)
            elif self.update_data:
                response = await client.patch(url, headers=headers, json=self.update_data, params=params)
            else:
                response = await client.get(url, headers=headers, params=params)

            # Reset attributes to None to avoid retaining previous values
            self.table_name = None
            self.select_columns = None
            self.order_by_columns = None
            self.limit_value = None
            self.insert_data = None
            self.update_data = None
            self.eq_column = None
            self.eq_value = None

            if response.status_code == 200:  # Successful response
                data = response.json()
                return data
            elif response.status_code in range(200, 300):  # handle 2xx status codes
                return
            else:
                return logging.error(f'Error: {response.status_code}, {response.json()}')
