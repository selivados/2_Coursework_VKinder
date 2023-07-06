import vk_api
from datetime import date
from Settings.vk_config import TOKEN_VK_USER


class VKManager:
    def __init__(self):
        self.session_user = vk_api.VkApi(token=TOKEN_VK_USER)

    def get_user_data(self, user_id):
        response = self.session_user.method(
            'users.get', {
                'user_ids': user_id,
                'fields': 'city, bdate, sex'
            }
        )
        if response:
            item = response[0]
            user_data = {
                'user_id': item['id'],
                'first_name': item['first_name'],
                'last_name': item['last_name'],
                'sex': item['sex']
            }
            if item['bdate']:
                current_year = date.today().year
                birth_year = int(item['bdate'].split('.')[2])
                age = current_year - birth_year
                user_data['age'] = age
            else:
                user_data['age'] = 0
            if item['city']:
                user_data['city'] = item['city']['title']
                user_data['city_id'] = item['city']['id']
            return user_data
        return False

    def get_partner_list(self, user_sex, age_from, age_to, city_id, count=500):
        partner_sex = 1 if user_sex == 2 else 2
        response = self.session_user.method(
            'users.search', {
                'count': count,
                'sex': partner_sex,
                'age_from': age_from,
                'age_to': age_to,
                'city_id': city_id,
                'has_photo': 1,
                'fields': 'sex, bdate, city'
            }
        )
        partner_list = []
        for item in response['items']:
            if item['is_closed']:
                continue
            if 'city' not in item:
                continue
            if item['city']['id'] != city_id:
                continue
            if 'bdate' not in item:
                continue
            if len(item['bdate'].split('.')) < 3:
                continue
            photo_ids_list = self.get_most_popular_photos_by_user_id(item['id'])
            if not photo_ids_list:
                continue
            current_year = date.today().year
            birth_year = int(item['bdate'].split('.')[2])
            age = current_year - birth_year
            partner_data = {
                'user_id': item['id'],
                'first_name': item['first_name'],
                'last_name': item['last_name'],
                'sex': item['sex'],
                'age': age,
                'city': item['city']['title'],
                'photo_ids': photo_ids_list
            }
            partner_list.append(partner_data)
        return partner_list

    def get_most_popular_photos_by_user_id(self, user_id, count=3):
        response = self.session_user.method(
            'photos.get', {
                'owner_id': user_id,
                'album_id': 'profile',
                'extended': 1,
                'photo_sizes': 1
            }
        )
        if response:
            if response['count'] < count:
                return False
            most_popular_photos = self.sort_photos_by_likes(response['items'])[:count]
            return most_popular_photos
        return False

    @staticmethod
    def sort_photos_by_likes(photos):
        photo_dict = {}
        for photo in photos:
            photo_dict[str(photo['id'])] = photo['likes']['count']
        sorted_photo_list = sorted(photo_dict, key=photo_dict.get, reverse=True)
        return sorted_photo_list
