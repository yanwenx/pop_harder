import time
import serial
import numpy as np
import matplotlib.pyplot as plt

ser = serial.Serial(
    port='COM3',
    baudrate=19200,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.SEVENBITS
)

# fig, ax = plt.subplots()
fig = plt.figure()
ax = plt.axes()
ax.set_ylim(0, 1023)
ys = 50 * [0.0]
force = 0
line, = ax.plot(ys, 'r-')

sample_count = 0
start_time = time.time()
end_time = time.time()
fig.show()

while True:
    start_time = time.time()

    sensor_data = ser.readline()
    data_string = sensor_data.strip().decode('UTF-8')
    data_array = data_string.split(' ')
    # print(data_array)

    if data_array[0].isdigit():# len(data_array) < 2:
        force = int(data_array[0])
        # print(force)
    ys.append(force)

    sample_count += 1
    if len(ys) > 50:
        ys.pop(0)

    end_time = time.time()
    # print('time cost', end_time - start_time, 's')

    line.set_ydata(ys)
    fig.canvas.draw()
    fig.canvas.flush_events()

