from dataclasses import dataclass, field
from typing import List

from builder_package.core.enums import SlotName
from builder_package.core.structs import TMessage


@dataclass
class STMemory:
    user_id: str
    conversation_history: List[TMessage] = field(default_factory=list)
    slots: dict[SlotName, any] = field(default_factory=dict)
    
    def add_message(self, message: TMessage) -> None:
        self.conversation_history.append(message)
        self.slots.update(message.slots)
    
    def get_conversation_history(self) -> List[TMessage]:
        return self.conversation_history

    def conversation_summary(self) -> str:
        return "\n".join([f"{message.role}: {message.content}" for message in self.conversation_history])

    def last_user_turn(self) -> tuple[TMessage, int]:
        for index in range(len(self.conversation_history) - 1, -1, -1):
            message = self.conversation_history[index]
            if message.role == "user":
                return message, index
        return None, -1

    def last_user_turn_index(self) -> int:
        return self.last_user_turn()[1]

    def conversation_history_before_last_user_turn(self) -> str:
        # Returns all messages up to and including the last bot turn before the last user turn
        last_user_idx = self.last_user_turn_index()
        if last_user_idx <= 0:
            return ""
        # Find the last bot message before the last user turn
        for idx in range(last_user_idx - 1, -1, -1):
            if self.conversation_history[idx].role == "bot":
                return "\n".join(f"{m.role}: {m.content}" for m in self.conversation_history[:idx+1])
        # If no bot message, return up to before last user turn
        return "\n".join(f"{m.role}: {m.content}" for m in self.conversation_history[:last_user_idx])

    def __str__(self) -> str:
        ret = f"User ID: {self.user_id} "
        ret += f"messages: {self.conversation_history} "
        ret += "slots: {"
        ret += ','.join([f"{s_enum.value}: {s_value}" for s_enum, s_value in self.slots.items()])
        ret += "}"

        return ret
    
