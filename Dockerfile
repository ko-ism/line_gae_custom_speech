FROM gcr.io/google-appengine/python
LABEL python_version=python3.6
RUN virtualenv --no-download /env -p python3.6

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-64bit-static.tar.xz \
	&& tar Jxvf ./ffmpeg-release-64bit-static.tar.xz \
	&& cp ./ffmpeg*64bit-static/ffmpeg /env/bin/ \
	&& cp ./ffmpeg*64bit-static/ffprobe /env/bin/
ADD requirements.txt /app/
RUN pip install -r requirements.txt
ADD . /app/
RUN mkdir /app/tmp
CMD exec gunicorn -b :$PORT main:app
