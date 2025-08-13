from builder_package.core.enums import SlotName, IntentName
from builder_package.core.structs import TIntent

HOTEL_BOOKING_INTENTS = {
    IntentName.SEARCH_HOTELS: TIntent(
        name=IntentName.SEARCH_HOTELS.value,
        description="search for hotels",
        required_slots=[SlotName.LOCATION, SlotName.CHECK_IN, SlotName.CHECK_OUT, SlotName.GUESTS],
        optional_slots=[SlotName.PRICE_RANGE, SlotName.PARKING],
        required_result_slots=[SlotName.HOTEL_NAME, SlotName.HOTEL_ADDRESS, SlotName.HOTEL_PRICE, SlotName.HOTEL_RATING],
        optional_result_slots=[SlotName.HOTEL_AMENITIES, SlotName.HOTEL_POLICIES, SlotName.HOTEL_IMAGES, SlotName.HOTEL_REVIEWS, SlotName.HOTEL_AVAILABILITY, SlotName.HOTEL_BOOKINGS]
    ),
    IntentName.GET_LISTING_DETAILS: TIntent(
        name=IntentName.GET_LISTING_DETAILS.value,
        description="get details of a hotel",
        required_slots=[SlotName.HOTEL_NAME],
        optional_slots=[],
        required_result_slots=[SlotName.HOTEL_NAME, SlotName.HOTEL_PRICE]
    ),
    IntentName.BOOK_LISTING: TIntent(
        name=IntentName.BOOK_LISTING.value,
        description="book a hotel",
        required_slots=[SlotName.HOTEL_NAME, SlotName.CHECK_IN, SlotName.CHECK_OUT, SlotName.GUESTS],
        optional_slots=[SlotName.PARKING],
        required_result_slots=[SlotName.BOOKING_STATUS]
    ),
    IntentName.GET_BOOKING: TIntent(
        name=IntentName.GET_BOOKING.value,
        description="get details of a booking",
        required_slots=[SlotName.BOOKING_ID],
        optional_slots=[],
        required_result_slots=[SlotName.BOOKING_ID, SlotName.BOOKING_TIME, SlotName.BOOKING_STATUS],
        optional_result_slots=[]
    ),
    IntentName.CANCEL_BOOKING: TIntent(
        name=IntentName.CANCEL_BOOKING.value,
        description="cancel a booking",
        required_slots=[SlotName.BOOKING_ID, SlotName.BOOKING_CANCELLATION_REASON],
        optional_slots=[],
        required_result_slots=[SlotName.BOOKING_ID, SlotName.BOOKING_STATUS],
        optional_result_slots=[]
    ),
    IntentName.OTHER: TIntent(
        name=IntentName.OTHER.value,
        description="other",
        required_slots=[],
        optional_slots=[],
        required_result_slots=[],
        optional_result_slots=[]
    ),
    IntentName.AGENT_BUILDING: TIntent(
        name=IntentName.AGENT_BUILDING.value,
        description="build an agent",
        required_slots=[],
        optional_slots=[],
        required_result_slots=[],
        optional_result_slots=[]
    ),
    IntentName.RETRIEVER_BUILDING: TIntent(
        name=IntentName.RETRIEVER_BUILDING.value,
        description="build a retriever",
        required_slots=[],
        optional_slots=[],
        required_result_slots=[],
        optional_result_slots=[]
    ),
    IntentName.QB: TIntent(
        name=IntentName.QB.value,
        description="query Quickbooks",
        required_slots=[],
        optional_slots=[],
        required_result_slots=[],
        optional_result_slots=[]
    )
}