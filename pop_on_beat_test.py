from Pop_on_Beat import Pop_on_Beat
from multiprocessing import Process

serial_port = 'COM3'
baud_rate = 19200
filename = 'F:/My Documents/pop_harder/test_audio/West_Bubbles.wav'
west_bubble_pop = Pop_on_Beat(serial_port, baud_rate, filename)

west_bubble_pop.init_plot()
west_bubble_pop.get_audio_waveform()
west_bubble_pop.get_onset_envelope()
west_bubble_pop.reinit_onset_plot()

if __name__ == '__main__':
    while len(west_bubble_pop.read_audio_chunk()) > 0:
        p_audio = Process(target=west_bubble_pop.update_audio_data)
        p_sensor = Process(target=west_bubble_pop.update_sensor_data)
        p_plot = Process(target=west_bubble_pop.update_plot)

        p_audio.start()
        p_sensor.start()
        p_plot.start()

        p_audio.join()
        p_sensor.join()
        p_plot.join()
        # west_bubble_pop.update_audio_data()
        # west_bubble_pop.update_sensor_data()
        # west_bubble_pop.update_plot()
