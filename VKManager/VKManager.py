import vk_api
from pprint import pprint
from datetime import date
from vk_config import TOKEN_VK_USER, TOKEN_VK_GROUP


class VKManager:
    def __init__(self):
        self.session_group = vk_api.VkApi(token=TOKEN_VK_GROUP)
        self.session_user = vk_api.VkApi(token=TOKEN_VK_USER)

    # Получаем данные пользователя
    def get_user_data(self, user_id):
        user_data = {}
        link_url = 'https://vk.com/id'
        user_get = self.session_user.method('users.get', {'user_ids': user_id, 'fields': 'city, bdate, sex'})[0]
        current_date = int(date.today().strftime("%d.%m.%Y").split('.')[2])
        if user_get.get('bdate'):
            birh_date = int(user_get['bdate'].split('.')[2])
            age = current_date - birh_date
            user_data['age'] = int(age)
        else:
            user_data['age'] = 25
        user_data['user_id'] = int(user_get['id'])
        user_data['first_name'] = str(user_get['first_name'])
        user_data['last_name'] = str(user_get['last_name'])
        user_data['sex'] = int(user_get['sex'])
        if user_get.get('city'):
            user_data['city'] = str(user_get['city']['title'])
            user_data['city_id'] = user_get['city']['id']
        user_data['profile_link'] = str(link_url + str(user_get['id']))
        return user_data

    # Получаем данные партнера по параметрам
    def get_partner_list(self, user_id=None, age_from=None, age_to=None, city_id=None):
        count_persons = 200
        partner_list = []
        get_sex_user = self.get_user_data(user_id).get('sex')
        if get_sex_user == 1:
            partner_sex = 2
        else:
            partner_sex = 1
        for i in range(0, 201, 50):
            search_partners = self.session_user.method("users.search",
                                                   {"count": count_persons,
                                                    "offset": i,
                                                    "sex": partner_sex,
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
                if partner_data['is_closed'] == False:
                    dict_persons = {}
                    if 'city' not in partner_data:
                        continue
                    if partner_data['city']['id'] != city_id:
                        continue
                    if 'bdate' not in partner_data:
                        continue
                    if len(partner_data['bdate'].split('.')[0:3]) != 3:
                        continue
                    current_date = int(date.today().strftime("%d.%m.%Y").split('.')[2])
                    birh_date = int(partner_data['bdate'].split('.')[2])
                    age = current_date - birh_date
                    dict_persons['user_id'] = int(partner_data['id'])
                    dict_persons['first_name'] = str(partner_data['first_name'])
                    dict_persons['last_name'] = str(partner_data['last_name'])
                    dict_persons['sex'] = int(partner_data['sex'])
                    dict_persons['age'] = int(age)
                    dict_persons['city'] = partner_data['city']['title']
                    dict_persons['photo_ids'] = self.get_photos_id(partner_data['id'])
                    partner_list.append(dict_persons)
        return partner_list

    # Получаем фото по id
    def get_photos_id(self, user_id=None):
        get_photos = self.session_user.method("photos.get",
                                              {"owner_id": user_id,
                                               "album_id": 'profile',
                                               "extended": 1,
                                               "photo_sizes": 1
                                               }
                                              )
        return self.list_sorted_photos(get_photos)

    def list_sorted_photos(self, get_photos):
        photo_list = []
        for item in get_photos['items']:
            count_likes = {}
            count_likes['photo_id'] = str(item["id"])
            count_likes['likes'] = item['likes']['count']
            photo_list.append(count_likes)

        sorted_photos_count_likes = sorted(photo_list, key=lambda item: item['likes'], reverse=True)[0:3]
        return self.partner_photos_list(sorted_photos_count_likes)

    def partner_photos_list(self, sorted_photos_count_likes):
        photo_id = []
        for lists_photos in sorted_photos_count_likes:
            photo_id.append(lists_photos['photo_id'])
        return photo_id

    # Лайк фото
    def likes_photo(self, user_id=None, photo_id=None):
        get_photos = self.session_user.method("likes.add",
                                              {"type": 'photo',
                                               "owner_id": user_id,
                                               "item_id": photo_id
                                               }
                                              )
        return get_photos


if __name__ == '__main__':
    vk = VKManager()
    # pprint(vk.get_photos_id(42203928))
    # pprint(len(vk.name(1,20,21,"Хабаровск")))
    pprint(len(vk.get_partner_list(42203928,20,21,153)))
    # vk.likes_photo(42203928, 456239035)
    #
    # gg = vk.get_partner_list(1, 20, 21, "Хабаровск")
    # for i in gg:
    #     lists = i['user_id']
    #     pprint(vk.get_photos_id(lists))