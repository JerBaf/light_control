from stupidArtnet import StupidArtnet
import time


# Setup Constants
DEFAULT_CHANNEL_START_ID = 1
DEFAULT_CHANNEL_WIDTH = 11
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
# Mappings
FIXTURE_TO_ID_DICT = {'dimmer':DIMMER_ID,'red':RED_ID,'green':GREEN_ID,
                    'blue':BLUE_ID,'white':WHITE_ID,'amber':AMBER_ID,
                    'uv':UV_ID}
ID_TO_FIXTURE_DICT = dict([(i,fixture) for fixture,i in FIXTURE_TO_ID_DICT.items()])
DEFAULT_GROUPS = {'group_1':['light_1','light_3','light_5'],
                  'group_2':['light_2','light_4','light_6']}




class Channel:
    """
    ArtNet Channel Object. A Channel is to a range of
    fixture of size channel_width. It is modeled by a
    simple part of the underlying artnet server. 
    
    """
    def __init__(self,server:StupidArtnet,channel_start:int,channel_width:int):
        """
        Instantiate an ArtNet Channel object.

        :param server: ArtNet server to communicate with the lights.
        :param channel_start: Id of the starting DMX address.
        :param channel_width: Width of the channel, equal to fixture number.
        
        """
        self.server = server
        self.channel_start = channel_start
        self.channel_width = channel_width
        self.offset = self.channel_start - 1

    def set_value(self,fixture_id:int,value:int,show=True):
        """
        Set the given fixture to the provided value.

        :param fixture_id: Id of the DMX fixture.
        :param value: Value of the fixture. Should be contained in [0,255].
        :param show: If set to True, then the packet will be sent.
        
        """
        if value < 0 or value > 255:
            raise ValueError(f'The value for {ID_TO_FIXTURE_DICT[fixture_id]} should be contained in [0,255]')
        self.server.set_single_value(self.offset+fixture_id,value)
        time.sleep(0.002)
        if show:
            self.server.show()
        time.sleep(0.002)

    def set_values(self,values:list):
        """
        Set all the fixtures of the channel to the given list of values.

        :param values: List of the fixtures values.
        
        """
        if len(values) != self.channel_width:
            raise ValueError(f'The list of values sent by the channel must be of size equal to the channel width: {self.channel_width}')
        for fixture_id, value in enumerate(values):
            self.set_value(fixture_id+1, value, show=False)

    def set_values_(self,values:list):
        """
        Set all the fixtures of the channel to the given list of values.

        :param values: List of the fixtures values.
        
        """
        self.set_multiple_values(self.offset+1,self.offset+self.channel_width,values)
    
    def reset(self):
        """ Reset the channel to its default state. """
        self.set_values(RESET_VALUE)


class LightSource:
    """ Abstract Light Source Object """
    
    def __init__(self,name:str,state=DEFAULT_LIGHT_VALUE.copy()):
        """ Instantiate the Light Source, defined by a name and a state. """
        self.name = name
        self.state = state

    def set_fixture_value(self,fixture_id:int, value:int):
        """ Define the value of a fixture. """

    def set_fixture_values(self,fixture_id:int, value:int):
        """ Define the values of all fixtures. """

    def blink():
        """ Make the Light Source Blink. """

    def set_rgb(self, values:list):
        """ Define the RGB values. """

    def turn_off(self):
        """ Turn off the Light Source"""

    def turn_on(self):
        """ Turn on the Light Source"""

    def reset(self):
        """ Reset the Light Source to its default state. """


class Light(LightSource):
    """
    Light object class. A light is model by the channel to which
    it is linked and a state. The latter is a list containing the 
    values for each of the fixture in the channel. 
    
    """
    
    def __init__(self,name:str, channel:Channel):
        """
        Create a Light instance.

        :param name: String identifier for the light. If the light is used in a Group,
                     please be sure to enter unique identifiers.
        :param channel: ArtNet channel object to which the light is bound. 

        """
        super().__init__(name)
        self.group_name = ''
        self.channel = channel
        self.turn_on()
        
    def set_fixture_value(self,fixture_id:int,value:int):
        """
        Set the fixture to the given value.

        :param fixture_id: Id of the fixture to be set.
        :param value: Integer value of the fixture, should be contained in [0,255].
        
        """
        new_state = self.state.copy()
        new_state[fixture_id-1] = value
        self.channel.set_value(fixture_id, value)
        self.state = new_state

    def set_fixture_values(self,values=[]):
        """
        Set the fixtures to the given list of values.

        :param values: Ordered list of values to be set.
        
        """
        self.channel.set_values(values)
        new_state = values
        self.state = new_state

    def set_rgb(self, values:list):
        """
        Set the RGB fixtures to the color code given in values.

        :param values: List containing the values for the red, green and blue fixtures.
        
        """
        for idx, fixture_id in enumerate([RED_ID,GREEN_ID,BLUE_ID]):
            self.set_fixture_value(fixture_id,values[idx])

    def blink(self,blink_time=0.2,n_repeat=2):
        """ """
        prev_state = self.state.copy()
        self.turn_off()
        time.sleep(blink_time)
        self.reset()
        self.set_fixture_value(WHITE_ID, 255)
        for i in range(n_repeat):
            time.sleep(blink_time)
            self.turn_on()
            time.sleep(blink_time)
            self.turn_off()
        self.set_fixture_values(prev_state)
        self.turn_on()

    def turn_off(self):
        """ Turn off the light by setting dimmer to 0. """
        self.set_fixture_value(DIMMER_ID,0)

    def turn_on(self):
        """ Turn on the light by setting dimmer to 255. """
        self.set_fixture_value(DIMMER_ID,255)

    def reset(self):
        """ Reset the light to its default state, i.e. zero value for each fixture. """
        self.turn_off()
        self.channel.reset()
        new_state = RESET_VALUE
        self.state = new_state


class Group(LightSource):
    """
    Group object class. A group is modeled by a list
    of lights. Every action applied to the group
    will be executed on all lights present. Each light in the 
    group should be unique and have a unique name.
    
    """
    
    def __init__(self,name:str, lights=[]):
        """
        Create a Group instance.

        :param name: String identifier for the group of lights.
        :param lights: List containing the initial lights of the group,
                       empty by default. All lights should be unique.
        
        """
        super().__init__(name)
        self.lights = []
        self.light_names = set()
        if len(self.light_names) != len(self.lights):
            raise ValueError('Duplicate names in the list of lights provided to the Group constructor')
        for l in lights:
            self.add_light(l)

    def add_light(self,light:Light):
        """
        Add a light to the existing pool. Must be a new unique light.

        :param light. Light object to add to the existing pool of lights in the group.
        
        """
        if light.name in self.light_names:
            raise ValueError('Tried to add a light whose name is already present in the group.')
        if light.group_name != '' and light.group_name != self.name:
            raise ValueError('Tried to add a light which is already present in another group.') 
        self.lights.append(light)
        light.set_fixture_values(self.state)
        light.group_name = self.name
        self.light_names = self.light_names.union(set(light.name))

    def remove_light(self,light_name:str):
        """
        Remove a light from the existing pool.

        :param light_name: Identifier of the light to be removed.
        
        """
        light.group_name = ''
        self.light_names = self.light_names.difference()
        self.lights = [l for l in self.lights if l.name != light_name]
        self.light.reset()
        
        
    def set_fixture_value(self, fixture_id:int, value:int):
        """
        Set the given fixture to 'value' for all lights in the group.

        :param fixture_id: Id of the fixture to be set.
        :param value: Integer value of the fixture, should be contained in [0,255].
        
        """
        new_state = self.state.copy()
        for l in self.lights:
            l.set_fixture_value(fixture_id,value)
        new_state[fixture_id-1] = value
        self.state = new_state

    def set_fixture_values(self,values=[]):
        """
        Set the fixtures to the given list of values for all lights in the group.

        :param values: Ordered list of values to be set.
        
        """
        for l in self.lights:
            l.set_fixture_values(values)
        new_state = values
        self.state = new_state

    def set_rgb(self, values:list):
        """
        Set the RGB fixtures to the color code given in values.

        :param values: List containing the values for the red, green and blue fixtures.
        
        """
        for idx, fixture_id in enumerate([RED_ID,GREEN_ID,BLUE_ID]):
            self.set_fixture_value(fixture_id,values[idx])

    def blink(self):
        """ Make all lights in the group blink. """
        for l in self.lights:
            l.blink()

    def turn_off(self):
        """ Turn off the light by setting dimmer to 0. """
        self.set_fixture_value(DIMMER_ID,0)

    def turn_on(self):
        """ Turn on the light by setting dimmer to 255. """
        self.set_fixture_value(DIMMER_ID,255)

    def reset(self):
        """ Reset all lights in the group to their default states, i.e. zero value for each fixture. """
        for l in self.lights:
            l.reset()