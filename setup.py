# use after git cloning.
import os
import getpass
from pathlib import Path

# required_dirs = [
#     'xlsx',
#     'docx'
# ]
# required_files = [
#     'users.yml',
#     'ignored.txt'
# ]

def create():
    # for directory in required_dirs:
    #     if not os.path.exists(directory):
    #         os.makedirs(directory)
    #         print(f"Создана папка: {directory}")
    # for file in required_files:
    #     path = Path(file)
    #     if not path.exists():
    #         path.touch()
    #         print(f"Создан файл: {file}")

    if not os.path.exists('token.txt'):
        token=getpass.getpass("введи токен приложения VK:\n")
        with open ('token.txt', 'w') as f:
            f.write(token)
        print(f"токен успешно записан")


if __name__ == "__main__":
    create()
    print("установка успешно завершена!")