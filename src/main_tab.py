# -*- coding: utf-8 -*-
"""
Main tab

@author: karlen
"""

from __future__ import print_function
import ipywidgets as widgets

import open_tab
import settings_tab
import explore_tab
import analyze_tab
import compare_tab

def init_tab(self):

    self.main_tab_widget = widgets.Tab()
    self.open_tab_widget = open_tab.get_tab(self)
    self.main_tab_widget.children = [self.open_tab_widget]
    self.main_tab_widget.set_title(0, 'Open')

def all_tabs(self):
    # adds more children, only if model exists

    if self.model is not None:
        settings_t = settings_tab.get_tab(self)
        explore_t = explore_tab.get_tab(self)
        analyze_t = analyze_tab.get_tab(self)
        compare_t = compare_tab.get_tab(self)
        self.main_tab_widget.children = [self.open_tab_widget, 
                                         settings_t, explore_t, analyze_t,
                                         compare_t]
        self.main_tab_widget.set_title(0, 'Open')
        self.main_tab_widget.set_title(1, 'Settings (explore)')
        self.main_tab_widget.set_title(2, 'Explore')
        self.main_tab_widget.set_title(3, 'Analyze')
        self.main_tab_widget.set_title(4, 'Compare')
    