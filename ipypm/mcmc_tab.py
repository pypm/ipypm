# -*- coding: utf-8 -*-
"""
MCMC: Shows how undetermined parameters affect predictions

Use MCMC to define range of possible values for future predictions

@author: karlen
"""


from __future__ import print_function
import ipywidgets as widgets
from ipywidgets import AppLayout

import copy

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms

from pypmca.analysis.Optimizer import Optimizer
import pypmca.tools.table as ptt

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

def get_tab(self):
    
    output = widgets.Output()
    plot_output = widgets.Output()

    def plot_total(self, models, axis, y_axis_type='linear'):

        region = self.region_dropdown.value        
        region_data = None
        if self.region_dropdown.value != 'None' and self.region_dropdown.value != 'Simulation':
            region_data = self.data_description['regional_data'][region]
        
        for pop_name in self.model.populations:
            pop = self.model.populations[pop_name]
            if (not pop.hidden) and pop.show_sim:
                t = range(len(pop.history))
                axis.plot(t, pop.history, lw=2, label=pop_name, color=pop.color, zorder=2)

                x_ref = self.optimizer.data_range[1]
                y_ref = pop.history[x_ref]

                lower = []
                upper = []
                x_extend = range(x_ref,self.n_days_widget.value)
                for x in x_extend:
                    dy_ref = pop.history[x]-y_ref
                    values = []
                    for model in models:
                        sim_pop = model.populations[pop_name]
                        # scale the models to the same value at x_ref
                        scale = pop.history[x_ref]/sim_pop.history[x_ref]
                        values.append((sim_pop.history[x]-sim_pop.history[x_ref])*scale - dy_ref)
                    lower.append(np.percentile(values,2.5))
                    upper.append(np.percentile(values,97.5))
                    
                ref_hist = np.array(pop.history[x_ref:self.n_days_widget.value])
                lower = np.array(lower)
                upper = np.array(upper)
                #symmetrize, since calculation with auto_covariance yields asymmetric solutions
                # - but for a monotonic function there should be asymmetry!
                #dy = np.maximum(np.abs(np.array(lower)), np.abs(np.array(upper)))
                #axis.fill_between(x_extend, ref_hist-dy, ref_hist+dy, color=pop.color, zorder=0, alpha=0.3)
                axis.fill_between(x_extend, ref_hist+lower, ref_hist+upper, color=pop.color, zorder=0, alpha=0.3)

                if region_data is not None:
                    if pop_name in region_data:
                        if 'total' in region_data[pop_name]:
                            filename = region_data[pop_name]['total']['filename']
                            header = region_data[pop_name]['total']['header']
                            data = self.pd_dict[filename][header].values
                            td = range(len(data))
                            axis.scatter(td, data, color=pop.color, zorder=1)

                if region == 'Simulation':
                    if self.sim_model is not None:
                        sim_pop = self.sim_model.populations[pop_name]
                        if hasattr(sim_pop,'show_sim') and sim_pop.show_sim:
                            st = range(len(sim_pop.history))
                            axis.scatter(st, sim_pop.history, color=sim_pop.color, zorder=1)

        title = 'Totals'
        if region_data is not None:
            title += ' - ' + region
        if region == 'Simulation':
            title += ' - Simulation ('+str(self.seed_text_widget.value)+')' 
        axis.set_title(title)
        axis.legend()
        axis.set_yscale(y_axis_type)
        axis.set_xlim(left=0, right=self.n_days_widget.value)
        if y_axis_type == 'log':
            axis.set_ylim(bottom=3)
        else:
            axis.set_ylim(bottom=0)
    
    def make_plot(models):
        output.clear_output(True)
        plot_output.clear_output(True)
        
        self.model.reset()
        self.model.evolve_expectations(self.n_days_widget.value)
        
        with plot_output:
    
            fig, axes = plt.subplots(1, 2, figsize=(16,7))

            axis = axes[0]
            y_axis_type = 'linear'
            plot_total(self, models, axis, y_axis_type)

            plot_improvements(axis)

            axis = axes[1]
            y_axis_type = 'log'
            plot_total(self, models, axis, y_axis_type)

            plot_improvements(axis)
    
            self.last_plot = plt.gcf()
            plt.show()
    
    def plot_improvements(axis):

        axis.set_xlabel('days since t0',
                           horizontalalignment='right', position = (1.,-0.1))
        axis.set_ylabel('Number of people')
           
        pypm_props = dict(boxstyle='round', facecolor='blue', alpha=0.1)
        axis.text(0.01, 1.02, 'pyPM.ca', transform=axis.transAxes, fontsize=10,
                     verticalalignment='bottom', bbox=pypm_props)

    
    variable_checkbox = widgets.Checkbox(value=False, description='variable', disabled=False)
    prior_par_text = widgets.Text(value='0,1', placeholder='prior parameters eg. 0.,1.',
                                       description='Prior pars:', disabled=True, continuous_update=False)
    prior_function_dropdown = widgets.Dropdown(options=['uniform','normal'], 
                                               description='Prior:', disabled=True)
    mcmc_step_widget = widgets.FloatText(value = 0., description='mcmc step:',
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
                par.set_variable('norm', prior_dict)

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
            if par.prior_function is not None and par.prior_function == 'norm':
                prior_function_dropdown.value = 'normal'
            else:
                prior_function_dropdown.value = 'uniform'
            mcmc_step_widget.disabled = False
            if hasattr(par,'mcmc_step') and par.mcmc_step is not None:
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
    chi2n_widget = widgets.FloatText(value = 500., description='mean chi2n',
                                     continuous_update=False, disabled=False)
    n_mcmc_widget = widgets.IntText(value = 5000, description='# MCMC:', 
                                   continuous_update=False, disabled=False)
    chi2f_checkbox = widgets.Checkbox(value=False, description='calculate chi2f', disabled=False)
    
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
        n_points = self.optimizer.data_range[1] - self.optimizer.data_range[0]
        if n_rep < 2*n_points:
            with output:
                print('Not enough repititions to calculate the')
                print('autocovariance. Should be more than double the')
                print('number of data points.')
        else:
            self.optimizer.calc_auto_covariance(n_rep)
            with output:
                print('Autocovariance calculated')
                
    auto_cov_button.on_click(do_auto_cov)

    def do_sim_gof(b):
        output.clear_output(True)
        n_rep = n_rep_widget.value
        self.optimizer.calc_chi2f = chi2f_checkbox.value
        self.optimizer.calc_chi2s = True
        self.optimizer.calc_sim_gof(n_rep)
        with output:
            print('Simulated goodness of fit distribution calculated')
            print('Take note of these values:')
            print('chi2d = {0:0.1f}'.format(self.optimizer.chi2d))
            print('chi2m = {0:0.1f} sd = {1:0.1f}'.format(self.optimizer.chi2m, self.optimizer.chi2m_sd))
            print('chi2n = {0:0.1f} sd = {1:0.1f}'.format(self.optimizer.chi2n, self.optimizer.chi2n_sd))
            if chi2f_checkbox.value:
                print('chi2f = {0:0.1f} sd = {1:0.1f}'.format(self.optimizer.chi2f, self.optimizer.chi2f_sd))
            print('chi2s = {0:0.1f} sd = {1:0.1f}'.format(self.optimizer.chi2s, self.optimizer.chi2s_sd))

    sim_gof_button.on_click(do_sim_gof)

    def do_mcmc(b):
        output.clear_output(True)
        status = True
        # check that autocovariance matrix is calculated
        if self.optimizer.auto_cov is None:
            status = False
            with output:
                print('Auto covariance is needed before starting MCMC')
        # check that mcmc steps are defined. Check there are no integer variables
        for par_name in self.model.parameters:
            par = self.model.parameters[par_name]
            if par.get_status() == 'variable':
                if par.parameter_type != 'float':
                    status = False
                    with output:
                        print('Only float parameters allowed in MCMC treatment')
                        print('Remove: '+par.name)
                elif par.mcmc_step is None:
                    status = False
                    with output:
                        print('MCMC step size missing for: '+par.name)

        if status:
            n_dof = n_dof_widget.value
            n_mcmc = n_mcmc_widget.value
            chi2n = chi2n_widget.value
            self.chain = self.optimizer.mcmc(n_dof, chi2n, n_mcmc)
            with output:
                print('MCMC chain produced.')
                print('fraction accepted =',self.optimizer.accept_fraction)
    
    mcmc_button.on_click(do_mcmc)

    def do_mcmc_plot(b):
        # draw 1/10 of the chain points at random
        # to produce an ensemble of data outcomes
        n_models = int(n_mcmc_widget.value/10)
        n_days = self.n_days_widget.value
        models = []
        for i in range(n_models):
            sim_model = copy.deepcopy(self.model)
            ipnt = int(n_models*stats.uniform.rvs())
            link = self.chain[ipnt]
            for var_name in link:
                par = sim_model.parameters[var_name]
                par.set_value(link[var_name])
            sim_model.reset()
            # produce data not expectations
            sim_model.generate_data(n_days)
            models.append(sim_model)
            
        make_plot(models)    
    
    mcmc_plot_button.on_click(do_mcmc_plot)
        
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
            print(ptt.variable_parameter_table(self.model, width=110))
    
    show_vars_button = widgets.Button(
        description='  Show variables', button_style='', tooltip='Show a table of variable parameters', icon='')
    show_vars_button.on_click(show_vars)
    
    hspace = widgets.HTML(
        value="&nbsp;"*24,
        placeholder='Some HTML',
        description='')
    
    header_html = widgets.VBox([
        widgets.HTML(
            value="<h1><a href:='https://www.pypm.ca'>pyPM.ca</a></h1><p style='font-size: 26px;'>MCMC</p>",
            placeholder='',
            description='')])

    buttons = widgets.VBox([widgets.HBox([auto_cov_button, sim_gof_button]),
                            widgets.HBox([mcmc_button, mcmc_plot_button])])

    header_hbox = widgets.HBox([header_html, hspace, show_vars_button, hspace, hspace, buttons])
            
    left_box = widgets.VBox([self.full_par_dropdown, 
                             variable_checkbox,  
                             prior_function_dropdown,
                             prior_par_text,
                             mcmc_step_widget,
                             widgets.HBox([fix_button])
                             ])
    right_box = widgets.VBox([n_rep_widget,
                              chi2n_widget,
                              n_dof_widget,
                              n_mcmc_widget,
                              chi2f_checkbox
                              ])
    
    return AppLayout(header=header_hbox,
              left_sidebar=left_box,
              center=output,
              right_sidebar=right_box,
              footer=plot_output,
              pane_widths=[2, 2, 2],
              pane_heights=[1, 2, '460px'])
