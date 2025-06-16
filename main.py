import os

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from dotenv import load_dotenv

from Database.db_manager import DBManager
from VKontakte.vk_manager import VKManager
from VKontakte.vk_keyboards import (
    keyboard_search,
    keyboard_main,
    keyboard_partners,
    keyboard_favorites,
    keyboard_blocked
)

load_dotenv()


def send_message(user_id, message, keyboard=None, attachment=None):
    vk_group.messages.send(
        user_id=user_id,
        message=message,
        random_id=get_random_id(),
        keyboard=keyboard,
        attachment=attachment
    )


def select_partner(
    user_data, partner_list, database, cursor, increment, keyboard, menu_state
):
    user_id = user_data['user_id']
    cursor += increment

    while 0 <= cursor < len(partner_list):
        partner_data = partner_list[cursor]
        is_favorite = database.find_in_favorite_partners(
            user_data, partner_data
        )
        is_blocked = database.find_in_blocked_partners(user_data, partner_data)

        if (
            menu_state not in ['favorites', 'blocked'] and
            not is_favorite and not is_blocked
        ) or (
            menu_state == 'favorites' and is_favorite
        ) or (
            menu_state == 'blocked' and is_blocked
        ):
            show_partner_info(user_id, partner_data, keyboard)
            return cursor

        cursor += increment

    if cursor < 0:
        message = 'начала'
        cursor = -1
    else:
        message = 'конца'
        cursor = len(partner_list)

    send_message(user_id, f'Вы дошли до {message} списка.', keyboard)
    return cursor


def show_partner_info(user_id, partner_data, keyboard):
    photo_list = [
        f"photo{partner_data['user_id']}_{photo_id}"
        for photo_id in partner_data['photo_ids']
    ]
    photo_links = ','.join(photo_list)
    message = (f"{partner_data['first_name']} {partner_data['last_name']}\n"
               f"Возраст: {partner_data['age']}\n"
               f"Город: {partner_data['city']}\n"
               f"https://vk.com/id{partner_data['user_id']}")
    send_message(user_id, message, keyboard, photo_links)


def validate_user_data(session, message):
    user_data = session['user_data']
    user_id = user_data['user_id']
    menu_state = session['menu_state']

    if 'age' not in user_data:
        if menu_state != 'set_age':
            send_message(user_id, 'Укажите свой возраст.')
            session['menu_state'] = 'set_age'
            return False
        elif not (message.isdigit() and int(message) > 0):
            send_message(user_id, 'Возраст указан неверно. Повторите ввод.')
            return False
        else:
            user_data['age'] = int(message)

    if not (session['partner_age_from'] and session['partner_age_to']):
        session['partner_age_from'] = (
            user_data['age'] - 5 if user_data['age'] > 5 else 1
        )
        session['partner_age_to'] = user_data['age'] + 5

    if 'sex' not in user_data or user_data['sex'] == 0:
        if menu_state != 'set_sex':
            send_message(
                user_id, 'Укажите свой пол (1 - женский, 2 - мужской).'
            )
            session['menu_state'] = 'set_sex'
            return False
        elif not (message.isdigit() and message in ('1', '2')):
            send_message(user_id, 'Пол указан неверно. Повторите ввод.')
            return False
        else:
            user_data['sex'] = int(message)

    if 'city_id' not in user_data:
        send_message(
            user_id,
            'Поскольку в Вашем профиле не указан город, по умолчанию будет '
            'выбран город Москва для поиска партнёров.'
        )
        user_data['city_id'] = 1
        user_data['city'] = 'Москва'

    return True


if __name__ == '__main__':
    vk_session = vk_api.VkApi(token=os.getenv('VK_GROUP_TOKEN'))
    vk_group = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, os.getenv('VK_GROUP_ID'))

    vk = VKManager()
    db = DBManager()

    sessions = {}
    main_menu_message = 'Вы находитесь в главном меню.'

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            message = event.message.text
            user_id = event.message.from_id

            if user_id not in sessions:
                user_data = vk.get_user_data(user_id)
                sessions[user_id] = {
                    'user_data': user_data,
                    'partner_age_from': 0,
                    'partner_age_to': 0,
                    'partner_list': [],
                    'favorite_partners': [],
                    'blocked_partners': [],
                    'is_checked': False,
                    'menu_state': '',
                    'cursor': 0
                }

            session = sessions[user_id]

            if not session['is_checked']:
                if validate_user_data(session, message):
                    session['is_checked'] = True
                    session['menu_state'] = 'search'
                    send_message(
                        user_id,
                        'Нажмите кнопку внизу для начала поиска партнёров.',
                        keyboard_search
                    )

            elif (
                session['menu_state'] == 'search' and
                message == 'Начать поиск'
            ):
                send_message(user_id, 'Выполняется поиск...')
                session['partner_list'] = vk.get_partner_list(
                    session['user_data']['sex'],
                    session['partner_age_from'],
                    session['partner_age_to'],
                    session['user_data']['city_id']
                )
                session['menu_state'] = 'partners'
                session['cursor'] = select_partner(
                    user_data=session['user_data'],
                    partner_list=session['partner_list'],
                    database=db,
                    cursor=session['cursor'] - 1,
                    increment=1,
                    keyboard=keyboard_partners,
                    menu_state=session['menu_state']
                )

            elif (
                session['menu_state'] == 'main' and
                message == 'Список партнёров'
            ):
                session['menu_state'] = 'partners'
                session['cursor'] = select_partner(
                    user_data=session['user_data'],
                    partner_list=session['partner_list'],
                    database=db,
                    cursor=session['cursor'] - 1,
                    increment=1,
                    keyboard=keyboard_partners,
                    menu_state=session['menu_state']
                )

            elif (
                session['menu_state'] == 'main' and
                message == 'Список избранных'
            ):
                session['favorite_partners'] = db.get_favorite_partners(
                    session['user_data']
                )
                if session['favorite_partners']:
                    session['menu_state'] = 'favorites'
                    session['cursor'] = select_partner(
                        user_data=session['user_data'],
                        partner_list=session['favorite_partners'],
                        database=db,
                        cursor=session['cursor'] - 1,
                        increment=1,
                        keyboard=keyboard_favorites,
                        menu_state=session['menu_state']
                    )
                else:
                    send_message(
                        user_id,
                        'В списке избранных никого нет.',
                        keyboard_main
                    )

            elif (
                session['menu_state'] == 'main' and
                message == 'Чёрный список'
            ):
                session['blocked_partners'] = db.get_blocked_partners(
                    session['user_data']
                )
                if session['blocked_partners']:
                    session['menu_state'] = 'blocked'
                    session['cursor'] = select_partner(
                        user_data=session['user_data'],
                        partner_list=session['blocked_partners'],
                        database=db,
                        cursor=session['cursor'] - 1,
                        increment=1,
                        keyboard=keyboard_blocked,
                        menu_state=session['menu_state']
                    )
                else:
                    send_message(
                        user_id,
                        'В чёрном списке никого нет.',
                        keyboard_main
                    )

            elif (
                session['menu_state'] == 'partners' and
                message == '<< Предыдущий'
            ):
                session['cursor'] = select_partner(
                    user_data=session['user_data'],
                    partner_list=session['partner_list'],
                    database=db,
                    cursor=session['cursor'],
                    increment=-1,
                    keyboard=keyboard_partners,
                    menu_state=session['menu_state']
                )

            elif (
                session['menu_state'] == 'partners' and
                message == 'Следующий >>'
            ):
                session['cursor'] = select_partner(
                    user_data=session['user_data'],
                    partner_list=session['partner_list'],
                    database=db,
                    cursor=session['cursor'],
                    increment=1,
                    keyboard=keyboard_partners,
                    menu_state=session['menu_state']
                )

            elif (
                session['menu_state'] == 'partners' and
                message == 'Добавить в чёрный список'
            ):
                db.add_to_blocked_partners(
                    session['user_data'],
                    session['partner_list'][session['cursor']]
                )
                send_message(
                    user_id,
                    'Партнёр добавлен в чёрный список.',
                    keyboard_partners
                )

            elif (
                session['menu_state'] == 'partners' and
                message == 'Добавить в список избранных'
            ):
                db.add_to_favorite_partners(
                    session['user_data'],
                    session['partner_list'][session['cursor']]
                )
                send_message(
                    user_id,
                    'Партнёр добавлен в список избранных.',
                    keyboard_partners
                )

            elif (
                session['menu_state'] == 'favorites' and
                message == '<< Предыдущий'
            ):
                session['cursor'] = select_partner(
                    user_data=session['user_data'],
                    partner_list=session['favorite_partners'],
                    database=db,
                    cursor=session['cursor'],
                    increment=-1,
                    keyboard=keyboard_favorites,
                    menu_state=session['menu_state']
                )

            elif (
                session['menu_state'] == 'favorites' and
                message == 'Удалить из списка избранных'
            ):
                partner_data = session['favorite_partners'][session['cursor']]
                db.delete_from_favorite_partners(
                    session['user_data'], partner_data
                )
                session['favorite_partners'].remove(partner_data)
                if session['favorite_partners']:
                    send_message(
                        user_id,
                        'Партнёр удалён из списка избранных.',
                        keyboard_favorites
                    )
                else:
                    send_message(
                        user_id,
                        'Партнёр удалён, в списке избранных никого нет.',
                        keyboard_main
                    )
                    session['menu_state'] = 'main'

            elif (
                session['menu_state'] == 'favorites' and
                message == 'Следующий >>'
            ):
                session['cursor'] = select_partner(
                    user_data=session['user_data'],
                    partner_list=session['favorite_partners'],
                    database=db,
                    cursor=session['cursor'],
                    increment=1,
                    keyboard=keyboard_favorites,
                    menu_state=session['menu_state']
                )

            elif (
                session['menu_state'] == 'blocked' and
                message == '<< Предыдущий'
            ):
                session['cursor'] = select_partner(
                    user_data=session['user_data'],
                    partner_list=session['blocked_partners'],
                    database=db,
                    cursor=session['cursor'],
                    increment=-1,
                    keyboard=keyboard_blocked,
                    menu_state=session['menu_state']
                )

            elif (
                session['menu_state'] == 'blocked' and
                message == 'Удалить из чёрного списка'
            ):
                partner_data = session['blocked_partners'][session['cursor']]
                db.delete_from_blocked_partners(
                    session['user_data'], partner_data
                )
                session['blocked_partners'].remove(partner_data)
                if session['blocked_partners']:
                    send_message(
                        user_id,
                        'Партнёр удалён из чёрного списка.',
                        keyboard_blocked
                    )
                else:
                    send_message(
                        user_id,
                        'Партнёр удалён, в чёрном списке никого нет.',
                        keyboard_main
                    )
                    session['menu_state'] = 'main'

            elif (
                session['menu_state'] == 'blocked' and
                message == 'Следующий >>'
            ):
                session['cursor'] = select_partner(
                    user_data=session['user_data'],
                    partner_list=session['blocked_partners'],
                    database=db,
                    cursor=session['cursor'],
                    increment=1,
                    keyboard=keyboard_blocked,
                    menu_state=session['menu_state']
                )

            elif (
                session['menu_state'] in ['partners', 'favorites', 'blocked']
                and message == 'Выход в главное меню'
            ):
                session['menu_state'] = 'main'
                session['cursor'] = 0
                send_message(user_id, main_menu_message, keyboard_main)

            elif session['menu_state'] == 'main':
                send_message(user_id, main_menu_message, keyboard_main)
