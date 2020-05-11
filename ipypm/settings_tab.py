# -*- coding: utf-8 -*-
"""
Defines the settings tab for selecting populations and parameters

@author: karlen
"""

from __future__ import print_function
import ipywidgets as widgets

def get_tab(self):

    settings_tab = widgets.Tab()    
    populations_tab = get_populations_tab(self)
    parameters_tab = get_parameters_tab(self)

    settings_tab.children = [populations_tab, parameters_tab]
    settings_tab.set_title(0, 'Populations')
    settings_tab.set_title(1, 'Parameters')
    
    return settings_tab

def get_populations_tab(self):
    
    items = []
    pop_name_list = list(self.model.populations.keys())
    pop_name_list.sort()
    for pop_name in pop_name_list:
        pop = self.model.populations[pop_name]
        cb = widgets.Checkbox(
        value=not pop.hidden,
        description=pop_name,
        disabled=False)
        items.append(cb)
        
    def pop_eventhandler(change):
        owner = change['owner']
        pop_name = owner.description
        new_val = change['new']
        pop = self.model.populations[pop_name]
        pop.hidden = not new_val
    
    for item in items:
        item.observe(pop_eventhandler, names='value')
        
    return widgets.GridBox(items,
        layout=widgets.Layout(grid_template_columns="repeat(3, 200px)"))
    
def get_parameters_tab(self):
    
    items = []
    par_name_list = list(self.model.parameters.keys())
    par_name_list.sort()
    for par_name in par_name_list:
        par = self.model.parameters[par_name]
        cb = widgets.Checkbox(
        value=not par.hidden,
        description=par_name,
        disabled=False)
        items.append(cb)
        
    def par_eventhandler(change):
        owner = change['owner']
        pop_name = owner.description
        new_val = change['new']
        pop = self.model.parameters[pop_name]
        pop.hidden = not new_val
    
    for item in items:
        item.observe(par_eventhandler, names='value')
        
    return widgets.GridBox(items,
        layout=widgets.Layout(grid_template_columns="repeat(3, 200px)"))









