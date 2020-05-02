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

    def include_delay_pars(delay, a_dict):
        if delay.delay_type == 'norm':
            a_dict[delay.delay_parameters['mean'].name] = delay.delay_parameters['mean']
            a_dict[delay.delay_parameters['sigma'].name] = delay.delay_parameters['sigma']
        elif delay.delay_type == 'uniform':
            a_dict[delay.delay_parameters['mean'].name] = delay.delay_parameters['mean']
            a_dict[delay.delay_parameters['half_width'].name] = delay.delay_parameters['half-width']
        elif delay.delay_type == 'erlang':
            a_dict[delay.delay_parameters['mean'].name] = delay.delay_parameters['mean']
            a_dict[delay.delay_parameters['k'].name] = delay.delay_parameters['k']

    def get_delay_list(self):
        delay_par_dict = {}
        for key in self.edit_model.connectors:
            con = self.edit_model.connectors[key]
            if hasattr(con,'delay'):
                if isinstance(con.delay, list):
                    for delay in con.delay:
                        self.delays[str(delay)] = delay
                        include_delay_pars(delay, delay_par_dict)
                        if type(con).__name__ == 'Chain':
                            for chain_con in con.chain:
                                self.delays[str(chain_con.delay)] = chain_con.delay
                                include_delay_pars(chain_con.delay, delay_par_dict)
                else:
                    self.delays[str(con.delay)] = con.delay
                    include_delay_pars(con.delay, delay_par_dict)
                    if type(con).__name__ == 'Chain':
                        for chain_con in con.chain:
                            self.delays[str(chain_con.delay)] = chain_con.delay
                            include_delay_pars(chain_con.delay, delay_par_dict)
        delay_list = list(self.delays.keys()) + list(self.new_delays.keys())
        delay_list.sort()
        return delay_list, delay_par_dict

    def refresh(b):
        if self.edit_model is not None:
            delay_dropdown_options, self.delay_par_dict = get_delay_list(self)

            par_name_list = list(self.edit_model.parameters.keys()) + \
            list(self.new_parameters.keys()) + list(self.delay_par_dict.keys())
            # remove duplicates
            par_name_list = list(dict.fromkeys(par_name_list))
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
            delay_par1.disabled = True
        else:
            delay_par1.disabled = False
            delay_par1.disabled = False
        
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
        pop_report_noise.value = pop.report_noise
        if pop_report_noise.value:
            pop_report_noise_parameter.disabled = False
            pop_report_noise_parameter.value = str(pop.report_noise_par)
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
            pop.report_noise = pop_report_noise.value
            if pop_report_noise.value:
                par_name = pop_report_noise_parameter.value
                par = None
                if par_name in self.edit_model.parameters:
                    par = self.edit_model.parameters[par_name]
                else:
                    par = self.new_parameters[par_name]
                pop.report_noise_par = par

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
    #parameters_tab = get_parameters_tab(self)
    #delays_tab = get_delays_tab(self)
    #populations_tab = get_populations_tab(self)
    #connectors_tab = get_connectors_tab(self)
    
    hspace = widgets.HTML(
    value="&nbsp;"*4,
    placeholder='Some HTML',
    description='')

    connectors_tab.children = [adder_tab,hspace,hspace,hspace,hspace,hspace]
    connectors_tab.set_title(0, 'Adder')
    connectors_tab.set_title(1, 'Chain')
    connectors_tab.set_title(2, 'Multiplier')
    connectors_tab.set_title(3, 'Propagator')
    connectors_tab.set_title(4, 'Splitter')
    connectors_tab.set_title(5, 'Subtractor')
    
    table_output = widgets.Output()
    con_table = widgets.Button(description='Conn Table', tooltip='Show all connectors in a table')
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
    add_new = widgets.Button(description='New adder', tooltip='Create new adder')
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
                print('You change the name of an existing adder prior asking to remove it.')
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
        widgets.HBox([add_save, add_delete]),
        widgets.HBox([add_location, add_new])
        ])
    
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])
