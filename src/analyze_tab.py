# -*- coding: utf-8 -*-
"""
Analyze: get point estimates by fitting data

Use MCMC to define range of possible values for future predictions

@author: karlen
"""


from __future__ import print_function
import ipywidgets as widgets
from ipywidgets import AppLayout

from datetime import date
import time
import copy

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms

def get_par_list(self):
    # full names include '* ' if variable
    full_par_namess = []
    for par_name in self.model.parameters:
        par = self.model.parameters[par_name]
        if not par.hidden:
            prefix = '  '
            if par.get_status() == 'variable':
                prefix = '* '
            full_par_names.append(par_name)
    full_par_names.sort()
    return full_par_names

def delta(cumul):
    diff = []
    for i in range(1,len(cumul)):
        diff.append(cumul[i] - cumul[i-1])
    return diff

def get_pop_list(self):
    # full names includes total or daily
    full_pop_names = []
    pop_data = {}
    
    region = self.region_dropdown.value        
    region_data = None
    if self.region_dropdown.value != 'None' and self.region_dropdown.value != 'Simulation':
        region_data = self.data_description['regional_data'][region]
    
    for pop_name in self.model.populations:
        pop = self.model.populations[pop_name]
        if not pop.hidden:
            
            if region_data is not None:
                if pop_name in region_data:
                    if 'total' in region_data[pop_name]:                        
                        filename = region_data[pop_name]['total']['filename']
                        header = region_data[pop_name]['total']['header']
                        data = self.pd_dict[filename][header].values
                        full_pop_names.append('total ' + pop_name)
                        pop_data['total ' + pop_name] = data

            if region == 'Simulation':
                if self.sim_model is not None:
                    sim_pop = self.sim_model.populations[pop_name]
                    if hasattr(sim_pop,'show_sim') and sim_pop.show_sim:                        
                        full_pop_names.append('total ' + pop_name)
                        pop_data['total ' + pop_name] = sim_pop.history                       
                        
                        
    for pop_name in self.model.populations:
        pop = self.model.populations[pop_name]
        if not pop.hidden and pop.monotonic:
            
            if region_data is not None:
                if pop_name in region_data:
                    if 'daily' in region_data[pop_name]:
                        filename = region_data[pop_name]['daily']['filename']
                        header = region_data[pop_name]['daily']['header']
                        data = self.pd_dict[filename][header].values
                        full_pop_names.append('daily ' + pop_name)
                        pop_data['daily ' + pop_name] = data
    
            if region == 'Simulation':
                if self.sim_model is not None:
                    sim_pop = self.sim_model.populations[pop_name]
                    if hasattr(sim_pop,'show_sim') and sim_pop.show_sim:
                        sim_daily = delta(sim_pop.history)
                        full_pop_names.append('daily ' + pop_name)
                        pop_data['daily ' + pop_name] = sim_daily 
                        
    return full_pop_names, pop_data 

def get_tab(self):

    full_pop_names, pop_data = get_pop_list(self)
    self.pop_data = pop_data
    self.pop_dropdown = widgets.Dropdown(options=full_pop_names, description='Population:', disabled=False)
    
    def dropdown_eventhandler(change):
        # update list of visible populations in case it has changed
        full_pop_names, pop_data = get_pop_list(self)
        self.pop_data = pop_data
        self.pop_dropdown.options = full_pop_names

    self.pop_dropdown.observe(dropdown_eventhandler, names='value')

    self.date_range_text = widgets.Text(value='', placeholder='range eg. 20:50',
                                        description='String:', disabled=False)


    full_par_names = get_par_list(self)
    self.full_par_dropdown = widgets.Dropdown(options=full_par_names, description='Parameter:', disabled=False)






    self.val_text_widget = widgets.FloatText(value = par.get_value(), description='Value:')
    #widgets.link((val_slide, 'value'), (val_text, 'value'))
    
    def val_change_eventhandler(change):
        if self.param_dropdown.value in self.model.parameters:
            self.model.parameters[self.param_dropdown.value].set_value(change['new'])        
            b=[]
            make_plot(b)
    
    self.param_dropdown.observe(dropdown_eventhandler, names='value')
    self.val_text_widget.observe(val_change_eventhandler, names='value')