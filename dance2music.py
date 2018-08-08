import serial
import pyaudio
import librosa as rosa
import wave
import numpy as np
import matplotlib.pyplot as plt

class Dance2Music:
    """A class that detects beats and/or onsets in audio signal and 'pop' signal from sensor
    to see if they're well aligned in time domain.

    Copyright 2018 Yanwen Xiong
    """

    def __init__(self, serial_port, baud_rate, audio_filename, chunk=2048, hop_length=512, data_on_graph=200):
        """Initialize serial input, plot handle, wave object and audio stream etc.

        Args:
            serial_port (str): From which serial port the sensor data is input
            baud_rate (int): baud rate of serial input
            audio_filename (str): From which file to read the audio
            chunk (int): The chunk (frame) length (in # of samples)
            hop_length (int): By how many samples the frame is shifted
        """

        self.__chunk = chunk
        self.__hop_length = hop_length
        self.__frames_per_chunk = int(self.__chunk / self.__hop_length)

        # initialize serial input
        self.__ser = serial.Serial(
            port=serial_port,
            baudrate=baud_rate,
            parity=serial.PARITY_ODD,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.SEVENBITS)

        # initialize plot handle, call __init_plot() method
        self.__init_plot(data_on_graph)

        # initialize wave object
        self.__wf = wave.open(audio_filename, 'rb')
        self.__fs = self.__wf.getframerate() # sampling rate

        # initialize audio stream
        self.__p = pyaudio.PyAudio()

    def __init_plot(self, data_on_graph):
        """Internal class method for initializing the plots.

        Args:
            data_on_graph (int): How many data points to be shown on the graph
        """

        self.__fig, (self.__ax_sensor, self.__ax_onset) = plt.subplots(nrows=2, ncols=1, sharex=False)

        # initialize sensor data plot
        self.__ax_sensor.set_ylim(0, 1023)
        self.__ysensor = data_on_graph * [0.0]
        self.__line_sensor, = self.__ax_sensor.plot(self.__ysensor, 'r-')

        # initialize beat plot
        self.__ax_onset.set_ylim(-.1, 1.)
        self.__yonset = data_on_graph * [0.0]
        self.__line_onset, = self.__ax_onset.plot(self.__yonset, 'r-')

    def __callback(self, in_data, frame_count, time_info, status):
        """Internal method for audio stream callback."""

        data = self.__wf.readframes(frame_count)
        return (data, pyaudio.paContinue)

    def get_audio_waveform(self, channel='right'):
        """Class method for getting the audio (mono) waveform.

        Args:
            channel (str): Either 'left' or 'right', from which channel to get the audio waveform
        """

        bytes_per_sample = self.__wf.getsampwidth()
        bits_per_sample = 8 * bytes_per_sample
        dtype = 'int{0}'.format(bits_per_sample)

        channels = self.__wf.getnchannels()     # number of channels
        samples = self.__wf.getnframes()        # total samples in the track
        duration = samples / float(self.__fs)   # duration of the track

        self.__audio = np.fromstring(
            self.__wf.readframes(int(duration * self.__fs * bytes_per_sample / channels)),
            dtype=dtype)
        # reshape the audio array into 2D
        self.__audio.shape = (self.__audio.shape[0] // channels, channels)
        if channel == 'left':
            ch = 0
        else:
            ch = 1
        # select only one channel for analysis
        self.__audio_waveform = self.__audio[:, ch]

    def get_onset_envelope(self):
        """Class method for getting the onset envelope of the audio file."""

        self.__onset_env = rosa.onset.onset_strength(
            self.__audio_waveform.astype(np.float),
            sr=self.__fs,
            aggregate=np.mean)

        # normalize the onset envelope
        self.__onset_env /= np.max(self.__onset_env)
        # convert onset array to list
        self.__onset_env_list = self.__onset_env.tolist()

    def __rewind_audio(self):
        """Rewind the audio stream (shift cursor to the beginning of the file)."""
        self.__wf.rewind()
        return int(self.__wf.tell() / self.__hop_length)

    def get_down(self):
        """Start playing the audio stream and plot the onset envelope, as well as display the serial input."""

        cur_frame = self.__rewind_audio()
        self.__fig.show()
        self.__stream = self.__p.open(
            format=self.__p.get_format_from_width(self.__wf.getsampwidth()),
            channels=self.__wf.getnchannels(),
            rate=self.__wf.getframerate(),
            output=True,
            stream_callback=self.__callback)
        self.__stream.start_stream()

        while self.__stream.is_active():
            # update onset graph
            prev_frame = cur_frame
            cur_frame = int(self.__wf.tell() / self.__hop_length)
            self.__yonset = self.__yonset[cur_frame-prev_frame : ] + self.__onset_env_list[prev_frame : cur_frame]
            self.__line_onset.set_ydata(self.__yonset)

            # update sensor data graph
            sensor_data = self.__ser.readline()
            data_string = sensor_data.strip().decode('UTF-8')
            data_array = data_string.split(' ')

            force = 0
            if data_array[0].isdigit():
                force = int(data_array[0])
            self.__ysensor = self.__ysensor[cur_frame - prev_frame:] + (cur_frame - prev_frame) * [force]
            self.__line_sensor.set_ydata(self.__ysensor)

            self.__fig.canvas.draw()
            self.__fig.canvas.flush_events()

