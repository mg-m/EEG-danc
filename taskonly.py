
import psychopy.visual
import psychopy.event
import psychopy.clock
import psychopy.core
import psychopy.gui
import os
import pandas as pd
import numpy as np
from psychopy import core, event
import random
import egi.simple as egi
import datetime
import socket
import pyttsx3

ms_localtime=egi.ms_localtime
engine=pyttsx3.init()

# gui interface
gui = psychopy.gui.Dlg()
gui.addField("Subject ID:")
gui.addField("Visit")
gui.addField("Age")
gui.addField('Screens', initial=True, choices=["1", "2"])
gui.addField('EEG', initial=True, choices=[True, False])
gui.addField('Show Plot', initial=True, choices=[True, False])
gui.addField('Video Computer', initial=True, choices=[True, False])
gui.show()
print(gui.data)
if gui.OK:
    correct_input = True
    subj_id = gui.data[0]
        # if not (subj_id.startswith('sub-') and subj_id.split('-')[1].isdigit() and len(subj_id.split('-')[1])==3):
        # correct_input=False
        # print('Bad subject ID')
    visit=gui.data[1]
    # if not gui.data[1].isdigit():
    #     correct_input=False
    #     print('Bad visit number')
    # else:
    #     visit = 'ses-{}'.format(gui.data[1])
    age = gui.data[2]
    # if not gui.data[2].isdigit():
    #     correct_input = False
    #     print('Incorrect age')
    screens = gui.data[3]
    EEG = gui.data[4]
    showgraph = gui.data[5]
    video=gui.data[6]
else:
    core.quit()

if correct_input:

    if video:
        # connection video computer
        TCP_IP = "192.168.3.48"
        TCP_PORT = 5005
        buffer_size = 1024

        # setting up the connection
        print("waiting for the video computer to init")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(999)
        s.bind((TCP_IP, TCP_PORT))
        s.listen(1)
        conn, addr = s.accept()

        print("CONNECTION ADDRESS:", addr)

        # waiting for the client to initialize and connect
        while True:
            data = conn.recv(buffer_size)
            if data.decode() == "connected":
                print("video PC ready and connected")
                break

    # file location
    df = pd.DataFrame()
    data_path = os.path.join("./data", subj_id, visit)
    if not os.path.exists(data_path):
        os.makedirs(data_path, exist_ok=True)
    timestamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    logfile_fname = os.path.join(data_path, "{}_{}_{}_logfile.csv".format(subj_id, visit, timestamp))

    # win
    win = psychopy.visual.Window(size=[600, 600], units="pix", fullscr=False, color=[1, 1, 1], checkTiming=True,screen=0)
    if screens=="2":
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

    if EEG:
        ns = egi.Netstation()
        ns.connect('10.10.10.42', 55513)
        ns.BeginSession()
        ns.sync()
        ns.StartRecording()

        # shutdown and save data
    def quit(data):
        if EEG:
            ns.StopRecording()
            ns.EndSession()
            ns.disconnect()
        data.to_csv(logfile_fname)
        if video:
            message_finish = "exit_stop"
            conn.send(message_finish.encode())

        data = conn.recv(buffer_size)
        if "dumped" in data.decode():
            dump_output = data.decode()
            x, dump_time, x, rec_time = dump_output.split("_")
            print(dump_output, "video data dumped")
        win.close()
        core.quit()

    #callonflip
    def callonflip (condition, block_type, trial):
        if EEG:
            ns.send_event(bytes('obj'.encode()), label=bytes(("%s %s" % (condition, block_type)).encode()),
                          description=bytes(("%s %s" % (condition, block_type)).encode()))
        if video:
            message_start = str(trial).zfill(4) + "_start_" + str(timestamp)
            conn.send(message_start.encode())

    def run_block(block_type, block_conditions,df):

        text = psychopy.visual.TextStim(win=win, text="Bloc %s" % block_type, color=[-1, -1, -1])
        if screens == "2":
            text.draw = make_draw_mirror(text.draw)
        text.draw()
        engine.say('Bloc %s' % block_type)
        engine.runAndWait()
        win.flip()
        psychopy.clock.wait(3, hogCPUperiod=0.2)

        text = psychopy.visual.TextStim(win=win, text=" Press a key when the child reached the object",
                                        color=[-1, -1, -1])
        if screens == "2":
            text.draw = make_draw_mirror(text.draw)
        text.draw()
        engine.say('Press a key when the child reached the object')
        engine.runAndWait()
        psychopy.clock.wait(1, hogCPUperiod=1.5)
        win.flip()

        for trial in range(nTrials):
            run_trial(trial, block_type, block_conditions,df)

        text = psychopy.visual.TextStim(win=win, text=" End of Bloc %s. Press a key to continue " % (block_type),
                                        color=[-1, -1, -1])
        if screens == "2":
            text.draw = make_draw_mirror(text.draw)
        text.draw()
        engine.say('End of Bloc %s' % (block_type))
        engine.runAndWait()
        win.flip()
        psychopy.event.waitKeys()
        # end of bloc


    def run_trial(trial, block_type, block_conditions,df):

        condition = random.choice(block_conditions)
        text = psychopy.visual.TextStim(win=win, text="%s %s Press a key when ready" % (condition, block_type), color=[-1, -1, -1])
        if screens == "2":
            text.draw = make_draw_mirror(text.draw)
        text.draw()
        engine.say('Condition %s Press a key when ready' % condition)
        engine.runAndWait()
        trialClock = core.Clock()
        psychopy.event.waitKeys()
        win.callOnFlip(callonflip, condition, block_type, trial)
        win.flip()

        while True:
            keys = psychopy.event.getKeys()
            if keys:
                keytime = trialClock.getTime()
                if EEG:
                    ns.send_event(bytes("cond".encode()), label=bytes("%s %s" % (condition, block_type).encode()),
                                  description=bytes("%s %s" % (condition, block_type).encode()))
                break

        #go signal
        text = psychopy.visual.TextStim(win=win, text="show object", color=[-1, -1, -1])
        if screens == "2":
            text.draw = make_draw_mirror(text.draw)
        text.draw()
        engine.say("show object")
        engine.runAndWait()
        trialClock = core.Clock()
        trial_start = core.getTime()
        win.callOnFlip(callonflip, condition, block_type, trial)
        win.flip()

        while True:
            keys = psychopy.event.getKeys()
            if keys:
                keytime = trialClock.getTime()
                if EEG:
                    ns.send_event(bytes('grsp'.encode()), label=bytes("grasping".encode()),
                                  description=bytes("grasping".encode()))
                # end video recording
                if video:
                    message_stop = str(trial).zfill(4) + "_stop"
                    conn.send(message_stop.encode())
                break

        trial_dur = trialClock.getTime()

        dump_time = float('NaN')
        rec_time = float('NaN')
        trial_rec_diff = float('NaN')
        if video:
            while True:
                data = conn.recv(buffer_size)
                if "dumped" in data.decode():
                    dump_output = data.decode()
                    print(dump_output, "video data dumped")
                    x, dump_time, x, rec_time = dump_output.split("_")
                    dump_time=eval(dump_time)
                    rec_time=eval(rec_time)
                    trial_rec_diff=trial_dur-eval(rec_time)
                    break

        df = df.append({
            'id': subj_id,
            'visit': visit,
            'age': age,
            'block_type': block_type,
            'block': block,
            'trial': trial,
            'cond': condition,
            'keytime': keytime,
            'trial_start': trial_start,
            'trial_dur': trial_dur,
            'vid_dump_duration': dump_time,
            'vid_rec_duration': rec_time,
            'trial_rec_diff': trial_rec_diff
        }, ignore_index=True)
        df.to_csv(logfile_fname)

        text = psychopy.visual.TextStim(win=win, text=" Press a key when ready for next trial", color=[-1, -1, -1])
        if screens == "2":
            text.draw = make_draw_mirror(text.draw)
        text.draw()
        engine.say('Press a key when ready for next trial')
        engine.runAndWait()
        win.flip()
        psychopy.event.waitKeys()
    

    #start
    text = psychopy.visual.TextStim(win=win, text="Welcome to this experiment ! ", color=[-1, -1, -1])
    if screens=="2":
        text.draw=make_draw_mirror(text.draw)
    text.draw()
    engine.say('Welcome to this experiment')
    engine.runAndWait()
    win.flip()
    psychopy.clock.wait(3, hogCPUperiod=0.2)
    text = psychopy.visual.TextStim(win=win, text=" Press a key to continue ", color=[-1, -1, -1])
    if screens=="2":
        text.draw=make_draw_mirror(text.draw)
    text.draw()
    win.flip()
    psychopy.event.waitKeys()

    # start of bloc
    block_types=['Cylinder','Ball']
    conditions=[['Horizontal','Vertical'],['Small','Medium','Large']]
    nBlocks = 4
    nTrials=1

    for block in range(nBlocks):

        for block_type,block_conditions in zip(block_types,conditions):
            run_block(block_type, block_conditions,df)

        keys = psychopy.event.getKeys(['c','b','q'])
        for key in keys:
            if key=='c':
                run_block('Cylinder',conditions[0])
            elif key=='b':
                run_block('Ball', conditions[1])
            elif key=='q':
                quit(data)


    # end of experiment
    text = psychopy.visual.TextStim(win=win, text="End of the experiment", color=[-1, -1, -1])
    if screens=="2":
        text.draw=make_draw_mirror(text.draw)
    text.draw()
    engine.say('End of the experiment')
    engine.runAndWait()
    win.flip()
    psychopy.clock.wait(3, hogCPUperiod=0.2)
    win.close()

    # save experiment data
    df.to_csv(logfile_fname)

    #end EEG recording
    if EEG:
        ns.StopRecording()
        ns.EndSession()
        ns.disconnect()

    #save video data
    if video:
        message_finish = "exit_stop"
        conn.send(message_finish.encode())

    core.quit()


