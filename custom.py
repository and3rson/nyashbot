from telegram.inlinequeryresult import InlineQueryResult


class InlineQueryResultAudio(InlineQueryResult):
    """This object represents a Telegram InlineQueryResultVideo.

    Attributes:
        id (str):
        audio_url (str):
        mime_type (str):
        audio_duration (int):
        title (str):
        performer (str):

    Args:
        id (str): Unique identifier for this result, 1-64 Bytes
        video_url (str):
        mime_type (str):
        thumb_url (str):
        title (str):
        message_text (str):

    Keyword Args:
        video_width (Optional[int]):
        video_height (Optional[int]):
        video_duration (Optional[int]):
        description (Optional[str]):
        caption (Optional[str]):
        parse_mode (Optional[str]):
        disable_web_page_preview (Optional[bool]):
    """

    def __init__(self,
                 id,
                 audio_url,
                 mime_type,
                 performer,
                 title,
                 audio_duration=None):

        # Required
        super(InlineQueryResultAudio, self).__init__('audio', id)
        self.audio_url = audio_url
        self.mime_type = mime_type
        self.performer = performer
        self.title = title

        # Optional

    @staticmethod
    def de_json(data):
        """
        Args:
            data (dict):

        Returns:
            telegram.InlineQueryResultVideo:
        """
        if not data:
            return None
        data = data.copy()
        data.pop('type', None)

        return InlineQueryResultAudio(**data)
