import serial
import pyaudio
import librosa as rosa
import wave
import numpy as np
import matplotlib.pyplot as plt

class Pop_on_Beat:
    """A class that detects beat in audio file and 'pop' signal from sensor
    to see if they're well aligned in time domain.

    Copyright 2018 Yanwen Xiong
    """

    def __init__(self, serial_port, baud_rate, audio_filename, chunk=2048, hop_length=512):
        """Initialize serial input handle, plot handle, wave object and audio stream.

        Args:
            serial_port (str): From which serial port the sensor data is input
            baud_rate (int): baud rate of serial input
            audio_filename (str): From which file to read the audio
            chunk (int): The chunk (frame) length (in # of samples)
            hop_length (int): By how many samples the frame is shifted
        """

        self.__chunk = chunk
        self.__hop_length = hop_length
        self.__frames_per_chunk = int(self.__chunk/self.__hop_length)

        # initialize serial input handle
        self.__ser = serial.Serial(
            port=serial_port,
            baudrate=baud_rate,
            parity=serial.PARITY_ODD,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.SEVENBITS)

        # initialize plot handle
        self.__fig, (self.__ax_sensor, self.__ax_onset) = plt.subplots(nrows=2, ncols=1, sharex=False)

        # initialize wave object
        self.__wf = wave.open(audio_filename, 'rb')

        # initialize audio stream
        self.__p = pyaudio.PyAudio()
        self.__stream = self.__p.open(
            format=self.__p.get_format_from_width(self.__wf.getsampwidth()),
            channels=self.__wf.getnchannels(),
            rate=self.__wf.getframerate(),
            output=True)

    def init_plot(self, sensor_data_point=50, frames_in_sec=86):
        """Class method for initializing the plots.

        Args:
            sensor_data_point (int): How many data points are shown on the sensor data plot
            frames_in_sec (int): How many frames (data points) are shown on the beat plot
        """

        # initialize sensor data plot
        self.__ax_sensor.set_ylim(0, 1023)
        self.__ysensor = sensor_data_point * [0.0]
        self.__line_sensor, = self.__ax_sensor.plot(self.__ysensor, 'r-')

        # initialize beat plot
        self.__ax_onset.set_ylim(-.1, 1.)
        self.__yonset = frames_in_sec * [0.0]
        self.__line_onset, = self.__ax_onset.plot(self.__yonset, 'r-')

    def get_audio_waveform(self, channel='right'):
        """Class method for getting the audio (mono) waveform.

        Args:
            channel (str): Either 'left' or 'right', from which channel to get the audio waveform
        """

        self.__fs = self.__wf.getframerate()                # sampling rate

        bytes_per_sample = self.__wf.getsampwidth()
        bits_per_sample = 8 * bytes_per_sample
        dtype = 'int{0}'.format(bits_per_sample)

        channels = self.__wf.getnchannels()                 # number of channels
        samples = self.__wf.getnframes()                    # total samples in the track
        duration = samples / float(self.__fs)               # duration of the track

        self.__audio = np.fromstring(
            self.__wf.readframes(int(duration*self.__fs*bytes_per_sample/channels)),
            dtype=dtype)
        # reshape the audio array into 2D
        self.__audio.shape = (self.__audio.shape[0] // channels, channels)
        if channel == 'left':
            ch = 0
        else:
            ch = 1
        self.__audio_waveform = self.__audio[:, ch]

    def get_onset_envelope(self):
        """Class method for getting the onset envelope of the audio file."""

        self.__onset_env = rosa.onset.onset_strength(
            self.__audio_waveform,
            sr=self.__fs,
            aggregate=np.mean)

        # normalize the onset envelope
        self.__onset_env /= np.max(self.__onset_env)
        # convert onset array to list
        self.__onset_env_list = self.__onset_env.tolist()

    def read_audio_chunk(self):
        self.__audio_input = self.__wf.readframes(self.__chunk)
        return self.__audio_input

    def reinit_onset_plot(self):
        """Reinitialize the onset plot."""

        self.__wf.rewind()
        self.__audio_input = self.read_audio_chunk()
        self.__cur_env = self.__onset_env_list[0: int(self.__chunk / self.__hop_length)]
        self.__frame_count = 0
        self.__sensor_count = 0
        self.__force = 0
        self.__fig.show()

    def update_audio_data(self):
        """Class method for updating the audio (onset) data."""

        self.__yonset = self.__yonset[len(self.__cur_env):] + self.__cur_env
        self.__frame_count += 1

        self.__line_onset.set_ydata(self.__yonset)
        self.__stream.write(self.__audio_input)
        # self.__audio_input = self.read_audio_chunk()

        if (self.__frame_count + 1) * self.__frames_per_chunk > len(self.__onset_env_list):
            self.__cur_env = self.__onset_env_list[self.__frame_count * self.__frames_per_chunk:]
        else:
            self.__cur_env = self.__onset_env_list[
                             self.__frame_count * self.__frames_per_chunk:
                             (self.__frame_count + 1) * self.__frames_per_chunk]

    def update_sensor_data(self):
        """Class method for updating the sensor data."""

        sensor_data = self.__ser.readline()
        data_string = sensor_data.strip().decode('UTF-8')
        data_array = data_string.split(' ')

        if data_array[0].isdigit():
            self.__force = int(data_array[0])
        self.__ysensor.append(self.__force)

        self.__sensor_count += 1
        if len(self.__ysensor) > 50:
            self.__ysensor.pop(0)

        self.__line_sensor.set_ydata(self.__ysensor)

    def update_plot(self):
        """Class method for updating the (audio and sensor) plot."""

        self.__fig.canvas.draw()
        self.__fig.canvas.flush_events()
