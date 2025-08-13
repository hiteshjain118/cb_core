from abc import ABC
from datetime import datetime
import json
import logging
from typing import Self
from builder_package.core.enums import SlotName
from builder_package.core.tod_types import IIntentServer, IntentServerInput, STMemory, TMessage
from builder_package.core.intents import IntentName, HOTEL_BOOKING_INTENTS
from builder_package.model_providers.imodel_provider import IModelProvider

from builder_package.core.sgd_dialog_state import SGDUserDialogAct
from builder_package.core.imodel_io import IModelOutputParser, IModelPrompt, ModelIO
import re

class IntentClassifierPrompt(IModelPrompt): 
    def __init__(self, st_memory: STMemory, user_turn: TMessage):
        self.st_memory = st_memory
        self.user_turn = user_turn

    def get_messages(self) -> list[dict]:
        return [
            {
                "role": "system",
                "content": self.get_system_prompt()
            },
            {
                "role": "user",
                "content": (
                    "Now analyze the conversation history and last user turn to determine the intent and dialog act.\n"
                    "Conversation history:\n"
                    f"{self.st_memory.conversation_summary()}\n"
                    "Last user turn:\n"
                    f"{self.user_turn.content}\n"
                    "Respond in JSONL format:\n"
                )
            }
        ]

    def get_system_prompt(self) -> str:
        prompt = (
            f"You are a user intent and dialog act classifier for a hotel booking system.\n"
            f"The system has the following intents:\n"
            f"{', '.join([intent.name for intent in IntentName])}\n"
            "The dialog act can be one of the following:\n"
            f"{', '.join([act.name for act in SGDUserDialogAct])}\n"
            "You also extract entities from the user turn. The entities are: \n"
            f"{', '.join([slot.value for slot in SlotName])}\n"
            "If entity is a date, it should be in the format YYYY-MM-DD. If entity is a time, it should be in the format HH:MM:SS.\n"
            "If entity is a datetime, it should be in the format YYYY-MM-DD HH:MM:SS.\n"
            "If entity was spelled incorrectly or partially spelled, try to correct it. If you are not sure, do not include it in the response.\n"
            "If there are no entities, do not include them in the response.\n"
            f"Current date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "Respond in JSONL format. If the user message has multiple intents, create a new line for each intent.\n"
            "All property names and string values must be enclosed in double quotes. Do not use single quotes. Do not include any text before or after the JSON.\n"
            "{"
            '    "intent1": "intent_name1",'
            '    "dialog_act1": "dialog_act_name1",'
            '    "entities1": {'
            '        "entity1": "entity_value1",'
            '        "entity2": "entity_value2"'
            '    }'
            "}"
            "{"
            '    "intent2": "intent_name2",'
            '    "dialog_act2": "dialog_act_name2",'
            '    "entities2": {'
            '        "entity3": "entity_value3",'
            '        "entity4": "entity_value4"'
            '    }'
            "}"
        )
        return prompt


class IntentClassifierOutputParser(IModelOutputParser):
    def __init__(self):
        self.intents: list[IntentName] = []
        self.dialog_acts: list[SGDUserDialogAct] = []
        self.slots: dict[SlotName, any] = {}
        self.error_reason: str = None

    def __str__(self) -> str:
        return (
            f"Intents: {[intent.name for intent in self.intents]}, "
            f"Dialog Acts: {[act.name for act in self.dialog_acts]}, "
            f"Slots: {{{', '.join(f'{slot.name}: {value}' for slot, value in self.slots.items())}}}, "
            f"Error: {self.error_reason}"
        )

    def search_for_intent(self, parsed_intent: str) -> IntentName:
        parsed_intent = parsed_intent.lower()
        for intent_enum in IntentName:
            if intent_enum.value.lower() == parsed_intent:
                return intent_enum
        return None
    
    def search_for_dialog_act(self, parsed_dialog_act: str) -> SGDUserDialogAct:
        parsed_dialog_act = parsed_dialog_act.lower()
        for act in SGDUserDialogAct:
            if act.value.lower() == parsed_dialog_act or act.name.lower() == parsed_dialog_act:
                return act
        return None
    
    def search_for_slot(self, parsed_slot: str) -> SlotName:
        parsed_slot = parsed_slot.lower()
        for slot_enum in SlotName:
            if slot_enum.value.lower() == parsed_slot:
                return slot_enum
        return None
    
    def set_success(self, response_content: str) -> Self:
        # Remove code block markers and language tags
        response_content = response_content.strip()
        if response_content.startswith("```"):
            response_content = re.sub(r"^```[a-zA-Z0-9]*\n?", "", response_content)
            response_content = re.sub(r"```$", "", response_content)
            response_content = response_content.strip()
        # Now handle JSONL (one JSON object per line)
        lines = [line for line in response_content.splitlines() if line.strip()]
        for line in lines:
            obj = json.loads(line)
            for key, value in obj.items():
                if "intent" in key and value is not None:
                    known_intent = self.search_for_intent(value)
                    if known_intent is not None:
                        self.intents.append(known_intent)
                elif "dialog_act" in key:
                    known_dialog_act = self.search_for_dialog_act(value)
                    if known_dialog_act is not None:
                        self.dialog_acts.append(known_dialog_act)
                else:
                    for sname, svalue in value.items():
                        known_slot = self.search_for_slot(sname)
                        if known_slot is not None:
                            self.slots[known_slot] = svalue
        logging.info(f"In intent classifier output parser: {self}")
        return self

    def set_error(self, error_reason: str) -> Self:
        self.error_reason = error_reason
        return self

    def get_output(self) -> dict:
        return {
            "is_successful": self.intents is not None,
            "intents": self.intents,
            "dialog_acts": self.dialog_acts,
            "error_reason": self.error_reason,
            "slots": self.slots
        }

class IntentClassifier():
    def __init__(self, model_provider: IModelProvider):
        self.model_provider = model_provider
    
    def classify_with_entities(self, input: IntentServerInput) -> dict:
        return self.model_provider.get_response(
            model_io=ModelIO(
                prompt=IntentClassifierPrompt(input.st_memory, input.user_turn),
                output_parser_class=IntentClassifierOutputParser,
                intent=None
            )
        ).get_output()
