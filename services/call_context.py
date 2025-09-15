from typing import List, Optional


class CallContext:
    """
    Stores and manages the context for a single phone call.

    This class holds all relevant information about a call, such as stream and call SIDs,
    the conversation history, and various metadata.

    Attributes:
        stream_sid (Optional[str]): The SID of the media stream.
        call_sid (Optional[str]): The SID of the call.
        call_ended (bool): A flag indicating if the call has ended.
        user_context (List): A list of messages in the conversation.
        system_message (str): The initial system message for the LLM.
        initial_message (str): The initial message to be spoken to the user.
        start_time (Optional[str]): The start time of the call.
        end_time (Optional[str]): The end time of the call.
        final_status (Optional[str]): The final status of the call.
    """
    def __init__(self):
        """Initializes a new CallContext object."""
        self.stream_sid: Optional[str] = None
        self.call_sid: Optional[str] = None
        self.call_ended: bool = False
        self.user_context: List = []
        self.system_message: str = ""
        self.initial_message: str = ""
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.final_status: Optional[str] = None
        
