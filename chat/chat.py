from dataclasses import dataclass, field, asdict, is_dataclass
import enum
from datetime import datetime, timedelta
import json
import random
from typing import Callable
import uuid


# датаклассы используются только ради дефолтных конструкторов
@dataclass
class Profile:
    name: str
    surname: str
    patronymic: str
    city: str
    date_of_birth: datetime
    position: str
    work_experience: timedelta


@dataclass
class _BaseUser:
    uuid: str
    profile: Profile


@dataclass
class _Operator(_BaseUser):
    is_free: bool = True


@dataclass
class _User(_BaseUser):
    pass


@dataclass
class _Message:
    sender: _BaseUser
    text: str
    datetime: datetime


class _ChatState(enum.Enum):
    OPENED = enum.auto()
    ASSIGNED = enum.auto()
    CLOSED = enum.auto()
    RATED = enum.auto()


@dataclass
class _Chat:
    user: _User
    operator: _Operator | None = None
    csat: int | None = None
    messages: list[_Message] = field(default_factory=list)
    state: _ChatState = _ChatState.OPENED


UUIDGenerator = Callable[[], str]


def default_uuid_generator() -> str:
    return uuid.uuid4().hex


class PlatformError(Exception):
    pass


class Platform:
    _uuid_generator: UUIDGenerator
    _users: list[_User]
    _operators: list[_Operator]
    _chats: list[_Chat]

    def __init__(self, uuid_generator: UUIDGenerator = default_uuid_generator):
        self._uuid_generator = uuid_generator
        self._users = []
        self._operators = []
        self._chats = []

    def create_user(self, profile: Profile) -> _User:
        """создает и возвращает нового пользователя"""
        user = _User(uuid=self._uuid_generator(), profile=profile)
        self._users.append(user)
        return user

    def create_operator(self, profile: Profile) -> _Operator:
        """создает и возвращает нового оператора"""
        operator = _Operator(uuid=self._uuid_generator(), profile=profile)
        self._operators.append(operator)
        return operator

    def create_chat(self, user: _User) -> _Chat:
        """создает и возвращает новый чат"""
        chat = _Chat(user=user)
        self._chats.append(chat)
        return chat

    def get_free_operator(self) -> _Operator | None:
        """возвращает случайного свободного оператора или None"""
        free_operators = [operator for operator in self._operators if operator.is_free]
        return random.choice(free_operators) if free_operators else None

    def send_message(self, sender: _BaseUser, chat: _Chat, text: str):
        """отправляет сообщение от заданного пользователя с заданным текстом в чат"""
        if not (sender is chat.user or sender is chat.operator):
            raise PlatformError(
                "только создатель чата и назначенный оператор могут отправить сообщение в чат"
            )

        chat.messages.append(
            _Message(
                sender=sender,
                text=text,
                datetime=datetime.now(),
            )
        )

    def assign_operator_to_chat(self, operator: _Operator, chat: _Chat):
        """назначает оператора на чат"""
        if not operator.is_free:
            raise PlatformError("оператор должен быть свободен")

        if chat.state != _ChatState.OPENED:
            raise PlatformError("оператор уже назначен на чат")

        operator.is_free = False
        chat.operator = operator
        chat.state = _ChatState.ASSIGNED

    def close_chat(self, operator: _Operator, chat: _Chat):
        """закрывает чат"""
        if operator is not chat.operator:
            raise PlatformError("только назначенный оператор может закрыть чат")

        if chat.state == _ChatState.CLOSED:
            raise PlatformError("чат уже закрыт")

        chat.state = _ChatState.CLOSED
        operator.is_free = True

    def rate_chat(self, user: _User, chat: _Chat, csat: int):
        """ставит оценку чату"""
        if user is not chat.user:
            raise PlatformError("только создатель чата может оценить чат")

        if chat.state == _ChatState.RATED:
            raise PlatformError("чат уже оценен")

        if chat.state != _ChatState.CLOSED:
            raise PlatformError("только закрытому чату можно поставить оценку")

        if not (1 <= csat <= 5):
            raise PlatformError("csat должен быть между 1 и 5")

        chat.csat = csat
        chat.state = _ChatState.RATED

    def get_chats(self) -> list[_Chat]:
        """возвращает все чаты"""
        return self._chats

    def get_operators(self) -> list[_Operator]:
        """возвращает всех операторов"""
        return self._operators

    def get_users(self) -> list[_User]:
        """возвращает всех пользователей"""
        return self._users

    def get_user_chats(self, uuid: str) -> list[_Chat]:
        """возвращает чаты пользователя по uuid"""
        return [chat for chat in self._chats if chat.user.uuid == uuid]

    def get_operator_chats(self, uuid: str) -> list[_Chat]:
        """возвращает чаты оператора по uuid"""
        return [
            chat for chat in self._chats if chat.operator and chat.operator.uuid == uuid
        ]


class ChatSerializer(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            for m in o.messages:
                m.sender = m.sender.uuid
            o.user = o.user.uuid
            o.operator = o.operator.uuid if o.operator else None
            d = asdict(o)
            return {k: d[k] for k in ["user", "operator", "csat", "messages"]}

        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, timedelta):
            return int(o.total_seconds())

        if isinstance(o, _ChatState):
            return o.name

        return json.JSONEncoder.default(self, o)


class UserSerializer(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            d = asdict(o)
            return {k: d[k] for k in ["uuid", "profile"]}

        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, timedelta):
            return str(o)

        return json.JSONEncoder.default(self, o)
