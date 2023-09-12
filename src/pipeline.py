from stupidArtnet import StupidArtnet
import json
from helpers import *

# Setup Constants
DEFAULT_PACKET_SIZE = 512
DEFAULT_FPS = 40
DEFAULT_LIGHT_NUM = 6
ENFORCE_EVEN_PACKET = True
ENFORCE_BROADCAST = True
DEFAULT_UNIVERSE_ID = 1
DEFAULT_CHANNEL_START_ID = 1
DEFAULT_CHANNEL_WIDTH = 11
PRESETS_PATH = '../presets/preset.json'
BITFOCUS_CONFIG_FOLDER = '../config/'
BITFOCUS_CONFIG_PATH = BITFOCUS_CONFIG_FOLDER+'bitfocus_config.json'
DEFAULT_IP = '169.254.79.148'
PRESET_BUTTON_PREFIX = 'preset_group_'


#### Pipeline
def live_color_picker(ip:str=DEFAULT_IP, num_lights:int=DEFAULT_LIGHT_NUM, groups_mapping=DEFAULT_GROUPS,
                      packet_size=DEFAULT_PACKET_SIZE, fps=DEFAULT_FPS,
                      even_packet_size = ENFORCE_EVEN_PACKET, broadcast=ENFORCE_BROADCAST,
                      universe_id=DEFAULT_UNIVERSE_ID,channel_width=DEFAULT_CHANNEL_WIDTH,
                      presets_path=PRESETS_PATH):
    """
    Pipeline to select color of each light source in real time.

    :param ip: Ip of the ArtNet receiving device.
    :param num_lights: Number of lights to be configured. 
    :param groups_mapping: Mapping between group name and set of lights.
    :param packet_size: Size of ArtNet packets.
    :param fps: Refresh rate of the server.
    :param even_packet_size: Boolean variable to enforce even packets (May be
                             required by the receiver).
    :param broadcast: Boolean variable to allow broadcast in the subnet.
    :param universe_id: Identifier of the universe with which we want to communicate.
    :param channel_width: Number of fixtures per channel.
    :param presets_path: Path to the JSON file containing the presets.
    
    """
    # Init connections
    server = StupidArtnet(ip,universe_id,packet_size,fps,even_packet_size,broadcast)
    with open(PRESETS_PATH,'r') as file:
        presets = json.load(file)
   # Lights
    lights = []
    for i in range(num_lights):
        channel_start = DEFAULT_CHANNEL_START_ID + i*channel_width
        lights.append(Light(name='light_'+str(i+1),channel=Channel(server,channel_start,channel_width)))
    # Groups
    groups = []
    for group_name, group_lights_names in groups_mapping.items():
        group_lights = [l for l in lights if l.name in group_lights_names]
        groups.append(Group(name=group_name, lights=group_lights))
    # light Object Mapping
    light_object_dict = [('group_'+str(i+1),groups[i]) for i in range(len(groups))]
    light_object_dict.extend([('light_'+str(i+1),lights[i]) for i in range(num_lights)])
    light_object_dict = dict(light_object_dict)
    # UI Loop
    UI_process(ip,light_object_dict,presets,presets_path)

live_color_picker()