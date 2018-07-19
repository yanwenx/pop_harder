import pyaudio
import wave
import numpy as np
import multiprocessing as mp
# from multiprocessing import Process
import matplotlib.pyplot as plt

duration = 5.0
filename = 'F:/My Documents/E-TATTOO/test_audio/Impeach_The_President.wav'
wf = wave.open(filename,'rb')

fs = wf.getframerate()
bytes_per_sample = wf.getsampwidth()
bits_per_sample  = bytes_per_sample * 8
dtype = 'int{0}'.format(bits_per_sample)
channels = wf.getnchannels()

audio = np.fromstring(wf.readframes(int(duration*fs*bytes_per_sample/channels)), dtype=dtype)
audio.shape = (audio.shape[0]//channels, channels)
ch_left = 0
ch_right = 1
ch = ch_right
times = np.arange(audio.shape[0]) / float(fs)

fig = plt.figure(figsize=(8, 4))
plt.plot(times, audio[:, ch])
plt.xlabel('Time (s)')
plt.xlim(0, duration)
plt.ylim(-32768, 32768)
time_posn, = plt.plot([0,0], [-32768,32768], 'k')
dt = .5

def audiostream(queue, n_channels, sampling, n_bytes_per_sample):
    # open stream
    p = pyaudio.PyAudio()

    stream = p.open(format =
                    p.get_format_from_width(n_bytes_per_sample),
                    channels = n_channels,
                    rate = sampling,
                    output = True)
    stream.start_stream()

    while True:
        data = queue.get()
        print("input latency: {0}".format(stream.get_input_latency()))
        print("output latency: {0}".format(stream.get_output_latency()))
        print("avail read: {0}".format(stream.get_read_available()))
        print("avail write: {0}".format(stream.get_write_available()))
        if data == 'Stop':
            break
        stream.write(data)
    # stream.stop_stream()
    stream.close()
    # wf.close()

class AudioSubsetter(object):
    def __init__(self, audio_array, audio_device_queue, n_channels, sampling_rate, n_bytes_per_sample, chunk_dt=0.1):
        self.last_chunk = -1
        self.queue = audio_device_queue
        self.audio_dat = audio_array.tostring()
        self.to_t = 1.0 / (sampling_rate * n_channels * n_bytes_per_sample)
        chunk = int(chunk_dt * fs) * n_channels * bytes_per_sample
        self.chunk0 = np.arange(0, len(self.audio_dat), chunk, dtype=int)
        self.chunk1 = self.chunk0 + chunk

    def update(self, *args):
        """ Timer callback for audio position indicator. Called with """
        self.last_chunk += 1
        if self.last_chunk >= len(self.chunk0):
            # self.queue.put("Stop")
            self.last_chunk = 0

        i = self.last_chunk
        i0, i1 = self.chunk0[i], self.chunk1[i]
        self.queue.put(self.audio_dat[i0:i1])
        t0, t1 = i0 * self.to_t, i1 * self.to_t
        print(t0, t1)
        for line_artist in args:
            line_artist.set_xdata([t1, t1])
        args[0].figure.canvas.draw()

def plotwaveform(queue, subsetter, audio, n_channels, sampling, n_bytes_per_sample, dt, fig, cursor):
    playhead = subsetter(audio, queue, n_channels, sampling, n_bytes_per_sample, chunk_dt=dt)
    timer = fig.canvas.new_timer(interval=dt * 1000.0)
    timer.add_callback(playhead.update, cursor)
    timer.start()
    plt.show()

if __name__ == '__main__':
    Q = mp.Queue()
    audio_process = mp.Process(target=audiostream,
                               args=(Q, channels, fs, bytes_per_sample))
    waveform_process = mp.Process(target=plotwaveform,
                                  args=(Q, AudioSubsetter, audio, channels, fs, bytes_per_sample, dt, fig, time_posn))
    audio_process.start()
    waveform_process.start()
    audio_process.join()
    waveform_process.join()

