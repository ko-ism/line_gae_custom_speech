import os,sys
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (CarouselColumn, CarouselTemplate, ImageMessage, AudioMessage, 
                            MessageEvent, TemplateSendMessage, TextMessage,
                            TextSendMessage, URITemplateAction)

import config

#Storage
from google.cloud import storage
#Speech
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from pydub import AudioSegment

app = Flask(__name__)


PROJECT_ID = config.PROJECT_ID
CLOUD_STORAGE_BUCKET = config.CLOUD_STORAGE_BUCKET
line_bot_api = LineBotApi(config.CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.CHANNEL_SECRET)


# [START upload_file]
def upload_file(file_stream, filename, content_type):
    """
    Uploads a file to a given Cloud Storage bucket and returns the public url
    to the new object.
    """
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(CLOUD_STORAGE_BUCKET)

    if content_type=='audio/aac':
        file_fullname = filename+'.m4a'

    blob = bucket.blob(file_fullname)

    blob.upload_from_string(
        file_stream,
        content_type=content_type)

    url = 'gs://{}/{}'.format(CLOUD_STORAGE_BUCKET, file_fullname)

    return url
# [END upload_file]


@app.route("/auto_ocr", methods=['POST'])
def auto_ocr():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)

    # handle webhook body
    try:
        handler.handle(body, signature)

    except InvalidSignatureError as e:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    messages = [
        #TextSendMessage(text=text),
        TextSendMessage(text='音声を送ってみてね!含まれている文字を結果として返すよ。'),
    ]

    reply_message(event, messages)


@handler.add(MessageEvent, message=AudioMessage)
def handle_audio(event):

    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)

    response_text = ""

    audio = message_content.content

    file_path = 'tmp/'+message_id+'.m4a'
    with open(file_path, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)
    

    sound = AudioSegment.from_file(file_path, "m4a")
    sound.export("tmp/output.flac", format="flac")


    try:
        # Audio Upload
        audio_url = upload_file(audio,message_id,"audio/aac")

        if audio_url:
            try:
                speech_client = speech.SpeechClient()

                with open('tmp/output.flac',mode='rb') as f:
                    output = f.read()
                    audio = types.RecognitionAudio(content=output)

                #audio = types.RecognitionAudio(uri="tmp/output.flac")
                config = types.RecognitionConfig(
                        encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
                        sample_rate_hertz=16000,
                        language_code='ja-JP')

                operation = speech_client.long_running_recognize(config, audio)
                response = operation.result(timeout=90)

                if len(response.results[0].alternatives) > 0 :
                    for result in response.results:
                        # The first alternative is the most likely one for this portion.
                        response_text += 'Transcript:'+result.alternatives[0].transcript+'\n'
                        response_text += 'Confidence:'+str(result.alternatives[0].confidence)+'\n'
                else:
                    response_text = 'テキストを正常に検出できませんでした。'


                messages = [
                        TextSendMessage(text='結果は、下記です。'),
                        TextSendMessage(text=response_text),
                        ]
        
                reply_message(event, messages)

            except Exception as e:
                messages = [
                        TextSendMessage(text='Error: '+str(e)),
                        ]
                reply_message(event, messages)
        

    except Exception as e:
        messages = [
                TextSendMessage(text='Error: '+str(e)),
                ]
        reply_message(event, messages)
        



def reply_message(event, messages):
    line_bot_api.reply_message(
        event.reply_token,
        messages=messages,
    )

