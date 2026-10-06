from datetime import datetime
from psychopy import core, event, visual, logging, gui, event, monitors, data 
from helper_functions import *
import numpy as np
import os
import itertools
import json
logging.console.setLevel(logging.WARNING)
## ======================================================================
## Get experiment and monitor information 
## ======================================================================
expInfo = {
    'Monitor Name': 'BENQ',
    'Monitor Refresh Rate': '60',
    'Subject Number': '',
    'Screen Number': '1',
    'Demo': True,
    'Demographics': True,
    'Debrief': True,
    'Full Screen': True}

dlg = gui.DlgFromDict(
    expInfo, 
    title = 'Experinent Information')

if not dlg.OK:
    core.quit()

EXPERIMENT = 'valDecodeV3'
DATETIME = datetime.now().strftime("%y%m%d%H%M") 
SUBID = 'sub-' + f'{int(expInfo["Subject Number"])}'.zfill(2)
REFRATE = int(expInfo['Monitor Refresh Rate'])
SCREEN = int(expInfo['Screen Number'])
FULLSCREEN = expInfo['Full Screen']
DEMO = expInfo['Demo']
DEMOGRAPHICS = expInfo['Demographics']
DEBRIEF = expInfo['Debrief']

# configure monitor
if expInfo['Monitor Name'] in monitors.getAllMonitors():
    MONITOR = monitors.Monitor(expInfo['Monitor Name'])

else:
    monInfo = {
        'Monitor y (pxl)': '1080',
        'Monitor x (pxl)': '1920',
        'Monitor Width (cm)': '',
        'Monitor Distance (cm)': ''}

    dlg = gui.DlgFromDict(
        monInfo, 
        title = 'Monitor Information')

    if dlg.OK:
        MONITOR = monitors.Monitor(expInfo['Monitor Name'])
        MONITOR.setDistance(int(monInfo['Monitor Distance (cm)']))
        MONITOR.setWidth(float(monInfo['Monitor Width (cm)']))
        MONITOR.setSizePix((int(monInfo['Monitor x (pxl)']), 
                            int(monInfo['Monitor y (pxl)'])))
        MONITOR.saveMon()
    else:
        gui.criticalDlg('Something went wrong. Aborting')
        core.quit()
        
if DEMOGRAPHICS:

    demographics = {
        'What is your age? (Leave blank if you would rather not say.)': '',
        'How do you describe your sex?': ['Woman/Female', 'Man/Male', 'Intersex', 'I use a different term', 'I prefer not to answer']}

    if expInfo['Demographics']:

        dlg = gui.DlgFromDict(
            demographics, 
            title = 'Demographics')
        if not dlg.OK:
            core.quit()

    AGE = int(demographics['What is your age? (Leave blank if you would rather not say.)'])
    SEX = demographics['How do you describe your sex?']


## ======================================================================
## Create data paths
## ======================================================================
DATAPATH = 'C:/Users/tbmlp-lab/Experiments/valDecode_v3/data/'
os.mkdir(DATAPATH + SUBID)
folders = ['/beh/', '/eeg/']
for folder in folders:
    os.mkdir(DATAPATH + SUBID + folder)
FILENAME = f'{SUBID}_task-{EXPERIMENT}_beh.txt'
LOGFILENAME = f'{SUBID}_task-{EXPERIMENT}_log.txt'
FRMSFILENAME = f'{SUBID}_task-{EXPERIMENT}_frms.txt'
FILEPATH = DATAPATH + SUBID + folders[0] + FILENAME
LOGFILEPATH = DATAPATH + SUBID + folders[0] + LOGFILENAME
FRMSFILEPATH = DATAPATH + SUBID + folders[0] + FRMSFILENAME
logging.LogFile(LOGFILEPATH)
## ======================================================================
## Create window, stimuli, and other experiment features
## ======================================================================
# create window
win = visual.Window(
        screen = SCREEN, 
        monitor = MONITOR,
        size = MONITOR.getSizePix(),
        fullscr=FULLSCREEN,
        pos = [0, 0],
        color = [0, 0, 0], # black
        units = 'pix', 
        colorSpace = 'rgb255',
        blendMode = 'avg')
win.refreshThreshold = 1/REFRATE + 0.002

# set mouse to invisible
mouse = event.Mouse(visible=False)

# create clock
clock = core.Clock()

# define stimulus positions
size_params = { # common parameters used to calculate stimulus size in pixels
    'distance': MONITOR.getDistance(), 
    'screen_res': MONITOR.getSizePix(), 
    'screen_width': MONITOR.getWidth()
}
CENTRE = [0, 0]

# define colours in RGB255
BLUE =   [37, 141, 165] 
ORANGE = [194, 99, 32]
WHITE = [255, 255, 255]
GREY = [119, 119, 119]

# define rules
COLOUR = 'C' # respond based on the colour 
SHAPE = 'S' # respond based on the shape

# define key mapping 
RESPKEYS = {
    'orange': 'z',
    'blue': 'n',
    'circle': 'x',
    'square': 'm'
}
QUITKEYS = ['escape']
CONKEYS = ['space']
EXITKEYS = ['return']

# define number of trials/blocks
NPRACTRIALS = 20
NTRIALS = 64
NBLOCKS = 2 #8
NBLOCKSREPEAT = 1 #4 swap high value dimension after 5 blocks

# Assign high and low value to different initial dimensions
DIMS = ['colour', 'shape']
if int(expInfo["Subject Number"]) % 2 == 0: # if even, assign high value dimention to colour first
    high_val_dim_assign = [0, 1]
else:
    high_val_dim_assign = [1, 0]
# create array to index DIMS on every block to assign high-value dimension
high_val_dim_array = np.repeat(high_val_dim_assign*int(NBLOCKS/NBLOCKSREPEAT/len(high_val_dim_assign)), 
                               repeats=NBLOCKSREPEAT) 

# define points boost
POINTS_HIGH = 50
POINTS_LOW = 1 # no points boost for low-value dimension

# define function to convert RT into points
# NOTE: During the main experiment, participants can respond as soon as the second stimulus appears (either the cue or the object). 
# The second stimulus is presented for 0.3 s, then there is 1 s of fixation cross, so the total available response time is 1.3 s. 
# We don't want particpants to respond too quickly, so the min_rt here is 0.2 s. Correct responses faster than 0.2 s will earn no more points than responses of 0.2 s, 
# and errors faster than 0.2 s will have a specific error message telling PTs to slow down. 
# During the first two demo blocks, participants can respond after seeing only the first stimulus, 
# so the max_rt increases to 1.8 s (i.e., 0.3 s stim + 0.2 s SOA + 0.3 s stim + 1 s response period)
MIN_RT = 0.2
MAX_RT = 1.3 
MAX_RT_DEMO = 1.8
def points_function(rt, min_rt=MIN_RT, max_rt=MAX_RT):

    max_points = 10

    if rt <= min_rt:
        coef = max_points
    elif (rt > min_rt) & (rt < max_rt):
        coef = np.round((1 + (-1/(max_rt-min_rt))*(rt - min_rt)) * max_points, 3)
    elif rt >= max_rt:
        coef = 0
    return coef

# calculate total possible points
max_total_points = (((NTRIALS*NBLOCKS)/2)*POINTS_HIGH*points_function(MIN_RT, min_rt=MIN_RT, max_rt=MAX_RT) + # max points for high-value trials
                    ((NTRIALS*NBLOCKS)/2)*POINTS_LOW*points_function(MIN_RT, min_rt=MIN_RT, max_rt=MAX_RT)) # max points for low-value trials

total_reward = 1500 # $15, or 1500 cents
cents_per_point = total_reward / max_total_points

# define timing 
ITI_RANGE = [int(0.5*REFRATE), int(0.7*REFRATE)] 
STIM_DUR = int(0.3*REFRATE)
SOA_DUR = int(0.2*REFRATE)
RES_DUR = int(1*REFRATE)
FDB_DUR = int(0.4*REFRATE)
FDB_DUR_LNG = int(1*REFRATE)

# create stimuli
stim_params = { # common parameters used across stimuli
    'win': win, 
    'units': 'pix', 
    'opacity': 1,
    'contrast': 1,
    'colorSpace': 'rgb255'}
crc_stim_rad = dva_to_pix(dva=1.5, **size_params)
crc_stim = visual.Circle(
    radius = crc_stim_rad,
    edges = 100,
    lineWidth = 0,
    **stim_params)
sqr_stim = visual.Rect(
    size=crc_stim_rad*2,
    lineWidth=0,
    **stim_params)
txt_stim_height = dva_to_pix(dva=1, **size_params)
txt_stim = visual.TextStim(
    pos=CENTRE,
    color=WHITE,
    height=txt_stim_height,
    wrapWidth=MONITOR.getSizePix()[0]*0.8, # 80% of width of screen
    **stim_params)
fix_stim_height = dva_to_pix(dva=1, **size_params)
fix_stim = visual.TextStim(
    text= "+",
    pos=CENTRE,
    color=WHITE,
    height=fix_stim_height,
    **stim_params)
cue_stim_height = dva_to_pix(dva=1, **size_params)
cue_stim = visual.TextStim(
    pos=CENTRE,
    color=WHITE,
    height=cue_stim_height,
    **stim_params)
txt_stim2 = visual.TextStim(
    pos=[0, -(MONITOR.getSizePix()[1]/2)*0.8],
    color=WHITE,
    height=txt_stim_height,
    wrapWidth=MONITOR.getSizePix()[0], # 100% of width of screen
    **stim_params)

# create experiment handler to save output
if not DEMOGRAPHICS:
    AGE = np.nan
    SEX = np.nan
    HAND = np.nan

experimentDict = {
    'Experiment': EXPERIMENT,
    'Date': DATETIME,
    'Refrate': REFRATE,
    'MonitorSize' : MONITOR.getSizePix(),
    'Subject': SUBID,
    'SubjectAge': AGE,
    'SubjectSex': SEX}

exp = data.ExperimentHandler(name=EXPERIMENT,
                             extraInfo=experimentDict)
exp.dataNames = []                     

# write instruction text
instructText = {

'INSTRUCTIONS_1': '''
    Welcome to our experiment! \n\n\n
    On every trial, you will see an object and a word. \n
    Sometimes the word will appear first, and sometimes the object will appear first. \n
    Depending on the word, you will need to press a response key to identify either the COLOUR or the SHAPE of the object. \n\n\n
    Press space to continue. 
    ''',

'INSTRUCTIONS_2': f'''
    If you see the word "COLOUR", you need to identify the COLOUR of the object.\n\n
    If the object is ORANGE, press the {RESPKEYS["orange"].upper()} key. \n
    If the object is BLUE, press the {RESPKEYS["blue"].upper()} key. \n\n\n
    Press space to continue. 
    ''',

'INSTRUCTIONS_3': f'''
    If you see the word "SHAPE", you need to identify the SHAPE of the object.\n\n
    If the object is a CIRCLE, press the {RESPKEYS["circle"].upper()} key. \n
    If the object is a SQUARE, press the {RESPKEYS["square"].upper()} key. \n\n\n
    Press space to continue. 
    ''',

'INSTRUCTIONS_4': f'''
    The faster you respond, the more points you can earn! \n
    However, if you make a mistake you won't earn any points on that trial, so you need to be accurate, too. \n
    At the end of the experiment, the points will be converted into additional reimbursement. \n\n\n
    Press space to continue.
    '''
} 

demoText = {

'DEMO_1': f'''
    Let's do some practice.\n
    To start, you will just need to identify the COLOUR of the object. \n
    Remember, if the object is ORANGE press the {RESPKEYS["orange"].upper()} key, and if the object is BLUE press the {RESPKEYS["blue"].upper()} key. \n
    The response keys will be shown at the bottom of the screen to help you remember. \n\n\n
    Press space to begin.
    ''',

'DEMO_2': f'''
    Great! Now let's practice identifying the SHAPE of the object.\n
    Remember, if the object is a CIRCLE press the {RESPKEYS["circle"].upper()} key, and if the object is a SQUARE press the {RESPKEYS["square"].upper()} key. \n
    The response keys will be shown at the bottom of the screen to help you remember. \n\n\n
    Press space to begin.
    ''', 

'DEMO_3': f'''
    Nice work! Now let's practice putting it all together. On each trial, you will need to identify either the COLOUR or the SHAPE of the object. \n
    Remember your response keys: \n
    ORANGE = {RESPKEYS["orange"].upper()}
    CIRCLE = {RESPKEYS["circle"].upper()}
    BLUE = {RESPKEYS["blue"].upper()}
    SQUARE = {RESPKEYS["square"].upper()} \n\n
    The response keys will be shown at the bottom of the screen to help you remember. \n\n\n
    Press space to begin. 
    ''',

'DEMO_4': f'''
    Nice work! Let's practice it one more time, but now your deadline to respond will be a little faster.\n
    Remember your response keys: \n
    ORANGE = {RESPKEYS["orange"].upper()}
    CIRCLE = {RESPKEYS["circle"].upper()}
    BLUE = {RESPKEYS["blue"].upper()}
    SQUARE = {RESPKEYS["square"].upper()} \n\n
    The response keys will no longer be shown at the bottom of the screen. Good luck!\n\n\n
    Press space to begin. 
    '''
} 

mainText = {

'MAIN_1': f'''
    You will now start the main experiment. \n
    Importantly, you will now receive a POINTS BOOST in some blocks for correctly identifying the COLOUR of the object. \n 
    In other blocks, you will receive a POINTS BOOST for correctly identifying the SHAPE of the object. \n 
    You will be told at the start of each block whether you will receive the POINTS BOOST for identifying the COLOUR or the SHAPE of the object in that block. \n\n\n
    Press space to begin.
    '''
}

## ======================================================================
## Create trial structure
## ======================================================================
trl_stc = np.repeat(
    np.asarray(
        tuple(
            itertools.product(
                ['cue_first', 'stim_first'], # order of stimulus presentation
                ['colour', 'shape'], # cued dimension  
                ['orange', 'blue'], # stimulus colour
                ['square', 'circle'])), # stimulus shape  
            dtype = 'object'), 
    repeats=4, # number of each trial type per block
    axis=0)
## ======================================================================
## Present stimuli
## ======================================================================
## Present instructions -------------------------------------------------------------- START INSTRUCTIONS
for txt in instructText.keys():

    event.clearEvents()
    logging.warning(f'{txt}')
    logging.flush()
    txt_stim.text = instructText[txt]
    while True:

        # draw stimuli
        txt_stim.draw()
        win.flip()

        # collect user input to exit 
        pressed = event.getKeys(keyList = CONKEYS)
        if pressed: 
            break

# do some practice trials
if DEMO:

    # present instructions 
    for txt in demoText.keys():

        event.clearEvents()
        logging.warning(f'{txt}')
        logging.flush()
        txt_stim.text = demoText[txt] 

        while True:

            # draw stimuli
            txt_stim.draw()
            win.flip()

            # collect user input to exit 
            pressed = event.getKeys(keyList = CONKEYS)
            if pressed: 
                break

        # start presenting trials
        while True:

            correct_responses_tally = []
            for trial in range(NPRACTRIALS):

                ## set stimulus properties for current trial
                stim_shape = np.random.choice(['circle', 'square']) # randomly select a shape
                stim_colour = np.random.choice(['orange', 'blue']) # randomly select a colour
                order = np.random.choice(['cue_first', 'stim_first']) # randomly select an order
                # set stimulus shape and colour
                if stim_shape == 'circle':
                    if stim_colour == 'orange':
                        crc_stim.fillColor = ORANGE
                    else:
                        crc_stim.fillColor = BLUE
                else:
                    if stim_colour == 'orange':
                        sqr_stim.fillColor = ORANGE
                    else:
                        sqr_stim.fillColor = BLUE       
                # set cue for each demo block
                if txt == 'DEMO_1':
                    cue = 'colour'
                    cue_stim.text = 'COLOUR' # just classify colour
                    txt_stim2.setText(f'''ORANGE = {RESPKEYS["orange"].upper()}    BLUE = {RESPKEYS["blue"].upper()}'''),
                elif txt == 'DEMO_2':
                    cue = 'shape'
                    cue_stim.text = 'SHAPE' # just classify shape 
                    txt_stim2.setText(f'''CIRCLE = {RESPKEYS["circle"].upper()}    SQUARE = {RESPKEYS["square"].upper()}'''),
                else:
                    cue = np.random.choice(['shape', 'colour']) # randomly select a cue
                    if cue == 'shape':
                        cue_stim.text = 'SHAPE' 
                    else:
                        cue_stim.text = 'COLOUR'
                    txt_stim2.setText(f'''ORANGE = {RESPKEYS["orange"].upper()}    CIRCLE = {RESPKEYS["circle"].upper()}    BLUE = {RESPKEYS["blue"].upper()}    SQUARE = {RESPKEYS["square"].upper()}'''),
                # set response duration for each demo block
                if txt == 'DEMO__4':
                    RES_DUR_DEMO = RES_DUR
                else:
                    RES_DUR_DEMO = RES_DUR*2

                # set ITI duration
                ITI_DUR = np.random.randint(ITI_RANGE[0], ITI_RANGE[1])

                # start stimulus presentation
                event.clearEvents()
                frame = 0
                while True:

                    if (frame < ITI_DUR):#------------------------------------------------------------------------------------------ITI ONSET
            
                        # draw fixation
                        fix_stim.draw()

                    # prepare for recording response
                    if (frame == ITI_DUR) & (txt in ['DEMO_1', 'DEMO_2']):

                        max_rt = MAX_RT_DEMO
                        event.clearEvents()
                        clock.reset()

                    if (frame >= ITI_DUR) & (frame < ITI_DUR + STIM_DUR):# ----------------------------------------------------------STIM_1 ONSET

                        # draw cue
                        if order == 'cue_first':
                            cue_stim.draw()
                        elif order == 'stim_first':
                            if stim_shape == 'circle':
                                crc_stim.draw()
                            else:
                                sqr_stim.draw()

                    if (frame >= ITI_DUR + STIM_DUR) & (frame < ITI_DUR + STIM_DUR + SOA_DUR):#--------------------------------------SOA ONSET
                    
                        # draw fixation
                        fix_stim.draw()

                    # prepare for recording response
                    if (frame == ITI_DUR + STIM_DUR + SOA_DUR) & (txt in ['DEMO_3', 'DEMO_4']):

                        max_rt = MAX_RT
                        event.clearEvents()
                        clock.reset()

                    if (frame >= ITI_DUR + STIM_DUR + SOA_DUR) & (frame < ITI_DUR + STIM_DUR*2 + SOA_DUR):#--------------------------STIM_2 ONSET
             
                        # draw cue
                        if order == 'cue_first':
                            if stim_shape == 'circle':
                                crc_stim.draw()
                            else:
                                sqr_stim.draw()
                        else:
                            cue_stim.draw()

                    if (frame >= ITI_DUR + STIM_DUR*2 + SOA_DUR) & (frame < ITI_DUR + STIM_DUR*2 + SOA_DUR + RES_DUR_DEMO):#---------RES ONSET 

                        # draw fixation
                        fix_stim.draw()

                    if (frame >= ITI_DUR + STIM_DUR*2 + SOA_DUR + RES_DUR_DEMO): #----------------------------------------------------End trial if too slow 
                        break

                    # collect response input
                    quitPressed = event.getKeys(keyList = QUITKEYS)
                    pressed = event.getKeys(keyList = list(RESPKEYS.values()), timeStamped = clock)
                    if quitPressed: # exit task 
                        core.quit()
                    elif pressed:
                        response = pressed[0][0]
                        rt = pressed[0][1]
                        break

                    # show response prompts for first 3 demo blocks
                    if txt in ['DEMO_1', 'DEMO_2', 'DEMO_3']:
                        txt_stim2.setAutoDraw(True)
                    else: 
                        txt_stim2.setAutoDraw(False)

                    # show stims
                    win.flip()
                    frame += 1 

                # calculate correct response
                if cue == 'colour':
                    if stim_colour == 'blue':
                        cor_response = RESPKEYS['blue']
                    elif stim_colour == 'orange':
                        cor_response = RESPKEYS['orange']
                elif cue == 'shape':
                    if stim_shape == 'circle':
                        cor_response = RESPKEYS['circle']
                    elif stim_shape == 'square':
                        cor_response = RESPKEYS['square']
        
                # calculate response accuracy and points if a response is made
                if pressed: # or early_pressed   
                    if cor_response == response:
                        acc = 1
                        correct_responses_tally.append(acc)
                    else:
                        acc = 0
                    # update points and feedback display 
                    if acc == 0:
                        points = 0
                        if rt < MIN_RT:
                            txt_stim.text = 'Incorrect!\n No points.\n Slow down!'
                        else: 
                            txt_stim.text = 'Incorrect!\n No points.'
                    elif acc == 1:
                            points = np.floor(points_function(rt, min_rt=MIN_RT, max_rt=max_rt)).astype(int)
                            txt_stim.text = f'+ {points} points!'

                # if no response made, assign missing values etc.     
                elif not pressed: #(not early_pressed) & (
                    txt_stim.text = 'Too slow! No points.'
                    acc = 999
                
                if acc == 1:
                    fdb_dur = FDB_DUR
                else:
                    fdb_dur = FDB_DUR_LNG

                for frame in range(0, fdb_dur): # --------------------------------------------------- FDB ONSET
        
                    # draw stimulus
                    txt_stim.draw()
                    win.flip()

            # stop showing key reminders
            txt_stim2.setAutoDraw(False)

            # present instructions 
            practice_block_accuracy = (sum(correct_responses_tally)/NPRACTRIALS)*100
            if practice_block_accuracy > 75:
                txt_stim.text = f'''Great job, you got {practice_block_accuracy}% of trials correct!\n\n Press ENTER to continue.''' 
            else:
                txt_stim.text = f'''You got {practice_block_accuracy}% of trials correct.\n\nLet's try that again. \n\nPress SPACE to continue.''' 
            # present text
            while True:
        
                # draw stimuli
                txt_stim.draw()
                win.flip()
        
                # collect user input to exit 
                repeat = event.getKeys(keyList = CONKEYS)
                cont = event.getKeys(keyList = EXITKEYS)
                if repeat or cont: 
                    break
            if cont:
                break

## Start experiment ------------------------------------------------------------------ EXP ONSET
for txt in mainText.keys():

    event.clearEvents()
    logging.warning(f'{txt}')
    logging.flush()
    txt_stim.text = mainText[txt]
    while True:

        # draw stimuli
        txt_stim.draw()
        win.flip()

        # collect user input to exit 
        pressed = event.getKeys(keyList = CONKEYS)
        if pressed: 
            break

logging.warning('START_EXP')
logging.flush()
framesPerBlock = {}
runningTrialNo = 1
cumulative_points = 0
cumulative_cents = 0
for block in range(1, NBLOCKS + 1): #------------------------------------------------- BLOCK ONSET

    # update high value dimension
    high_val_dim = DIMS[high_val_dim_array[block - 1]] # block - 1 to get index to start at 0 again
    low_val_dim = DIMS[1 - high_val_dim_array[block - 1]]

    # present instructions 
    txt_stim.text = f'''
    This is Block {block}. \n\n 
    {high_val_dim.upper()} = {POINTS_HIGH}x POINTS BOOST. \n
    Remember your response keys: \n
    ORANGE = {RESPKEYS["orange"].upper()}
    CIRCLE = {RESPKEYS["circle"].upper()}
    BLUE = {RESPKEYS["blue"].upper()}
    SQUARE = {RESPKEYS["square"].upper()} \n\n
    Please keep your eyes on the fixation cross throughout each trial. \n\n\n
    Press space to begin.''' 

    while True:

        # draw stimuli
        txt_stim.draw()
        win.flip()

        # collect user input to exit 
        pressed = event.getKeys(keyList = CONKEYS)
        if pressed: 
            break
    
    # randomise trial order at start of each block and make sure there are about the same number (+- 1) of dimension switch vs. stay trials
    trl_strc = trl_stc.copy()
    while True:
        np.random.shuffle(trl_strc)
        repeats = 0
        switch = 0
        for i in range(0, len(trl_strc)-1):
            if trl_strc[i][1] == trl_strc[i+1][1]:
                repeats += 1
            elif trl_strc[i][1] != trl_strc[i+1][1]:
                switch += 1
        if np.isin(repeats - switch, [-1, 1]) == True:
            break
        else: 
            continue 
    
    # logging 
    logging.warning(f'START_BLOCK_{block}')
    logging.flush()
    # turn on recording of frame intervals
    win.recordFrameIntervals = True
    framesPerTrial = {}
    points_this_block = 0
    cents_this_block = 0
    # start presenting trials ---------------------------------------------------------- TRIAL ONSET
    for trial in range(0, NTRIALS):
        
        # set stimulus properties for this trial 
        order = trl_strc[trial][0] # assign order
        cue = trl_strc[trial][1] # assign cue
        stim_colour = trl_strc[trial][2] # assign colour
        stim_shape = trl_strc[trial][3] # assign shape   

        if cue == 'colour':
            cue_stim.text = 'COLOUR'
        else:
            cue_stim.text = 'SHAPE'

        if stim_shape == 'circle':
            if stim_colour == 'orange':
                crc_stim.fillColor = ORANGE
            else:
                crc_stim.fillColor = BLUE
        else:
            if stim_colour == 'orange':
                sqr_stim.fillColor = ORANGE
            else:
                sqr_stim.fillColor = BLUE      
         
        ITI_DUR = np.random.randint(ITI_RANGE[0], ITI_RANGE[1])
        
        # reset frame interval counting
        win.frameClock.reset()
        win.frameIntervals = []

        # housekeeping
        event.clearEvents()
        logging.warning(f'START_TRIAL_{trial}')
        logging.warning('START_ISI')
        # start stimulus presentation -------------------------------------------------- ITI ONSET

        for frame in range(0, ITI_DUR): 

            # draw fixation
            fix_stim.draw()
            win.flip()
            
        logging.warning('START_STIM1')
        for frame in range(0, STIM_DUR): # --------------------------------------------- STIM_1 ONSET

            # draw stim
            if order == 'cue_first':
                cue_stim.draw()
            else:
                if stim_shape == 'circle':
                    crc_stim.draw()
                else:
                    sqr_stim.draw()
            win.flip()

        logging.warning('START_SOA')
        for frame in range(0, SOA_DUR): # ---------------------------------------------- SOA ONSET

            # draw fixation
            fix_stim.draw()
            win.flip()

        logging.warning('START_STIM2')
        event.clearEvents()
        clock.reset()
        for frame in range(0, STIM_DUR): # --------------------------------------------- STIM_2 ONSET

            # draw cue
            if order == 'cue_first':
                if stim_shape == 'circle':
                    crc_stim.draw()
                else:
                    sqr_stim.draw()
            else:
                cue_stim.draw()
            win.flip()

            # collect response input
            early_pressed = event.getKeys(keyList = list(RESPKEYS.values()), timeStamped = clock)
            if early_pressed:
                logging.warning('RESPONSE')
                logging.flush()
                response = early_pressed[0][0]
                rt = early_pressed[0][1]
                break

        logging.warning('START_RES')
        for frame in range(0, RES_DUR): # ------------------------------------------------ RES ONSET

            # don't show if participant has already responded
            if early_pressed:
                break

            # draw stimuli
            fix_stim.draw()
            win.flip()
            
            # collect response input
            quitPressed = event.getKeys(keyList = QUITKEYS)
            pressed = event.getKeys(keyList = list(RESPKEYS.values()), timeStamped = clock)
            if quitPressed: # exit task 
                core.quit()
            elif pressed:
                logging.warning('RESPONSE')
                logging.flush()
                response = pressed[0][0]
                rt = pressed[0][1]
                break

        # calculate correct response
        if cue == 'colour':
            if stim_colour == 'blue':
                cor_response = RESPKEYS['blue']
            elif stim_colour == 'orange':
                cor_response = RESPKEYS['orange']
        elif cue == 'shape':
            if stim_shape == 'circle':
                cor_response = RESPKEYS['circle']
            elif stim_shape == 'square':
                cor_response = RESPKEYS['square']

        # calculate response accuracy and points if a response is made
        if early_pressed or pressed:  
            if cor_response == response:
                acc = 1
            else:
                acc = 0
            # update points and feedback display 
            if acc == 0:
                points = 0
                if rt < MIN_RT:
                    txt_stim.text = 'Incorrect! \n No points. \n Slow down!'
                else: 
                    txt_stim.text = 'Incorrect! \n No points.'
            elif acc == 1:
                if high_val_dim == cue:
                    points = np.floor(points_function(rt)*POINTS_HIGH).astype(int)
                else:
                    points = np.floor(points_function(rt)*POINTS_LOW).astype(int)
                txt_stim.text = f'+ {points} points!'
                 
        # if no response made, assign missing values etc.     
        elif (not early_pressed) & (not pressed):
            response = 999
            rt = 999
            acc = 999
            points = 0
            txt_stim.text = 'Too slow! No points.'
        
        if acc == 1:
            fdb_dur = FDB_DUR
        else:
            fdb_dur = FDB_DUR_LNG

        logging.warning('START_FDB')
        for frame in range(0, fdb_dur): # --------------------------------------------------- FDB ONSET

            # draw stimulus
            txt_stim.draw()
            win.flip()
        
        # calculate reward
        cents_this_trial = points*cents_per_point
        points_this_block += points
        cents_this_block += cents_this_trial
        cumulative_cents += cents_this_trial
        cumulative_points += points

        # update experiment handler data to save
        exp.addData('Trial', trial + 1)
        exp.addData('RunningTrialNo', runningTrialNo)
        exp.addData('Block', block)
        exp.addData('HighValueDim', high_val_dim)
        exp.addData('Order', order)
        exp.addData('StimulusColour', stim_colour)
        exp.addData('StimulusShape', stim_shape)
        exp.addData('ResponseRule', cue)
        exp.addData('CorrectResponse', cor_response)
        exp.addData('Response', response)
        exp.addData('RT', rt)
        exp.addData('Accuracy', acc)
        exp.addData('Points', points)
        exp.addData('CumulativePoints', cumulative_points)
        exp.addData('Cents', cents_this_trial)
        exp.addData('CumulativeCents', cumulative_cents)

        exp.nextEntry() # move to next line in data output
        runningTrialNo += 1
        framesPerTrial[f'Trial_{trial + 1}'] = win.frameIntervals
        logging.flush()

    # take a break and save data at the end of the block --------------------------------------------------
    win.recordFrameIntervals = False
    exp.saveAsWideText(
        fileName = FILEPATH, 
        appendFile=None,
        fileCollisionMethod='overwrite')
    framesPerBlock[f'Block_{block}'] = framesPerTrial
    with open(FRMSFILEPATH, 'w') as file:
        file.write(json.dumps(framesPerBlock)) 

    # present end of block text
    if block < NBLOCKS:
        txt_stim.text = f'''
        End of Block {block}. Take a break. \n\n 
        You earned {points_this_block} points in that block! That's an extra ${np.round(cents_this_block/100, 2)}\n\n
        You've earned an extra ${np.round(cumulative_cents/100, 2)} so far. Great job! \n\n
        Press SPACE when you're ready to continue.''' 
    elif block == NBLOCKS:
        txt_stim.text = f'''
        End of Block {block}. You're all done! \n\n 
        You earned {cumulative_points} points! That's an extra ${np.round(cumulative_cents/100, 2)}\n\n
        Press SPACE to exit the experiment.''' 

    event.clearEvents()
    txt_idx = 0
    while True:

        # draw
        txt_stim.draw()
        win.flip()

        # collect user input to exit 
        pressed = event.getKeys(keyList = CONKEYS)
        if pressed:
            break

        # udpate frame
        txt_idx += 1 
    
# end experiment and shut everything down ----------------------------------------------------
logging.warning(f'EXTRA REIMBURSEMENT: ${np.round(cumulative_cents/100, 2)}')
logging.warning('END_EXPERIMENT')
logging.flush()
win.close()

## ======================================================================
## Run debriefing
## ======================================================================
if DEBRIEF: 
    debrief = {
        'I acknowledge that I have been appropriately debriefed and shown a copy of the debriefing questions': False,
        'Name': '',
        'Date': ''}
    dlg = gui.DlgFromDict(
        debrief, 
        title = 'Acknowledgement of Debriefing')
    if not dlg.OK:
        core.quit()

    # create experiment handler to save output
    dbrf = data.ExperimentHandler(name=EXPERIMENT,
                                  extraInfo=debrief)
    dbrf.dataNames = []
    dbrf.nextEntry() 
    identifier = datetime.now().timestamp()
    identifier = str.split(str(identifier), '.')[0]    
    dbrf.saveAsWideText(
            fileName = DATAPATH + f'AcknowledgementOfDebriefing_{identifier}.txt', 
            appendFile=None,
            fileCollisionMethod='overwrite')

