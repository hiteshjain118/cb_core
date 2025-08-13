import unittest
from builder_package.core.memory import STMemory
from builder_package.core.structs import TMessage
from builder_package.core.enums import SlotName, IntentName

class TestSTMemory(unittest.TestCase):
    def setUp(self):
        self.memory = STMemory(user_id="user1")
        self.msg1 = TMessage(role="user", content="hello", intent=IntentName.SEARCH_HOTELS, slots={SlotName.LOCATION: "paris"})
        self.msg2 = TMessage(role="bot", content="hi there", intent=IntentName.OTHER, slots={})
        self.msg3 = TMessage(role="user", content="book hotel", intent=IntentName.BOOK_LISTING, slots={SlotName.HOTEL_NAME: "Hilton"})

    def test_add_message_and_get_conversation_history(self):
        self.memory.add_message(self.msg1)
        self.memory.add_message(self.msg2)
        self.assertEqual(self.memory.get_conversation_history(), [self.msg1, self.msg2])

    def test_conversation_summary(self):
        self.memory.add_message(self.msg1)
        self.memory.add_message(self.msg2)
        summary = self.memory.conversation_summary()
        self.assertIn("user: hello", summary)
        self.assertIn("bot: hi there", summary)



    def test_last_user_turn(self):
        self.memory.add_message(self.msg1)
        self.memory.add_message(self.msg2)
        self.memory.add_message(self.msg3)
        last_user_turn, idx = self.memory.last_user_turn()
        self.assertEqual(last_user_turn, self.msg3)
        self.assertEqual(idx, 2)

    def test_last_user_turn_index(self):
        self.memory.add_message(self.msg1)
        self.memory.add_message(self.msg2)
        self.memory.add_message(self.msg3)
        idx = self.memory.last_user_turn_index()
        self.assertEqual(idx, 2)

    def test_slots_update(self):
        self.memory.add_message(self.msg1)
        self.memory.add_message(self.msg3)
        self.assertIn(SlotName.LOCATION, self.memory.slots)
        self.assertIn(SlotName.HOTEL_NAME, self.memory.slots)
        self.assertEqual(self.memory.slots[SlotName.LOCATION], "paris")
        self.assertEqual(self.memory.slots[SlotName.HOTEL_NAME], "Hilton")

    def test_conversation_history_before_last_user_turn_no_bot(self):
        # Only user messages before last user turn
        self.memory.add_message(self.msg1)
        self.memory.add_message(self.msg3)
        result = self.memory.conversation_history_before_last_user_turn()
        # Should return only the first user message
        self.assertIn("user: hello", result)
        self.assertNotIn("book hotel", result)

    def test_conversation_history_before_last_user_turn_with_bot(self):
        # Add user, bot, user
        self.memory.add_message(self.msg1)
        self.memory.add_message(self.msg2)
        self.memory.add_message(self.msg3)
        result = self.memory.conversation_history_before_last_user_turn()
        # Should include up to and including the bot message
        self.assertIn("user: hello", result)
        self.assertIn("bot: hi there", result)
        self.assertNotIn("book hotel", result)

    def test_conversation_history_before_last_user_turn_multiple(self):
        # Add user, bot, user, bot, user
        msg4 = TMessage(role="bot", content="booking confirmed", intent=IntentName.OTHER, slots={})
        msg5 = TMessage(role="user", content="thanks", intent=IntentName.OTHER, slots={})
        self.memory.add_message(self.msg1)
        self.memory.add_message(self.msg2)
        self.memory.add_message(self.msg3)
        self.memory.add_message(msg4)
        self.memory.add_message(msg5)
        result = self.memory.conversation_history_before_last_user_turn()
        # Should include up to and including the last bot before last user
        self.assertIn("booking confirmed", result)
        self.assertNotIn("thanks", result)

if __name__ == "__main__":
    unittest.main() 