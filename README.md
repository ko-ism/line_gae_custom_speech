# 概要
## LINEと、GAEで簡単、自動音声文字起こしくん
Line Messaging APIを利用して、GAEとSpeech-To-Text API連携して、簡単に音声を文字起こしするコードです

ffmpegを使って、Lineでの音声形式m4aから、Speech-To-Textで利用可能なflac形式へ変更するため、
GAEはstandard/flexではなく、customで作っています。

## 技術要素
* GCP Speech-To-Text API
* GCP GoogleAppEngine Custom(Python3.6)
* GCP GoogleCloudStorage
* LINE Messaging API
