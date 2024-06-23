# sandbox V3

import argparse
from datetime import datetime, timedelta
import json
import random
import string
import sys
import time

from chat import Platform, Profile, ChatSerializer, UserSerializer


def random_str() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=random.randint(5, 10)))


def random_datetime() -> datetime:
    return datetime.fromtimestamp(random.randint(0, int(time.time())))


def random_timedelta() -> timedelta:
    return timedelta(random.randint(1, 100))


def generate_random_profile() -> Profile:
    return Profile(
        name=random_str().title(),
        surname=random_str().title(),
        patronymic=random_str().title(),
        city=random_str().title(),
        date_of_birth=random_datetime(),
        position=random_str(),
        work_experience=random_timedelta(),
    )


def uuid_generator() -> str:
    # используем рандом, чтобы можно было установить seed для воспроизводимой генерации данных
    return str(random.randint(1, sys.maxsize))


def create_platform(
    n_users: int = 100, n_operators: int = 50, n_chats: int = 100
) -> Platform:
    """возвращает Platform со сгенерированными данными"""

    # устанавливаем seed для воспроизводимости генерации данных
    random.seed(42)

    platform = Platform(uuid_generator=uuid_generator)

    for _ in range(n_users):
        platform.create_user(generate_random_profile())

    for _ in range(n_operators):
        platform.create_operator(generate_random_profile())

    users = platform.get_users()

    for _ in range(n_chats):
        user = random.choice(users)
        chat = platform.create_chat(user)
        platform.send_message(user, chat, f"Hello from user {user.profile.name}")

        operator = platform.get_free_operator()
        if operator:
            platform.assign_operator_to_chat(operator, chat)
            platform.send_message(
                operator, chat, f"Hello from operator {operator.profile.name}"
            )

            if random.randint(0, 1):
                platform.close_chat(operator, chat)
                if random.randint(0, 1):
                    platform.rate_chat(user, chat, random.randint(1, 5))

    return platform


def print_json(o, cls):
    print(json.dumps(o, cls=cls, indent=2))


if __name__ == "__main__":

    platform = create_platform()

    arg_parser = argparse.ArgumentParser(
        add_help=True, formatter_class=argparse.RawTextHelpFormatter
    )

    arg_parser.add_argument(
        "command",
        choices=[
            "chats",
            "user_chats",
            "operator_chats",
            "user_profiles",
            "operator_profiles",
        ],
        help="""
            chats - все чаты
            user_chats <user_uuid> - все чаты пользователя
            operator_chats <operator_uuid> - все чаты оператора
            user_profiles - профили пользователя
            operator_profiles - профили операторов
        """,
    )
    arg_parser.add_argument("uuid", nargs="?")
    args = arg_parser.parse_args()

    match args.command:
        case "chats":
            print_json(platform.get_chats(), cls=ChatSerializer)
        case "user_chats":
            if not args.uuid:
                raise Exception("требуются следующие аргументы: uuid")
            print_json(
                platform.get_user_chats(args.uuid),
                cls=ChatSerializer,
            )
        case "operator_chats":
            if not args.uuid:
                raise Exception("требуются следующие аргументы: uuid")

            print_json(platform.get_operator_chats(args.uuid), cls=ChatSerializer)
        case "user_profiles":
            print_json(platform.get_users(), cls=UserSerializer)
        case "operator_profiles":
            print_json(platform.get_operators(), cls=UserSerializer)
        case _:
            raise Exception("неверная команда")
