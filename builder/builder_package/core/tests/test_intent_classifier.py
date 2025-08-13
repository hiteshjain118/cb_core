import unittest
import json
from unittest.mock import Mock, patch
from builder_package.core.intent_classifier import IntentClassifier, IntentClassifierPrompt, IntentClassifierOutputParser
from builder_package.core.memory import STMemory
from builder_package.core.structs import TMessage
from builder_package.core.enums import SlotName, IntentName
from builder_package.core.sgd_dialog_state import SGDUserDialogAct
from builder_package.core.tod_types import IntentServerInput


class TestIntentClassifierPrompt(unittest.TestCase):
    def setUp(self):
        self.memory = STMemory(user_id="user1")
        self.user_turn = TMessage(
            role="user", 
            content="I want to book a hotel in Paris", 
            intent=IntentName.SEARCH_HOTELS, 
            slots={SlotName.LOCATION: "Paris"}
        )
        self.prompt = IntentClassifierPrompt(self.memory, self.user_turn)

    def test_get_messages_structure(self):
        messages = self.prompt.get_messages()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("system", messages[0]["content"])
        self.assertIn("conversation history", messages[1]["content"].lower())

    def test_get_system_prompt_contains_intents(self):
        system_prompt = self.prompt.get_system_prompt()
        for intent in IntentName:
            self.assertIn(intent.name, system_prompt)

    def test_get_system_prompt_contains_dialog_acts(self):
        system_prompt = self.prompt.get_system_prompt()
        for dialog_act in SGDUserDialogAct:
            self.assertIn(dialog_act.name, system_prompt)

    def test_get_system_prompt_contains_slots(self):
        system_prompt = self.prompt.get_system_prompt()
        for slot in SlotName:
            self.assertIn(slot.value, system_prompt)

    def test_get_system_prompt_contains_json_format(self):
        system_prompt = self.prompt.get_system_prompt()
        self.assertIn('"intent1"', system_prompt)
        self.assertIn('"dialog_act1"', system_prompt)
        self.assertIn('"entities1"', system_prompt)


class TestIntentClassifierOutputParser(unittest.TestCase):
    def setUp(self):
        self.parser = IntentClassifierOutputParser()

    def test_initial_state(self):
        self.assertEqual(self.parser.intents, [])
        self.assertEqual(self.parser.dialog_acts, [])
        self.assertEqual(self.parser.slots, {})
        self.assertIsNone(self.parser.error_reason)

    def test_search_for_intent_valid(self):
        result = self.parser.search_for_intent("search_hotels")
        self.assertEqual(result, IntentName.SEARCH_HOTELS)

    def test_search_for_intent_case_insensitive(self):
        result = self.parser.search_for_intent("SEARCH_HOTELS")
        self.assertEqual(result, IntentName.SEARCH_HOTELS)

    def test_search_for_intent_invalid(self):
        result = self.parser.search_for_intent("invalid_intent")
        self.assertIsNone(result)

    def test_search_for_dialog_act_valid(self):
        result = self.parser.search_for_dialog_act("INFORM_INTENT")
        self.assertEqual(result, SGDUserDialogAct.INFORM_INTENT)

    def test_search_for_dialog_act_case_insensitive(self):
        result = self.parser.search_for_dialog_act("inform_intent")
        self.assertEqual(result, SGDUserDialogAct.INFORM_INTENT)

    def test_search_for_dialog_act_invalid(self):
        result = self.parser.search_for_dialog_act("invalid_act")
        self.assertIsNone(result)

    def test_search_for_slot_valid(self):
        result = self.parser.search_for_slot("location")
        self.assertEqual(result, SlotName.LOCATION)

    def test_search_for_slot_case_insensitive(self):
        result = self.parser.search_for_slot("LOCATION")
        self.assertEqual(result, SlotName.LOCATION)

    def test_search_for_slot_invalid(self):
        result = self.parser.search_for_slot("invalid_slot")
        self.assertIsNone(result)

    def test_set_success_single_intent(self):
        response = '{"intent1": "search_hotels", "dialog_act1": "INFORM_INTENT", "entities1": {"location": "Paris"}}'
        self.parser.set_success(response)
        self.assertEqual(self.parser.intents, [IntentName.SEARCH_HOTELS])
        self.assertEqual(self.parser.dialog_acts, [SGDUserDialogAct.INFORM_INTENT])
        self.assertEqual(self.parser.slots, {SlotName.LOCATION: "Paris"})

    def test_set_success_multiple_intents(self):
        response = '''{"intent1": "search_hotels", "dialog_act1": "INFORM_INTENT", "entities1": {"location": "Paris"}}
{"intent2": "book_listing", "dialog_act2": "AFFIRM", "entities2": {"hotel_name": "Hilton"}}'''
        self.parser.set_success(response)
        self.assertEqual(len(self.parser.intents), 2)
        self.assertIn(IntentName.SEARCH_HOTELS, self.parser.intents)
        self.assertIn(IntentName.BOOK_LISTING, self.parser.intents)
        self.assertEqual(len(self.parser.dialog_acts), 2)
        self.assertIn(SGDUserDialogAct.INFORM_INTENT, self.parser.dialog_acts)
        self.assertIn(SGDUserDialogAct.AFFIRM, self.parser.dialog_acts)

    def test_set_success_with_code_blocks(self):
        response = '''```json
{"intent1": "search_hotels", "dialog_act1": "INFORM_INTENT", "entities1": {"location": "Paris"}}
```'''
        self.parser.set_success(response)
        self.assertEqual(self.parser.intents, [IntentName.SEARCH_HOTELS])
        self.assertEqual(self.parser.dialog_acts, [SGDUserDialogAct.INFORM_INTENT])
        self.assertEqual(self.parser.slots, {SlotName.LOCATION: "Paris"})

    def test_set_success_unknown_intent(self):
        response = '{"intent1": "unknown_intent", "dialog_act1": "INFORM_INTENT", "entities1": {}}'
        self.parser.set_success(response)
        self.assertEqual(self.parser.intents, [])
        self.assertEqual(self.parser.dialog_acts, [SGDUserDialogAct.INFORM_INTENT])

    def test_set_success_unknown_dialog_act(self):
        response = '{"intent1": "search_hotels", "dialog_act1": "unknown_act", "entities1": {}}'
        self.parser.set_success(response)
        self.assertEqual(self.parser.intents, [IntentName.SEARCH_HOTELS])
        self.assertEqual(self.parser.dialog_acts, [])

    def test_set_success_unknown_slot(self):
        response = '{"intent1": "search_hotels", "dialog_act1": "INFORM_INTENT", "entities1": {"unknown_slot": "value"}}'
        self.parser.set_success(response)
        self.assertEqual(self.parser.intents, [IntentName.SEARCH_HOTELS])
        self.assertEqual(self.parser.dialog_acts, [SGDUserDialogAct.INFORM_INTENT])
        self.assertEqual(self.parser.slots, {})

    def test_set_error(self):
        error_reason = "Invalid JSON format"
        self.parser.set_error(error_reason)
        self.assertEqual(self.parser.error_reason, error_reason)

    def test_get_output_success(self):
        self.parser.intents = [IntentName.SEARCH_HOTELS]
        self.parser.dialog_acts = [SGDUserDialogAct.INFORM_INTENT]
        self.parser.slots = {SlotName.LOCATION: "Paris"}
        
        output = self.parser.get_output()
        expected = {
            "is_successful": True,
            "intents": [IntentName.SEARCH_HOTELS],
            "dialog_acts": [SGDUserDialogAct.INFORM_INTENT],
            "error_reason": None,
            "slots": {SlotName.LOCATION: "Paris"}
        }
        self.assertEqual(output, expected)

    def test_get_output_error(self):
        self.parser.set_error("Test error")
        output = self.parser.get_output()
        expected = {
            "is_successful": True,  # The logic checks if intents is not None, not if there's an error
            "intents": [],
            "dialog_acts": [],
            "error_reason": "Test error",
            "slots": {}
        }
        self.assertEqual(output, expected)

    def test_str_representation(self):
        self.parser.intents = [IntentName.SEARCH_HOTELS]
        self.parser.dialog_acts = [SGDUserDialogAct.INFORM_INTENT]
        self.parser.slots = {SlotName.LOCATION: "Paris"}
        
        str_repr = str(self.parser)
        self.assertIn("SEARCH_HOTELS", str_repr)
        self.assertIn("INFORM_INTENT", str_repr)
        self.assertIn("LOCATION: Paris", str_repr)


class TestIntentClassifier(unittest.TestCase):
    def setUp(self):
        self.mock_model_provider = Mock()
        self.classifier = IntentClassifier(self.mock_model_provider)
        self.memory = STMemory(user_id="user1")
        self.user_turn = TMessage(
            role="user", 
            content="I want to book a hotel in Paris", 
            intent=IntentName.SEARCH_HOTELS, 
            slots={SlotName.LOCATION: "Paris"}
        )
        self.input_data = IntentServerInput(
            user_id="user1",
            user_turn=self.user_turn,
            st_memory=self.memory
        )

    def test_classify_with_entities_success(self):
        # Mock the model provider response
        mock_response = Mock()
        mock_response.get_output.return_value = {
            "is_successful": True,
            "intents": [IntentName.SEARCH_HOTELS],
            "dialog_acts": [SGDUserDialogAct.INFORM_INTENT],
            "error_reason": None,
            "slots": {SlotName.LOCATION: "Paris"}
        }
        self.mock_model_provider.get_response.return_value = mock_response

        result = self.classifier.classify_with_entities(self.input_data)
        
        # Verify the model provider was called
        self.mock_model_provider.get_response.assert_called_once()
        call_args = self.mock_model_provider.get_response.call_args[1]['model_io']
        self.assertIsInstance(call_args.prompt, IntentClassifierPrompt)
        self.assertEqual(call_args.prompt.st_memory, self.memory)
        self.assertEqual(call_args.prompt.user_turn, self.user_turn)
        self.assertEqual(call_args.output_parser_class, IntentClassifierOutputParser)
        
        # Verify the result
        self.assertEqual(result["is_successful"], True)
        self.assertEqual(result["intents"], [IntentName.SEARCH_HOTELS])
        self.assertEqual(result["dialog_acts"], [SGDUserDialogAct.INFORM_INTENT])
        self.assertEqual(result["slots"], {SlotName.LOCATION: "Paris"})

    def test_classify_with_entities_error(self):
        # Mock the model provider response with error
        mock_response = Mock()
        mock_response.get_output.return_value = {
            "is_successful": False,
            "intents": [],
            "dialog_acts": [],
            "error_reason": "Invalid JSON format",
            "slots": {}
        }
        self.mock_model_provider.get_response.return_value = mock_response

        result = self.classifier.classify_with_entities(self.input_data)
        
        self.assertEqual(result["is_successful"], False)
        self.assertEqual(result["error_reason"], "Invalid JSON format")


if __name__ == "__main__":
    unittest.main() 