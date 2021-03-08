import tkinter as tk
import json
from tkinter import *
import os

varNames = ['version', 'delay', 'fill', 'replace', 'webMod', 'popupMod', 'audioMod', 'promptMod', 'replaceThresh', 'slowMode']
defaultVars = ['1.1.0', '250', '0', '0', '15', '40', '0', '0', '500', '0']

PATH = os.path.abspath(os.getcwd())

settingJsonObj = {}
for var in varNames:
    settingJsonObj[var] = defaultVars[varNames.index(var)]

if not os.path.exists(PATH + '\\config.cfg'):
    with open(PATH + '\\config.cfg', 'w') as f:
        f.write(json.dumps(settingJsonObj))

with open(PATH + '\\config.cfg', 'r') as f:
    settingJsonObj = json.loads(f.readline())

root = tk.Tk()
root.title('EdgeWare Config')
root.resizable(False,False)
root.geometry('260x400')
root.iconbitmap(os.path.abspath(os.getcwd()) + '\\resource\\icon.ico')

def configWindow(delay, fill, replace, webMod, popupMod, audioMod, promptMod, slow):
    delayVar = IntVar(root, value=settingJsonObj['delay'], name='delay')
    fillVar = IntVar(root, value=settingJsonObj['fill'], name='fill')
    replaceVar = IntVar(root, value=settingJsonObj['replace'], name='replace')
    webModVar = IntVar(root, value=settingJsonObj['webMod'], name='webMod')
    audModVar = IntVar(root, value=settingJsonObj['audioMod'], name='audioMod')
    promptModVar = IntVar(root, value=settingJsonObj['promptMod'], name='promptMod')
    popupModVar = IntVar(root, value=settingJsonObj['popupMod'], name='popupMod')
    slowVar = IntVar(root, value=settingJsonObj['slowMode'], name='slow')

    timerSlider = Scale(root, label='Timer Delay (ms)', from_=50, to=2000, orient=HORIZONTAL, variable=delayVar)
    timerSlider.set(delay)
    timerSlider.pack()
    webSlider = Scale(root, label='Website Freq', from_=0, to=100, orient=HORIZONTAL, variable=webModVar)
    webSlider.set(webMod)
    webSlider.pack()
    popupSlider = Scale(root, label='Popup Freq', from_=0, to=100, orient=HORIZONTAL, variable=popupModVar)
    popupSlider.set(popupMod)
    popupSlider.pack()
    audioSlider = Scale(root, label='Audio Freq', from_=0, to=100, orient=HORIZONTAL, variable=audModVar)
    audioSlider.set(audioMod)
    audioSlider.pack()
    promptSlider = Scale(root, label='Prompt Freq', from_=0, to=100, orient=HORIZONTAL, variable=promptModVar)
    promptSlider.set(promptMod)
    promptSlider.pack()
    isFill = Checkbutton(root, text='Fill Drive', variable=fillVar)
    isFill.pack()
    slowBox = Checkbutton(root, text='Slow Fill', variable=slowVar)
    slowBox.pack()
    isReplace = Checkbutton(root, text='Replace Images', variable=replaceVar)
    isReplace.pack()
    saveButton = Button(root, text='Save Config', command= lambda: save(delayVar.get(), fillVar.get(), replaceVar.get(), webModVar.get(), popupModVar.get(), audModVar.get(), promptModVar.get(), slowVar.get())) 
    saveButton.pack()
    root.mainloop()

#['version', 'delay', 'fill', 'replace', 'webMod', 'popupMod', 'audioMod', 'promptMod', 'replaceThresh', 'slowMode']
def save(delay, fill, replace, webMod, popupMod, audioMod, promptMod, slow):
    val = [settingJsonObj['version'], delay, fill, replace, webMod, popupMod, audioMod, promptMod, 500, slow]
    for v in varNames:
        settingJsonObj[v] = val[varNames.index(v)]
    with open('config.cfg', 'w') as f:
        f.write(json.dumps(settingJsonObj))
    exit()

with open('config.cfg', 'r') as f:
    vals = f.readline().split(';')

configWindow(int(settingJsonObj['delay']), int(settingJsonObj['fill'])==1, int(settingJsonObj['replace'])==1, int(settingJsonObj['webMod']), int(settingJsonObj['popupMod']), int(settingJsonObj['audioMod']), int(settingJsonObj['promptMod']), int(settingJsonObj['slowMode'])==1)