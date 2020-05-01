# -*- coding: utf-8 -*-
"""
Defines the edit tab for adding/removing/adjusting objects

@author: karlen
"""

from __future__ import print_function
import ipywidgets as widgets

from datetime import date
import pickle

# TEMPORARY HACK - PROPER DISTRIBUTION REQUIRED
import sys
sys.path.insert(1, '/Users/karlen/pypm/src')
from Population import Population
from Model import Model
from Delay import Delay
from Parameter import Parameter
from Multiplier import Multiplier
from Propagator import Propagator
from Splitter import Splitter
from Adder import Adder
from Subtractor import Subtractor
from Chain import Chain
from Modifier import Modifier
from Injector import Injector

def get_tab(self):

    edit_tab = widgets.Tab()
    model_tab = get_model_tab(self)
    parameters_tab = get_parameters_tab(self)
    delays_tab = get_delays_tab(self)

    edit_tab.children = [model_tab, parameters_tab, delays_tab]
    edit_tab.set_title(0, 'Model')
    edit_tab.set_title(1, 'Parameters')
    edit_tab.set_title(2, 'Delays')
    
    return edit_tab

def get_model_tab(self):
    
    output = widgets.Output()
    model_upload = widgets.FileUpload(accept='.pypm',multiple=False)

    model_name = widgets.Text(description='Name:')
    model_description = widgets.Textarea(description='Description:')
    model_t0 = widgets.DatePicker(description='t_0:', value = date(2020,3,1), 
                                  tooltip='Defines day 0 on plots', disabled=True)
    model_time_step = widgets.FloatText(description='time_step:', disabled=True,
                                        tooltip='Duration of one time step. Units: days')

    model_save = widgets.Button(description='Save changes', tooltip='Save changes to loaded model')
    model_new = widgets.Button(description='New model', tooltip='Create new empty model', 
                               button_style='warning', icon='warning')

    def model_upload_eventhandler(change):
        output.clear_output(True)
        filename = list(model_upload.value.keys())[0]
        my_pickle = model_upload.value[filename]['content']
        self.edit_model = pickle.loads(my_pickle)
        model_name.value = self.edit_model.name
        model_description.value = self.edit_model.description
        model_t0.value = self.edit_model.t0
        model_time_step.value = self.edit_model.get_time_step()
        with output:
            print('Model loaded for editing.')

    model_upload.observe(model_upload_eventhandler, names='value')

    def model_save_handler(b):
        output.clear_output(True)
        self.edit_model.name = model_name.value
        self.edit_model.description = model_description.value
        self.edit_model.t0 = model_t0.value
        self.edit_model.get_time_step(model_time_step.value)
        with output:
            print('Changes saved to model.')
            print('You must save model to disk to make this permanent.')

    model_save.on_click(model_save_handler)

    def model_new_handler(b):
        output.clear_output(True)
        self.edit_model = Model(model_name.value)
        self.edit_model.description = model_description.value
        self.edit_model.t0 = model_t0.value
        self.edit_model.get_time_step(model_time_step.value)
        with output:
            print('New model created.')
            print('You must save model to disk to make this permanent.')
        
    model_new.on_click(model_new_handler)
    
    v_box1 = widgets.VBox([
        model_upload,
        model_name,
        model_description,
        model_t0,
        model_time_step,
        model_save,
        model_new
        ])
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')
    
    return widgets.HBox([v_box1, hspace, output])  
    
def get_parameters_tab(self):
        
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    par_dropdown = widgets.Dropdown(description='Parameter:', disabled=False)
    
    par_name = widgets.Text(description='Name:')
    par_description = widgets.Textarea(description='Description:')
    par_value = widgets.Text(description='Value:', tooltip='Current value')
    par_min = widgets.Text(description='Min:', tooltip='Minimum bound for fitting')
    par_max = widgets.Text(description='Max:', tooltip='Maximum bound for fitting')
    par_type = widgets.Dropdown(description='Type:', options=['float','int','bool'])
    par_hidden = widgets.Checkbox(description='Hidden', 
                                  tooltip='If hidden, by default does not appear in dropdown menus')

    par_save = widgets.Button(description='Save changes', tooltip='Save changes to loaded model')
    par_new = widgets.Button(description='New parameter', tooltip='Create new parameter') 

    def refresh(b):
        if self.edit_model is not None:
            par_name_list = list(self.edit_model.parameters.keys()) + \
                list(self.new_parameters.keys())
            par_name_list.sort()
            par_dropdown.options = par_name_list

    refresh_button.on_click(refresh)
    
    def dropdown_eventhandler(change):
        output.clear_output(True)
        parameter_name = par_dropdown.value
        par = None
        if parameter_name in self.edit_model.parameters:
            par = self.edit_model.parameters[parameter_name]
        else:
            par = self.new_parameters[parameter_name]
        par_name.value = par.name
        par_description.value = par.description
        par_value.value = str(par.get_value())
        par_min.value = str(par.get_min())
        par_max.value = str(par.get_max())
        par_type.value = par.parameter_type
        par_hidden.value = par.hidden
        with output:
            print('Parameter options loaded')
        
    par_dropdown.observe(dropdown_eventhandler, names='value')
    
    def par_save_handler(b):
        output.clear_output(True)
        parameter_name = par_dropdown.value
        if par_name.value != parameter_name:
            with output:
                print('You are not allowed to change the name of an existing parameter.')
                print('You click the "new parameter" button to create a new parameter')
                print('with this name.')
        else:
            par = None
            if parameter_name in self.edit_model.parameters:
                par = self.edit_model.parameters[parameter_name]
            else:
                par = self.new_parameters[parameter_name]
            par.description = par_description.value
            par.parameter_type = par_type.value
            if par.parameter_type == 'int':
                par.set_value(int(par_value.value))
                par.set_min(int(par_min.value))
                par.set_max(int(par_max.value))
            if par.parameter_type == 'float':
                par.set_value(float(par_value.value))
                par.set_min(float(par_min.value))
                par.set_max(float(par_max.value))
            if par.parameter_type == 'bool':
                par.set_value(bool(par_value.value))
            par.hidden = par_hidden.value
    
            with output:
                print('Changes saved to parameter.')
                print('You must save model to disk to make this permanent.')

    par_save.on_click(par_save_handler)    

    def par_new_handler(b):
        output.clear_output(True)

        value = None
        if par_type.value == 'int':
            value = int(par_value.value)
        if par_type.value == 'float':
             value = float(par_value.value)
        if par_type.value == 'bool':
             value = bool(par_value.value)

        par = Parameter(par_name.value, value, parameter_type=par_type.value)
        par.description = par_description.value
        par.parameter_type = par_type.value
        if par.parameter_type == 'int':
            par.set_min(int(par_min.value))
            par.set_max(int(par_max.value))
        if par.parameter_type == 'float':
            par.set_min(float(par_min.value))
            par.set_max(float(par_max.value))
        par.hidden = par_hidden.value
        
        with output:
            if par.name in self.edit_model.parameters or \
                par.name in self.new_parameters:
                print('Parameter with this name already exists.')
                print('Please change the name and try again.')
            else:
                self.new_parameters[str(par)] = par
                print('New parameter created.')
                print('You must use this parameter and save the model to disk')
                print('to make this permanent.')

    par_new.on_click(par_new_handler)

    v_box1 = widgets.VBox([
        refresh_button, 
        par_dropdown,
        par_name,
        par_description,
        par_value,
        par_min,
        par_max,
        par_type,
        par_hidden,
        par_save,
        par_new,
        ])
    
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])

def get_delays_tab(self):
    
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    delay_dropdown = widgets.Dropdown(description='Delay:', disabled=False)
    
    DELAY_PAR_KEYS = {'fast':[], 'norm':['mean', 'sigma'],
                      'uniform':['mean', 'half_width'],
                      'erlang':['mean', 'k']}


    delay_name, delay_type,
                 delay_parameters=None, model=None):
    
    
    delay_name = widgets.Text(description='Name:')
    delay_type = widgets.Dropdown(description='Type:', options=['fast', 'norm', 'uniform', 'erlang'])
    
    delay_par1 = widgets.Dropdown(description='')
    delay_par2 = widgets.Dropdown(description='')

    delay_save = widgets.Button(description='Save changes', tooltip='Save changes to loaded model')
    delay_new = widgets.Button(description='New parameter', tooltip='Create new delay') 

    def refresh(b):
        if self.edit_model is not None:
            par_name_list = list(self.edit_model.parameters.keys()) + \
                list(self.new_parameters.keys())
            par_name_list.sort()
            if delay_type == 'fast':
                delay_par1.options = []
                delay_par2.options = []
            else:
                delay_par1.options = par_name_list
                delay_par2.options = par_name_list
            

    refresh_button.on_click(refresh)
    
    def name_dropdown_eventhandler(change):
        output.clear_output(True)
        parameter_name = par_dropdown.value
        par = None
        if parameter_name in self.edit_model.parameters:
            par = self.edit_model.parameters[parameter_name]
        else:
            par = self.new_parameters[parameter_name]
        par_name.value = par.name
        par_description.value = par.description
        par_value.value = str(par.get_value())
        par_min.value = str(par.get_min())
        par_max.value = str(par.get_max())
        par_type.value = par.parameter_type
        par_hidden.value = par.hidden
        with output:
            print('Parameter options loaded')
        
    par_dropdown.observe(dropdown_eventhandler, names='value')
    
    def par_save_handler(b):
        output.clear_output(True)
        parameter_name = par_dropdown.value
        if par_name.value != parameter_name:
            with output:
                print('You are not allowed to change the name of an existing parameter.')
                print('You click the "new parameter" button to create a new parameter')
                print('with this name.')
        else:
            par = None
            if parameter_name in self.edit_model.parameters:
                par = self.edit_model.parameters[parameter_name]
            else:
                par = self.new_parameters[parameter_name]
            par.description = par_description.value
            par.parameter_type = par_type.value
            if par.parameter_type == 'int':
                par.set_value(int(par_value.value))
                par.set_min(int(par_min.value))
                par.set_max(int(par_max.value))
            if par.parameter_type == 'float':
                par.set_value(float(par_value.value))
                par.set_min(float(par_min.value))
                par.set_max(float(par_max.value))
            if par.parameter_type == 'bool':
                par.set_value(bool(par_value.value))
            par.hidden = par_hidden.value
    
            with output:
                print('Changes saved to parameter.')
                print('You must save model to disk to make this permanent.')

    par_save.on_click(par_save_handler)    

    def par_new_handler(b):
        output.clear_output(True)

        value = None
        if par_type.value == 'int':
            value = int(par_value.value)
        if par_type.value == 'float':
             value = float(par_value.value)
        if par_type.value == 'bool':
             value = bool(par_value.value)

        par = Parameter(par_name.value, value, parameter_type=par_type.value)
        par.description = par_description.value
        par.parameter_type = par_type.value
        if par.parameter_type == 'int':
            par.set_min(int(par_min.value))
            par.set_max(int(par_max.value))
        if par.parameter_type == 'float':
            par.set_min(float(par_min.value))
            par.set_max(float(par_max.value))
        par.hidden = par_hidden.value
        
        with output:
            if par.name in self.edit_model.parameters or \
                par.name in self.new_parameters:
                print('Parameter with this name already exists.')
                print('Please change the name and try again.')
            else:
                self.new_parameters[str(par)] = par
                print('New parameter created.')
                print('You must use this parameter and save the model to disk')
                print('to make this permanent.')

    par_new.on_click(par_new_handler)

    v_box1 = widgets.VBox([
        refresh_button, 
        par_dropdown,
        par_name,
        par_description,
        par_value,
        par_min,
        par_max,
        par_type,
        par_hidden,
        par_save,
        par_new,
        ])
    
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])