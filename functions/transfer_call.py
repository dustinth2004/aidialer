import os
from twilio.rest import Client
import asyncio

async def transfer_call(context, args):
    """
    Transfers the current Twilio call to another number.

    This function retrieves the call SID from the context and uses the Twilio API
    to transfer the call to a pre-configured number.

    Args:
        context: The call context object, containing call-specific information.
        args: A dictionary of arguments for the function (not used in this function).

    Returns:
        str: A message indicating the result of the transfer operation.
    """
    # Retrieve the active call using the CallSid
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    transfer_number = os.environ['TRANSFER_NUMBER']

    client = Client(account_sid, auth_token)
    call_sid = context.call_sid

    # Wait for 10 seconds before transferring the call
    await asyncio.sleep(8)

    try:
        call = client.calls(call_sid).fetch()
        
        # Update the call with the transfer number
        call = client.calls(call_sid).update(
            url=f'http://twimlets.com/forward?PhoneNumber={transfer_number}',
            method='POST'
        )
            
        return f"Call transferred."

    except Exception as e:
        return f"Error transferring call: {str(e)}"