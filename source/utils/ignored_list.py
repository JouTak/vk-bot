class IgnoredList:
    def __init__(self):
        self.ignored = set()

    def add(self, uid):
        if uid not in self.ignored:
            self.ignored.add(uid)
            print(f'Пользователь {uid} добавлен в игнор.')
        else:
            print(f'Пользователь {uid} уже в игноре.')

    def remove(self, uid):
        if uid in self.ignored:
            self.ignored.remove(uid)
            print(f'Пользователь {uid} удалён из игнора.')
        else:
            print(f'Пользователь {uid} не найден в списке игнорируемых.')

    def is_ignored(self, uid):
        return uid in self.ignored

    def clear(self):
        self.ignored.clear()
        self.info('Список игнорируемых пользователей очищен.')

    def save_to_file(self):
        try:
            with open('ignored.txt', 'w+') as file:
                file.write('\n'.join(map(str, self.ignored)))
            print(f'Список игнорируемых сохранён.')
        except Exception as e:
            print(f'Ошибка при сохранении: {e}')

    def load_from_file(self):
        try:
            with open('ignored.txt', 'r') as file:
                self.ignored = set(map(lambda x: int(x.strip()), file.readlines()))
            return (f'Список игнорируемых загружен.')
        except Exception as e:
            print(f'Ошибка при загрузке: {e}')