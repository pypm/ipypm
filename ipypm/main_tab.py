# -*- coding: utf-8 -*-
"""
Main tab

@author: karlen
"""

from __future__ import print_function
import ipywidgets as widgets

from ipypm import open_tab, settings_tab, explore_tab, analyze_tab, mcmc_tab, \
    compare_tab, edit_tab

def init_tab(self):

    self.main_tab_widget = widgets.Tab()
    self.open_tab_widget = open_tab.get_tab(self,'model')
    self.edit_tab_widget = edit_tab.get_tab(self)
    self.main_tab_widget.children = [self.open_tab_widget, self.edit_tab_widget]
    self.main_tab_widget.set_title(0, 'Open')
    self.main_tab_widget.set_title(1, 'Edit')


def all_tabs(self):
    # adds more children, only if model exists

    if self.model is not None:
        self.open_tab_widget = open_tab.get_tab(self, 'all')
        settings_t = settings_tab.get_tab(self)
        explore_t = explore_tab.get_tab(self)
        analyze_t = analyze_tab.get_tab(self)
        mcmc_t = mcmc_tab.get_tab(self)
        compare_t = compare_tab.get_tab(self)
        self.main_tab_widget.children = [self.open_tab_widget, 
                                         settings_t, explore_t, analyze_t,
                                         mcmc_t, compare_t,
                                         self.edit_tab_widget]
        self.main_tab_widget.set_title(0, 'Open')
        self.main_tab_widget.set_title(1, 'Settings (explore)')
        self.main_tab_widget.set_title(2, 'Explore')
        self.main_tab_widget.set_title(3, 'Analyze')
        self.main_tab_widget.set_title(4, 'MCMC')
        self.main_tab_widget.set_title(5, 'Compare')
        self.main_tab_widget.set_title(6, 'Edit')
