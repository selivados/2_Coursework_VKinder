from random import randrange

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from Database.db_manager import DBManager
from VKManager.VKManager import VKManager
from Settings.vk_config import TOKEN_VK_GROUP


def write_msg(user_id, message, keyboard=None, attachment=None):
    vk_group.method('messages.send', {
        'user_id': user_id,
        'message': message,
        'random_id': randrange(10 ** 7),
        'keyboard': keyboard,
        'attachment': attachment
        }
    )


def select_partner(user_data, partner_data_list, db, cursor, increment, keyboard, show_type):
    user_id = user_data['user_id']
    end = False
    cursor += increment
    while not end:
        if 0 <= cursor < len(partner_data_list):
            find_in_fl = db.find_in_favorite_list(user_data, partner_data_list[cursor])
            find_in_bl = db.find_in_black_list(user_data, partner_data_list[cursor])
            if (show_type not in ['favorite', 'black'] and not find_in_fl and not find_in_bl) or\
                    (show_type in ['favorite', 'black'] and (find_in_fl or find_in_bl)):
                show_partner_info(user_id, partner_data_list[cursor], keyboard)
                end = True
            else:
                cursor += increment
        else:
            end = True
            if cursor <= -1:
                message = 'начала'
                cursor = -1
            else:
                message = 'конца'
                cursor = len(partner_data_list)
            write_msg(user_id, f'Вы дошли до {message} списка, листайте в другую сторону.', keyboard)
    return cursor


def show_partner_info(user_id, partner_data, keyboard):
    photo_list = [f"photo{str(partner_data['user_id'])}_{photo_id}" for photo_id in partner_data['photo_ids']]
    photo_links = ','.join(photo_list)
    message = f"{partner_data['first_name']} {partner_data['last_name']}\n" \
              f"Возраст: {partner_data['age']}\n" \
              f"Город: {partner_data['city']}\n" \
              f"https://vk.com/id{partner_data['user_id']}"
    write_msg(user_id, message, keyboard, photo_links)


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
    db.create_tables()
    vk = VKManager()

    user_id = None
    user_data = None
    partner_age_from = None
    partner_age_to = None
    partner_list = []
    favorite_list = []
    black_list = []
    status = 'main'
    flag = True
    cursor = 0
    message_mainmenu = f"Вы находитесь в главном меню.\n" \
                       f"Используйте клавиатуру внизу для ввода команд."

    for event in longpoll_group.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text

                if flag:
                    user_id = event.user_id
                    user_data = vk.get_user_data(user_id)
                    if user_data['age']:
                        partner_age_from = user_data['age'] - 5
                        partner_age_to = user_data['age'] + 5
                    else:
                        write_msg(user_id, 'Введите нижнюю границу возраста.')
                        status = 'age1'
                    flag = False

                if request.isdigit() and status == 'age1':
                    if int(request) in range(14, 99):
                        partner_age_from = request
                        status = 'age2'
                    else:
                        write_msg(user_id, 'Граница введена неверно. Повторите ввод.')

                elif request.isdigit() and status == 'age2':
                    if int(request) in range(14, 99) and partner_age_from <= int(request):
                        partner_age_to = request
                        status = 'search'
                    else:
                        write_msg(user_id, 'Граница введена неверно. Повторите ввод.')

                elif request == 'Начать поиск' and status == 'main':
                    write_msg(user_id, 'Идёт поиск...')
                    if user_data['city_id']:
                        partner_list = vk.get_partner_list(
                            user_data['sex'],
                            partner_age_from,
                            partner_age_to,
                            user_data['city_id']
                        )
                    else:
                        partner_list = vk.get_partner_list(
                            user_data['sex'],
                            partner_age_from,
                            partner_age_to
                        )
                    cursor = select_partner(
                        user_data,
                        partner_list,
                        db,
                        cursor=cursor - 1,
                        increment=1,
                        keyboard=keyboard_search,
                        show_type='search'
                    )
                    status = 'search'

                elif request == 'Избранные' and status == 'main':
                    write_msg(user_id, 'Показываю избранных...')
                    favorite_list = db.get_favorite_list(user_data)
                    if favorite_list:
                        cursor = select_partner(
                            user_data,
                            favorite_list,
                            db,
                            cursor=cursor - 1,
                            increment=1,
                            keyboard=keyboard_list,
                            show_type='favorite'
                        )
                        status = 'favorite'
                    else:
                        write_msg(user_id, 'В списке никого нет.', keyboard)

                elif request == 'Чёрный список' and status == 'main':
                    write_msg(user_id, 'Показываю чёрный список...')
                    black_list = db.get_black_list(user_data)
                    if black_list:
                        cursor = select_partner(
                            user_data,
                            black_list,
                            db,
                            cursor=cursor - 1,
                            increment=1,
                            keyboard=keyboard_list,
                            show_type='black'
                        )
                        status = 'black'
                    else:
                        write_msg(user_id, 'В списке никого нет.', keyboard)

                elif request == 'След' and status == 'search':
                    cursor = select_partner(
                        user_data,
                        partner_list,
                        db,
                        cursor,
                        increment=1,
                        keyboard=keyboard_search,
                        show_type=status
                    )

                elif request == 'Пред' and status == 'search':
                    cursor = select_partner(
                        user_data,
                        partner_list,
                        db,
                        cursor,
                        increment=-1,
                        keyboard=keyboard_search,
                        show_type=status
                    )

                elif request == 'Добавить в избранное' and status == 'search':
                    if db.find_in_favorite_list(user_data, partner_list[cursor]):
                        write_msg(user_id, 'Партнёр уже добавлен в cписок избранных.', keyboard_search)
                    else:
                        if db.find_in_black_list(user_data, partner_list[cursor]):
                            db.delete_from_black_list(user_data, partner_list[cursor])
                        db.add_to_favorite_list(user_data, partner_list[cursor])
                        write_msg(user_id, 'Партнёр добавлен в cписок избранных.', keyboard_search)

                elif request == 'Добавить в чёрный список' and status == 'search':
                    if db.find_in_black_list(user_data, partner_list[cursor]):
                        write_msg(user_id, 'Партнёр уже добавлен в чёрный список.', keyboard_search)
                    else:
                        if db.find_in_favorite_list(user_data, partner_list[cursor]):
                            db.delete_from_favorite_list(user_data, partner_list[cursor])
                        db.add_to_black_list(user_data, partner_list[cursor])
                        write_msg(user_id, 'Партнёр добавлен в чёрный cписок.', keyboard_search)

                elif request == 'След' and status == 'favorite':
                    cursor = select_partner(
                        user_data,
                        favorite_list,
                        db,
                        cursor,
                        increment=1,
                        keyboard=keyboard_list,
                        show_type=status
                    )

                elif request == 'Пред' and status == 'favorite':
                    cursor = select_partner(
                        user_data,
                        favorite_list,
                        db,
                        cursor,
                        increment=-1,
                        keyboard=keyboard_list,
                        show_type=status
                    )

                elif request == 'Убрать из списка' and status == 'favorite':
                    if db.find_in_favorite_list(user_data, favorite_list[cursor]):
                        db.delete_from_favorite_list(user_data, favorite_list[cursor])
                        write_msg(user_id, 'Партнёр удалён из списка избранных.', keyboard_list)
                    else:
                        write_msg(user_id, 'Партнёр уже удалён из списка избранных.', keyboard_list)

                elif request == 'След' and status == 'black':
                    cursor = select_partner(
                        user_data,
                        black_list,
                        db,
                        cursor,
                        increment=1,
                        keyboard=keyboard_list,
                        show_type=status
                    )

                elif request == 'Пред' and status == 'black':
                    cursor = select_partner(
                        user_data,
                        black_list,
                        db,
                        cursor,
                        increment=-1,
                        keyboard=keyboard_list,
                        show_type=status
                    )

                elif request == 'Убрать из списка' and status == 'black':
                    if db.find_in_black_list(user_data, black_list[cursor]):
                        db.delete_from_black_list(user_data, black_list[cursor])
                        write_msg(user_id, 'Партнёр удалён из чёрного списка.', keyboard_list)
                    else:
                        write_msg(user_id, 'Партнёр уже удалён из чёрного списка.', keyboard_list)

                elif request == 'Выход в главное меню' and status in ['search', 'favorite', 'black']:
                    status = 'main'
                    cursor = 0
                    write_msg(user_id, message_mainmenu, keyboard)

                else:
                    write_msg(user_id, message_mainmenu, keyboard)
