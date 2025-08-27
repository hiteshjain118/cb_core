export enum ChatIntentName {
  AGENT_BUILDING = "agent_building",
  RETRIEVER_BUILDING = "retriever_building",
  QB = "qb",
  OTHER = "other"
}

export enum ChatSlotName {
  PARKING = "parking",
  HOTEL_BOOKINGS = "hotel_bookings",
  BOOKING_ID = "booking_id",
  BOOKING_TIME = "booking_time",
  BOOKING_STATUS = "booking_status"
}

export enum SenderType {
  USER = "user",
  QB_BUILDER = "qb_builder",
}