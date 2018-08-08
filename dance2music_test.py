from dance2music import Dance2Music

serial_port = 'COM3'
baud_rate = 19200
filename = 'F:/My Documents/pop_harder/test_audio/West_Bubbles.wav'
west_bubble_pop = Dance2Music(serial_port, baud_rate, filename)

west_bubble_pop.get_audio_waveform()
west_bubble_pop.get_onset_envelope()

if __name__ == '__main__':
    west_bubble_pop.get_down()