from bleak import BleakScanner
from bleak import BleakClient
from psychopy.visual import TextStim
import psychopy.visual
import psychopy.event
import psychopy.clock
import psychopy.core
import psychopy.gui
import os
import glob
import pandas as pd
import numpy as np
import pprint
import time
from psychopy import data
from random import shuffle
from psychopy import core
from psychopy import core, event
from psychopy import logging
from psychopy import clock
from psychopy.hardware import keyboard
import random
import datetime
import matplotlib.pyplot as plt
from sensor import GyroAccelSensor, TempPressureSensor, AmbientLightSensor
import importlib
#_winrt=importlib.import_module("winrt._winrt")
#_winrt.uninit_apartment()
#import winrt
#import bleak
import asyncio
from sensor import RecordingDevice
import struct
import sys
import time
import egi.simple as egi

IO_SAMP_CHAR_UUID = "6a80ff0c-b5a3-f393-e0a9-e50e24dcca9e"
ms_localtime=egi.ms_localtime
event.globalKeys.add(key='q', func=core.quit, name='shutdown')

async def main():
    # gui interface
    gui = psychopy.gui.Dlg()
    gui.addField("Subject ID:")
    gui.addField("Visit")
    gui.addField("Age")
    gui.addField('Screens', initial=True, choices=["1", "2"])
    gui.addField('Accelerometer', initial=True, choices=[True, False])
    gui.addField('EEG', initial=True, choices=[True, False])
    gui.addField('Show Plot', initial=True, choices=[True, False])
    gui.show()
    print(gui.data)
    if gui.OK:
        ID = gui.data[0]
        visit = gui.data[1]
        age = gui.data[2]
        Screens = gui.data[3]
        Accelerometer = gui.data[4]
        EEG = gui.data[5]
        showgraph = gui.data[6]

    if Accelerometer:
        while True:
            print('Scanning...')
            address = None
            devices = await BleakScanner.discover()
            for d in devices:
                if d.name == 'SENSOR_PRO':
                    address = d.address
                    print('SENSOR_PRO found: %s' % address)
            if address is not None:
                print('Connecting...')
                try:
                    async with BleakClient(address) as client:
                        break
                except:
                    pass
        def callback(client):
            print('sensor got disconnected'.format(address))
        client.set_disconnected_callback(callback)
        client.connect

        client = BleakClient(address)
        await client.connect()
        print('Setting sampling rate')
        write_value = b"\x00\x64"
        value = await client.read_gatt_char(IO_SAMP_CHAR_UUID)
        await client.write_gatt_char(IO_SAMP_CHAR_UUID, write_value)
        value = await client.read_gatt_char(IO_SAMP_CHAR_UUID)
        assert value == write_value
        gyro_acc = GyroAccelSensor(client)
        await gyro_acc.enable()
        if showgraph:
            gyro_data = np.zeros((3, 100))
            accel_data = np.zeros((3, 100))
            plt.subplot(2, 1, 1)
            g_h1, = plt.plot(gyro_data[0, :])
            g_h2, = plt.plot(gyro_data[1, :])
            g_h3, = plt.plot(gyro_data[2, :])
            plt.ylim(-250, 250)
            plt.legend(['gyro x', 'gyro y', 'gyro z'])
            plt.subplot(2, 1, 2)
            a_h1, = plt.plot(accel_data[0, :])
            a_h2, = plt.plot(accel_data[1, :])
            a_h3, = plt.plot(accel_data[2, :])
            plt.ylim(-2, 2)
            plt.legend(['acc x', 'acc y', 'acc z'])
            plt.draw()
            plt.show(block=False)

    try:
        # file location
        data_path = "task.csv"
        data_path_exists = os.path.exists(data_path)  # data path
        print(data_path_exists)


        # save data
        data = pd.DataFrame()
        sdata = pd.DataFrame()

        # welcome
        win = psychopy.visual.Window(size=[600, 600], units="pix", fullscr=False, color=[1, 1, 1], checkTiming=True,screen=0)
        if Screens=="2":
            win2=psychopy.visual.Window(size=[600, 600], units="pix", fullscr=False, color=[1, 1, 1], checkTiming=True,screen=1)
            #2 screens
            def make_draw_mirror(draw_fun):
                def mirror_draw_fun(*args, **kwargs):
                    draw_fun(win=win2)
                    draw_fun(*args, **kwargs)
                return mirror_draw_fun
            def make_flip_mirror(flip_fun):
                def mirror_flip_fun(*args, **kwargs):
                    win2.flip(*args, **kwargs)
                    flip_fun(*args, **kwargs)
                return mirror_flip_fun
            win.flip=make_flip_mirror(win.flip)

        #netstationIP:10.10.10.42

        if EEG:
            ns = egi.Netstation()
            ns.connect('10.10.10.42', 55513)
            ns.BeginSession()
            ns.sync
            ns.StartRecording()

        text = psychopy.visual.TextStim(win=win, text="Welcome to this experiment ! ", color=[-1, -1, -1])
        if Screens=="2":
            text.draw=make_draw_mirror(text.draw)
        text.draw()
        win.flip()
        psychopy.clock.wait(3, hogCPUperiod=0.2)
        text = psychopy.visual.TextStim(win=win, text=" Press a key to continue ", color=[-1, -1, -1])
        if Screens=="2":
            text.draw=make_draw_mirror(text.draw)
        text.draw()
        win.flip()
        keys = psychopy.event.waitKeys()

        # start of bloc
        block_types=['Cylinder','Ball']
        conditions=[['Horizontal','Vertical'],['Small','Medium','Large']]
        nBlocks = 1
        nTrials = 1
        for block_type,block_conditions in zip(block_types,conditions):
            text = psychopy.visual.TextStim(win=win, text="Bloc %s" % block_type, color=[-1, -1, -1])
            if Screens=="2":
                text.draw=make_draw_mirror(text.draw)
            text.draw()
            win.flip()
            psychopy.clock.wait(3, hogCPUperiod=0.2)
            for block in range(nBlocks):
                text = psychopy.visual.TextStim(win=win, text=" Press a key when the child reached the object",color=[-1, -1, -1])
                if Screens=="2":
                    text.draw=make_draw_mirror(text.draw)
                text.draw()
                win.flip()
                psychopy.clock.wait(2, hogCPUperiod=0.2)
                for trial in range(nTrials):
                    condition = random.choice(block_conditions)
                    text = psychopy.visual.TextStim(win=win, text="%s %s" % (condition, block_type), color=[-1, -1, -1])
                    if Screens=="2":
                        text.draw=make_draw_mirror(text.draw)
                    text.draw()
                    if EEG:
                        ns.send_event(bytes('obj'.encode()), label=bytes("%s %s" % (condition, block_type).encode()),
                                      description=bytes("%s %s" % (condition, block_type).encode()))
                        time.sleep(0.1)
                    trialClock = core.Clock()
                    trial_start=core.getTime()
                    win.flip()

                    while True:
                        if Accelerometer:
                            trial_time=trialClock.getTime()
                            (gyro, accel) = await gyro_acc.read()
                            sdata = sdata.append({
                                'id': ID,
                                'visit': visit,
                                'age': age,
                                'block_type':block_type,
                                'block':block,
                                'trial':trial,
                                'cond': condition,
                                'gyro_x':gyro[0,0],
                                'gyro_y':gyro[0,1],
                                'gyro_z':gyro[0,2],
                                'accel_x':accel[0,0],
                                'accel_y':accel[0,1],
                                'accel_z':accel[0,2],
                                'trial_time':trial_time
                                }, ignore_index=True)

                            if showgraph:
                                gyro_data[:, 0:-1] = gyro_data[:, 1:]
                                gyro_data[:, -1] = gyro
                                accel_data[:, 0:-1] = accel_data[:, 1:]
                                accel_data[:, -1] = accel
                                g_h1.set_ydata(gyro_data[0, :])
                                g_h2.set_ydata(gyro_data[1, :])
                                g_h3.set_ydata(gyro_data[2, :])
                                a_h1.set_ydata(accel_data[0, :])
                                a_h2.set_ydata(accel_data[1, :])
                                a_h3.set_ydata(accel_data[2, :])
                                plt.draw()
                                #plt.pause(0.0000001)
                            #else:
                            #    plt.autoDraw=False

                        keys = psychopy.event.getKeys()
                        if keys:
                            keytime=trialClock.getTime()
                            break
                        if EEG:
                            ns.send_event(bytes('grsp'.encode()), label=bytes("grasping".encode()), description=bytes("infant grasping".encode()))
                            time.sleep(0.1)

                    trial_dur = trialClock.getTime()
                    data = data.append({
                        'id': ID,
                        'visit': visit,
                        'age': age,
                        'block_type':block_type,
                        'block':block,
                        'trial':trial,
                        'cond': condition,
                        'keytime': keytime,
                        'trial_start':trial_start,
                        'trial_dur':trial_dur
                        },ignore_index=True)
                    logfile_path = "eeg test"
                    logfile_name1 = "{}logfile_{}.csv".format(logfile_path, ID)
                    data.to_csv(logfile_name1)
                    if Accelerometer:
                        logfile_name2 = "{}logfilesensor_{}.csv".format(logfile_path, ID)
                        sdata.to_csv(logfile_name2)

                    text = psychopy.visual.TextStim(win=win, text=" Press a key when ready for next trial",color=[-1, -1, -1])
                    if Screens=="2":
                        text.draw=make_draw_mirror(text.draw)
                    text.draw()
                    win.flip()
                    psychopy.event.waitKeys()
                text = psychopy.visual.TextStim(win=win, text=" End of Bloc %s " % (block_type), color=[-1, -1, -1])
                if Screens=="2":
                    text.draw=make_draw_mirror(text.draw)
                text.draw()
                win.flip()
                psychopy.clock.wait(2, hogCPUperiod=0.2)
            text = psychopy.visual.TextStim(win=win, text=" Press a key to continue ", color=[-1, -1, -1])
            if Screens=="2":
                text.draw=make_draw_mirror(text.draw)
            text.draw()
            win.flip()
            psychopy.event.waitKeys()
           # end of bloc

        # end of experiment
        text = psychopy.visual.TextStim(win=win, text="End of the experiment", color=[-1, -1, -1])
        if Screens=="2":
            text.draw=make_draw_mirror(text.draw)
        text.draw()
        win.flip()
        psychopy.clock.wait(3, hogCPUperiod=0.2)
        win.close()

        if EEG:
            ns.StopRecording()
            ns.EndSession()
            ns.disconnect()

            # save data
        logfile_path = "eeg test"
        logfile_name1 = "{}logfile_{}.csv".format(logfile_path, ID)
        data.to_csv(logfile_name1)
        if Accelerometer:
            logfile_name2 = "{}logfilesensor_{}.csv".format(logfile_path, ID)
            sdata.to_csv(logfile_name2)
    finally:
        if Accelerometer:
            await gyro_acc.disable()
asyncio.run(main())
