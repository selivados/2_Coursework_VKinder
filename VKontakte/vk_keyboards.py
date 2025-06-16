from vk_api.keyboard import VkKeyboard, VkKeyboardColor

keyboard_search = VkKeyboard(one_time=True)
keyboard_search.add_button('Начать поиск', color=VkKeyboardColor.PRIMARY)
keyboard_search = keyboard_search.get_keyboard()

keyboard_main = VkKeyboard(one_time=True)
keyboard_main.add_button('Список партнёров', color=VkKeyboardColor.PRIMARY)
keyboard_main.add_line()
keyboard_main.add_button('Чёрный список', color=VkKeyboardColor.NEGATIVE)
keyboard_main.add_button('Список избранных', color=VkKeyboardColor.POSITIVE)
keyboard_main = keyboard_main.get_keyboard()

keyboard_partners = VkKeyboard(one_time=False)
keyboard_partners.add_button('<< Предыдущий', color=VkKeyboardColor.PRIMARY)
keyboard_partners.add_button('Следующий >>', color=VkKeyboardColor.PRIMARY)
keyboard_partners.add_line()
keyboard_partners.add_button(
    'Добавить в чёрный список', color=VkKeyboardColor.NEGATIVE
)
keyboard_partners.add_button(
    'Добавить в список избранных', color=VkKeyboardColor.POSITIVE
)
keyboard_partners.add_line()
keyboard_partners.add_button(
    'Выход в главное меню', color=VkKeyboardColor.PRIMARY
)
keyboard_partners = keyboard_partners.get_keyboard()

keyboard_favorites = VkKeyboard(one_time=False)
keyboard_favorites.add_button('<< Предыдущий', color=VkKeyboardColor.PRIMARY)
keyboard_favorites.add_button('Следующий >>', color=VkKeyboardColor.PRIMARY)
keyboard_favorites.add_line()
keyboard_favorites.add_button(
    'Удалить из списка избранных', color=VkKeyboardColor.NEGATIVE
)
keyboard_favorites.add_line()
keyboard_favorites.add_button(
    'Выход в главное меню', color=VkKeyboardColor.PRIMARY
)
keyboard_favorites = keyboard_favorites.get_keyboard()

keyboard_blocked = VkKeyboard(one_time=False)
keyboard_blocked.add_button('<< Предыдущий', color=VkKeyboardColor.PRIMARY)
keyboard_blocked.add_button('Следующий >>', color=VkKeyboardColor.PRIMARY)
keyboard_blocked.add_line()
keyboard_blocked.add_button(
    'Удалить из чёрного списка', color=VkKeyboardColor.NEGATIVE
)
keyboard_blocked.add_line()
keyboard_blocked.add_button(
    'Выход в главное меню', color=VkKeyboardColor.PRIMARY
)
keyboard_blocked = keyboard_blocked.get_keyboard()
