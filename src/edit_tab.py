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
import tools.table

def get_tab(self):

    edit_tab = widgets.Tab()
    model_tab = get_model_tab(self)
    parameters_tab = get_parameters_tab(self)
    delays_tab = get_delays_tab(self)
    populations_tab = get_populations_tab(self)
    connectors_tab = get_connectors_tab(self)

    edit_tab.children = [model_tab, parameters_tab, delays_tab, populations_tab,
                         connectors_tab]
    edit_tab.set_title(0, 'Model')
    edit_tab.set_title(1, 'Parameters')
    edit_tab.set_title(2, 'Delays')
    edit_tab.set_title(3, 'Populations')
    edit_tab.set_title(4, 'Connectors')
    edit_tab.set_title(5, 'Transitions')
    edit_tab.set_title(6, 'Boot')
    
    return edit_tab

def get_model_delays(self):
    # return a dictionary of model delays indexed by delay_name
    delays = {}
    for key in self.edit_model.connectors:
        con = self.edit_model.connectors[key]
        if hasattr(con,'delay'):
            if isinstance(con.delay, list):
                for delay in con.delay:
                    delays[str(delay)] = delay
                    if type(con).__name__ == 'Chain':
                        for chain_con in con.chain:
                            delays[str(chain_con.delay)] = chain_con.delay
            else:
                delays[str(con.delay)] = con.delay
                if type(con).__name__ == 'Chain':
                    for chain_con in con.chain:
                        delays[str(chain_con.delay)] = chain_con.delay
    return delays


def get_model_tab(self):
    
    output = widgets.Output()
    model_upload = widgets.FileUpload(decription='Open model', accept='.pypm',
                                      multiple=False)

    model_name = widgets.Text(description='Name:')
    model_description = widgets.Textarea(description='Description:')
    model_t0 = widgets.DatePicker(description='t_0:', value = date(2020,3,1), 
                                  tooltip='Defines day 0 on plots', disabled=True)
    model_time_step = widgets.FloatText(description='time_step:', value = 1., disabled=True,
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
            print('Model loaded for editing. It has:')
            print(len(self.edit_model.populations), ' Populations')
            print(len(self.edit_model.connectors), ' Connectors')
            print(len(self.edit_model.parameters), ' Parameters')
            print(len(self.edit_model.transitions), ' Transitions')

    model_upload.observe(model_upload_eventhandler, names='value')

    def model_save_handler(b):
        output.clear_output(True)
        self.edit_model.name = model_name.value
        self.edit_model.description = model_description.value
        self.edit_model.t0 = model_t0.value
        self.edit_model.set_time_step(model_time_step.value)
        with output:
            print('Changes saved to model.')
            print('You must save model to disk to make this permanent.')

    model_save.on_click(model_save_handler)

    def model_new_handler(b):
        output.clear_output(True)
        if model_name.value is None or len(model_name.value) == 0:
            with output:
                print('Model NOT created.')
                print('You must provide a valid name.')
        else:
            self.edit_model = Model(model_name.value)
            # clean away any work prior to starting with fresh model:
            self.new_parameters = {}
            self.delays = {}
            self.new_delays = {}
            self.new_populations = {}
            self.new_propagators = {}
            
            if model_description.value is not None and \
                len(model_description.value) > 0:
                self.edit_model.description = model_description.value
            if model_t0.value is not None:
                self.edit_model.t0 = model_t0.value
            if model_time_step.value is not None:
                self.edit_model.set_time_step(model_time_step.value)
            with output:
                print('New model created.')
                print('You must save model to disk to make this permanent.')
        
    model_new.on_click(model_new_handler)
    
    open_label = widgets.Label(value='Open model:')
    
    v_box1 = widgets.VBox([
        widgets.HBox([open_label, model_upload]),
        model_name,
        model_description,
        model_t0,
        model_time_step,
        widgets.HBox([model_save,
        model_new])
        ])
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')
    
    return widgets.HBox([v_box1, hspace, output])  
    
def get_parameters_tab(self):
        
    output = widgets.Output()
    table_output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    par_dropdown = widgets.Dropdown(description='Parameter:', disabled=False)
    
    par_name = widgets.Text(description='Name:')
    par_description = widgets.Textarea(description='Description:')
    par_value = widgets.Text(description='Value:', tooltip='Current value')
    par_min = widgets.Text(description='Min:', tooltip='Minimum bound for fitting')
    par_max = widgets.Text(description='Max:', tooltip='Maximum bound for fitting')
    par_type = widgets.Dropdown(description='Type:', options=['float','int','bool'])
    par_hidden = widgets.Checkbox(description='Hidden:', 
                                  tooltip='If hidden, by default does not appear in dropdown menus')

    par_save = widgets.Button(description='Save changes', tooltip='Save changes to loaded model')
    par_new = widgets.Button(description='New parameter', tooltip='Create new parameter')
    par_table = widgets.Button(description='Par Table', tooltip='Show all parameters in a table')

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
    
    def par_table_handler(b):
        table_output.clear_output(True)
        with table_output:
            print(tools.table.parameter_table(self.edit_model, width=110))
    
    par_table.on_click(par_table_handler)

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
        widgets.HBox([par_save,
        par_new]),
        par_table
        ])
    
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.VBox([widgets.HBox([v_box1, hspace, output]),table_output])

def get_delays_tab(self):
    
    output = widgets.Output()
    table_output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    delay_dropdown = widgets.Dropdown(description='Delay:', disabled=False)
    
    delay_name_widget = widgets.Text(description='Name:')
    delay_type = widgets.Dropdown(description='Type:', options=['fast', 'norm', 'uniform', 'erlang'])
    
    delay_par1 = widgets.Dropdown(description='')
    delay_par2 = widgets.Dropdown(description='')

    delay_save = widgets.Button(description='Save changes', tooltip='Save changes to loaded model')
    delay_new = widgets.Button(description='New delay', tooltip='Create new delay')
    delay_table = widgets.Button(description='Delay Table', tooltip='Show all delays in a table')

    def refresh(b):
        if self.edit_model is not None:
            self.delays = get_model_delays(self)
            delay_name_list =  list(self.delays.keys()) + list(self.new_delays.keys())
            delay_name_list.sort()
            
            delay_dropdown_options = delay_name_list

            par_name_list = list(self.edit_model.parameters.keys()) + \
                list(self.new_parameters.keys())
            par_name_list.sort()

            delay_par1.options = par_name_list
            delay_par2.options = par_name_list
            
            delay_dropdown.options = delay_dropdown_options
            #delay_par_setup()
                
    refresh_button.on_click(refresh)

    def delay_par_setup():
        delay_name = delay_dropdown.value
        delay = None
        if delay_name in self.delays:
            delay = self.delays[delay_name]
        else:
            delay = self.new_delays[delay_name]
        delay_name_widget.value = delay.name
        delay_type.value = delay.delay_type
        if delay.delay_type == 'norm':
            delay_par1.description = 'mean:'
            delay_par2.description = 'sigma:'
            delay_par1.value = delay.delay_parameters['mean'].name
            delay_par2.value = delay.delay_parameters['sigma'].name
        elif delay.delay_type == 'uniform':
            delay_par1.description = 'mean:'
            delay_par2.description = 'half_width:'
            delay_par1.value = delay.delay_parameters['mean'].name
            delay_par2.value = delay.delay_parameters['half_width'].name
        elif delay.delay_type == 'erlang':
            delay_par1.description = 'mean:'
            delay_par2.description = 'k:'
            delay_par1.value = delay.delay_parameters['mean'].name
            delay_par2.value = delay.delay_parameters['k'].name
        if delay.delay_type == 'fast':
            delay_par1.description = ''
            delay_par2.description = ''
            delay_par1.disabled = True
            delay_par1.disabled = True
        else:
            delay_par1.disabled = False
            delay_par1.disabled = False

    def name_dropdown_eventhandler(change):
        output.clear_output(True)
        delay_par_setup()
        with output:
            print('Delay loaded')
        
    delay_dropdown.observe(name_dropdown_eventhandler, names='value')
    
    def type_dropdown_eventhandler(change):
        if delay_type.value == 'norm':
            delay_par1.description = 'mean:'
            delay_par2.description = 'sigma:'
        elif delay_type.value == 'uniform':
            delay_par1.description = 'mean:'
            delay_par2.description = 'half_width:'
        elif delay_type.value == 'erlang':
            delay_par1.description = 'mean:'
            delay_par2.description = 'k:'
        if delay_type.value == 'fast':
            delay_par1.description = ''
            delay_par2.description = ''
            delay_par1.disabled = True
            delay_par2.disabled = True
        else:
            delay_par1.disabled = False
            delay_par2.disabled = False
        
    delay_type.observe(type_dropdown_eventhandler, names='value')

    def get_par(name):
        if name in self.edit_model.parameters:
            return self.edit_model.parameters[name]
        elif name in self.new_parameters:
            return self.new_parameters[name]
        else:
            return self.delay_par_dict[name]
    
    def get_delay_dict():
        delay_dict = None
        if delay_type.value == 'norm':
            delay_dict={'mean':get_par(delay_par1.value), 'sigma':get_par(delay_par2.value)}
        if delay_type.value == 'uniform':
            delay_dict={'mean':get_par(delay_par1.value), 'half_width':get_par(delay_par2.value)}
        if delay_type.value == 'erlang':
            delay_dict={'mean':get_par(delay_par1.value), 'k':get_par(delay_par2.value)}
        return delay_dict

    def delay_save_handler(b):
        output.clear_output(True)
        delay_name = delay_dropdown.value
        if delay_name_widget.value != delay_name:
            with output:
                print('You are not allowed to change the name of an existing delay.')
                print('You click the "new delay" button to create a new delay')
                print('with this name.')
        else:
            delay = None
            if delay_name in self.delays:
                delay = self.delays[delay_name]
            else:
                delay = self.new_delays[delay_name]
            delay_dict = get_delay_dict()
            delay.setup_delay(delay_type.value, delay_dict)
            # must update model lists in case new parameters now being used
            self.edit_model.update_lists()
            # update the delay distribution
            delay.update()
    
            with output:
                print('Changes saved to delay.')
                print('You must save model to disk to make this permanent.')

    delay_save.on_click(delay_save_handler)    

    def delay_new_handler(b):
        output.clear_output(True)

        delay_dict = get_delay_dict()

        delay = Delay(delay_name_widget.value, delay_type.value,
                      delay_parameters = delay_dict, model=self.edit_model)
        
        with output:
            if delay.name in self.edit_model.parameters or \
                delay.name in self.new_parameters:
                print('Delay with this name already exists.')
                print('Please change the name and try again.')
            else:
                self.new_delays[str(delay)] = delay
                print('New delay created.')
                print('You must use this delay and save the model to disk')
                print('to make this permanent.')

    delay_new.on_click(delay_new_handler)

    def delay_table_handler(b):
        table_output.clear_output(True)
        with table_output:
            print(tools.table.delay_table(self.edit_model, width=110))
    delay_table.on_click(delay_table_handler)

    
    v_box1 = widgets.VBox([
        refresh_button,
        delay_dropdown,
        delay_name_widget,
        delay_type,    
        delay_par1,
        delay_par2,
        widgets.HBox([delay_save,
        delay_new]),
        delay_table
        ])
    
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.VBox([widgets.HBox([v_box1, hspace, output]),table_output])

def get_populations_tab(self):
        
    output = widgets.Output()
    table_output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    pop_dropdown = widgets.Dropdown(description='Population:', disabled=False)
    
    pop_name = widgets.Text(description='Name:')
    pop_description = widgets.Textarea(description='Description:')
    pop_initial_value_by_parameter = widgets.Checkbox(description='Init by par', value=False,
                    tooltip='If selected, the initial value is set by a parameter')
    pop_initial_parameter = widgets.Dropdown(description='Init par:', disabled=False, 
                                             tooltip='Initial value is set by this parameter')
    pop_initial_value = widgets.Text(description='Init val:',
                                     tooltip='Initial value is set by this parameter')
    pop_hidden = widgets.Checkbox(description='Hidden:', 
                                  tooltip='If hidden, by default does not appear in plots')
    pop_color = widgets.Text(description='Color:', tooltip='Color for plotting population')
    pop_show_sim = widgets.Checkbox(description='Show sim:', 
                                    tooltip='If true, this population corresponds to a measured population '+
                                    'and therefore appropriate to show simulated data in plots.')
    pop_report_noise = widgets.Checkbox(description='Report noise:', 
                                  tooltip='If true, additional fluctuation from the reporting process is included')
    pop_report_noise_parameter = widgets.Dropdown(description='Noise par:', disabled=True, 
                                             tooltip='Report noise parameter: f = 0.-1. f is the minimum number '+
                                             'fraction of cases from that day reported that day.')
    pop_save = widgets.Button(description='Save changes', tooltip='Save changes to loaded model')
    pop_new = widgets.Button(description='New population', tooltip='Create new population')
    pop_table = widgets.Button(description='Pop Table', tooltip='Show all populations in a table')

    def refresh(b):
        if self.edit_model is not None:
            par_name_list = list(self.edit_model.parameters.keys()) + \
                list(self.new_parameters.keys())
            par_name_list.sort()
            pop_initial_parameter.options = par_name_list
            pop_report_noise_parameter.options = par_name_list

            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            pop_dropdown.options = pop_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        population_name = pop_dropdown.value
        pop = None
        if population_name in self.edit_model.populations:
            pop = self.edit_model.populations[population_name]
        else:
            pop = self.new_populations[population_name]
        pop_name.value = pop.name
        pop_description.value = pop.description
        pop_initial_value_by_parameter.value = isinstance(pop.initial_value,Parameter)
        if isinstance(pop.initial_value,Parameter):
            pop_initial_value.disabled = True
            pop_initial_parameter.disabled = False
            pop_initial_parameter.value = str(pop.initial_value)
        else:
            pop_initial_value.disabled = False
            pop_initial_parameter.disabled = True
            pop_initial_value.value = str(pop.initial_value)
        pop_hidden.value = pop.hidden
        pop_color.value = pop.color
        pop_show_sim.value = pop.show_sim
        report_noise, report_noise_par = pop.get_report_noise()
        pop_report_noise.value = report_noise
        if pop_report_noise.value:
            pop_report_noise_parameter.disabled = False
            pop_report_noise_parameter.value = str(report_noise_par)
        else:
            pop_report_noise_parameter.disabled = True

        with output:
            print('Population options loaded')
        
    pop_dropdown.observe(dropdown_eventhandler, names='value')
    
    def pop_init_checkbox_eventhandler(change):
        if pop_initial_value_by_parameter.value:
            pop_initial_parameter.disabled = False
            pop_initial_value.disabled = True
        else:
            pop_initial_parameter.disabled = True
            pop_initial_value.disabled = False
            
    pop_initial_value_by_parameter.observe(pop_init_checkbox_eventhandler, names='value')
    
    def pop_report_noise_checkbox_eventhandler(change):
        pop_report_noise_parameter.disabled = not pop_report_noise.value
            
    pop_report_noise.observe(pop_report_noise_checkbox_eventhandler, names='value')

    def value_from_string(s):
        try:
            return int(s)
        except ValueError:
            return float(s)

    def pop_save_handler(b):        
        output.clear_output(True)
        population_name = pop_dropdown.value
        if pop_name.value != population_name:
            with output:
                print('You are not allowed to change the name of an existing population.')
                print('You click the "new population" button to create a new population')
                print('with this name.')
        else:
            pop = None
            if population_name in self.edit_model.populations:
                pop = self.edit_model.populations[population_name]
            else:
                pop = self.new_populations[population_name]
            pop.description = pop_description.value
            initial_value = None
            if pop_initial_value_by_parameter.value:
                par_name = pop_initial_parameter.value
                par = None
                if par_name in self.edit_model.parameters:
                    par = self.edit_model.parameters[par_name]
                else:
                    par = self.new_parameters[par_name]
                initial_value = par
            else:
                initial_value = value_from_string(pop_initial_value.value)
            pop.set_initial_value(initial_value)
            pop.hidden = pop_hidden.value
            pop.color = pop_color.value
            pop.show_sim = pop_show_sim.value
            if pop_report_noise.value:
                par_name = pop_report_noise_parameter.value
                par = None
                if par_name in self.edit_model.parameters:
                    par = self.edit_model.parameters[par_name]
                else:
                    par = self.new_parameters[par_name]
                pop.report_noise_par = par
                pop.set_report_noise(True, par)
            else:
                pop.set_report_noise(False, None)
                
            # must update model lists in case new parameters now being used
            self.edit_model.update_lists()

            with output:
                print('Changes saved to population.')
                print('You must save model to disk to make this permanent.')

    pop_save.on_click(pop_save_handler)    

    def pop_new_handler(b):
        output.clear_output(True)

        initial_value = None
        if pop_initial_value_by_parameter.value:
            par_name = pop_initial_parameter.value
            par = None
            if par_name in self.edit_model.parameters:
                par = self.edit_model.parameters[par_name]
            else:
                par = self.new_parameters[par_name]
            initial_value = par
        else:
            initial_value = value_from_string(pop_initial_value.value)
            
        report_noise_parameter = None
        if pop_report_noise.value:
            par_name = pop_report_noise_parameter.value
            par = None
            if par_name in self.edit_model.parameters:
                par = self.edit_model.parameters[par_name]
            else:
                par = self.new_parameters[par_name]
            report_noise_parameter = par

        pop = Population(pop_name.value, initial_value, description='description',
                         hidden=pop_hidden.value, color=pop_color.value,
                         show_sim=pop_show_sim.value, report_noise=pop_report_noise.value,
                         report_noise_par=report_noise_parameter)
        
        with output:
            if pop.name in self.edit_model.populations or \
                pop.name in self.new_populations:
                print('population with this name already exists.')
                print('Please change the name and try again.')
            else:
                self.new_populations[str(pop)] = pop
                print('New population created.')
                print('You must use this population and save the model to disk')
                print('to make this permanent.')

    pop_new.on_click(pop_new_handler)
    
    def pop_table_handler(b):
        table_output.clear_output(True)
        with table_output:
            print(tools.table.population_table(self.edit_model, width=110))
    
    pop_table.on_click(pop_table_handler)

    v_box1 = widgets.VBox([
        refresh_button,
        pop_dropdown,
        pop_name,
        pop_description,
        pop_initial_value_by_parameter,
        pop_initial_parameter,
        pop_initial_value,
        pop_hidden,
        pop_color,
        pop_show_sim,
        pop_report_noise,
        pop_report_noise_parameter,
        widgets.HBox([pop_save,
        pop_new]),
        pop_table
        ])
    
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.VBox([widgets.HBox([v_box1, hspace, output]),table_output])

def get_connectors_tab(self):

    connectors_tab = widgets.Tab()
    adder_tab = get_adder_tab(self)
    chain_tab = get_chain_tab(self)
    multiplier_tab = get_multiplier_tab(self)
    propagator_tab = get_propagator_tab(self)
    splitter_tab = get_splitter_tab(self)
    #populations_tab = get_populations_tab(self)
    #connectors_tab = get_connectors_tab(self)
    
    hspace = widgets.HTML(
    value="&nbsp;"*4,
    placeholder='Some HTML',
    description='')

    connectors_tab.children = [adder_tab,chain_tab,multiplier_tab,propagator_tab,splitter_tab,hspace]
    connectors_tab.set_title(0, 'Adder')
    connectors_tab.set_title(1, 'Chain')
    connectors_tab.set_title(2, 'Multiplier')
    connectors_tab.set_title(3, 'Propagator')
    connectors_tab.set_title(4, 'Splitter')
    connectors_tab.set_title(5, 'Subtractor')
    
    table_output = widgets.Output()
    con_table = widgets.Button(description='Connector Table', tooltip='Show all connectors in a table')
    def con_table_handler(b):
        table_output.clear_output(True)
        with table_output:
            print(tools.table.connector_table(self.edit_model, width=110))    
    con_table.on_click(con_table_handler)

    return widgets.VBox([con_table,connectors_tab,table_output])

def get_adder_tab(self):
        
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    add_dropdown = widgets.Dropdown(description='Adder:', disabled=False)
    
    add_name = widgets.Text(description='Name:')

    add_from_population = widgets.Dropdown(description='From pop:', disabled=False, 
                                           tooltip='Add from population') 
    add_to_population = widgets.Dropdown(description='To pop:', disabled=False, 
                                         tooltip='Add to population')
    add_location = widgets.Dropdown(description='After:', disabled=False, 
                                         tooltip='Insert after this connector')
    add_save = widgets.Button(description='Save changes', tooltip='Save changes to loaded model')
    add_new = widgets.Button(description='Insert adder', tooltip='Create new adder and insert into model')
    add_delete = widgets.Button(description='Delete adder', tooltip='Remove from model',
                                button_style='warning', icon='warning')

    def refresh(b):
        # Remember that connector order is important - do not sort them!
        if self.edit_model is not None:
            
            connector_name_list = ['AT TOP']
            for con_name in self.edit_model.connector_list:
                connector_name_list.append(con_name)
            add_location.options = connector_name_list

            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            add_from_population.options = pop_name_list
            add_to_population.options = pop_name_list
            
            adder_name_list = []
            for con_name in self.edit_model.connector_list:
                con = self.edit_model.connectors[con_name]
                if isinstance(con,Adder):
                    adder_name_list.append(str(con))
            add_dropdown.options = adder_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        adder_name = add_dropdown.value
        adder = self.edit_model.connectors[adder_name]
        add_name.value = adder.name
        add_from_population.value = str(adder.from_population)
        add_to_population.value = str(adder.to_population)

        with output:
            print('Adder options loaded')

    add_dropdown.observe(dropdown_eventhandler, names='value')

    # This function should not be used: considered risky to allow to modify
    # connectors - maintaining the list of parameters etc.    
    def add_save_handler(b):        
        output.clear_output(True)
        adder_name = add_dropdown.value
        if add_name.value != adder_name:
            with output:
                print('You are not allowed to change the name of an existing adder.')
                print('You click the "new adder" button to create a new adder')
                print('with this name.')
        else:
            adder = self.edit_model.connectors[adder_name]
            from_pop_name = add_from_population.value
            from_pop = None
            if from_pop_name in self.edit_model.populations:
                from_pop = self.edit_model.populations[from_pop_name]
            else:
                from_pop = self.new_populations[from_pop_name]
            adder.from_population = from_pop

            to_pop_name = add_to_population.value
            to_pop = None
            if to_pop_name in self.edit_model.populations:
                to_pop = self.edit_model.populations[to_pop_name]
            else:
                to_pop = self.new_populations[to_pop_name]
            adder.to_population = to_pop            
            
            # after modifying a connector, it is necessary for the model to
            # update its lists of populations etc.
        
            self.edit_model.update_lists()

            with output:
                print('Changes saved to adder.')
                print('You must save model to disk to make this permanent.')

    add_save.on_click(add_save_handler)    

    def add_new_handler(b):
        output.clear_output(True)
              
        from_pop_name = add_from_population.value
        from_pop = None
        if from_pop_name in self.edit_model.populations:
            from_pop = self.edit_model.populations[from_pop_name]
        else:
            from_pop = self.new_populations[from_pop_name]

        to_pop_name = add_to_population.value
        to_pop = None
        if to_pop_name in self.edit_model.populations:
            to_pop = self.edit_model.populations[to_pop_name]
        else:
            to_pop = self.new_populations[to_pop_name]           

        adder = Adder(add_name.value, from_pop, to_pop)
        
        loc_name = add_location.value
        loc_con = None
        if loc_name != 'AT TOP':
            loc_con = self.edit_model.connectors[loc_name]
        else:
            top_con_name = self.edit_model.connector_list[0]
            loc_con = self.edit_model.connectors[top_con_name]
            
        with output:
            if adder.name in self.edit_model.connectors:
                print('Connector with this name already exists.')
                print('Please change the name and try again.')
            else:
                print('New adder created and added')
                if loc_name != 'AT TOP':
                    self.edit_model.add_connector(adder, after_connector=loc_con)
                    print('after connector: '+loc_name)
                else:
                    self.edit_model.add_connector(adder, before_connector=loc_con)
                    print('at the top.')
                print('You must save the model to disk')
                print('to make this permanent.')

    add_new.on_click(add_new_handler)
    
    def add_delete_handler(b):
        output.clear_output(True)
        adder_name = add_dropdown.value
        if add_name.value != adder_name:
            with output:
                print('You changed the name of an existing adder before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            adder = self.edit_model.connectors[adder_name]
        
        self.edit_model.remove_connector(adder)
        with output:
            print('Adder '+str(adder)+' removed from model.')
            print('You must save the model to disk')
            print('to make this permanent.')
            
    add_delete.on_click(add_delete_handler)
 
    v_box1 = widgets.VBox([
        refresh_button,
        add_dropdown, 
        add_name,
        add_from_population,
        add_to_population,
        widgets.HBox([add_new, add_location]),
        add_delete
        ])
    
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])

def get_propagator_tab(self):
        
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    prop_dropdown = widgets.Dropdown(description='Propagator:', disabled=False)
    
    prop_name_widget = widgets.Text(description='Name:')

    prop_from_population = widgets.Dropdown(description='From pop:', disabled=False, 
                                            tooltip='Add from population') 
    prop_to_population = widgets.Dropdown(description='To pop:', disabled=False, 
                                          tooltip='Add to population')
    fraction_dropdown = widgets.Dropdown(description='Fraction:', disabled=False, 
                                         tooltip='Fraction to be propagated')
    delay_dropdown = widgets.Dropdown(description='Delay:', disabled=False, 
                                      tooltip='Delay in propagation')
    prop_location = widgets.Dropdown(description='After:', disabled=False, 
                                     tooltip='Insert after this connector')

    prop_new = widgets.Button(description='Insert new', tooltip='Create new propagator and insert into model')
    prop_delete = widgets.Button(description='Delete', tooltip='Remove propagator from model',
                                 button_style='warning', icon='warning')

    def refresh(b):
        # Remember that connector order is important - do not sort them!
        if self.edit_model is not None:
            
            connector_name_list = ['AT TOP','DO NOT INSERT']
            for con_name in self.edit_model.connector_list:
                connector_name_list.append(con_name)
            prop_location.options = connector_name_list

            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            prop_from_population.options = pop_name_list
            prop_to_population.options = pop_name_list
            
            par_name_list = list(self.edit_model.parameters.keys()) + \
                list(self.new_parameters.keys())
            par_name_list.sort()
            fraction_dropdown.options = par_name_list
            
            self.delays = get_model_delays(self)
            delay_name_list =  list(self.delays.keys()) + list(self.new_delays.keys())
            delay_name_list.sort()
            
            delay_dropdown.options = delay_name_list
            
            prop_name_list = []
            for con_name in self.edit_model.connector_list:
                con = self.edit_model.connectors[con_name]
                if isinstance(con,Propagator):
                    prop_name_list.append(str(con))
            prop_dropdown.options = prop_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        prop_name = prop_dropdown.value
        prop = self.edit_model.connectors[prop_name]
        prop_name_widget.value = prop.name
        prop_from_population.value = str(prop.from_population)
        prop_to_population.value = str(prop.to_population)
        fraction_dropdown.value = str(prop.fraction)
        delay_dropdown.value = str(prop.delay)

        with output:
            print('Propagator options loaded')

    prop_dropdown.observe(dropdown_eventhandler, names='value')

    def prop_new_handler(b):
        output.clear_output(True)
              
        from_pop_name = prop_from_population.value
        from_pop = None
        if from_pop_name in self.edit_model.populations:
            from_pop = self.edit_model.populations[from_pop_name]
        else:
            from_pop = self.new_populations[from_pop_name]

        to_pop_name = prop_to_population.value
        to_pop = None
        if to_pop_name in self.edit_model.populations:
            to_pop = self.edit_model.populations[to_pop_name]
        else:
            to_pop = self.new_populations[to_pop_name]
            
        fraction_name = fraction_dropdown.value
        fraction = None
        if fraction_name in self.edit_model.parameters:
            fraction = self.edit_model.parameters[fraction_name]
        else:
            fraction = self.new_parameters[fraction_name]

        self.delays = get_model_delays(self)
        delay_name = delay_dropdown.value
        delay = None
        if delay_name in self.delays:
            delay = self.delays[delay_name]
        else:
            delay = self.new_delays[delay_name]

        propagator = Propagator(prop_name_widget.value, from_pop, to_pop, fraction, delay)
        
        loc_name = prop_location.value
        loc_con = None
        if loc_name == 'AT TOP':
            top_con_name = self.edit_model.connector_list[0]
            loc_con = self.edit_model.connectors[top_con_name]
        elif loc_name =='DO NOT INSERT':
            loc_con = None
        else: 
            loc_con = self.edit_model.connectors[loc_name]

            
        with output:
            if propagator.name in self.edit_model.connectors:
                print('Connector with this name already exists.')
                print('Please change the name and try again.')
                print('If you want to modify this connector,')
                print('delete this one and add a new one with this name.')  
            else:
                print('New propagator created')
                if loc_name == 'AT TOP':
                    self.edit_model.add_connector(propagator, before_connector=loc_con)
                    print('and added at the top.')
                elif loc_name =='DO NOT INSERT':
                    self.new_propagators[propagator.name] = propagator
                    print('but not added to model.')
                    print('You can include this propagator in a chain.')
                else:
                    self.edit_model.add_connector(propagator, after_connector=loc_con)
                    print('and added after connector: '+loc_name)

                print('You must save the model to disk')
                print('to make this permanent.')

    prop_new.on_click(prop_new_handler)
    
    def prop_delete_handler(b):
        output.clear_output(True)
        prop_name = prop_dropdown.value
        if prop_name_widget.value != prop_name:
            with output:
                print('You changed the name of an existing propagator before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            prop = self.edit_model.connectors[prop_name]
        
        self.edit_model.remove_connector(prop)
        with output:
            print('Propagator '+str(prop)+' removed from model.')
            print('You must save the model to disk')
            print('to make this permanent.')
            
    prop_delete.on_click(prop_delete_handler)
 
    v_box1 = widgets.VBox([
        refresh_button,
        prop_dropdown, 
        prop_name_widget,
        prop_from_population,
        prop_to_population,
        fraction_dropdown,
        delay_dropdown,
        widgets.HBox([prop_new, prop_location]),
        widgets.HBox([prop_delete])
        ])
        
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])

def get_chain_tab(self):
        
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    chain_dropdown = widgets.Dropdown(description='Chain:', disabled=False)
    
    chain_name_widget = widgets.Text(description='Name:')

    chain_from_population = widgets.Dropdown(description='From pop:', disabled=False, 
                                             tooltip='Add from population') 
    chain_to_population = widgets.Dropdown(description='To pop:', disabled=False, 
                                           tooltip='Add to population')
    chain_list_text = widgets.Textarea(description='Prop list:', disabled=False,
                                       tootip = 'ordered list of one-to-one norm propagators',
                                       placeholder = 'ordered list of one-to-one norm propagators')
    fraction_dropdown = widgets.Dropdown(description='Fraction:', disabled=False, 
                                         tooltip='Fraction remaining to be propagated')
    delay_dropdown = widgets.Dropdown(description='Delay:', disabled=False, 
                                      tooltip='Delay in propagation of remainder')
    chain_location = widgets.Dropdown(description='After:', disabled=False, 
                                      tooltip='Insert after this connector')

    chain_new = widgets.Button(description='Insert new', tooltip='Create new chain and insert into model')
    chain_delete = widgets.Button(description='Delete', tooltip='Remove chain from model',
                                 button_style='warning', icon='warning')

    def refresh(b):
        # Remember that connector order is important - do not sort them!
        if self.edit_model is not None:
            
            connector_name_list = ['AT TOP']
            for con_name in self.edit_model.connector_list:
                connector_name_list.append(con_name)
            chain_location.options = connector_name_list

            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            chain_from_population.options = pop_name_list
            chain_to_population.options = pop_name_list
            
            par_name_list = list(self.edit_model.parameters.keys()) + \
                list(self.new_parameters.keys())
            par_name_list.sort()
            fraction_dropdown.options = par_name_list
            
            self.delays = get_model_delays(self)
            delay_name_list =  list(self.delays.keys()) + list(self.new_delays.keys())
            delay_name_list.sort()
            
            delay_dropdown.options = delay_name_list
            
            chain_name_list = []
            for con_name in self.edit_model.connector_list:
                con = self.edit_model.connectors[con_name]
                if isinstance(con,Chain):
                    chain_name_list.append(str(con))
            chain_dropdown.options = chain_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        chain_name = chain_dropdown.value
        chain = self.edit_model.connectors[chain_name]
        chain_name_widget.value = chain.name
        chain_from_population.value = str(chain.from_population)
        chain_to_population.value = str(chain.to_population)
        prop_name_list = []
        for prop in chain.chain:
            prop_name_list.append(str(prop))
        chain_list_text.value = ','.join(prop_name_list)
        fraction_dropdown.value = str(chain.fraction)
        delay_dropdown.value = str(chain.delay)

        with output:
            print('Chain options loaded')

    chain_dropdown.observe(dropdown_eventhandler, names='value')

    def chain_new_handler(b):
        output.clear_output(True)
              
        from_pop_name = chain_from_population.value
        from_pop = None
        if from_pop_name in self.edit_model.populations:
            from_pop = self.edit_model.populations[from_pop_name]
        else:
            from_pop = self.new_populations[from_pop_name]

        to_pop_name = chain_to_population.value
        to_pop = None
        if to_pop_name in self.edit_model.populations:
            to_pop = self.edit_model.populations[to_pop_name]
        else:
            to_pop = self.new_populations[to_pop_name]

        prop_list = []
        prop_name_list = chain_list_text.value.split(',')
        for prop_name in prop_name_list:
            name = prop_name.strip()
            if len(name) > 0:
                prop = None
                if name in self.edit_model.connectors:
                    prop = self.edit_model.connectors[name]
                elif name in self.new_propagators:
                    prop = self.new_propatators[name]
                else:
                    raise ValueError('Cannot find propagator with name:'+name)
                prop_list.append(prop)
        if len(prop_list) == 0:
            raise ValueError('List of propagators missing')

        fraction_name = fraction_dropdown.value
        fraction = None
        if fraction_name in self.edit_model.parameters:
            fraction = self.edit_model.parameters[fraction_name]
        else:
            fraction = self.new_parameters[fraction_name]

        self.delays = get_model_delays(self)
        delay_name = delay_dropdown.value
        delay = None
        if delay_name in self.delays:
            delay = self.delays[delay_name]
        else:
            delay = self.new_delays[delay_name]

        chain = Chain(chain_name_widget.value, from_pop, to_pop, prop_list, fraction,
                      delay, self.edit_model)
        
        loc_name = chain_location.value
        loc_con = None
        if loc_name == 'AT TOP':
            top_con_name = self.edit_model.connector_list[0]
            loc_con = self.edit_model.connectors[top_con_name]
        else: 
            loc_con = self.edit_model.connectors[loc_name]

        with output:
            if chain.name in self.edit_model.connectors:
                print('Connector with this name already exists.')
                print('Please change the name and try again.')
                print('If you want to modify this connector,')
                print('delete this one and add a new one with this name.')  
            else:
                print('New chain created')
                if loc_name == 'AT TOP':
                    self.edit_model.add_connector(chain, before_connector=loc_con)
                    print('and added at the top.')
                else:
                    self.edit_model.add_connector(chain, after_connector=loc_con)
                    print('and added after connector: '+loc_name)

                print('You must save the model to disk')
                print('to make this permanent.')

                match = False
                for prop in prop_list:
                    if prop in self.edit_model.connectors:
                        match = True
                if match:
                    print()
                    print('*** Warning: a propagator in the chain is also')
                    print('used in the model itself. Double check! ***')

    chain_new.on_click(chain_new_handler)
    
    def chain_delete_handler(b):
        output.clear_output(True)
        chain_name = chain_dropdown.value
        if chain_name_widget.value != chain_name:
            with output:
                print('You changed the name of an existing chain before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            chain = self.edit_model.connectors[chain_name]
        
        self.edit_model.remove_connector(chain)
        with output:
            print('Chain '+str(chain)+' removed from model.')
            print('You must save the model to disk')
            print('to make this permanent.')
            
    chain_delete.on_click(chain_delete_handler)
 
    v_box1 = widgets.VBox([
        refresh_button,
        chain_dropdown, 
        chain_name_widget,
        chain_from_population,
        chain_to_population,
        chain_list_text,
        fraction_dropdown,
        delay_dropdown,
        widgets.HBox([chain_new, chain_location]),
        widgets.HBox([chain_delete])
        ])
        
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])


def get_multiplier_tab(self):
        
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    mult_dropdown = widgets.Dropdown(description='Multiplier:', disabled=False)
    
    mult_name_widget = widgets.Text(description='Name:')

    mult_from_population0 = widgets.Dropdown(description='From pop1:', disabled=False, 
                                             tooltip='Mult from population0')
    mult_from_population1 = widgets.Dropdown(description='From pop2:', disabled=False, 
                                             tooltip='Mult from population1')
    mult_has_divider = widgets.Checkbox(description='Has divider', disabled=False,
                                        tooltip='Include a divider')
    mult_from_population2 = widgets.Dropdown(description='From pop3:', disabled=False, 
                                             tooltip='Divider population') 
    mult_to_population = widgets.Dropdown(description='To pop:', disabled=False, 
                                          tooltip='Add to population')
    scale_parameter_dropdown = widgets.Dropdown(description='Scale par:', disabled=False, 
                                         tooltip='Scaling parameter')
    delay_dropdown = widgets.Dropdown(description='Delay:', disabled=False, 
                                      tooltip='Delay in propagation')
    distribution_dropdown = widgets.Dropdown(description='Distribution:', disabled=False,
                                             options=['poisson','nbinom'],
                                             tooltip='Newly infected distribution')
    nbinom_par_dropdown = widgets.Dropdown(description='nbinom p', disabled=True, 
                                           tooltip='Negative binomial parameter p')    
    mult_location = widgets.Dropdown(description='After:', disabled=False, 
                                     tooltip='Insert after this connector')

    mult_save = widgets.Button(description='Save', tooltip='Save changes to Multiplier')
    mult_new = widgets.Button(description='Insert new', tooltip='Create new propagator and insert into model')
    mult_delete = widgets.Button(description='Delete', tooltip='Remove multiplier from model',
                                 button_style='warning', icon='warning')

    def refresh(b):
        # Remember that connector order is important - do not sort them!
        if self.edit_model is not None:
            
            connector_name_list = ['AT TOP']
            for con_name in self.edit_model.connector_list:
                connector_name_list.append(con_name)
            mult_location.options = connector_name_list

            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            mult_from_population0.options = pop_name_list
            mult_from_population1.options = pop_name_list
            mult_from_population2.options = pop_name_list
            mult_to_population.options = pop_name_list
            
            par_name_list = list(self.edit_model.parameters.keys()) + \
                list(self.new_parameters.keys())
            par_name_list.sort()
            scale_parameter_dropdown.options = par_name_list
            nbinom_par_dropdown.options = par_name_list
            
            self.delays = get_model_delays(self)
            delay_name_list =  list(self.delays.keys()) + list(self.new_delays.keys())
            delay_name_list.sort()
            
            delay_dropdown.options = delay_name_list
            
            mult_name_list = []
            for con_name in self.edit_model.connector_list:
                con = self.edit_model.connectors[con_name]
                if isinstance(con,Multiplier):
                    mult_name_list.append(str(con))
            mult_dropdown.options = mult_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        mult_name = mult_dropdown.value
        mult = self.edit_model.connectors[mult_name]
        mult_name_widget.value = mult.name
        from_populations = mult.from_population        
        mult_from_population0.value = str(from_populations[0])
        mult_from_population1.value = str(from_populations[1])
        if len(from_populations) == 3:
            mult_from_population2.value = str(from_populations[2])
            mult_has_divider.value = True
        mult_to_population.value = str(mult.to_population)
        scale_parameter_dropdown.value = str(mult.scale_parameter)
        delay_dropdown.value = str(mult.delay)
        distribution, nbinom_par = mult.get_distribution()
        distribution_dropdown.value = distribution
        if distribution == 'nbinom':
            nbinom_par_dropdown.value = nbinom_par
            nbinom_par_dropdown.disabled = False
        else:
            nbinom_par_dropdown.disabled = True

        with output:
            print('Multiplier options loaded')

    mult_dropdown.observe(dropdown_eventhandler, names='value')

    def mult_has_divider_checkbox_eventhandler(change):
        mult_from_population2.disabled = not mult_has_divider.value
            
    mult_has_divider.observe(mult_has_divider_checkbox_eventhandler, names='value')

    def distribution_dropdown_eventhandler(change):
        nbinom_par_dropdown.disabled = distribution_dropdown.value != 'nbinom'
    
    distribution_dropdown.observe(distribution_dropdown_eventhandler, names='value')

    # allow the multiplier to be modified (changing the distribution)
    def mult_save_handler(b):        
        output.clear_output(True)
        mult_name = mult_dropdown.value
        if mult_name.value != mult_name:
            with output:
                print('You are not allowed to change the name of an existing multiplier.')
                print('You click the "Insert new" button to create a new multiplier')
                print('with this name.')
        else:
            mult = self.edit_model.connectors[mult_name]
            from_pop_names = [mult_from_population0.value,mult_from_population1.value]
            if mult_has_divider.value:
                from_pop_names.append(mult_from_population2.value)
            from_pops = []
            for from_pop_name in from_pop_names:
                from_pop = None
                if from_pop_name in self.edit_model.populations:
                    from_pop = self.edit_model.populations[from_pop_name]
                else:
                    from_pop = self.new_populations[from_pop_name]
                from_pops.append(from_pop)
            mult.from_population = from_pops

            to_pop_name = mult_to_population.value
            to_pop = None
            if to_pop_name in self.edit_model.populations:
                to_pop = self.edit_model.populations[to_pop_name]
            else:
                to_pop = self.new_populations[to_pop_name]
            mult.to_population = to_pop

            scale_parameter_name = scale_parameter_dropdown.value
            scale_parameter = None
            if scale_parameter_name in self.edit_model.parameters:
                scale_parameter = self.edit_model.parameters[scale_parameter_name]
            else:
                scale_parameter = self.new_parameters[scale_parameter_name]
            mult.scale_parameter =  scale_parameter
            
            self.delays = get_model_delays(self)
            delay_name = delay_dropdown.value
            delay = None
            if delay_name in self.delays:
                delay = self.delays[delay_name]
            else:
                delay = self.new_delays[delay_name]
            mult.delay = delay

            nbinom_par_name = nbinom_par_dropdown.value
            nbinom_par = None
            if distribution_dropdown.value == 'nbinom':
                if nbinom_par_name in self.edit_model.parameters:
                    nbinom_par = self.edit_model.parameters[nbinom_par_name]
                else:
                    nbinom_par = self.new_parameters[nbinom_par_name]
            mult.set_distribution(distribution_dropdown.value, nbinom_par)

            # after modifying a connector, it is necessary for the model to
            # update its lists of populations etc.
        
            self.edit_model.update_lists()

            with output:
                print('Changes saved to multiplier.')
                print('You must save model to disk to make this permanent.')

    mult_save.on_click(mult_save_handler)    

    def mult_new_handler(b):
        output.clear_output(True)

        from_pop_names = [mult_from_population0.value,mult_from_population1.value]
        if mult_has_divider.value:
            from_pop_names.append(mult_from_population2.value)
        from_pops = []
        for from_pop_name in from_pop_names:
            from_pop = None
            if from_pop_name in self.edit_model.populations:
                from_pop = self.edit_model.populations[from_pop_name]
            else:
                from_pop = self.new_populations[from_pop_name]
            from_pops.append(from_pop)

        to_pop_name = mult_to_population.value
        to_pop = None
        if to_pop_name in self.edit_model.populations:
            to_pop = self.edit_model.populations[to_pop_name]
        else:
            to_pop = self.new_populations[to_pop_name]
            
        scale_parameter_name = scale_parameter_dropdown.value
        scale_parameter = None
        if scale_parameter_name in self.edit_model.parameters:
            scale_parameter = self.edit_model.parameters[scale_parameter_name]
        else:
            scale_parameter = self.new_parameters[scale_parameter_name]

        self.delays = get_model_delays(self)
        delay_name = delay_dropdown.value
        delay = None
        if delay_name in self.delays:
            delay = self.delays[delay_name]
        else:
            delay = self.new_delays[delay_name]
            
        nbinom_par_name = nbinom_par_dropdown.value
        nbinom_par = None
        if distribution_dropdown.value == 'nbinom':
            if nbinom_par_name in self.edit_model.parameters:
                nbinom_par = self.edit_model.parameters[nbinom_par_name]
            else:
                nbinom_par = self.new_parameters[nbinom_par_name]

        multiplier = Multiplier(mult_name_widget.value, from_pops, to_pop, scale_parameter, delay,
                                self.edit_model, distribution=distribution_dropdown.value,
                                nbinom_par=nbinom_par)

        loc_name = mult_location.value
        loc_con = None
        if loc_name == 'AT TOP':
            top_con_name = self.edit_model.connector_list[0]
            loc_con = self.edit_model.connectors[top_con_name]
        else: 
            loc_con = self.edit_model.connectors[loc_name]

            
        with output:
            if multiplier.name in self.edit_model.connectors:
                print('Connector with this name already exists.')
                print('Please change the name and try again.')
  
            else:
                print('New multiplier created')
                if loc_name == 'AT TOP':
                    self.edit_model.add_connector(multiplier, before_connector=loc_con)
                    print('and added at the top.')
                else:
                    self.edit_model.add_connector(multiplier, after_connector=loc_con)
                    print('and added after connector: '+loc_name)

                print('You must save the model to disk')
                print('to make this permanent.')

    mult_new.on_click(mult_new_handler)
    
    def mult_delete_handler(b):
        output.clear_output(True)
        mult_name = mult_dropdown.value
        if mult_name_widget.value != mult_name:
            with output:
                print('You changed the name of an existing multiplier before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            mult = self.edit_model.connectors[mult_name]
        
        self.edit_model.remove_connector(mult)
        with output:
            print('Multiplier '+str(mult)+' removed from model.')
            print('You must save the model to disk')
            print('to make this permanent.')
            
    mult_delete.on_click(mult_delete_handler)
 
    v_box1 = widgets.VBox([
        refresh_button,
        mult_dropdown, 
        mult_name_widget,
        mult_from_population0,
        mult_from_population1,
        mult_has_divider,
        mult_from_population2,
        mult_to_population,
        scale_parameter_dropdown,
        delay_dropdown,
        distribution_dropdown,
        nbinom_par_dropdown,
        widgets.HBox([mult_new, mult_location]),
        widgets.HBox([mult_save, mult_delete])
        ])
        
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])



    """
    Splitter distributes its incoming population to other populations,
    either in the next time step or distributed in time:
        - connector_name: string, short descriptor
        - from_population: Population object, source of population to be
        propagated
        - to_population: list of two or more Population objects,
        the destination populations.
        - fractions: list of Parameter object with expected
        fraction of population to be propagated to the first to_population,
        the second is the fraction of the remaining to go to the next to_population
        and so on, with the remainder going to the other population
        The fractions must be in the range (0.,1.)
        - delay: Delay object or list of the Delay objects that define how
        propagation is spread over time.


    def __init__(self, connector_name, from_population, to_population,
                 fractions, delay):
        
            """
            
def get_splitter_tab(self):
        
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    splitter_dropdown = widgets.Dropdown(description='Splitter:', disabled=False)
    
    splitter_name_widget = widgets.Text(description='Name:')

    splitter_from_population = widgets.Dropdown(description='From pop:', disabled=False, 
                                             tooltip='Add from population') 
    splitter_to_list_text = widgets.Textarea(description='To pops:', disabled=False,
                                       tootip = 'commma separated list of populations',
                                       placeholder = 'commma separated list of populations')
    fractions_list_text = widgets.Textarea(description='Fractions:', disabled=False, 
                                          tooltip= 'comma separated list of fraction parameters',
                                          placeholder = 'comma separated list of fraction parameters')
    delay_dropdown = widgets.Dropdown(description='Delay:', disabled=False, 
                                      tooltip='Delay in propagation of remainder')
    splitter_location = widgets.Dropdown(description='After:', disabled=False, 
                                      tooltip='Insert after this connector')

    splitter_new = widgets.Button(description='Insert new', tooltip='Create new splitter and insert into model')
    splitter_delete = widgets.Button(description='Delete', tooltip='Remove splitter from model',
                                 button_style='warning', icon='warning')

    def refresh(b):
        # Remember that connector order is important - do not sort them!
        if self.edit_model is not None:
            
            connector_name_list = ['AT TOP']
            for con_name in self.edit_model.connector_list:
                connector_name_list.append(con_name)
            splitter_location.options = connector_name_list

            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            splitter_from_population.options = pop_name_list
            
            self.delays = get_model_delays(self)
            delay_name_list =  list(self.delays.keys()) + list(self.new_delays.keys())
            delay_name_list.sort()
            
            delay_dropdown.options = delay_name_list
            
            splitter_name_list = []
            for con_name in self.edit_model.connector_list:
                con = self.edit_model.connectors[con_name]
                if isinstance(con,Splitter):
                    splitter_name_list.append(str(con))
            splitter_dropdown.options = splitter_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        splitter_name = splitter_dropdown.value
        splitter = self.edit_model.connectors[splitter_name]
        splitter_name_widget.value = splitter.name
        splitter_from_population.value = str(splitter.from_population)
        pop_name_list = []
        for pop in splitter.to_population:
            pop_name_list.append(str(pop))
        splitter_to_list_text.value = ','.join(pop_name_list)
        par_name_list = []
        for par in splitter.fractions:
            par_name_list.append(str(par))
        fractions_list_text.value = ','.join(par_name_list)

        delay_dropdown.value = str(splitter.delay)

        with output:
            print('Splitter options loaded')

    splitter_dropdown.observe(dropdown_eventhandler, names='value')

    def splitter_new_handler(b):
        output.clear_output(True)
              
        from_pop_name = splitter_from_population.value
        from_pop = None
        if from_pop_name in self.edit_model.populations:
            from_pop = self.edit_model.populations[from_pop_name]
        else:
            from_pop = self.new_populations[from_pop_name]

        to_pops = []
        to_pop_names = splitter_to_list_text.value.split(',')
        for to_pop_name in to_pop_names:
            to_pop = None
            if to_pop_name in self.edit_model.populations:
                to_pop = self.edit_model.populations[to_pop_name]
            else:
                to_pop = self.new_populations[to_pop_name]
            to_pops.append(to_pop)

        fractions = []
        fraction_names = fractions_list_text.value.split(',')
        for fraction_name in fraction_names:
            fraction = None
            if fraction_name in self.edit_model.parameters:
                fraction = self.edit_model.parameters[fraction_name]
            else:
                fraction = self.new_parameters[fraction_name]
            fractions.append(fraction)

        self.delays = get_model_delays(self)
        delay_name = delay_dropdown.value
        delay = None
        if delay_name in self.delays:
            delay = self.delays[delay_name]
        else:
            delay = self.new_delays[delay_name]

        splitter = Splitter(splitter_name_widget.value, from_pop, to_pops, fractions,
                      delay)
                
        loc_name = splitter_location.value
        loc_con = None
        if loc_name == 'AT TOP':
            top_con_name = self.edit_model.connector_list[0]
            loc_con = self.edit_model.connectors[top_con_name]
        else: 
            loc_con = self.edit_model.connectors[loc_name]

        with output:
            if splitter.name in self.edit_model.connectors:
                print('Connector with this name already exists.')
                print('Please change the name and try again.')
                print('If you want to modify this connector,')
                print('delete this one and add a new one with this name.')  
            else:
                print('New splitter created')
                if loc_name == 'AT TOP':
                    self.edit_model.add_connector(splitter, before_connector=loc_con)
                    print('and added at the top.')
                else:
                    self.edit_model.add_connector(splitter, after_connector=loc_con)
                    print('and added after connector: '+loc_name)

                print('You must save the model to disk')
                print('to make this permanent.')

    splitter_new.on_click(splitter_new_handler)
    
    def splitter_delete_handler(b):
        output.clear_output(True)
        splitter_name = splitter_dropdown.value
        if splitter_name_widget.value != splitter_name:
            with output:
                print('You changed the name of an existing splitter before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            splitter = self.edit_model.connectors[splitter_name]
        
        self.edit_model.remove_connector(splitter)
        with output:
            print('Splitter '+str(splitter)+' removed from model.')
            print('You must save the model to disk')
            print('to make this permanent.')
            
    splitter_delete.on_click(splitter_delete_handler)
 
    v_box1 = widgets.VBox([
        refresh_button,
        splitter_dropdown, 
        splitter_name_widget,
        splitter_from_population,
        splitter_to_list_text,
        fractions_list_text,
        delay_dropdown,
        widgets.HBox([splitter_new, splitter_location]),
        widgets.HBox([splitter_delete])
        ])
        
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])
