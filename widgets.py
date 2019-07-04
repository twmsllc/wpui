# -*- coding: utf-8 -*-
"""Contains classes of custom widgets
or shortcuts for frequently used urwid
widgets
"""
import urwid as U
from settings import Settings
from logmod import Log
S = Settings()
L = Log()
PYTHONIOENCODING = "utf-8"
class WpConfigValueEdit(U.Edit):
    """Class of Edit widgets for changing WpConfig Values"""
    def __init__(self, directive_name=''):
        super(WpConfigValueEdit, self).__init__()
        self.directive_name = directive_name
    def keypress(self, size, key):
        if key != 'enter':
            return super(WpConfigValueEdit, self).keypress(size, key)
        self = U.AttrMap(self, 'blue')
        L.debug(
            'Directive: %s, Value: %s',
            self.original_widget.directive_name,
            self.original_widget.get_edit_text())

class BoxButton(U.WidgetWrap):
    """Custom Button that appears with text and a line'd border"""
    _border_char = u'─'
    def __init__(self, label, on_press=None, user_data=None, enabled=True):
        padding_size = 2
        border = self._border_char * (len(label) + padding_size * 2)
        self.cursor_position = len(border) + padding_size
        self.top = u'┌' + border + u'┐\n'
        self.middle = u'│  ' + label + u'  │\n'
        self.bottom = u'└' + border + u'┘'
        self.on_press_action = on_press
        self.on_press_user_data = user_data
        self.enabled = enabled
        # self.widget = urwid.Text([self.top, self.middle, self.bottom])
        self.widget = U.Pile([
            U.Text(self.top[:-1], align='center'),
            U.Text(self.middle[:-1], align='center'),
            U.Text(self.bottom, align='center'),
        ])

        self.widget = U.AttrMap(self.widget, 'body', 'highlight')

        # self.widget = urwid.Padding(self.widget, 'center')
        # self.widget = urwid.Filler(self.widget)

        # here is a lil hack: use a hidden button for evt handling
        #debug('on_press: %s, user_data: %s', )
        self._hidden_btn = U.Button('hidden %s' % label, on_press, user_data)

        super(BoxButton, self).__init__(self.widget)

    def selectable(self):
        """Defines button as selectable"""
        if self.enabled:
            return True
        else:
            return False
    def disable(self):
        """disables button"""
        self.enabled = False
    def enable(self):
        """enables button"""
        self.enabled = True

    def keypress(self, *args, **kw):
        """passes keypress to button"""
        return self._hidden_btn.keypress(*args, **kw)

    def mouse_event(self, *args, **kw):
        """passes mouse events to button"""
        return self._hidden_btn.mouse_event(*args, **kw)
class CustomWidgets(object):
    """Collection of custom widget getters"""
    def __init__(self):
        L.debug("CustomWidgets Initialized")
        self.subtitle = None
    def get_blank_box(self):
        """returns a blank box type widget"""
        return U.Filler(self.get_blank_flow())
    def get_blank_flow(self):
        """returns a blank flow type widget"""
        return self.get_text('body', '', 'center')
    def get_edit(self,edit_text, caption='', align=''):
        """returns an edit widget"""
        return U.Edit(caption=caption, edit_text=edit_text, align=align)
    def get_text(self, text_format, text_string, alignment, **kwargs):
        """returns a text flow type widget"""
        return U.Text((text_format, text_string), align=alignment, wrap='space', **kwargs)
    def get_div(self, div_char=' '):
        """returns a divider flow type widget"""
        return U.Divider(div_char=div_char, top=0, bottom=0)
    def get_header(self, name, title, subtitle):
        """returns a frame header widget"""
        L.debug("Title: %s,  Name:, %s, Subtitle: %s", title, name, subtitle)
        if title:
            title = self.get_text('bold', title, 'center')
        else:
            title = self.get_text('bold', S.display['title'], 'center')
        if subtitle:
            self.subtitle = self.get_text('bold', subtitle, 'center')
        else:
            L.debug("Passed Subtitle: %s, Settings Subtitle:%s", subtitle, S.display['subtitle'])
            self.subtitle = self.get_text('bold', S.display['subtitle'], 'center')
        title_map = U.AttrMap(title, 'bold')
        div_map = U.AttrMap(self.get_div(), 'body')
        if self.subtitle:
            subtitle_map = U.AttrMap(self.subtitle, 'bold')
            return U.Pile((title_map, subtitle_map, div_map), focus_item=None)
        else:
            return U.Pile((title_map, div_map), focus_item=None)
    def get_footer(self, name, app):
        """returns a frame footer widget"""
        menu = app.menus.get_menu(name)
        menu_items = menu.items
        menu_grid_items = []
        for item in menu_items:
            if len(item) == 3:
                menu_grid_items.append(
                    BoxButton(
                        item[0],
                        on_press=app.views.activate,
                        user_data=(item[1], item[2])))
            else:
                menu_grid_items.append(
                    BoxButton(
                        item[0],
                        on_press=app.views.activate,
                        user_data=(item[1])))
        item_widths = []
        for item in menu_grid_items:
            item_widths.append(item.cursor_position)
        item_widths.sort()
        if item_widths:
            menu_grid = U.GridFlow(menu_grid_items, item_widths[-1], 0, 0, 'center')
        else:
            menu_grid = self.get_div()
        legend_items = []
        for legend in S.display['legend']:
            legend_items.append(self.get_text('bold', legend[0], 'center'))
        legend_grid = U.GridFlow(legend_items, 21, 0, 0, 'center')
        legend_grid_map = U.AttrMap(legend_grid, 'bold')
        legend_items = []
        for legend in S.display['legend']:
            legend_items.append(self.get_text('highlight', legend[1], 'center'))
        legend_items_grid = U.GridFlow(legend_items, 21, 0, 0, 'center')
        legend_items_map = U.AttrMap(legend_items_grid, 'highlight')
        return U.Pile([menu_grid, legend_grid_map, legend_items_map])
    def get_col_row(self, items, dividechars=None, **kwargs):
        """Creates a single row of columns

        Arguments:
            items {list} -- List of widgets, each item forming one column.
                             Items may be tuples containing width specs

        Returns:
            [urwid.Column] -- An urwid.Columns object
            FLOW / BOX WIDGET
        """
        L.debug("kwargs: %s", kwargs)
        if dividechars:
            return U.Columns(
                items,
                dividechars=dividechars,
                focus_column=None,
                min_width=1,
                box_columns=None)
        else:
            return U.Columns(
                items,
                dividechars=S.display['col_div_chars'],
                focus_column=None,
                min_width=1,
                box_columns=None)
    def get_line_box(
            self, contents, title,
            tlcorner='┌', tline='─',
            lline='│', trcorner='┐',
            blcorner='└', rline='│',
            bline='─', brcorner='┘',
            **kwargs):
        """ Creates a SimpleFocusListWalker using contents as the list,
            adds a centered title, and draws a box around it. If the contents
            are not a list of widgets, then set content_list to False.

            The character that is used to draw the border can
            be adjusted with the following keyword arguments:
                tlcorner,tline,trcorner,blcorner,rline,bline,brcorner

        Arguments:
            contents {widget} -- an original_widget, no widget lists -
            title {string} -- Title String

        Keyword Argumnts:
            content_list -- If true, the value of contents must be a list of widgets
                            If false, the value must be a single widget to be used as
                            original_widget -- default{False}

        Returns:
            urwid.LineBox -- urwid.LineBox object
            FLOW / BOX WIDGET
        """
        L.debug("kwargs: %s", kwargs)
        linebox = U.LineBox(
            contents,
            title=str(title),
            title_align='center',
            tlcorner=tlcorner,
            tline=tline,
            lline=lline,
            trcorner=trcorner,
            blcorner=blcorner,
            rline=rline,
            bline=bline,
            brcorner=brcorner)
        return U.AttrMap(linebox, 'boxborder')
    def get_list_box(self, contents):
        """Creates a ListBox using a SimpleFocusListWalker, with the contents
           being a list of widgets

        Arguments:
            contents {list} -- list of widgets

        Returns:
            list -- [0]: urwid.ListBox
                    [1]: urwid.SimpleFocusListWalker - Access this to make changes to the list
                               which the SimpleFocusListWalker will follow.
        BOX WIDGET
        """
        #debug('Started getListBox: %s', contents)
        walker = U.SimpleFocusListWalker(contents)
        list_box = U.ListBox(walker)
        return [list_box, walker]
    def centered_list_box(self, contents, title, list_height, **kwargs):
        """returns a list/line box that is screen centered"""
        L.debug("kwargs: %s", kwargs)
        filler = U.Filler(contents, height=list_height)
        inside_col = self.get_col_row([
            self.get_blank_box(),
            ('weight', 2, filler),
            self.get_blank_box()])
        #debug('centeredListLineBox filler.sizing(): %s', filler.sizing())
        line_box = self.get_line_box(inside_col, title)
        #debug('centeredListLineBox listBox: %s', contents)
        outsidefiller = U.Filler(line_box, height=list_height)
        outside_col = self.get_col_row([
            self.get_blank_box(),
            ('weight', 2, outsidefiller),
            self.get_blank_box()])
        return U.Filler(outside_col, height=list_height)
