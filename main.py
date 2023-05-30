from random import randrange
import vk_api

from vk_api.longpoll import VkLongPoll, VkEventType

from Database.db_manager import DBManager
from VKManager.VKManager import VKManager
from Settings.vk_config import TOKEN_VK_GROUP

text_message_mainmenu = 'Напишите: \n Начать поиск \n Избранные \n Чёрный список'


def write_msg(user_id, message, vk_keyboard=None, attachment=None):
    vk_group.method('messages.send', {'user_id': user_id,
                                      'message': message,
                                      'random_id': randrange(10 ** 7),
                                      'keyboard': vk_keyboard,
                                      'attachment': attachment})


def show_partners(user_data, vk_object, partners_data_list, keyboard, show_type):
    cursor = 0
    db = DBManager()
    cursor = select_show_partner(user_data['user_id'], vk_object, partners_data_list,
                                 db, cursor-1, 1, keyboard, show_type)

    for event in longpoll_group.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text
                if request == "След":
                    cursor = select_show_partner(user_data['user_id'], vk_object, partners_data_list, db, cursor, 1,
                                                 keyboard, show_type)
                elif request == "Пред":
                    cursor = select_show_partner(user_data['user_id'], vk_object, partners_data_list, db, cursor, -1,
                                                 keyboard, show_type)
                elif (request == "Добавить в избранное") and (show_type == 'search'):
                    db.add_to_favorite_list(user_data, partners_data_list[cursor])
                    write_msg(user_data['user_id'], f"Партнёр добавлен в cписок избранных", keyboard)
                elif (request == "Добавить в чёрный список") and (show_type == 'search'):
                    db.add_to_black_list(user_data, partners_data_list[cursor])
                    write_msg(user_data['user_id'], f"Партнёр добавлен в чёрный cписок", keyboard)
                elif (request == "Убрать из списка") and (show_type == 'favorite'):
                    db.delete_from_favorite_list(user_data, partners_data_list[cursor])
                    partners_data_list.pop(cursor)
                    write_msg(user_data['user_id'], f"Партнёр удалён из списка избранных", keyboard)
                elif (request == "Убрать из списка") and (show_type == 'black'):
                    db.delete_from_black_list(user_data, partners_data_list[cursor])
                    partners_data_list.pop(cursor)
                    write_msg(user_data['user_id'], f"Партнёр удалён из чёрного списка", keyboard)
                elif (request == "Выход в главное меню"):
                    break
                else:
                    write_msg(user_data['user_id'], f"Повторите команду")


def select_show_partner(user_id, vk_object, partners_data_list, db, cursor, inc, keyboard, show_type):
    f = False
    cursor += inc
    while not f:
        if (cursor < len(partners_data_list)) and (cursor >= 0):
            if (not db.find_in_black_list(user_data, partners_data_list[cursor])) or \
                    ((show_type == 'black') or (show_type == 'favorite')):
                show_one_partner(user_id, vk_object, partners_data_list[cursor], keyboard)
                f = True
            else:
                cursor += inc
        else:
            f = True
            if cursor <= -1:
                message = 'начала'
                cursor = 1
            else:
                message = 'конца'
                cursor = len(partners_data_list)-1
            write_msg(user_id, f"Вы дошли до {message} списка, листайте в другую сторону.", keyboard)
    return cursor


def show_one_partner(user_id, vk_object, partner, keyboard):
    photo_list = []
    lens = len(partner['photo_ids'])
    for i in range(0, lens):
        photo_list.append('photo' + str(partner['user_id']) + '_' + str(partner['photo_ids'][i]))
    photo_links = ','.join(photo_list)
    message = f"{partner['first_name']} {partner['last_name']} \n Возраст: {partner['age']} " \
              f"\n Город: {partner['city']} \n http://vk.com/id{partner['user_id']}"
    partner_photos = vk_object.get_photos_id(partner['user_id'])
    write_msg(user_id, message, keyboard,  photo_links)


def organize_search(user_data, vk_object, keyboard=None):
    if user_data['age']:
        partner_age_from = user_data['age'] - 5
        partner_age_to = user_data['age'] + 5
    else:
        write_msg(user_data['user_id'], "Введите нижнюю границу возраста.")

        partner_age_to = 0

        partner_age_from = input_age(user_data)

        if partner_age_from:
            write_msg(user_data['user_id'], "Введите верхнюю границу возраста.")
            partner_age_to = input_age(user_data)

    if partner_age_from and partner_age_to:
        if partner_age_from <= partner_age_to:
            write_msg(event.user_id, "Идёт поиск...")
            if user_data['city_id']:
                partner_list = vk_object.get_partner_list(user_data['user_id'], partner_age_from, partner_age_to,
                                                          user_data['city_id'])
            else:
                partner_list = vk_object.get_partner_list(user_data['user_id'], partner_age_from, partner_age_to)
            show_partners(user_data, vk_object, partner_list, keyboard, 'search')
            return partner_list
        else:
            write_msg(event.user_id, "Неверно указаны данные")
            return []


def input_age(user_data):
    for event in longpoll_group.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text
                if request.isdigit():
                    if int(request) in range(14, 99):
                        partner_age = request
                        break
                    else:
                        write_msg(user_data['user_id'],
                                  "Граница введена неверно. Повторите или нажмите q для выхода")
                elif (request == "q") or (request == "й"):
                    write_msg(user_data['user_id'], text_message_mainmenu, keyboard)
                    return 0
                else:
                    write_msg(user_data['user_id'],
                              "Граница введена неверно. Повторите или нажмите q для выхода")
    return partner_age


if __name__ == '__main__':

    with open('keyboard/keyboard.json', 'r', encoding='UTF-8') as f:
        keyboard = f.read()

    with open('keyboard/keyboard_search.json', 'r', encoding='UTF-8') as f:
        keyboard_search = f.read()

    with open('keyboard/keyboard_list.json', 'r', encoding='UTF-8') as f:
        keyboard_list = f.read()

    vk_group = vk_api.VkApi(token=TOKEN_VK_GROUP)
    longpoll_group = VkLongPoll(vk_group)

    db = DBManager()
    db.create_db()
    vk_object = VKManager()

    for event in longpoll_group.listen():
        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:
                request = event.text
                user_data = vk_object.get_user_data(event.user_id)

                if request == "Начать":
                    write_msg(event.user_id, text_message_mainmenu, keyboard)
                elif request == "Начать поиск":
                    partner_list = organize_search(user_data, vk_object, keyboard_search)
                    write_msg(event.user_id, text_message_mainmenu, keyboard)
                elif request == "Избранные":
                    write_msg(event.user_id, "Показываю избранных...")
                    favorite_list = db.get_favorite_list(user_data)
                    if favorite_list:
                        show_partners(user_data, vk_object, favorite_list, keyboard_list, 'favorite')
                        write_msg(event.user_id, text_message_mainmenu, keyboard)
                    else:
                        write_msg(event.user_id, f"В списке никого нет", keyboard)
                elif request == "Чёрный список":
                    write_msg(event.user_id, "Показываю чёрный список...")
                    black_list = db.get_black_list(user_data)
                    if black_list:
                        show_partners(user_data, vk_object, black_list, keyboard_list, 'black')
                        write_msg(event.user_id, text_message_mainmenu, keyboard)
                    else:
                        write_msg(event.user_id, f"В списке никого нет", keyboard)
                else:
                    write_msg(event.user_id, f"Не понял вашего ответа", keyboard)
