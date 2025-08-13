from enum import Enum

class SGDSystemDialogAct(Enum):
    INFORM = "INFORM"  # Inform the value for a slot to the user.
    REQUEST = "REQUEST"  # Request the value of a slot from the user.
    CONFIRM = "CONFIRM"  # Confirm the value of a slot before making a transactional service call.
    OFFER = "OFFER"  # Offer a certain value for a slot to the user.
    NOTIFY_SUCCESS = "NOTIFY_SUCCESS"  # Inform the user that their request was successful.
    NOTIFY_FAILURE = "NOTIFY_FAILURE"  # Inform the user that their request failed.
    INFORM_COUNT = "INFORM_COUNT"  # Inform the number of items found that satisfy the user's request.
    OFFER_INTENT = "OFFER_INTENT"  # Offer a new intent to the user.
    REQ_MORE = "REQ_MORE"  # Asking the user if they need anything else.
    GOODBYE = "GOODBYE"  # End the dialogue.
    GREETING = "GREETING"  # Greet the user.

class SGDUserDialogAct(Enum):
    INFORM_INTENT = "INFORM_INTENT"  # Express the desire to perform a certain task to the system.
    NEGATE_INTENT = "NEGATE_INTENT"  # Negate the intent which has been offered by the system.
    AFFIRM_INTENT = "AFFIRM_INTENT"  # Agree to the intent which has been offered by the system.
    INFORM = "INFORM"  # Inform the value of a slot to the system.
    REQUEST = "REQUEST"  # Request the value of a slot from the system.
    AFFIRM = "AFFIRM"  # Agree to the system's proposition.
    NEGATE = "NEGATE"  # Deny the system's proposal.
    SELECT = "SELECT"  # Select a result being offered by the system.
    REQUEST_ALTS = "REQUEST_ALTS"  # Ask for more results besides the ones offered by the system.
    THANK_YOU = "THANK_YOU"  # Thank the system.
    GOODBYE = "GOODBYE"  # End the dialogue.
    GREETING = "GREETING"  # Greet the system.

    def is_refered_by(self, any_str: str) -> bool:
        return any_str.lower() == self.name.lower()