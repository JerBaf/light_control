from stupidArtnet import StupidArtnet
import copy
import random
import string
import PySimpleGUI as sg
import pyautogui
import json
from PIL import ImageGrab
from light_sources import *

# Setup Constants
DEFAULT_PACKET_SIZE = 512
DEFAULT_FPS = 40
ENFORCE_EVEN_PACKET = True
ENFORCE_BROADCAST = True
DEFAULT_UNIVERSE_ID = 1
DEFAULT_CHANNEL_START_ID = 1
DEFAULT_CHANNEL_WIDTH = 11
PRESETS_PATH = '../presets/preset.json'
BITFOCUS_CONFIG_FOLDER = '../config/'
BITFOCUS_CONFIG_PATH = BITFOCUS_CONFIG_FOLDER+'bitfocus_config.json'

PRESET_BUTTON_PREFIX = 'preset_group_'
# Control Constants
DIMMER_ID = 1
DIMMER_FINE_ID = 2
STROBE_ID = 3
RED_ID = 4
GREEN_ID = 5
BLUE_ID = 6
WHITE_ID = 7
AMBER_ID = 8
UV_ID = 9
PRESET_ID = 10
SOUND_ID = 11
DEFAULT_LIGHT_VALUE = [255]+[0]*(DEFAULT_CHANNEL_WIDTH-1)
RESET_VALUE = [0]*DEFAULT_CHANNEL_WIDTH
LIGHT_OFF_VALUE = RESET_VALUE
# Config
MAX_BUTTON_ID = 32
DEFAULT_FADE_TIME = 750
DEFAULT_ID_LENGTH = 21
# Mappings
FIXTURE_TO_ID_DICT = {'dimmer':DIMMER_ID,'red':RED_ID,'green':GREEN_ID,
                    'blue':BLUE_ID,'white':WHITE_ID,'amber':AMBER_ID,
                    'uv':UV_ID}
ID_TO_FIXTURE_DICT = dict([(i,fixture) for fixture,i in FIXTURE_TO_ID_DICT.items()])
DEFAULT_GROUPS = {'group_1':['light_1','light_3','light_5'],
                  'group_2':['light_2','light_4','light_6']}
# Events
LIGHT_SELECTION_EVENTS = {'group_1','group_2','light_1','light_2','light_3',
              'light_4','light_5','light_6'}
LIGHT_FIXTURE_EVENTS = set(['slider_'+fixture for fixture in FIXTURE_TO_ID_DICT.keys()])



#### Config
def create_config_structure(ip_address:str,preset:dict,number_of_pages:int=10,
                            instance_id:str="TKdJlb-N6u8sGy0ufAlx1") -> dict:
    """ 
    Create global BitFocus Companion config skeleton. 
    
    :param ip_address: IP address of the artnet module.
    :param number_of_pages: Number of button pages to generate.

    :return: Config in dictionnary format.
    """
    config = {'version':3,'type':'full','pages':dict([(str(i+1),{"name":"PAGE"}) for i in range(number_of_pages)]),
              'controls':create_controls_config(preset,instance_id),
              'instances':{instance_id:{"instance_type":"generic-artnet",
                        "sortOrder":1,"label":"artnet","isFirstInit":False,
                        "config":{"host":ip_address,"universe":1,
                        "timer_slow":1000,"timer_fast":40},"enabled":True,
                        "lastUpgradeIndex":0}}}
    return config

def generate_config_id(id_length:int) -> str:
    """ Generate ascii random id of given length. """
    return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=id_length))

def create_channel_config(channel_id:int,channel_value:int,
                            instance_id:str,id_length:int,
                            fade_time:int) -> dict:
    """ Create config step for a single channel. """
    channel_dict = {"id":generate_config_id(id_length),"action":"set",
                    "instance":instance_id,
                    "options":{"channel":channel_id,"value":channel_value,
                    "duration":fade_time},"delay":0}
    return channel_dict

def create_button_config(preset_config:dict,instance_id:str,preset_name:str,
                        id_length:int,fade_time:int) -> dict:
    """ Create the Bitfocus companion config for a single button based on a preset. """
    light_values = [v for values in list(preset_config.values())[2:] for v in values]
    light_data = [(idx+1,light_values[idx]) for idx in range(len(light_values))]
    button_config = {"type":"button",
                     "style":{"text":preset_name,"size":"auto","png":None,
                              "alignment":"center:top","pngalignment":"center:center",
                              "color":16777215,"bgcolor":0,"show_topbar":True},
                     "options":{"relativeDelay":False,"stepAutoProgress":True},
                     "feedbacks":[],
                     "steps":{"0":{"action_sets":{"down":[
                         create_channel_config(idx,value,instance_id,id_length,fade_time) for
                         idx,value in light_data],
                     "up":[]},"options":{"runWhileHeld":[]}}}}
    return button_config
    
def create_controls_config(preset:dict,instance_id:str,id_length:int=DEFAULT_ID_LENGTH,
                            fade_time:int=DEFAULT_FADE_TIME) -> dict:
    """ Create the global control config, i.e. all the different buttons. """
    control_dict = dict()
    bank_id = 1
    button_id = 1
    for preset_name, preset_config in preset.items():
        button_config = create_button_config(preset_config,instance_id,
                                                preset_name,id_length,fade_time)
        control_dict[f'bank:{bank_id}-{button_id}'] = copy.deepcopy(button_config)
        # If we reached the end of the page
        if button_id == MAX_BUTTON_ID:
            bank_id +=1
            button_id = 0
        button_id += 1
    return control_dict

#### GUI
##### Layout
def create_preset_layout(presets:dict) -> list:
    """ Create the layout for the preset menu. """
    layout = []
    for preset_group in presets.keys():
        layout.append([sg.Button(preset_group,button_color="black on SkyBlue1",key=PRESET_BUTTON_PREFIX+preset_group,s=(90,5))])
    return layout

def create_preset_selector_layout(presets:dict,preset_group:str) -> list:
    """ Create the layout of the popup window for presets. """
    layout = [[sg.Text(preset_group,justification='center',font='bold',s=(80,3))]]
    for preset_name, preset_state in presets[preset_group].items():
        preset_line = []
        preset_line.append(sg.Button(preset_name,button_color="black on SkyBlue1",key=f'preset_{preset_name}',s=(12,3)))
        for light_source_name, light_source_state in preset_state.items():
            if 'light' in light_source_name:
                hex_color = sg.rgb(*light_source_state[RED_ID-1:BLUE_ID])
                preset_line.append(sg.Text('',background_color=hex_color,s=(12,1)))
        layout.append(preset_line.copy())
    return layout

def create_edit_layout() -> list:
    """ Create the user interface layout using PySimpleGui. """
    layout = [
    [sg.Column([[sg.Text("Control Center Group 1",justification="center",s=(56,1))],
                [sg.Button("Main",button_color="black on SkyBlue1",key="group_1",s=(12,5)),
                 sg.Text('',background_color='white',s=(0,5)),
                 sg.Button("Light 1",button_color="black on SkyBlue1",key="light_1",s=(12,5)),
                 sg.Button("Light 3",button_color="black on SkyBlue1",key="light_3",s=(12,5)),
                 sg.Button("Light 5",button_color="black on SkyBlue1",key="light_5",s=(12,5))],
                [sg.Text("Control Center Group 2",justification="center",s=(56,1))],
                [sg.Button("Ambiance",button_color="black on gold",key="group_2",s=(12,5)),
                 sg.Text('',background_color='white',s=(0,5)),
                 sg.Button("Light 2",button_color="black on gold",key="light_2",s=(12,5)),
                 sg.Button("Light 4",button_color="black on gold",key="light_4",s=(12,5)),
                 sg.Button("Light 6",button_color="black on gold",key="light_6",s=(12,5))],]),
     sg.Column([[sg.Text('Save/Load Controls',justification='center',s=(30,1))],
                [sg.Text('',s=(8,0)),
                 sg.Button("Load Preset",button_color="black on SkyBlue1",key="load",s=(12,5)),
                 sg.Text('',s=(8,0))],
                [sg.Text('',s=(0,1))],
                [sg.Text('',s=(8,0)),
                 sg.Button("Save",button_color="black on SkyBlue1",key="save",s=(12,5)),
                 sg.Text('',s=(8,0))]])],
    [sg.Text("Light Source Under Control: ",justification='center',size=91,key='target')],
    [sg.Column([[sg.Image('../img/color_wheel.png',size=(512,512), enable_events=True, key='color_wheel')]]),
     sg.Column([[sg.Text('Red', s=(6,1)),sg.Slider((0,255), default_value=0, resolution=1, enable_events=True,
                         orientation='horizontal', tick_interval=255, key='slider_red')],
                [sg.Text('Green', s=(6,1)),sg.Slider((0,255), default_value=0, resolution=1, enable_events=True,
                         orientation='horizontal', tick_interval=255, key='slider_green')],
                [sg.Text('Blue', s=(6,1)),sg.Slider((0,255), default_value=0, resolution=1, enable_events=True,
                         orientation='horizontal', tick_interval=255, key='slider_blue')],
                [sg.Text('White', s=(6,1)),sg.Slider((0,255), default_value=0, resolution=1, enable_events=True,
                         orientation='horizontal', tick_interval=255, key='slider_white')],
                [sg.Text('Amber', s=(6,1)),sg.Slider((0,255), default_value=0, resolution=1, enable_events=True,
                         orientation='horizontal', tick_interval=255, key='slider_amber')],
                [sg.Text('UV', s=(6,1)),sg.Slider((0,255), default_value=0, resolution=1, enable_events=True,
                         orientation='horizontal', tick_interval=255, key='slider_uv')],
                [sg.Text('Dimmer', s=(6,1)),sg.Slider((0,255), default_value=0, resolution=1, enable_events=True,
                         orientation='horizontal', tick_interval=255, key='slider_dimmer')]])]]
    return layout

def create_UI_layout(presets:dict) -> list:
    """ Create the user interface layout using PySimpleGui. """
    layout = [[sg.TabGroup([[
                sg.Tab('Presets',create_preset_layout(presets)),
                sg.Tab('Edit',create_edit_layout())]])]]
    return layout

##### Helpers
def update_sliders(window:sg.Window, light_object:LightSource):
    """ Update the sliders with the light source state. """
    for name in list(LIGHT_FIXTURE_EVENTS):
        fixture_id = FIXTURE_TO_ID_DICT[name.split('_')[-1]]
        window[name].update(light_object.state[fixture_id-1])
    
def update_button(window:sg.Window, light_object:LightSource):
    """ Update the button with the light source state. """
    button_id = light_object.name
    hex_color = sg.rgb(*light_object.state[RED_ID-1:BLUE_ID])
    window[button_id].update(button_color=hex_color)

def update_buttons(window:sg.Window, light_object_dict:dict):
    """ Update all buttons with the light sources state. """
    for light_object in light_object_dict.values():
        update_button(window,light_object)
    
def save_presets(presets:dict,presets_path:str):
    """ Save the presets given as a dictionnary in json format. """
    with open(presets_path,'w') as file:
        json.dump(presets,file)

##### Process
def preset_process(presets:dict,preset_group:str,light_object_dict:dict):
    """ """
    layout = create_preset_selector_layout(presets,preset_group)
    preset_window = sg.Window('Preset', layout, background_color='black', resizable=False).finalize()
    preset_selected = False
    while True:
        # Update GUI
        event, values = preset_window.read(timeout=1000)
        if event == sg.WIN_CLOSED:
            break 
        elif event != '__TIMEOUT__':
            preset_state = presets[preset_group][event.split('preset_')[-1]]
            for light_source_name, state in preset_state.items():
                light_object_dict[light_source_name].set_fixture_values(state)
                light_object_dict[light_source_name].turn_on()
            preset_selected = True
            break
    preset_window.close();
    return preset_selected

def save_preset_process(presets:dict,light_object_dict:dict,presets_path:str):
    """ """
    layout = create_preset_layout(presets)
    preset_window = sg.Window('Save Preset', layout, background_color='black', resizable=False).finalize()
    while True:
        # Update GUI
        event, values = preset_window.read(timeout=1000)
        if event == sg.WIN_CLOSED:
            break 
        elif event != '__TIMEOUT__':
            text = sg.popup_get_text('Entrez nom du preset', title="Textbox")
            if text != None and text != '':
                if text in presets[event.split(PRESET_BUTTON_PREFIX)[-1]].keys():
                    sg.popup_auto_close('Le nom du preset existe déjà, veuillez en entrer un nouveau.')
                else:
                    presets[event.split(PRESET_BUTTON_PREFIX)[-1]][text] = dict([(name,l.state) for name,l in light_object_dict.items()])
                    save_presets(presets,presets_path)
                    break
    preset_window.close();

def load_preset_process(window:sg.Window,presets:dict,light_object_dict:dict):
    """ """
    layout = create_preset_layout(presets)
    preset_window = sg.Window('Save Preset', layout, background_color='black', resizable=False).finalize()
    while True:
        # Update GUI
        event, values = preset_window.read(timeout=1000)
        if event == sg.WIN_CLOSED:
            break 
        elif event != '__TIMEOUT__':
            preset_selected = preset_process(presets,event.split(PRESET_BUTTON_PREFIX)[-1],light_object_dict)
            if preset_selected:
                update_buttons(window,light_object_dict)
            break
    preset_window.close();

def select_config(ip:str,presets:dict):
    """ """
    layout = create_preset_layout(presets)
    preset_window = sg.Window('Save Preset', layout, background_color='black', resizable=False).finalize()
    while True:
        # Update GUI
        event, values = preset_window.read(timeout=1000)
        if event == sg.WIN_CLOSED:
            break 
        elif event != '__TIMEOUT__':
            preset_name = event.split(PRESET_BUTTON_PREFIX)[-1]
            bitfocus_config = create_config_structure(ip,presets[preset_name])
            with open(BITFOCUS_CONFIG_FOLDER+preset_name+'.json','w') as f:
                json.dump(bitfocus_config,f)
            break
    preset_window.close();

def UI_process(ip:str,light_object_dict:dict,presets:dict,presets_path:str):
    """ 
    User interface process, handling user actions. 
    
    :param light_object_dict: Dictionnary with event_id as key and 
                              corresponding light object as value.
    
    """
    layout = create_UI_layout(presets)
    window = sg.Window("Delta Control", layout, background_color='black', resizable=False).finalize()
    window.bind('<Motion>', 'Motion')
    position = pyautogui.position()
    light_object = None
    while True:
        # Update GUI
        event, values = window.read(timeout=1000)
        if event == sg.WIN_CLOSED:
            select_config(ip,presets)
            for light_object in light_object_dict.values():
                light_object.turn_off()
            break
        elif PRESET_BUTTON_PREFIX in event:
            preset_group = event.split(PRESET_BUTTON_PREFIX)[-1]
            preset_selected = preset_process(presets,preset_group,light_object_dict)
            if preset_selected:
                update_buttons(window,light_object_dict)
        elif event == 'save':
            save_preset_process(presets,light_object_dict,presets_path)
        elif event == 'load':
            load_preset_process(window, presets,light_object_dict)
        elif event == 'color_wheel' and light_object != None:
            e = window.user_bind_event
            pixel = ImageGrab.grab(bbox=(
                e.x_root, e.y_root, e.x_root+1, e.y_root+1)).getdata()[0]
            light_object.set_rgb(pixel)
            update_sliders(window,light_object)
            update_button(window,light_object)
        elif event in LIGHT_FIXTURE_EVENTS and light_object != None:
            fixture_id = FIXTURE_TO_ID_DICT[event.split('_')[-1]]
            light_object.set_fixture_value(fixture_id,int(values[event]))
            update_button(window,light_object)
        elif event in LIGHT_SELECTION_EVENTS:
            light_object = light_object_dict[event]
            window['target'].update('Light Source Under Control: '+event)
            update_sliders(window,light_object)
            update_button(window,light_object)
            #light_object.blink()
    window.close();
