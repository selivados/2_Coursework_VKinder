# from main import organize_search
from pprint import pprint

import vk_api
from datetime import date
from Settings.vk_config import TOKEN_VK_USER


class VKManager:
    def __init__(self):
        self.session_user = vk_api.VkApi(token=TOKEN_VK_USER)

    def get_user_data(self, user_id):
        '''Get the user data'''
        user_data = {}
        link_url = 'https://vk.com/id'
        try:
            user_get = self.session_user.method('users.get', {'user_ids': user_id,
                                                              'fields': 'city, bdate, sex'}
                                                )
        except IndexError:
            print("Пользователя нет")
        current_date = int(date.today().strftime("%d.%m.%Y").split('.')[2])
        for user in user_get:
            if user['bdate']:
                birh_date = int(user['bdate'].split('.')[2])
                age = current_date - birh_date
                user_data['age'] = int(age)
            else:
                user_data['age'] = 0
            user_data['user_id'] = int(user['id'])
            user_data['first_name'] = str(user['first_name'])
            user_data['last_name'] = str(user['last_name'])
            user_data['sex'] = int(user['sex'])
            if user['city']:
                user_data['city'] = str(user['city']['title'])
                user_data['city_id'] = user['city']['id']
            user_data['profile_link'] = str(link_url + str(user['id']))
        return user_data

    def get_partner_list(self, sex=None, age_from=None, age_to=None, city_id=None):
        '''Get the partner's data by parameters'''
        partner_list = []
        search_partners = self.session_user.method("users.search",
                                                   {"count": 50,
                                                    "sex": sex,
                                                    "age_from": age_from,
                                                    "age_to": age_to,
                                                    "city_id": city_id,
                                                    "has_photo": 1,
                                                    "fields": "sex, "
                                                              "bdate, "
                                                              "city"
                                                    }
                                                   )
        for partner_data in search_partners['items']:
            if partner_data['is_closed']:
                continue
            dict_persons = {}
            if 'city' not in partner_data:
                continue
            if partner_data['city']['id'] != city_id:
                continue
            if 'bdate' not in partner_data:
                continue
            if len(partner_data['bdate'].split('.')[0:3]) < 3:
                continue
            birth_day, birth_month, birth_year = map(int, partner_data['bdate'].split('.'))
            current_year = date.today().year
            age = current_year - birth_year
            dict_persons['photo_ids'] = self.get_photos_id(partner_data['id'])
            if dict_persons['photo_ids'] is None:
                del dict_persons
            else:
                dict_persons['user_id'] = int(partner_data['id'])
                dict_persons['first_name'] = str(partner_data['first_name'])
                dict_persons['last_name'] = str(partner_data['last_name'])
                dict_persons['sex'] = int(partner_data['sex'])
                dict_persons['age'] = age
                dict_persons['city'] = partner_data['city']['title']
                partner_list.append(dict_persons)
        pprint(partner_list)
        return partner_list

    def get_photos_id(self, user_id=None):
        '''Get a photo by id'''
        get_photos = self.session_user.method("photos.get",
                                              {"owner_id": user_id,
                                               "album_id": 'profile',
                                               "extended": 1,
                                               "photo_sizes": 1
                                               }
                                              )
        if get_photos.get('count') >= 3:
            return self.list_sorted_photos(get_photos)

    @staticmethod
    def list_sorted_photos(get_photos):
        photo_list = dict()
        for item in get_photos['items']:
            count_likes = dict()
            count_likes['photo_id'] = str(item["id"])
            count_likes['likes'] = int(item['likes']['count'])
            photo_list[item["id"]] = item['likes']['count']
        sorted_photos_count_likes = sorted(photo_list, reverse=True)[0:3]
        return sorted_photos_count_likes
