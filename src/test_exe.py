from stupidArtnet import StupidArtnet
import copy
import random
import string
import sys
import time
import os
import PySimpleGUI as sg
import pygame_gui
import pygame
from pygame.event import Event
from pygame_gui.elements import UIButton
from pygame_gui.windows import UIColourPickerDialog
from pynput.mouse import Listener
import pyautogui
import json
from PIL import Image, ImageGrab

"""
    Demo - Simple Snake Game using PyGame and PySimpleGUI
    This demo may not be fully functional in terms of getting the coordinate
    systems right or other problems due to a lack of understanding of PyGame
    The purpose of the demo is to show one way of adding a PyGame window into your PySimpleGUI window
    Note, you must click on the game area in order for PyGame to get keyboard strokes, etc.
    Tried using set_focus to switch to the PyGame canvas but still needed to click on game area
"""

# --- Globals ---
# Colors
BLACK = (0, 0, 0)

print(BLACK)