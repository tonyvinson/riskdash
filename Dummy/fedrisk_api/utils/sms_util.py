from fedrisk_api.utils.sns import SnsWrapper

# publish text message
async def publish_notification(
    user_message_data,
):
    SnsWrapper().publish_text_message(
        user_message_data["phone_no"],
        user_message_data["message"],
    )
