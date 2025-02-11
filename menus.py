"""Imports Menus from associated menus.json file"""
from logmod import Log
from config import Config
L = Log()


class Menus(object):
    """Imports Menus from associated menus.json file"""

    def __init__(self, app):
        self.app = app
        menus_json = Config.load('menus.json')
        for key, value in menus_json.items():
            setattr(self, key, Menu(key, value))

    def get_menu(self, menu_name):
        """getter for view's menu

        Returns:
            boolean, attr
        """
        try:
            getattr(self, menu_name)
        except AttributeError:
            L.warning(
                "No Menu Exists by the name %s!!! Menu Retrieval Failed!",
                menu_name)
            return False
        else:
            return getattr(self, menu_name)

    def get_view_menu_items(self, menu_name):
        """Returns menu item list"""
        try:
            getattr(self, menu_name)
        except AttributeError:
            L.debug(
                "No Menu Exists by the name %s!!! Menu Retrieval Failed!",
                menu_name)
            return []
        else:
            menu = getattr(self, menu_name)
            return menu.items


class Menu(object):
    """Individual menu object for each view"""

    def __init__(self, menu_name, menu_items):
        # L.debug("Menu %s Initialized", menu_name)
        self.name = menu_name
        self.items = menu_items
        # L.debug("Menu Items: %s", self.items)
