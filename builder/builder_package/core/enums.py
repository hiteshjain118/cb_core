from enum import Enum

class SlotName(Enum):
    LOCATION = "location"
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"
    GUESTS = "guests"
    PRICE_RANGE = "price_range"
    PARKING = "parking"
    HOTEL_NAME = "hotel_name"
    HOTEL_ADDRESS = "hotel_address"
    HOTEL_PRICE = "hotel_price"
    HOTEL_RATING = "hotel_rating"
    HOTEL_AMENITIES = "hotel_amenities"
    HOTEL_POLICIES = "hotel_policies"
    HOTEL_IMAGES = "hotel_images"
    HOTEL_REVIEWS = "hotel_reviews"
    HOTEL_AVAILABILITY = "hotel_availability"
    HOTEL_BOOKINGS = "hotel_bookings"
    BOOKING_ID = "booking_id"
    BOOKING_TIME = "booking_time"
    BOOKING_STATUS = "booking_status"
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING_CANCELLATION_REASON = "cancellation_reason"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

    def __repr__(self) -> str:
        return self.__str__()

class IntentName(Enum):
    SEARCH_HOTELS = "search_hotels"
    GET_LISTING_DETAILS = "get_listing_details"
    BOOK_LISTING = "book_listing"
    GET_BOOKING = "get_booking"
    CANCEL_BOOKING = "cancel_booking"
    AGENT_BUILDING = "agent_building"
    RETRIEVER_BUILDING = "retriever_building"
    QB = "qb"
    OTHER = "other" 

    def __str__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}" 

    def __repr__(self) -> str:
        return self.__str__()