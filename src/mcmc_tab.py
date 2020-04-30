# -*- coding: utf-8 -*-
"""
MCMC: Shows how undetermined parameters affect predictions

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
import tools.table

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

def get_tab(self):
    
    output = widgets.Output()
    plot_output = widgets.Output()
    
    variable_checkbox = widgets.Checkbox(value=False, description='variable', disabled=False)
    prior_par_text = widgets.Text(value='0,1', placeholder='prior parameters eg. 0.,1.',
                                       description='Prior pars:', disabled=True, continuous_update=False)
    prior_function_dropdown = widgets.Dropdown(options=['uniform','normal'], 
                                               description='Prior:', disabled=True)
    mcmc_step_widget = widgets.FloatText(value = 0, description='mcmc step:', 
                                         continuous_update=False, disabled=True)

    def get_bounds(parameter, bound_text):
        # decode the bound_text
        bounds = [parameter.get_min(), parameter.get_max()]
        if bound_text.find(':') > 0:
            bound_split = bound_text.split(':')
            if len(bound_split) == 2:
                bounds[0] = float(bound_split[0])
                bounds[1] = float(bound_split[1])
                if parameter.parameter_type == 'int':
                    bounds[0] = int(bounds[0])
                    bounds[1] = int(bounds[1])
        return bounds
    
    def get_bounds_text(parameter):
        # turn the existing bounds into bound_text
        if parameter.parameter_type == 'float':
            bound_text = "{0:0.3f}:{1:0.3f}".format(parameter.get_min(), parameter.get_max())
        elif parameter.parameter_type == 'int':
            bound_text = str(int(parameter.get_min()))+':'+str(int(parameter.get_max()))
        return bound_text
    
    def get_par_vals(parameter, par_vals_text):
        # decode the par_vals
        par_vals = [(parameter.get_min()+parameter.get_max())/2,
                    (parameter.get_max()-parameter.get_min())/2]
        if par_vals_text.find(',') > 0:
            par_vals_split = par_vals_text.split(',')
            if len(par_vals_split) == 2:
                par_vals[0] = float(par_vals_split[0])
                par_vals[1] = float(par_vals_split[1])
                if parameter.parameter_type == 'int':
                    par_vals[0] = int(par_vals[0])
                    par_vals[1] = int(par_vals[1])
        return par_vals
    
    def get_par_vals_text(parameter):
        # turn the existing par_vals into par_vals_text
        par_vals_text = ''
        if parameter.parameter_type == 'float':
            if parameter.prior_function is None or parameter.prior_function == 'uniform':
                if parameter.prior_parameters is None:
                    mean = (parameter.get_min()+parameter.get_max())/2
                    half_width = (parameter.get_max()-parameter.get_min())/2
                    par_vals_text = "{0:0.3f},{1:0.3f}".format(mean,half_width)
                else:
                    mean = parameter.prior_parameters['mean']
                    half_width = parameter.prior_parameters['half_width']
                    par_vals_text = "{0:0.3f},{1:0.3f}".format(mean,half_width)
            else:
                mean = parameter.prior_parameters['mean']
                sigma = parameter.prior_parameters['sigma']
                par_vals_text = "{0:0.3f},{1:0.3f}".format(mean,sigma)
        elif parameter.parameter_type == 'int':
            if parameter.prior_function is None:
                if parameter.prior_parameters is None:
                    mean = (parameter.get_min()+parameter.get_max())/2
                    half_width = (parameter.get_max()-parameter.get_min())/2
                    par_vals_text = str(mean)+','+str(half_width)
                else:
                    mean = parameter.prior_parameters['mean']
                    half_width = parameter.prior_parameters['half_width']
                    par_vals_text = str(mean)+','+str(half_width)
        return par_vals_text

    def variable_checkbox_eventhandler(change):
        # update the status of the model parameter - set bounds if appropriate
        output.clear_output(True)
        par_name = self.full_par_dropdown.value[2:]
        par = self.model.parameters[par_name]
        status_changed = False
        if variable_checkbox.value:
            if par.get_status() == 'fixed':
                status_changed = True
                par.set_variable(None, None)
                prior_par_text.disabled = False
                prior_par_text.value = get_par_vals_text(par)
                prior_function_dropdown.disabled = False
                if par.prior_function is None or par.prior_function == 'uniform':
                    prior_function_dropdown.value = 'uniform'
                else:
                    prior_function_dropdown.value = 'normal'
                mcmc_step_widget.disabled = False
                if par.mcmc_step is not None:
                    mcmc_step_widget.value = par.mcmc_step

        else:
            prior_par_text.disabled = True
            prior_function_dropdown.disabled = True
            mcmc_step_widget.disabled = True
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
    
    def prior_function_dropdown_eventhandler(change):
        par_name = self.full_par_dropdown.value[2:]
        par = self.model.parameters[par_name]
        prior_par_text.value = get_par_vals_text(par)

    prior_function_dropdown.observe(prior_function_dropdown_eventhandler, names='value')

    def prior_par_text_eventhandler(change):
        # update the prior values
        par_name = self.full_par_dropdown.value[2:]
        par = self.model.parameters[par_name]
        if variable_checkbox.value:
            par_vals = get_par_vals(par, prior_par_text.value)
            if prior_function_dropdown.value == 'uniform':
                prior_dict = {'mean':par_vals[0], 'half_width':par_vals[1]}
                par.set_variable('uniform', prior_dict)
            else:
                prior_dict = {'mean':par_vals[0], 'sigma':par_vals[1]}
                par.set_variable('normal', prior_dict)

    prior_par_text.observe(prior_par_text_eventhandler, names='value')
    
    def mcmc_step_change_eventhandler(change):
        par_name = self.full_par_dropdown.value[2:]
        par = self.model.parameters[par_name]
        par.mcmc_step = mcmc_step_widget.value

    mcmc_step_widget.observe(mcmc_step_change_eventhandler, names='value')

    def par_dropdown_eventhandler(change):
        # update list of visible parameters in case it has changed
        full_par_names = get_par_list(self)
        self.full_par_dropdown.options = full_par_names
        
        par_name = self.full_par_dropdown.value[2:]
        prefix = self.full_par_dropdown.value[:2]
        par = self.model.parameters[par_name]
        if prefix == '* ':
            variable_checkbox.value = True
            prior_par_text.disabled = False
            prior_par_text.value = get_par_vals_text(par)
            prior_function_dropdown.disabled = False
            if par.prior_function is not None and par.prior_function == 'normal':
                prior_function_dropdown.value = 'normal'
            else:
                prior_function_dropdown.value = 'uniform'
            mcmc_step_widget.disabled = False
            if par.mcmc_step is not None:
                mcmc_step_widget.value = par.mcmc_step
        else:
            variable_checkbox.value = False
            prior_par_text.disabled = True
            prior_function_dropdown.disabled = True
            mcmc_step_widget.disabled = True

    self.full_par_dropdown.observe(par_dropdown_eventhandler, names='value')
    
    n_rep_widget = widgets.IntText(value = 100, description='repetitions:', 
                                   continuous_update=False, disabled=False)
    n_dof_widget = widgets.IntText(value = 60, description='# dof:', 
                                   continuous_update=False, disabled=False)
    n_mcmc_widget = widgets.IntText(value = 5000, description='# MCMC:', 
                                   continuous_update=False, disabled=False) 
    
    auto_cov_button = widgets.Button(
        description='calc autocov', button_style='', 
        tooltip='Calculate the autocovariance matrix', icon='')
    sim_gof_button = widgets.Button(
        description='calc sim gof', button_style='', 
        tooltip='Calculate the goodness of fit statistic distribution for simulated samples', icon='')
    mcmc_button = widgets.Button(
        description='   Do MCMC', button_style='', 
        tooltip='Produce an MCMC chain', icon='check')
    mcmc_plot_button = widgets.Button(
        description='mcmc plot', button_style='', 
        tooltip='make a plot', icon='')
    
    def do_auto_cov(b):
        output.clear_output(True)
        n_rep = n_rep_widget.value
        self.optimizer.calc_auto_covariance(n_rep)
        with output:
            print('Autocovariance calculated')
            print('chi2m =',self.optimizer.chi2m)
                
    auto_cov_button.on_click(do_auto_cov)

    def do_sim_gof(b):
        output.clear_output(True)
        n_rep = n_rep_widget.value
        self.optimizer.calc_sim_gof(n_rep)
        with output:
            print('Simulated goodness of fit distribution calculated')
            print('chi2s =',self.optimizer.chi2s)

    sim_gof_button.on_click(do_sim_gof)

    def do_mcmc(b):
        output.clear_output(True)
        n_dof = n_dof_widget.value
        n_mcmc = n_mcmc_widget.value
        self.chain = self.optimizer.mcmc(n_dof,n_mcmc)
        with output:
            print('Simulated goodness of fit distribution calculated')
            print('fraction accepted =',self.optimizer.accept_fraction)    
    
    mcmc_button.on_click(do_mcmc)
        
    def fix_all(b):
        full_par_names = get_par_list(self)
        changed_list = []
        for full_par_name in full_par_names:
            par_name = full_par_name[2:]
            prefix = full_par_name[:2]
            if prefix == '* ':
                par = self.model.parameters[par_name]
                par.set_fixed()
                changed_list.append(par_name)
        if len(changed_list) > 0:
            output.clear_output(True)
            # update the dropdown list
            full_par_names = get_par_list(self)
            self.full_par_dropdown.options = full_par_names
            with output:
                print('All variable parameters set to fixed:')
                print('\n'.join(changed_list))

    fix_button = widgets.Button(
        description='  Fix all', button_style='', tooltip='Change all variable parameters to fixed', icon='warning')

    fix_button.on_click(fix_all)
    
    def show_vars(b):
        plot_output.clear_output(True)

        with plot_output:
            print(tools.table.variable_parameter_table(self.model, width=110))
    
    show_vars_button = widgets.Button(
        description='  Show vars', button_style='', tooltip='Show a table of variable parameters', icon='')
    show_vars_button.on_click(show_vars)
    
    hspace = widgets.HTML(
        value="&nbsp;"*24,
        placeholder='Some HTML',
        description='')
    
    header_html = widgets.VBox([
        widgets.HTML(
            value="<h1><a href:='https://www.pypm.ca'>pyPM</a></h1><p style='font-size: 26px;'>MCMC</p>",
            placeholder='',
            description='')])

    header_hbox = widgets.HBox([header_html, hspace, show_vars_button])
            
    left_box = widgets.VBox([self.full_par_dropdown, 
                             variable_checkbox,  
                             prior_function_dropdown,
                             prior_par_text,
                             mcmc_step_widget,
                             widgets.HBox([fix_button])
                             ])
    right_box = widgets.VBox([n_rep_widget,
                              n_dof_widget,
                              n_mcmc_widget,
                              widgets.HBox([auto_cov_button, sim_gof_button]),
                              widgets.HBox([mcmc_button, mcmc_plot_button])
                              ])
    
    return AppLayout(header=header_hbox,
              left_sidebar=left_box,
              center=output,
              right_sidebar=right_box,
              footer=plot_output,
              pane_widths=[2, 2, 2],
              pane_heights=[1, 2, '460px'])
