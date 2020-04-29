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

# TEMPORARY HACK - PROPER DISTRIBUTION REQUIRED
import sys
sys.path.insert(1, '/Users/karlen/pypm/src')
from analysis.Optimizer import Optimizer

def get_par_list(self):
    # full names include '* ' if variable
    full_par_names_fixed = []
    full_par_names_variable = []
    for par_name in self.model.parameters:
        par = self.model.parameters[par_name]
        if not par.hidden:
            if par.get_status() == 'variable':
                prefix = '* '
                full_par_names_variable.append(prefix+par_name)
            else:
                prefix = '  '                
                full_par_names_fixed.append(prefix+par_name)
    full_par_names_fixed.sort()
    full_par_names_variable.sort()
    
    return full_par_names_variable+full_par_names_fixed

def delta(cumul):
    diff = []
    for i in range(1,len(cumul)):
        diff.append(cumul[i] - cumul[i-1])
    return diff

def get_pop_list(self):
    # full names includes total or daily
    full_pop_names = []
    self.pop_data = {}
    
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
                        self.pop_data['total ' + pop_name] = data

            if region == 'Simulation':
                if self.sim_model is not None:
                    sim_pop = self.sim_model.populations[pop_name]
                    if hasattr(sim_pop,'show_sim') and sim_pop.show_sim:                        
                        full_pop_names.append('total ' + pop_name)
                        self.pop_data['total ' + pop_name] = sim_pop.history                       
                        
                        
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
                        self.pop_data['daily ' + pop_name] = data
    
            if region == 'Simulation':
                if self.sim_model is not None:
                    sim_pop = self.sim_model.populations[pop_name]
                    if hasattr(sim_pop,'show_sim') and sim_pop.show_sim:
                        sim_daily = delta(sim_pop.history)
                        full_pop_names.append('daily ' + pop_name)
                        self.pop_data['daily ' + pop_name] = sim_daily 
                        
    return full_pop_names

def new_region_opened(self):
    # update the population chooser
    full_pop_names = get_pop_list(self)
    self.pop_dropdown.options = full_pop_names
    self.full_pop_name = self.pop_dropdown.value

def get_tab(self):
    
    output = widgets.Output()
    plot_output = widgets.Output()
    
    def plot_total(self, axis, y_axis_type, range_list):

        region = self.region_dropdown.value
        region_data = None
        if self.region_dropdown.value != 'None' and self.region_dropdown.value != 'Simulation':
            region_data = self.data_description['regional_data'][region]
            
        pop_name = self.full_pop_name[6:]
        pop = self.model.populations[pop_name]
        
        t = range(len(pop.history))
        axis.plot(t, pop.history, lw=2, label=pop_name, color=pop.color)

        td = range(range_list[0], range_list[1])
        data = []
        for i in td:
            data.append(self.pop_data[self.full_pop_name][i])
        axis.scatter(td, data, color=pop.color)

        title = self.full_pop_name
        if region_data is not None:
            title += ' - ' + region
        if region == 'Simulation':
            title += ' - Simulation ('+str(self.seed_text_widget.value)+')' 
        axis.set_title(title)
        axis.legend()
        axis.set_yscale(y_axis_type)
        #axis.set_xlim(left=-1, right=n_days_widget.value)
        if y_axis_type == 'log':
            axis.set_ylim(bottom=3)
        else:
            axis.set_ylim(bottom=0)
            
    def plot_daily(self, axis, y_axis_type, range_list):
        
        region = self.region_dropdown.value
        region_data = None
        if self.region_dropdown.value != 'None' and self.region_dropdown.value != 'Simulation':
            region_data = self.data_description['regional_data'][region]

        pop_name = self.full_pop_name[6:]
        pop = self.model.populations[pop_name]
        
        daily = delta(pop.history)
        t = range(len(daily))
        axis.step(t, daily, lw=2, label=pop_name, color=pop.color)

        td = range(range_list[0], range_list[1])
        data = []
        for i in td:
            data.append(self.pop_data[self.full_pop_name][i])
        axis.scatter(td, data, color=pop.color)
       
        title = self.full_pop_name
        if region_data is not None:
            title += ' - ' + region
        if region == 'Simulation':
            title += ' - Simulation ('+str(self.seed_text_widget.value)+')' 
        axis.set_title(title)
        axis.legend()
        axis.set_yscale(y_axis_type)
        #axis.set_xlim(left=-1, right=n_days_widget.value)
        if y_axis_type == 'log':
            axis.set_ylim(bottom=3)
        else:
            axis.set_ylim(bottom=0)
    
    def make_plot(self, range_list):
        output.clear_output(True)
        plot_output.clear_output(True)
        
        with plot_output:
    
            fig, axes = plt.subplots(1, 2, figsize=(16,7))
    
            axis = axes[0]
            y_axis_type = 'linear'
    
            if self.pop_dropdown.value[:5] == 'total':
                plot_total(self, axis, y_axis_type, range_list)
            else:
                plot_daily(self, axis, y_axis_type, range_list)
    
            axis = axes[1]
            y_axis_type = 'log'
    
            if self.pop_dropdown.value[:5] == 'total':
                plot_total(self, axis, y_axis_type, range_list)
            else:
                plot_daily(self, axis, y_axis_type, range_list)
    
            self.last_plot = plt.gcf()
            plt.show()

    full_pop_names = get_pop_list(self)
    self.pop_dropdown = widgets.Dropdown(options=full_pop_names, description='Population:', disabled=False)
    
    def pop_dropdown_eventhandler(change):
        # update list of visible populations in case it has changed
        full_pop_names = get_pop_list(self)
        self.pop_dropdown.options = full_pop_names
        self.full_pop_name = self.pop_dropdown.value

    self.pop_dropdown.observe(pop_dropdown_eventhandler, names='value')

    self.date_range_text = widgets.Text(value='', placeholder='range eg. 20:50',
                                        description='Fit days:', disabled=False,
                                        continuous_update=False)

    full_par_names = get_par_list(self)
    self.full_par_dropdown = widgets.Dropdown(options=full_par_names, description='Parameter:', disabled=False)

    variable_checkbox = widgets.Checkbox(value=False, description='variable', disabled=False)
    variable_bound_text = widgets.Text(value='-inf:inf', placeholder='bounds eg. 0.:5.',
                                       description='Bounds:', disabled=True,continuous_update=False)

    def get_bounds(parameter, bound_text):
        # decode the bound_text
        bounds = [-np.inf, np.inf]
        if bound_text.find(':') > 0:
            bound_split = bound_text.split(':')
            if len(bound_split) == 2:
                bounds[0] = float(bound_split[0])
                bounds[1] = float(bound_split[1])
                if parameter.parameter_type == 'int':
                    bounds[0] = int(bounds[0])
                    bounds[1] = int(bounds[1])
        return bounds

    def variable_checkbox_eventhandler(change):
        # update the status of the model parameter - set bounds if appropriate
        output.clear_output(True)
        par_name = self.full_par_dropdown.value[2:]
        par = self.model.parameters[par_name]
        status_changed = False
        if variable_checkbox.value:
            if par.get_status() == 'fixed':
                status_changed = True
                variable_bound_text.disabled = False
                bounds = []
                # if uniform prior already set use that, otherwise set new bounds
                if par.prior_function == 'uniform' and par.prior_parameters is not None and \
                    'half_width' in par.prior_parameters:
                    par.set_variable(None, None)
                    mean = par.prior_parameters['mean']
                    half_width = par.prior_parameters['half_width']
                    bounds = [mean-half_width,mean+half_width]
                else:
                    bounds = get_bounds(par, variable_bound_text.value)
                    mean = (bounds[0]+bounds[1])/2.
                    half_width = bounds[1] - mean
                    prior_parameters = {'mean':mean, 'half_width':half_width}
                    par.set_variable('uniform', prior_parameters)
    
                with output:
                    print('Parameter '+par_name+' now set to variable.')
                    print('Bounds for variation:' +
                          str(bounds[0]) + ':' + str(bounds[1]))
        else:
            variable_bound_text.disabled = True
            if par.get_status() == 'variable':
                status_changed = True
                par.set_fixed()
                with output:
                    print('Parameter '+par_name+' now set to fixed.')
        # update parameter list, if a variable changed its status
        # after updating, go back to select the revised par
        if status_changed:
            selected = self.full_par_dropdown.value
            prefix = selected[:2]
            full_par_names = get_par_list(self)
            self.full_par_dropdown.options = full_par_names
            if prefix == '  ':
                prefix = '* '
            else:
                prefix = '  '
            self.full_par_dropdown.value = prefix+selected[2:]

    variable_checkbox.observe(variable_checkbox_eventhandler, names='value')
    
    def variable_bound_text_eventhandler(change):
        output.clear_output(True)
        # update the bounds
        par_name = self.full_par_dropdown.value[2:]
        par = self.model.parameters[par_name]
        if variable_checkbox.value:

            bounds = get_bounds(par, variable_bound_text.value)
            mean = (bounds[0]+bounds[1])/2.
            half_width = bounds[1] - mean
            prior_parameters = {'mean':mean, 'half_width':half_width}
            par.set_variable('uniform', prior_parameters)

            with output:
                print('Parameter '+par_name)
                print('Bounds for variation:' +
                      str(bounds[0]) + ':' + str(bounds[1]))
    variable_bound_text.observe(variable_bound_text_eventhandler, names='value')

    def par_dropdown_eventhandler(change):
        # update list of visible parameters in case it has changed
        full_par_names = get_par_list(self)
        self.full_par_dropdown.options = full_par_names
        
        par_name = self.full_par_dropdown.value[2:]
        prefix = self.full_par_dropdown.value[:2]
        par = self.model.parameters[par_name]
        if prefix == '* ':
            variable_checkbox.value = True
            variable_bound_text.disabled = False
            mean = par.prior_parameters['mean']
            half_width = par.prior_parameters['half_width']
            bound_text = "{0:0.2f}:{1:0.2f}".format(mean-half_width, mean+half_width)
            variable_bound_text.value = bound_text
        else:
            variable_checkbox.value = False
            variable_bound_text.disabled = True
    self.full_par_dropdown.observe(par_dropdown_eventhandler, names='value')
    
    def do_fit(b):
        date_range = self.date_range_text.value
        range_list = [0,0]
        if date_range.find(':') > 0:
            splits = date_range.split(':')
            if len(splits) == 2:
                range_list[0] = int(splits[0])
                range_list[1] = int(splits[1])
        else:
            range_list[0] = 0
            range_list[1] = len(self.pop_data[self.full_pop_name]) - 1
        my_opt = Optimizer(self.model, self.full_pop_name, self.pop_data[self.full_pop_name], range_list)
        popt, pcov = my_opt.fit()
        make_plot(self,range_list)
        # update the parameter value on the explore tab, so that when going to that page,
        # the old parameter value won't be reloaded
        par_name = self.param_dropdown.value
        par = self.model.parameters[par_name]
        self.val_text_widget.value = par.get_value()

    fit_button = widgets.Button(
        description='  Fit/plot', button_style='', tooltip='Perform fit and plot result', icon='check')
    
    fit_button.on_click(do_fit)
    
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')
    
    header_html = widgets.VBox([
        widgets.HTML(
            value="<h1><a href:='https://www.pypm.ca'>pyPM</a></h1><p style='font-size: 26px;'>analyze</p>",
            placeholder='',
            description='')])

    header_hbox = widgets.HBox([header_html])
            
    left_box = widgets.VBox([self.pop_dropdown, 
                             self.date_range_text, 
                             self.full_par_dropdown, 
                             variable_checkbox,  
                             variable_bound_text,
                             fit_button
                             ])
    
    return AppLayout(header=header_hbox,
              left_sidebar=left_box,
              center=output,
              right_sidebar=hspace,
              footer=plot_output,
              pane_widths=[2, 2, 2],
              pane_heights=[1, 2, '460px'])
