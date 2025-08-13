
from builder_package.core.enums import SlotName
from builder_package.core.structs import TSlot

SLOTS = {
    SlotName.LOCATION: TSlot(
        name=SlotName.LOCATION.value,
        type="str",
        description="location of the hotel"
    ),
    SlotName.CHECK_IN: TSlot(
        name=SlotName.CHECK_IN.value,
        type="datetime",
        description="check-in date"
    ),
    SlotName.CHECK_OUT: TSlot(
        name=SlotName.CHECK_OUT.value,
        type="datetime",
        description="check-out date"
    ),
    SlotName.GUESTS: TSlot(
        name=SlotName.GUESTS.value,
        type="int",
        description="number of guests"
    ),
    SlotName.PRICE_RANGE: TSlot(
        name=SlotName.PRICE_RANGE.value,
        type="list[int]",
        description="price range of the hotel"
    ),
    SlotName.PARKING: TSlot(
        name=SlotName.PARKING.value,
        type="bool",
        description="parking availability"
    ),
    SlotName.HOTEL_NAME: TSlot(
        name=SlotName.HOTEL_NAME.value,
        type="str",
        description="name of the hotel"
    ),
    SlotName.HOTEL_ADDRESS: TSlot(
        name=SlotName.HOTEL_ADDRESS.value,
        type="str",
        description="address of the hotel"
    ),
    SlotName.HOTEL_PRICE: TSlot(
        name=SlotName.HOTEL_PRICE.value,
        type="float",
        description="price of the hotel"
    ),
    SlotName.HOTEL_RATING: TSlot(
        name=SlotName.HOTEL_RATING.value,
        type="float",
        description="rating of the hotel"
    ),
    SlotName.HOTEL_AMENITIES: TSlot(
        name=SlotName.HOTEL_AMENITIES.value,
        type="list[str]",
        description="amenities of the hotel"
    ),
    SlotName.HOTEL_POLICIES: TSlot(
        name=SlotName.HOTEL_POLICIES.value,
        type="list[str]",
        description="policies of the hotel"
    ),
    SlotName.HOTEL_IMAGES: TSlot(
        name=SlotName.HOTEL_IMAGES.value,
        type="list[str]",
        description="images of the hotel"
    ),
    SlotName.HOTEL_REVIEWS: TSlot(
        name=SlotName.HOTEL_REVIEWS.value,
        type="list[str]",
        description="reviews of the hotel"
    ),
    SlotName.HOTEL_AVAILABILITY: TSlot(
        name=SlotName.HOTEL_AVAILABILITY.value,
        type="bool",
        description="availability of the hotel"
    ),
    SlotName.HOTEL_BOOKINGS: TSlot(
        name=SlotName.HOTEL_BOOKINGS.value,
        type="list[str]",
        description="bookings of the hotel"
    ),
    SlotName.BOOKING_ID: TSlot(
        name=SlotName.BOOKING_ID.value,
        type="str",
        description="booking id"
    ),
    SlotName.BOOKING_TIME: TSlot(
        name=SlotName.BOOKING_TIME.value,
        type="datetime",
        description="booking time"
    ),
    SlotName.BOOKING_STATUS: TSlot(
        name=SlotName.BOOKING_STATUS.value,
        type="str",
        description="booking status"
    ),
    SlotName.BOOKING_CONFIRMATION: TSlot(
        name=SlotName.BOOKING_CONFIRMATION.value,
        type="str",
        description="booking confirmation"
    ),
    SlotName.BOOKING_CANCELLATION_REASON: TSlot(
        name=SlotName.BOOKING_CANCELLATION_REASON.value,
        type="str",
        description="reason for canceling the booking"
    ),
}