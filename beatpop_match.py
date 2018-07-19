import time
import serial
import pyaudio
import librosa as rosa
import wave
import numpy as np
import matplotlib.pyplot as plt

# define serial port
ser = serial.Serial(
    port='COM3',
    baudrate=19200,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.SEVENBITS
)

# define plot
fig, (ax_sensor, ax_onset) = plt.subplots(nrows=2, ncols=1, sharex=False)

ax_sensor.set_ylim(0, 1023)
ysensor = 50 * [0.0]
line_sensor, = ax_sensor.plot(ysensor, 'r-')

ax_onset.set_ylim(-.1, 1)
frames_in_sec = 86
env = frames_in_sec * [0.0]
line_beat, = ax_onset.plot(env, 'r')

# audio info
CHUNK = 2048
filename = 'F:/My Documents/E-TATTOO/test_audio/West_Bubbles.wav'
wf = wave.open(filename, 'rb')
fs = wf.getframerate()                      # sampling rate
bytes_per_sample = wf.getsampwidth()
bits_per_sample  = 8 * bytes_per_sample
dtype = 'int{0}'.format(bits_per_sample)
channels = wf.getnchannels()                # number of channels
samples = wf.getnframes()                   # total samples in the track
duration = samples / float(fs)              # duration of the track

audio = np.fromstring(wf.readframes(int(duration*fs*bytes_per_sample/channels)), dtype=dtype)
audio.shape = (audio.shape[0]//channels, channels)  # reshape the audio array into 2D
ch_left = 0
ch_right = 1
ch = ch_right
audio_mono = audio[:, ch]                           # use one single channel

# onset detection
onset_env = rosa.onset.onset_strength(audio_mono, sr=fs,
                                      aggregate=np.mean)
onset_env /= np.max(onset_env)                      # normalize the onset envelope
onset_env_list = onset_env.tolist()                 # convert onset array to list
hop_length = 512                                    # hop length of frames
frames_per_chunk = int(CHUNK/hop_length)

# pyaudio object
p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)
wf.rewind()
data = wf.readframes(CHUNK)
cur_env = onset_env_list[0 : int(CHUNK/hop_length)]
frame_count = 0

# sensor data
sample_count = 0
force = 0

fig.show()

while len(data) > 0:
    # audio sample
    env = env[len(cur_env):] + cur_env
    frame_count += 1

    line_beat.set_ydata(env)
    stream.write(data)
    data = wf.readframes(CHUNK)
    if (frame_count + 1) * frames_per_chunk > len(onset_env_list):
        cur_env = onset_env_list[frame_count * frames_per_chunk:]
    else:
        cur_env = onset_env_list[frame_count * frames_per_chunk: (frame_count + 1) * frames_per_chunk]

    # sensor sample
    sensor_data = ser.readline()
    data_string = sensor_data.strip().decode('UTF-8')
    data_array = data_string.split(' ')

    if data_array[0].isdigit():
        force = int(data_array[0])
    ysensor.append(force)

    sample_count += 1
    if len(ysensor) > 50:
        ysensor.pop(0)

    line_sensor.set_ydata(ysensor)

    # update plot
    fig.canvas.draw()
    fig.canvas.flush_events()
