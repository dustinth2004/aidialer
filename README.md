# 🤖 ☎️ AI Dialer 

👉 A [blog post](https://amirkiani.xyz/posts/ai-dialer/) explaining the work behind this project.

## Summary
A full stack app for interruptible, low-latency and near-human quality AI phone calls built from stitching LLMs, speech understanding tools, text-to-speech models, and Twilio’s phone API

![UI Screenshot](examples/screenshot.png)

[Listen to example call](examples/sample.m4a)

## Features
The following components have been implemented and wrangled together in *streaming fashion* to achieve the tasks of *low-latency* and *interruptible* AI calls:
* **☎️ Phone Service:** makes and receives phone calls through a virtual phone number (Twilio)
* **🗣️ Speech-to-Text Service:** converts the caller’s voice to text (so that it can be passed to LLMs) and understands speech patterns such as when the user is done speaking and interruptions to facilitate interruptibility (Deepgram)
* **🤖 Text-to-text LLM:** understands the phone conversation, can make “function calls” and steers the conversation towards accomplishing specific tasks specified through a “system” message (OpenAI GPT-o or Anthropic Claude Sonnet 3.5)
* **🔈 Text-to-Speech Service:** converts the LLM response to high-quality speech
* **⚙️ Web Server:** A FastAPI-based web-server that provides end-points for:
   * Answering calls using Twilio’s Markup Language (Twilio ML),
   * Enabling audio streaming to/from Twilio through a per-call WebSocket
   * Interacting with the basic Steamlit web UI
* **📊 Frontend UI:** Simple Streamlit frontend to see initiate/end calls and view call progress in real-time in a browser


## Installation

### 1. Install dependencies:
(You might want to create a Python Virtual Environment to minimize the chance of conflicts.)
   ```
   pip install -r requirements.txt
   ```
### 2. Set up `ngrok`
Twilio requires an externally accessible server to be able to route calls. To do this while running a local instance, you need to expose the server to the outside world. One way to do this is through using [`ngrok`](https://ngrok.com)

Run `ngrok` to get an external URL that forwards traffic to your local web server:

```
ngrok http 3000
```

Copy the URL that ngrok gives you (e.g. `1bf0-157-131-155-236.ngrok-free.app`) without the `https://` at the beginning and set that as your `SERVER` variable in the following section.

### 3. Configure .env file

Make a copy of the `.env.example` file and rename it to `.env`. Then set the required credentials and configurations.

Please note that you have a choice between `anthropic` and `openai` for the LLM service, and between `deepgram` and `elevenlabs` for the TTS service.

```
# Server Configuration
SERVER=your_server_here
# port number if you are running the server locally
PORT=3000

# Service API Keys

# Twlio
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token

# AI Services
## LLM
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

## Speech Understanding/TTS
DEEPGRAM_API_KEY=your_deepgram_api_key

## TTS
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_MODEL_ID=eleven_turbo_v2
ELEVENLABS_VOICE_ID=XrExE9yKIg1WjnnlVkGX

# Which service to use for TTS
TTS_SERVICE=elevenlabs

# Which service to use for LLM
LLM_SERVICE=openai

# When you call a number, what should the caller ID be?
APP_NUMBER=your_app_number

# When UI launches, what number should it call by default
YOUR_NUMBER=your_number

# When a call needs to be transferred, what number should it be transferred to?
TRANSFER_NUMBER=your_transfer_number

# AI Configuration
SYSTEM_MESSAGE="You are a representative called Sarah from El Camino Hospital. Your goal is to obtain a prior authorization for a patient called John Doe for a knee surgery. Be brief in your correspondence."
INITIAL_MESSAGE="Hello, my name is Sarah, and I'm calling from El Camino Hospital. I need to discuss a prior authorization for a patient. Could you please direct me to the appropriate representative?"

# Should calls be recorded? (this has legal implications, so be careful)
RECORD_CALLS=false
```

### 4. Configure the Twilio end point
Assuming that you have created a [Twilio phone number](https://www.twilio.com/docs/phone-numbers) and installed Twilio's CLI, run the following to configure Twilio to use your app's endpoint:

```
twilio phone-numbers:update YOURNUMBER --voice-url=https://NGROKURL/incoming
```

### 4. Run the FastAPI server
```
python app.py
```

### 5. Run the Frontend server
```
streamlit ui/streamlit_app.py
```

## Architecture Overview

The application is built around a FastAPI web server that orchestrates several services to handle real-time AI-powered phone calls.

1.  **Incoming Call**: A call initiated to the Twilio number triggers a POST request to the `/incoming` endpoint.
2.  **WebSocket Connection**: The FastAPI server responds with TwiML instructions to establish a WebSocket connection to the `/connection` endpoint.
3.  **Media Streaming**: Twilio starts streaming the call's audio data to the WebSocket.
4.  **Transcription**: The `TranscriptionService` receives the audio stream and uses a real-time transcription service (like Deepgram) to convert speech to text. It emits `utterance` events for partial transcriptions and `transcription` events for final transcriptions.
5.  **LLM Processing**: The `LLMService` listens for `transcription` events. It sends the transcribed text, along with the conversation history, to a large language model (like OpenAI's GPT or Anthropic's Claude).
6.  **Text-to-Speech (TTS)**: The `LLMService` emits `llmreply` events with the LLM's response. The `TTSService` listens for these events and generates audio from the text using a TTS service (like ElevenLabs or Deepgram).
7.  **Audio Streaming back to Caller**: The `TTSService` emits `speech` events with the generated audio. The `StreamService` buffers this audio and sends it back to Twilio through the WebSocket, which is then played to the caller.
8.  **Interrupt Handling**: If the user speaks while the AI is talking, the `TranscriptionService` detects this as an `utterance`. The `app` then sends a `clear` event to Twilio to stop the currently playing audio, allowing for a natural, interruptible conversation.

This event-driven, streaming architecture allows for low-latency responses and a more human-like conversation flow.

## Project Structure

-   `app.py`: The main FastAPI application file. It defines all the API endpoints and orchestrates the different services.
-   `logger_config.py`: Configures the logging for the application using Loguru.
-   `requirements.txt`: Lists the Python dependencies for the project.
-   `.env.example`: An example environment file. Copy this to `.env` and fill in your credentials.
-   `settings.json`: Configuration for the LLM functions.
-   `functions/`: Contains the functions that the LLM can call, such as `transfer_call` and `end_call`.
    -   `function_manifest.py`: A manifest of the available functions for the LLM.
-   `services/`: Contains the core services of the application.
    -   `call_context.py`: A class to store the context of a call.
    -   `event_emmiter.py`: A simple event emitter class.
    -   `llm_service.py`: Handles interaction with the LLM (OpenAI or Anthropic).
    -   `stream_service.py`: Manages the audio stream to and from Twilio.
    -   `transcription_service.py`: Handles real-time speech-to-text transcription.
    -   `tts_service.py`: Handles text-to-speech synthesis.
-   `ui/`: Contains the Streamlit frontend application.
    -   `streamlit_app.py`: The main file for the Streamlit UI.
-   `examples/`: Contains example files, such as a sample call recording and a screenshot of the UI.

## Contribution
Contributions are welcome! Please feel free to submit a Pull Request.



## License
Copyright [Amir Kiani](https://amirkiani.xyz), 2024

Code shared under MIT License

## Acknowledgement 
This project would have not happened without [this great TypeScript example from Twilio Labs](https://github.com/twilio-labs/call-gpt). Claude Sonnet 3.5, GPT-4o, and [Aider](https://aider.chat) also provided ample help in writing parts of this code base 🦾
