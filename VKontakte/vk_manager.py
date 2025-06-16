import os
import time
from datetime import datetime

import vk_api
from vk_api import VkApiError
from dotenv import load_dotenv

load_dotenv()


class VKManager:

    def __init__(self):
        self.vk_session = vk_api.VkApi(token=os.getenv('VK_USER_TOKEN'))
        self.vk = self.vk_session.get_api()

    def get_user_data(self, user_id: int) -> dict:
        try:
            response = self.vk.users.get(
                user_ids=user_id,
                fields='bdate, sex, city'
            )
        except VkApiError:
            return {}
        if not response:
            return {}
        item = response[0]
        user_data = {
            'user_id': item['id'],
            'first_name': item['first_name'],
            'last_name': item['last_name'],
            'sex': item['sex']
        }
        if 'bdate' in item and len(item['bdate'].split('.')) == 3:
            user_data['age'] = self._calculate_age(item['bdate'])
        if 'city' in item:
            user_data['city_id'] = item['city']['id']
            user_data['city'] = item['city']['title']
        return user_data

    def get_partner_list(
        self,
        user_sex: int,
        age_from: int,
        age_to: int,
        city_id: int,
        count: int = 1000
    ) -> list[dict]:
        partner_sex = 1 if user_sex == 2 else 2
        try:
            response = self.vk.users.search(
                sex=partner_sex,
                age_from=age_from,
                age_to=age_to,
                city_id=city_id,
                count=count,
                has_photo=1,
                fields='bdate, sex, city, relation'
            )
        except VkApiError:
            return []
        if not response['items']:
            return []
        partner_list = []
        for item in response['items']:
            if not (
                not item.get('is_closed')
                and 'bdate' in item
                and len(item['bdate'].split('.')) == 3
                and 'city' in item
                and item['city']['id'] == city_id
                and item.get('relation') not in [3, 4, 7, 8]
            ):
                continue
            profile_photos = self._get_profile_photos(item['id'])
            if len(profile_photos) < 3:
                continue
            photo_ids = self._get_most_popular_profile_photo_ids(
                profile_photos
            )
            age = self._calculate_age(item['bdate'])
            partner_data = {
                'user_id': item['id'],
                'first_name': item['first_name'],
                'last_name': item['last_name'],
                'sex': item['sex'],
                'age': age,
                'city_id': item['city']['id'],
                'city': item['city']['title'],
                'photo_ids': photo_ids
            }
            partner_list.append(partner_data)
        return partner_list

    @staticmethod
    def _calculate_age(birth_date: str) -> int:
        day, month, year = map(int, birth_date.split('.'))
        today = datetime.today()
        age = today.year - year - ((today.month, today.day) < (month, day))
        return age

    def _get_profile_photos(self, user_id: int) -> list[dict]:
        profile_photos = []
        count = 1000
        offset = 0
        while True:
            try:
                response = self.vk.photos.get(
                    owner_id=user_id,
                    album_id='profile',
                    extended=1,
                    count=count,
                    offset=offset
                )
            except VkApiError:
                return []
            items = response['items']
            if not items:
                return []
            profile_photos.extend(items)
            if len(items) < count:
                break
            offset += count
            time.sleep(0.34)
        return profile_photos

    @staticmethod
    def _get_most_popular_profile_photo_ids(
        profile_photos: list[dict], count: int = 3
    ) -> list[int]:
        sorted_photos = sorted(
            profile_photos,
            key=lambda photo: photo['likes']['count'],
            reverse=True
        )
        photo_ids = [photo['id'] for photo in sorted_photos[:count]]
        return photo_ids
