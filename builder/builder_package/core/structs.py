from dataclasses import dataclass, field

from builder_package.core.enums import IntentName, SlotName


@dataclass
class TSlot:
    name: str
    type: str
    description: str

    def is_refered_by(self, any_str: str) -> bool:
        return any_str.lower() == self.name.lower()

@dataclass
class TIntent:
    name: str
    description: str
    required_slots: list[SlotName]
    required_result_slots: list[SlotName]
    optional_slots: list[SlotName] = field(default_factory=list)
    optional_result_slots: list[SlotName] = field(default_factory=list)

    def is_refered_by(self, any_str: str) -> bool:
        return any_str.lower() == self.name.lower()

@dataclass
class TMessage:
    role: str
    content: str
    intent: IntentName
    timestamp: int
    slots: dict[SlotName, any] = field(default_factory=dict)
    

