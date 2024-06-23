from datetime import datetime, timedelta
import unittest

from chat import _ChatState, Platform, PlatformError, Profile


class TestPlatform(unittest.TestCase):

    def setUp(self):
        self.platform = Platform()
        self.profile = Profile(
            name="name",
            surname="surname",
            patronymic="patronymic",
            city="city",
            date_of_birth=datetime.now(),
            position="position",
            work_experience=timedelta(42),
        )

    def _create(self):
        user = self.platform.create_user(self.profile)
        operator = self.platform.create_operator(self.profile)
        chat = self.platform.create_chat(user)
        return user, operator, chat

    def test_create_user(self):
        user = self.platform.create_user(self.profile)
        self.assertIn(user, self.platform.get_users())

    def test_create_operator(self):
        operator = self.platform.create_operator(self.profile)
        self.assertIn(operator, self.platform.get_operators())

    def test_get_free_operator(self):
        self.platform.create_operator(self.profile)
        free_operator = self.platform.get_free_operator()
        self.assertIsNotNone(free_operator)

        free_operator.is_free = False
        free_operator = self.platform.get_free_operator()
        self.assertIsNone(free_operator)

    def test_create_chat(self):
        user = self.platform.create_user(self.profile)
        chat = self.platform.create_chat(user)

        self.assertIn(chat, self.platform.get_chats())
        self.assertEqual(chat.state, _ChatState.OPENED)

    def test_send_message(self):
        user, operator, chat = self._create()
        self.platform.assign_operator_to_chat(operator, chat)

        self.platform.send_message(user, chat, "user")
        self.platform.send_message(operator, chat, "operator")

        self.assertEqual(chat.messages[0].sender, user)
        self.assertEqual(chat.messages[0].text, "user")
        self.assertEqual(chat.messages[1].sender, operator)
        self.assertEqual(chat.messages[1].text, "operator")

    def test_assign_operator_to_chat(self):
        _, operator, chat = self._create()
        self.platform.assign_operator_to_chat(operator, chat)

        self.assertEqual(chat.operator, operator)
        self.assertFalse(operator.is_free)
        self.assertEqual(chat.state, _ChatState.ASSIGNED)

    def test_assign_busy_operator_to_chat(self):
        _, operator, chat = self._create()
        operator.is_free = False

        with self.assertRaisesRegex(PlatformError, "оператор должен быть свободен"):
            self.platform.assign_operator_to_chat(operator, chat)

    def test_assign_operator_to_assigned_chat(self):
        _, operator, chat = self._create()
        self.platform.assign_operator_to_chat(operator, chat)
        new_operator = self.platform.create_operator(self.profile)

        with self.assertRaisesRegex(PlatformError, "оператор уже назначен на чат"):
            self.platform.assign_operator_to_chat(new_operator, chat)

    def test_close_chat(self):
        _, operator, chat = self._create()
        self.platform.assign_operator_to_chat(operator, chat)
        self.platform.close_chat(operator, chat)

        self.assertEqual(chat.state, _ChatState.CLOSED)
        self.assertTrue(operator.is_free)

    def test_close_chat_wrong_operator(self):
        _, operator, chat = self._create()
        self.platform.assign_operator_to_chat(operator, chat)
        new_operator = self.platform.create_operator(self.profile)

        with self.assertRaisesRegex(
            PlatformError, "только назначенный оператор может закрыть чат"
        ):
            self.platform.close_chat(new_operator, chat)

    def test_close_closed_chat(self):
        _, operator, chat = self._create()
        self.platform.assign_operator_to_chat(operator, chat)
        self.platform.close_chat(operator, chat)

        with self.assertRaisesRegex(PlatformError, "чат уже закрыт"):
            self.platform.close_chat(operator, chat)

    def test_rate_chat(self):
        user, operator, chat = self._create()
        self.platform.assign_operator_to_chat(operator, chat)
        self.platform.close_chat(operator, chat)
        self.platform.rate_chat(user, chat, 5)

        self.assertEqual(chat.csat, 5)
        self.assertEqual(chat.state, _ChatState.RATED)

    def test_rate_chat_wrong_user(self):
        _, operator, chat = self._create()
        self.platform.assign_operator_to_chat(operator, chat)
        self.platform.close_chat(operator, chat)
        new_user = self.platform.create_user(self.profile)

        with self.assertRaisesRegex(
            PlatformError, "только создатель чата может оценить чат"
        ):
            self.platform.rate_chat(new_user, chat, 5)

    def test_rate_rated_chat(self):
        user, operator, chat = self._create()
        self.platform.assign_operator_to_chat(operator, chat)
        self.platform.close_chat(operator, chat)
        self.platform.rate_chat(user, chat, 5)

        with self.assertRaisesRegex(PlatformError, "чат уже оценен"):
            self.platform.rate_chat(user, chat, 5)

    def test_rate_non_closed_chat(self):
        user, operator, chat = self._create()
        self.platform.assign_operator_to_chat(operator, chat)

        with self.assertRaisesRegex(
            PlatformError, "только закрытому чату можно поставить оценку"
        ):
            self.platform.rate_chat(user, chat, 5)

    def test_rate_chat_wrong_csat(self):
        user, operator, chat = self._create()
        self.platform.assign_operator_to_chat(operator, chat)
        self.platform.close_chat(operator, chat)

        for csat in [0, 6]:
            with self.assertRaisesRegex(PlatformError, "csat должен быть между 1 и 5"):
                self.platform.rate_chat(user, chat, csat)

    def test_get_user_chats(self):
        user, _, chat = self._create()
        user_chats = self.platform.get_user_chats(user.uuid)
        self.assertIn(chat, user_chats)

    def test_get_operator_chats(self):
        _, operator, chat = self._create()
        self.platform.assign_operator_to_chat(operator, chat)
        operator_chats = self.platform.get_operator_chats(operator.uuid)

        self.assertTrue(len(operator_chats), 1)
        self.assertIn(chat, operator_chats)


if __name__ == "__main__":
    unittest.main()
