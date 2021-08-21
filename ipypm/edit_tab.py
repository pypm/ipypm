# -*- coding: utf-8 -*-
"""
Defines the edit tab for adding/removing/adjusting objects

@author: karlen
"""

from __future__ import print_function
import ipywidgets as widgets

from datetime import date
import pickle

from pypmca import Model, Population, Delay, Parameter, Multiplier, Propagator, \
    Splitter, Adder, Subtractor, Chain, Modifier, Injector
import pypmca.tools.table as ptt

from ipypm import edit_connectors_tab

def get_tab(self):

    edit_tab = widgets.Tab()
    model_tab = get_model_tab(self)
    parameters_tab = get_parameters_tab(self)
    delays_tab = get_delays_tab(self)
    populations_tab = get_populations_tab(self)
    connectors_tab = edit_connectors_tab.get_conn_tab(self)
    transitions_tab = get_transitions_tab(self)
    boot_tab = get_boot_tab(self)

    edit_tab.children = [model_tab, parameters_tab, delays_tab, populations_tab,
                         connectors_tab, transitions_tab, boot_tab]
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
    model_upload = widgets.FileUpload(decription='Open model', accept='.pypm',
                                      multiple=False)

    model_name = widgets.Text(description='Name:')
    model_description = widgets.Textarea(description='Description:')
    model_t0 = widgets.DatePicker(description='t_0:', value = date(2020,3,1), 
                                  tooltip='Defines day 0 on plots', disabled=True)
    model_time_step = widgets.FloatText(description='time_step:', value = 1., disabled=True,
                                        tooltip='Duration of one time step. Units: days')

    model_new = widgets.Button(description='New model', tooltip='Create new empty model.', 
                               button_style='warning', icon='warning')
    model_file = widgets.Button(description='Save model', tooltip='Write edited model to disk.')
    model_filename = widgets.Text(value='', tooltip='Filename for saving edited model',
                                  placeholder='filename', description='Filename:')


    def model_upload_eventhandler(change):
        output.clear_output(True)
        filename = list(model_upload.value.keys())[0]
        self.edit_model_folder = filename[:filename.rfind('/')]
        my_pickle = model_upload.value[filename]['content']
        self.edit_model = pickle.loads(my_pickle)
        model_name.value = self.edit_model.name
        model_description.value = self.edit_model.description
        model_t0.value = self.edit_model.t0
        model_time_step.value = self.edit_model.get_time_step()
        with output:
            print(filename)
            print('Model loaded for editing. It has:')
            print(len(self.edit_model.populations), ' Populations')
            print(len(self.edit_model.connectors), ' Connectors')
            print(len(self.edit_model.parameters), ' Parameters')
            print(len(self.edit_model.transitions), ' Transitions')

    model_upload.observe(model_upload_eventhandler, names='value')

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
    
    def model_save_to_file(b):
        output.clear_output(True)
        mfn = model_filename.value
        if len(mfn) > 0:
            if '.pypm' not in mfn:
                mfn = mfn + '.pypm'
            self.edit_model.name = model_name.value
            self.edit_model.description = model_description.value
            self.edit_model.t0 = model_t0.value
            self.edit_model.set_time_step(model_time_step.value)
            self.edit_model.save_file(mfn)
        
            with output:
                print('Success. Model saved to:')
                print(mfn)
                model_filename.value=''

        else:
            with output:
                print(' Model not saved: Missing filename.')

    model_file.on_click(model_save_to_file)
    
    open_label = widgets.Label(value='Open model to edit:')
    
    v_box1 = widgets.VBox([
        widgets.HBox([open_label, model_upload]),
        model_name,
        model_description,
        model_t0,
        model_time_step,
        model_new,
        model_filename,
        model_file
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
    par_table = widgets.Button(description='Parameter Table', tooltip='Show all parameters in a table')

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
            print(ptt.parameter_table(self.edit_model, width=110))
    
    par_table.on_click(par_table_handler)

    v_box1 = widgets.VBox([
        par_table,
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
        par_new])
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
    delay_type = widgets.Dropdown(description='Type:', options=['fast', 'norm', 'uniform', 'erlang', 'gamma'])
    
    delay_par1 = widgets.Dropdown(description='')
    delay_par2 = widgets.Dropdown(description='')

    delay_save = widgets.Button(description='Save changes', tooltip='Save changes to loaded model')
    delay_new = widgets.Button(description='New delay', tooltip='Create new delay')
    delay_table = widgets.Button(description='Delay Table', tooltip='Show all delays in a table')

    def refresh(b):
        if self.edit_model is not None:
            self.delays = self.get_model_delays()
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
        if delay.delay_type in ['norm','gamma']:
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
        if delay_type.value in ['norm','gamma']:
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
        if delay_type.value in ['norm','gamma']:
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
            print(ptt.delay_table(self.edit_model, width=110))
    delay_table.on_click(delay_table_handler)

    
    v_box1 = widgets.VBox([
        delay_table,
        refresh_button,
        delay_dropdown,
        delay_name_widget,
        delay_type,    
        delay_par1,
        delay_par2,
        widgets.HBox([delay_save,
        delay_new])
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
                                             tooltip='Report noise parameter: f = 0.-1. f is the minimum '+
                                             'fraction of cases from that day reported that day.')
    pop_report_backlog_parameter = widgets.Dropdown(description='Backlog par:', disabled=True,
                                             tooltip='Report noise backlog parameter: f = 0.-1. f is the minimum '+
                                             'fraction of backlog cases reported that day.')
    pop_report_days_parameter = widgets.Dropdown(description='Report days:', disabled=True,
                                                    tooltip='Days reported (Mon=2^0, ..., Sun=2^6) ')
    pop_save = widgets.Button(description='Save changes', tooltip='Save changes to loaded model')
    pop_new = widgets.Button(description='New population', tooltip='Create new population')
    pop_table = widgets.Button(description='Population Table', tooltip='Show all populations in a table')

    def refresh(b):
        if self.edit_model is not None:
            par_name_list = list(self.edit_model.parameters.keys()) + \
                list(self.new_parameters.keys())
            par_name_list.sort()
            pop_initial_parameter.options = par_name_list
            pop_report_noise_parameter.options = par_name_list
            pop_report_backlog_parameter.options = par_name_list
            pop_report_days_parameter.options = par_name_list

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
        report_noise_dict = pop.get_report_noise()
        pop_report_noise.value = report_noise_dict['report_noise']
        if pop_report_noise.value:
            pop_report_noise_parameter.disabled = False
            pop_report_noise_parameter.value = str(report_noise_dict['report_noise_par'])
            pop_report_backlog_parameter.disabled = False
            pop_report_backlog_parameter.value = str(report_noise_dict['report_backlog_par'])
            pop_report_days_parameter.disabled = False
            pop_report_days_parameter.value = str(report_noise_dict['report_days'])
        else:
            pop_report_noise_parameter.disabled = True
            pop_report_backlog_parameter.disabled = True
            pop_report_days_parameter.disabled = True

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
                if par_name in self.edit_model.parameters:
                    noise_par = self.edit_model.parameters[par_name]
                else:
                    noise_par = self.new_parameters[par_name]
                par_name = pop_report_backlog_parameter.value
                if par_name in self.edit_model.parameters:
                    backlog_par = self.edit_model.parameters[par_name]
                else:
                    backlog_par = self.new_parameters[par_name]
                par_name = pop_report_days_parameter.value
                if par_name in self.edit_model.parameters:
                    days_par = self.edit_model.parameters[par_name]
                else:
                    days_par = self.new_parameters[par_name]

                pop.set_report_noise(True, noise_par, backlog_par, days_par)
            else:
                pop.set_report_noise(False, None, None, None)
                
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
        report_backlog_parameter = None
        report_days_parameter = None
        if pop_report_noise.value:
            par_name = pop_report_noise_parameter.value
            if par_name in self.edit_model.parameters:
                par = self.edit_model.parameters[par_name]
            else:
                par = self.new_parameters[par_name]
            report_noise_parameter = par
            par_name = pop_report_backlog_parameter.value
            if par_name in self.edit_model.parameters:
                par = self.edit_model.parameters[par_name]
            else:
                par = self.new_parameters[par_name]
            report_backlog_parameter = par
            par_name = pop_report_days_parameter.value
            if par_name in self.edit_model.parameters:
                par = self.edit_model.parameters[par_name]
            else:
                par = self.new_parameters[par_name]
            report_days_parameter = par

        pop = Population(pop_name.value, initial_value, description='description',
                         hidden=pop_hidden.value, color=pop_color.value,
                         show_sim=pop_show_sim.value, report_noise=pop_report_noise.value,
                         report_noise_par=report_noise_parameter, report_backlog_par=report_backlog_parameter,
                         report_days_par=report_days_parameter,)
        
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
            print(ptt.population_table(self.edit_model, width=110))
    
    pop_table.on_click(pop_table_handler)

    v_box1 = widgets.VBox([
        pop_table,
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
        pop_report_backlog_parameter,
        pop_report_days_parameter,
        widgets.HBox([pop_save,
        pop_new])
        ])
    
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.VBox([widgets.HBox([v_box1, hspace, output]),table_output])


def get_transitions_tab(self):

    transitions_tab = widgets.Tab()
    injector_tab = get_injector_tab(self)
    modifier_tab = get_modifier_tab(self)

    transitions_tab.children = [injector_tab, modifier_tab]
    transitions_tab.set_title(0, 'Injector')
    transitions_tab.set_title(1, 'Modifier')

    return transitions_tab

def get_injector_tab(self):
 
    output = widgets.Output()
    table_output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    inj_dropdown = widgets.Dropdown(description='Injector:', disabled=False)
    
    inj_name_widget = widgets.Text(description='Name:')

    time_spec_dropdown = widgets.Dropdown(description='Time spec:', disabled=False,
                                             options=['rel_days','rel_steps'],
                                             tooltip='Newly infected distribution')

    trans_time_dropdown = widgets.Dropdown(description='Time par:', disabled=False,
                                           tooltip='Transition time parameter')

    inj_to_population = widgets.Dropdown(description='To pop:', disabled=False, 
                                          tooltip='Add to population')

    inj_number_dropdown = widgets.Dropdown(description='Number:', disabled=False, 
                                           tooltip='Number injected')

    inj_enabled = widgets.Checkbox(description='Enabled', disabled=False,
                                            tooltip='Set default: enabled')

    inj_new = widgets.Button(description='New injector', tooltip='Create new propagator and insert into model')
    inj_delete = widgets.Button(description='Delete', tooltip='Remove multiplier from model',
                                 button_style='warning', icon='warning')
    inj_table = widgets.Button(description='Injector Table', tooltip='Show all injectors in a table')

    def refresh(b):
        if self.edit_model is not None:
            
            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            inj_to_population.options = pop_name_list
            
            int_par_name_list = []
            float_par_name_list = []
            for par_dict in [self.edit_model.parameters,self.new_parameters]:
                for par_name in list(par_dict.keys()):
                    par = par_dict[par_name]
                    if par.parameter_type == 'int':
                        int_par_name_list.append(par_name)
                    elif par.parameter_type == 'float':
                        float_par_name_list.append(par_name)
            
            int_par_name_list.sort()
            float_par_name_list.sort()
            trans_time_dropdown.options = int_par_name_list
            inj_number_dropdown.options = float_par_name_list
            
            inj_name_list = []
            for tran_name in self.edit_model.transitions:
                tran = self.edit_model.transitions[tran_name]
                if isinstance(tran,Injector):
                    inj_name_list.append(str(tran))
            inj_dropdown.options = inj_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        inj_name = inj_dropdown.value
        inj = self.edit_model.transitions[inj_name]
        inj_name_widget.value = inj.name
        time_spec_dropdown.value = inj.time_spec
        trans_time_dropdown.value = str(inj.transition_time)
        inj_to_population.value = str(inj.to_population)
        inj_number_dropdown.value = str(inj.injection)
        inj_enabled.value = inj.enabled

        with output:
            print('Injector options loaded')

    inj_dropdown.observe(dropdown_eventhandler, names='value')

    def inj_new_handler(b):
        output.clear_output(True)

        trans_time_name = trans_time_dropdown.value
        transition_time = None
        if trans_time_name in self.edit_model.parameters:
            transition_time = self.edit_model.parameters[trans_time_name]
        else:
            transition_time = self.new_parameters[trans_time_name]       

        to_pop_name = inj_to_population.value
        to_pop = None
        if to_pop_name in self.edit_model.populations:
            to_pop = self.edit_model.populations[to_pop_name]
        else:
            to_pop = self.new_populations[to_pop_name]
            
        inj_number_name = inj_number_dropdown.value
        inj_number = None
        if inj_number_name in self.edit_model.parameters:
            inj_number = self.edit_model.parameters[inj_number_name]
        else:
            inj_number = self.new_parameters[inj_number_name]

        injector = Injector(inj_name_widget.value, time_spec_dropdown.value, 
                            transition_time, to_pop, inj_number,
                            enabled=inj_enabled.value, model=self.edit_model)

        with output:
            if injector.name in self.edit_model.transitions:
                print('Transition with this name already exists.')
                print('Please change the name and try again.')
  
            else:
                self.edit_model.add_transition(injector)
                print('New injector created.')
                print('You must save the model to disk')
                print('to make this permanent.')

    inj_new.on_click(inj_new_handler)
    
    def inj_delete_handler(b):
        output.clear_output(True)
        inj_name = inj_dropdown.value
        if inj_name_widget.value != inj_name:
            with output:
                print('You changed the name of an existing injector before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            inj = self.edit_model.transitions[inj_name]
        
            self.edit_model.remove_transition(inj)
            with output:
                print('Injector '+str(inj)+' removed from model.')
                print('You must save the model to disk')
                print('to make this permanent.')
            
    inj_delete.on_click(inj_delete_handler)
    
    def inj_table_handler(b):
        table_output.clear_output(True)
        with table_output:
            print(ptt.injector_table(self.edit_model,
                                             width=105, reveal=True))
    
    inj_table.on_click(inj_table_handler)
 
    v_box1 = widgets.VBox([
        inj_table,
        refresh_button,
        inj_dropdown, 
        inj_name_widget,
        time_spec_dropdown,
        trans_time_dropdown,
        inj_to_population,
        inj_number_dropdown,
        inj_enabled,
        widgets.HBox([inj_new, inj_delete])
        ])
        
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.VBox([widgets.HBox([v_box1, hspace, output]),table_output])

def get_modifier_tab(self):
        
    output = widgets.Output()
    table_output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    mod_dropdown = widgets.Dropdown(description='Modifier:', disabled=False)
    
    mod_name_widget = widgets.Text(description='Name:')

    time_spec_dropdown = widgets.Dropdown(description='Time spec:', disabled=False,
                                             options=['rel_days','rel_steps'],
                                             tooltip='Newly infected distribution')

    trans_time_dropdown = widgets.Dropdown(description='Time par:', disabled=False,
                                           tooltip='Transition time parameter')

    par_dropdown = widgets.Dropdown(description='Parameter:', disabled=False, 
                                    tooltip='Parameter to be modified')
    
    par_before_dropdown = widgets.Dropdown(description='Before:', disabled=False, 
                                           tooltip='Parameter value before transition')
        
    par_after_dropdown = widgets.Dropdown(description='After:', disabled=False, 
                                          tooltip='Parameter value after transition')

    mod_enabled = widgets.Checkbox(description='Enabled', disabled=False,
                                            tooltip='Set default: enabled')

    mod_new = widgets.Button(description='New modifier', tooltip='Create new modifier and add into model')
    mod_delete = widgets.Button(description='Delete', tooltip='Remove multiplier from model',
                                 button_style='warning', icon='warning')
    mod_table = widgets.Button(description='Modifier Table', tooltip='Show all modifiers in a table')

    def refresh(b):
        if self.edit_model is not None:
            
            par_name_list = list(self.edit_model.parameters.keys()) + \
                list(self.new_parameters.keys())
            par_name_list.sort()
            
            par_dropdown.options = par_name_list
            par_before_dropdown.options = par_name_list
            par_after_dropdown.options = par_name_list

            int_par_name_list = []
            for par_dict in [self.edit_model.parameters,self.new_parameters]:
                for par_name in list(par_dict.keys()):
                    par = par_dict[par_name]
                    if par.parameter_type == 'int':
                        int_par_name_list.append(par_name)            
            int_par_name_list.sort()
            trans_time_dropdown.options = int_par_name_list
            
            mod_name_list = []
            for tran_name in self.edit_model.transitions:
                tran = self.edit_model.transitions[tran_name]
                if isinstance(tran,Modifier):
                    mod_name_list.append(str(tran))
            mod_dropdown.options = mod_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        mod_name = mod_dropdown.value
        mod = self.edit_model.transitions[mod_name]
        mod_name_widget.value = mod.name
        time_spec_dropdown.value = mod.time_spec
        trans_time_dropdown.value = str(mod.transition_time)
        par_dropdown.value = str(mod.parameter)
        par_before_dropdown.value = str(mod.parameter_before)
        par_after_dropdown.value = str(mod.parameter_after)
        mod_enabled.value = mod.enabled

        with output:
            print('Modifier options loaded')

    mod_dropdown.observe(dropdown_eventhandler, names='value')

    def mod_new_handler(b):
        output.clear_output(True)

        trans_time_name = trans_time_dropdown.value
        transition_time = None
        if trans_time_name in self.edit_model.parameters:
            transition_time = self.edit_model.parameters[trans_time_name]
        else:
            transition_time = self.new_parameters[trans_time_name]       
        
        par_name = par_dropdown.value
        parameter = None
        if par_name in self.edit_model.parameters:
            parameter = self.edit_model.parameters[par_name]
        else:
            parameter = self.new_parameters[par_name]

        par_name = par_before_dropdown.value
        parameter_before = None
        if par_name in self.edit_model.parameters:
            parameter_before = self.edit_model.parameters[par_name]
        else:
            parameter_before = self.new_parameters[par_name]

        par_name = par_after_dropdown.value
        parameter_after = None
        if par_name in self.edit_model.parameters:
            parameter_after = self.edit_model.parameters[par_name]
        else:
            parameter_after = self.new_parameters[par_name]

        modifier = Modifier(mod_name_widget.value, time_spec_dropdown.value, 
                            transition_time, parameter, parameter_before,
                            parameter_after,
                            enabled=mod_enabled.value, model=self.edit_model)

        with output:
            if modifier.name in self.edit_model.transitions:
                print('Transition with this name already exists.')
                print('Please change the name and try again.')
  
            else:
                self.edit_model.add_transition(modifier)
                print('New modifier created.')
                print('You must save the model to disk')
                print('to make this permanent.')

    mod_new.on_click(mod_new_handler)
    
    def mod_delete_handler(b):
        output.clear_output(True)
        mod_name = mod_dropdown.value
        if mod_name_widget.value != mod_name:
            with output:
                print('You changed the name of an existing modifier before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            mod = self.edit_model.transitions[mod_name]
        
            self.edit_model.remove_transition(mod)
            with output:
                print('Modifier '+str(mod)+' removed from model.')
                print('You must save the model to disk')
                print('to make this permanent.')
            
    mod_delete.on_click(mod_delete_handler)
    
    def mod_table_handler(b):
        table_output.clear_output(True)
        with table_output:
            print(ptt.modifier_table(self.edit_model,
                                             width=105))
    
    mod_table.on_click(mod_table_handler)
 
    v_box1 = widgets.VBox([
        mod_table,
        refresh_button,
        mod_dropdown, 
        mod_name_widget,
        time_spec_dropdown,
        trans_time_dropdown,
        par_dropdown,
        par_before_dropdown,
        par_after_dropdown,
        mod_enabled,
        widgets.HBox([mod_new, mod_delete])
        ])
        
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.VBox([widgets.HBox([v_box1, hspace, output]),table_output])


def get_boot_tab(self):
    
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')

    boot_dropdown = widgets.Dropdown(description='Population:', disabled=False, 
                                    tooltip='Boot population')
    
    boot_start_text = widgets.Text(description='Start:', disabled=False,
                                   tooltip='Starting value for boot population')
    
    boot_excl_list_text = widgets.Textarea(description='Exclusions:', disabled=False,
                                       tootip = 'commma separated list of populations',
                                       placeholder = 'commma separated list of populations')

    boot_save = widgets.Button(description='Save settings', tooltip='Save boot settings')

    def refresh(b):
        if self.edit_model is not None:
            
            pop_name_list = list(self.edit_model.populations.keys())
            pop_name_list.sort()
            boot_dropdown.options = pop_name_list
            
            boot_dropdown.value =  self.edit_model.boot_pars['boot_population']
            boot_start_text.value = str(self.edit_model.boot_pars['boot_value'])
            
            boot_excl_list = self.edit_model.boot_pars['exclusion_populations']
            bel = []
            if isinstance(boot_excl_list,list):
                for boot_excl in boot_excl_list:
                    bel.append(boot_excl)
            else:
                bel.append(boot_excl_list)
            boot_excl_list_text.value = ','.join(bel)

    refresh_button.on_click(refresh)

    def boot_save_handler(b):
        output.clear_output(True)

        pop_exist = True
        boot_excl_list = boot_excl_list_text.value
        pop_names = boot_excl_list.split(',')
        for pop_name in pop_names:
            if pop_name not in self.edit_model.populations:
                raise ValueError('Error setting exclusion list: '+pop_name+
                                 ' not in model populations.')

        self.edit_model.boot_setup(boot_dropdown.value, boot_start_text.value, 
                                   exclusion_populations=pop_names)

        with output:
            print('Boot parameters updated')   
            print('Boot population: '+self.edit_model.boot_pars['boot_population'])
            print('Starting value: '+self.edit_model.boot_pars['boot_value'])
            print('Excluded populations:')
            boot_excl_list = self.edit_model.boot_pars['exclusion_populations']
            if isinstance(boot_excl_list,list):
                for boot_excl in boot_excl_list:
                    print(boot_excl)
            else:
                print(boot_excl_list)
            print('')
            print('You must save the model to disk')
            print('to make this permanent.')

    boot_save.on_click(boot_save_handler)
 
    v_box1 = widgets.VBox([
        refresh_button,
        boot_dropdown, 
        boot_start_text,
        boot_excl_list_text,
        boot_save
        ])
        
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])