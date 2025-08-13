from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging
from typing import Any, Dict

from builder_package.core.enums import IntentName, SlotName
from builder_package.core.imodel_io import IModelPrompt, ModelIO
from builder_package.core.intents import HOTEL_BOOKING_INTENTS
from builder_package.core.memory import STMemory
from builder_package.core.structs import TMessage
    
@dataclass
class IntentServerInput:
    user_id: str
    user_turn: TMessage
    st_memory: STMemory = field(default_factory=STMemory)


class IIntentServer(ABC):

    def __init__(self, my_intent: IntentName):
        self.my_intent: IntentName = my_intent
        self.gathered_slots: dict[SlotName, any] = {}
        self.collab_servers: list[IntentName] = []

    def update_slots(self, slots: Dict[SlotName, any]) -> None:
        for slot_enum, slot_value in slots.items():
            if slot_enum in HOTEL_BOOKING_INTENTS[self.my_intent].required_slots:
                self.gathered_slots[slot_enum] = slot_value
            elif slot_enum in HOTEL_BOOKING_INTENTS[self.my_intent].optional_slots:
                self.gathered_slots[slot_enum] = slot_value
            else:
                logging.warning(f"Slot {slot_enum} is not a required or optional slot for intent {self.my_intent}")
    
    def can_continue_with_request(self) -> tuple[bool, list[str]]:
        missing_slots = self.missing_slots()
        return len(missing_slots) == 0, missing_slots
    
    def missing_slots(self) -> list[SlotName]:
        return [slot for slot in HOTEL_BOOKING_INTENTS[self.my_intent].required_slots 
                if slot not in self.gathered_slots]
        
    def serve(self, input: IntentServerInput) -> dict:
        logging.info(f"Serving intent: {self.my_intent.name} with input: {input}")
        self.update_slots(input.user_turn.slots)
        can_continue, missing_slots = self.can_continue_with_request()
        if can_continue:
            tools_output = self.run_tools(input)
            return self.use_tool_output(tools_output, input)
        else:
            return self._handle_missing_slots(missing_slots, input)
    
    def collab_gpt_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        return {
            intent.name: INTENT_REGISTRY.server(intent).gpt_tool_schema() 
                for intent in self.collab_servers
        }
    
    def gpt_tool_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.my_intent.name,
                "description": self.my_intent.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        slot.name: slot.type for slot in self.my_intent.required_slots + self.my_intent.optional_slots
                    },
                    "required": [slot.name for slot in self.my_intent.required_slots]
                }
            }
        }
    
    def validate_slots(self, slots: Dict[SlotName, any]) -> bool:
        # not implemented right now
        # use case is when user provides a bad booking id, that slot 
        # shouldn't be accepted by the server and assistant should respond right away 
        # with the error instead of waiting for all slots before invoking the 
        # intent server.
        return True
    
    @abstractmethod
    def run_tools(self, input: IntentServerInput) -> dict:
        pass
    
    @abstractmethod
    def use_tool_output(self, tools_output: dict, input: IntentServerInput) -> dict:
        pass
    
    @abstractmethod
    def _handle_missing_slots(
        self, 
        missing_slots: list[SlotName], 
        input: IntentServerInput
    ) -> dict:
        pass

class IntentRegistry:
    intents_to_handlers: dict[IntentName, IIntentServer]= {}

    def register(self, intent: IntentName, server: IIntentServer) -> None:
        self.intents_to_handlers[intent] = server

    def server(self, intent: IntentName) -> IIntentServer:
        return self.intents_to_handlers[intent]

INTENT_REGISTRY = IntentRegistry()

# class IRetreiver(ABC):
#     def get_slot_value(self, slot: SlotName, **kwargs) -> any:
#         pass
