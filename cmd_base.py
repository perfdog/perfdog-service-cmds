# coding: utf-8


class Command(object):
    def __init__(self, desc):
        self.desc = desc

    def get_desc(self):
        return self.desc

    # result -> quit | next_command | tuple(is_replace, next_command)
    def execute(self):
        raise NotImplementedError()


class Quit(Command):
    def __init__(self, desc=None):
        super(Quit, self).__init__(desc)

    def execute(self):
        pass


class Menu(Command):
    def __init__(self, commands, desc=None, quit_desc=None):
        super(Menu, self).__init__(desc)
        if quit_desc is None:
            quit_desc = 'Back to previous menu'
        self.commands = [Quit(quit_desc)]
        self.commands.extend(commands)

    def execute(self):
        for idx, command in enumerate(self.commands):
            print('%s.%s' % (idx, command.get_desc()))

        idx = int(input('Please select the operation to be performed: '))
        return self.commands[idx]


class Stack(object):
    def __init__(self, start_command):
        self.commands = [start_command]

    def push(self, command):
        self.commands.append(command)

    def pop(self):
        if len(self.commands) > 0:
            del self.commands[-1]

    def get_top(self):
        if len(self.commands) > 0:
            return self.commands[-1]
        else:
            return None

    def run(self):
        while len(self.commands) > 0:
            command = self.get_top()
            res = command.execute()

            is_replace = False
            if isinstance(res, tuple):
                is_replace, next_command = res
            else:
                next_command = res

            if is_replace:
                self.pop()
                self.push(next_command)
            else:
                if isinstance(next_command, Quit):
                    self.pop()
                else:
                    self.push(next_command)
