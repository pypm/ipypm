# -*- coding: utf-8 -*-
"""
Main tab

@author: karlen
"""

from __future__ import print_function
import ipywidgets as widgets

import open_tab
import settings_tab

main_model = None

def get_tab(self):

    main_tab = widgets.Tab()

    open_t = open_tab.get_tab(self)
    settings_t = settings_tab.get_tab(self)

    main_tab.children = [open_t, settings_t]
    main_tab.set_title(0, 'Open')
    main_tab.set_title(1, 'Settings')
    
    return main_tab
