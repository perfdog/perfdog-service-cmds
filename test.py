# coding: utf-8

from stub import init, de_init

from cmd_base import Stack, Menu
from cmds import get_top_menus


def run():
    Stack(Menu(get_top_menus(), quit_desc='退出')).run()


def main():
    init()
    run()
    de_init()


if __name__ == '__main__':
    main()
