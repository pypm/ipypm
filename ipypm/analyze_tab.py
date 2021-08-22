# -*- coding: utf-8 -*-
"""
Analyze: get point estimates by fitting data

Use MCMC to define range of possible values for future predictions

@author: karlen
"""

from __future__ import print_function
import ipywidgets as widgets
from ipywidgets import AppLayout

import numpy as np
import matplotlib.pyplot as plt
import copy

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
                full_par_names_variable.append(prefix + par_name)
            else:
                prefix = '  '
                full_par_names_fixed.append(prefix + par_name)
    full_par_names_fixed.sort()
    full_par_names_variable.sort()

    return full_par_names_variable + full_par_names_fixed


def delta(cumul):
    diff = []
    for i in range(1, len(cumul)):
        diff.append(cumul[i] - cumul[i - 1])
    # first daily value is repeated since val(t0-1) is unknown
    diff.insert(0,diff[0])
    return diff


def get_pop_list(self):
    # full names includes total or daily
    full_pop_names = []
    self.pop_data = {}

    region = self.region_dropdown.value
    region_data = None
    if region is not None and region != 'None' and region != 'Simulation':
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
                    if hasattr(sim_pop, 'show_sim') and sim_pop.show_sim:
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
                    if hasattr(sim_pop, 'show_sim') and sim_pop.show_sim:
                        sim_daily = delta(sim_pop.history)
                        full_pop_names.append('daily ' + pop_name)
                        self.pop_data['daily ' + pop_name] = sim_daily

    return full_pop_names


def new_region_opened(self):
    # update the population chooser
    full_pop_names = get_pop_list(self)
    self.pop_dropdown.options = full_pop_names
    if 'total reported' in full_pop_names:
        self.pop_dropdown.value = 'total reported'
    self.full_pop_name = self.pop_dropdown.value
    # update list of visible parameters in case it has changed
    full_par_names = get_par_list(self)
    self.full_par_dropdown.options = full_par_names


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

        model_data = pop.history
        t = range(len(model_data))
        if self.cumul_reset:
            cumul_offset = 0
            if pop.monotonic:
                cumul_offset = pop.history[range_list[0]]
            model_data = [pop.history[i] - cumul_offset for i in range(range_list[0],range_list[1])]
            t = range(range_list[0], range_list[1])

        axis.plot(t, model_data, lw=2, label=pop_name, color=pop.color)

        td = range(range_list[0], range_list[1])
        data = []
        if self.cumul_reset:
            cumul_offset = 0
            if pop.monotonic:
                cumul_offset = self.pop_data[self.full_pop_name][range_list[0]]
            for i in td:
                data.append(self.pop_data[self.full_pop_name][i] - cumul_offset)
        else:
            for i in td:
                data.append(self.pop_data[self.full_pop_name][i])
        axis.scatter(td, data, color=pop.color)

        title = self.full_pop_name
        if region_data is not None:
            title += ' - ' + region
        if region == 'Simulation':
            title += ' - Simulation (' + str(self.seed_text_widget.value) + ')'
        axis.set_title(title)
        axis.legend()
        axis.set_yscale(y_axis_type)
        # axis.set_xlim(left=-1, right=n_days_widget.value)
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
            title += ' - Simulation (' + str(self.seed_text_widget.value) + ')'
        axis.set_title(title)
        axis.legend()
        axis.set_yscale(y_axis_type)
        # axis.set_xlim(left=-1, right=n_days_widget.value)
        if y_axis_type == 'log':
            axis.set_ylim(bottom=3)
        else:
            axis.set_ylim(bottom=0)

    def make_plot(self, range_list):
        output.clear_output(True)
        plot_output.clear_output(True)

        with plot_output:

            fig, axes = plt.subplots(1, 2, figsize=(16, 7))

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

    self.pop_dropdown = widgets.Dropdown(description='Population:', disabled=False)

    def pop_dropdown_eventhandler(change):
        # update list of visible populations in case it has changed
        full_pop_names = get_pop_list(self)
        self.pop_dropdown.options = full_pop_names
        self.full_pop_name = self.pop_dropdown.value

    self.pop_dropdown.observe(pop_dropdown_eventhandler, names='value')

    self.date_range_text = widgets.Text(value='', placeholder='range eg. 20:50',
                                        description='Fit days:', disabled=False,
                                        continuous_update=False)
    self.skip_data_text = widgets.Text(value='', placeholder='dates to skip eg. 25,45:47',
                                        description='Skip days:', disabled=False,
                                        continuous_update=False)

    self.cumul_reset_checkbox = widgets.Checkbox(value=self.cumul_reset, description='start cumulative at 0 (local)', disabled=False)
    def cumul_reset_eventhandler(change):
        self.cumul_reset = self.cumul_reset_checkbox.value
    self.cumul_reset_checkbox.observe(cumul_reset_eventhandler, names='value')

    full_par_names = get_par_list(self)
    self.full_par_dropdown = widgets.Dropdown(options=full_par_names, description='Parameter:', disabled=False)

    variable_checkbox = widgets.Checkbox(value=False, description='variable', disabled=False)
    variable_bound_text = widgets.Text(value='-inf:inf', placeholder='bounds eg. 0.:5.',
                                       description='Bounds:', disabled=True, continuous_update=False)

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
            bound_text = str(int(parameter.get_min())) + ':' + str(int(parameter.get_max()))
        return bound_text

    def variable_checkbox_eventhandler(change):
        # update the status of the model parameter - set bounds if appropriate
        fit_sims_button.disabled = True
        save_sims_button.disabled = True
        check_trans_button.disabled = True
        mod_trans_button.disabled = True
        apply_mod_trans_button.disabled = True
        output.clear_output(True)
        par_name = self.full_par_dropdown.value[2:]
        par = self.model.parameters[par_name]
        status_changed = False
        if variable_checkbox.value:
            if par.get_status() == 'fixed':
                status_changed = True
                par.set_variable(None, None)
                variable_bound_text.disabled = False
                variable_bound_text.value = get_bounds_text(par)

        else:
            variable_bound_text.disabled = True
            if par.get_status() == 'variable':
                status_changed = True
                par.set_fixed()
                with output:
                    print('Parameter ' + par_name + ' now set to fixed.')
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
            self.full_par_dropdown.value = prefix + selected[2:]

    variable_checkbox.observe(variable_checkbox_eventhandler, names='value')

    def variable_bound_text_eventhandler(change):
        output.clear_output(True)
        # update the bounds
        par_name = self.full_par_dropdown.value[2:]
        par = self.model.parameters[par_name]
        if variable_checkbox.value:

            bounds = get_bounds(par, variable_bound_text.value)
            par.set_min(bounds[0])
            par.set_max(bounds[1])

            with output:
                print('Parameter ' + par_name)
                print('Bounds for variation:' + get_bounds_text(par))
                check_bounds(par)

    variable_bound_text.observe(variable_bound_text_eventhandler, names='value')

    def check_bounds(par):
        status = True
        if par.get_status() == 'variable':
            if par.parameter_type == 'int':
                bounds = get_bounds(par, variable_bound_text.value)
                if bounds[1] - bounds[0] > 15:
                    status = False
                    print('***')
                    print('*** NOTICE *** Integer variable')
                    print('    parameter ('+par.name+')')
                    print('    will be scanned ***')
                    print('*** REDUCE RANGE OF SCAN to less ')
                    print('    than 15 ***')
        return status

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
            variable_bound_text.value = get_bounds_text(par)
        else:
            variable_checkbox.value = False
            variable_bound_text.disabled = True

    self.full_par_dropdown.observe(par_dropdown_eventhandler, names='value')

    def get_range_list():
        date_range = self.date_range_text.value
        range_list = [0, 0]
        if date_range.find(':') > 0:
            splits = date_range.split(':')
            if len(splits) == 2:
                range_list[0] = int(splits[0])
                range_list[1] = int(splits[1])
        else:
            range_list[0] = 0
            range_list[1] = len(self.pop_data[self.full_pop_name]) - 1
        return range_list

    def get_skip_dates():
        skip_data = self.skip_data_text.value
        skip_dates = []
        if skip_data is not None and skip_data != '':
            blocks = skip_data.split(',')
            for block in blocks:
                if ':' in block:
                    limits = block.split(':')
                    for i in range(int(limits[0]),int(limits[1])+1):
                        skip_dates.append(i)
                else:
                    skip_dates.append(int(block))
        return skip_dates

    def do_fit(b):
        range_list = get_range_list()
        skip_dates = get_skip_dates()
        # check if NaNs exist or if days go outside range
        nan_list = []
        range_max = range_list[1]
        last_pop_day = len(self.pop_data[self.full_pop_name])
        status = True
        if range_list[1] > last_pop_day:
            status = False
            range_max = last_pop_day
            with output:
                print('Data available up to day ',last_pop_day)
                print('Remove the extra days from range')
        for day in range(range_list[0], range_max):
            if day not in skip_dates and np.isnan(self.pop_data[self.full_pop_name][day]):
                nan_list.append(str(day))
        if len(nan_list) != 0:
            status = False
            with output:
                print('Some data is Nan. Remove from range...')
                print(','.join(nan_list))
        if status:
            # check that no long scan of integers will happen
            status = True
            for par_name in self.model.parameters:
                par = self.model.parameters[par_name]
                if not check_bounds(par):
                    status = False
                    with output:
                        print('Problem with bounds for variable:')
                        print(par.name)
            if status:
                output.clear_output(True)
                # fit the parameters:
                self.optimizer = Optimizer(self.model, self.full_pop_name, self.pop_data[self.full_pop_name], range_list,
                                           cumul_reset=self.cumul_reset, skip_data=self.skip_data_text.value)
                # The optimizer cannot scan over integer variable parameters
                # Strip those out and do a scan over them to find the
                # fit with the lowest chi^2:
                scan_dict = self.optimizer.i_fit()
                if scan_dict is not None:
                    # print result of scan:
                    with output:
                        print('Scan performed over integer')
                        print('variable:' + scan_dict['name'])
                        val_list = scan_dict['val_list']
                        chi2_list = scan_dict['chi2_list']
                        for i in range(len(val_list)):
                            print(str(val_list[i]) + ': chi2=' + str(chi2_list[i]))
                else:
                    popt, pcov = self.optimizer.fit()
                    make_plot(self, range_list)
                    # update the parameter value on the explore tab, so that when going to that page,
                    # the old parameter value won't be reloaded
                    par_name = self.param_dropdown.value
                    par = self.model.parameters[par_name]
                    self.val_text_widget.value = par.get_value()
                    # print and save fit statistics
                    self.data_fit_statistics = self.optimizer.fit_statistics
                    fit_sims_button.disabled = False
                    check_trans_button.disabled = False
                    mod_trans_button.disabled = False
                    with output:
                        if self.cumul_reset:
                            print('Local fit. Iterations start at step:',self.optimizer.start_step)
                            print(' ')

                        print('Fit results:')
                        for par_name in self.optimizer.variable_names:
                            print('  '+par_name,'= {0:0.3f}'.format(self.model.parameters[par_name].get_value()))
                        print('Fit statistics:')
                        print('  chi2_c = {0:0.1f}'.format(self.optimizer.fit_statistics['chi2_c']))
                        print('  ndof = {0:d}'.format(self.optimizer.fit_statistics['ndof']))
                        print('  chi2 = {0:0.1f}'.format(self.optimizer.fit_statistics['chi2']))
                        print('  cov = {0:0.2f}'.format(self.optimizer.fit_statistics['cov']))
                        print('  acor = {0:0.4f}'.format(self.optimizer.fit_statistics['acor']))

    def fix_all(b):
        full_par_names = get_par_list(self)
        changed_list = []
        fit_sims_button.disabled = True
        save_sims_button.disabled = True
        check_trans_button.disabled = True
        mod_trans_button.disabled = True
        for full_par_name in full_par_names:
            par_name = full_par_name[2:]
            prefix = full_par_name[:2]
            if prefix == '* ':
                par = self.model.parameters[par_name]
                par.set_fixed()
                changed_list.append(par_name)
                if par.parameter_type == 'int':
                    # return the min/max to their original values
                    prior = par.prior_parameters
                    if prior is not None:
                        if 'half_width' in prior:
                            hw = prior['half_width']
                            mean = prior['mean']
                            par.set_min(mean-hw)
                            par.set_max(mean+hw)

        if len(changed_list) > 0:
            output.clear_output(True)
            # update the dropdown list
            full_par_names = get_par_list(self)
            self.full_par_dropdown.options = full_par_names
            with output:
                print('All variable parameters set to fixed:')
                print('\n'.join(changed_list))

    fit_button = widgets.Button(
        description='  Fit & plot', button_style='', tooltip='Perform fit and plot result', icon='check')
    fix_button = widgets.Button(
        description='  Fix all', button_style='', tooltip='Change all variable parameters to fixed', icon='warning')

    fit_button.on_click(do_fit)
    fix_button.on_click(fix_all)

    n_rep_widget = widgets.IntText(value=10, description='repetitions:',
                                   continuous_update=False, disabled=False)

    def fit_sims(b):
    # Estimate the properties of the estimators, by making many several simulated samples to find the bias and covariance
    # This presumes that the variability of the data is well represented: show the autocorrelation and chi^2
    #
        n_rep = n_rep_widget.value
        self.optimizer.calc_chi2f = True
        self.optimizer.calc_chi2s = False
        self.optimizer.calc_sim_gof(n_rep)
        save_sims_button.disabled = False

        results = []
        for i_rep in range(n_rep):
            results.append(self.optimizer.opt_lists['opt'][i_rep])
        transposed = np.array(results).T
        corr = None
        if len(self.optimizer.variable_names) > 1:
            corr = np.corrcoef(transposed)

        plot_output.clear_output(True)
        with plot_output:
            print('Reporting noise parameters:')
            pop_name = self.optimizer.population_name
            pop = self.optimizer.model.populations[pop_name]
            noise_pars = pop.get_report_noise()
            buff = []
            for noise_par_name in noise_pars:
                if noise_par_name == 'report_noise':
                    buff.append('enabled =' + str(noise_pars[noise_par_name]))
                else:
                    try:
                        buff.append(str(noise_pars[noise_par_name])+'='+str(noise_pars[noise_par_name].get_value()))
                    except:
                        pass
            print('  ',', '.join(buff))
            for conn_name in self.optimizer.model.connectors:
                conn = self.optimizer.model.connectors[conn_name]
                try:
                    dist, nbp = conn.get_distribution()
                    if dist == 'nbinom':
                        print('   '+conn_name+' neg binom parameter='+str(nbp.get_value()))
                except:
                    pass

            print('Fit results from: '+str(n_rep)+' simulations')
            for i, par_name in enumerate(self.optimizer.variable_names):
                truth = self.model.parameters[par_name].get_value()
                mean = np.mean(transposed[i])
                std = np.std(transposed[i])
                err_mean = std/np.sqrt(n_rep)
                print('  '+par_name, ': truth = {0:0.4f} mean = {1:0.4f}, std = {2:0.4f}, err_mean = {3:0.4f}'.format(truth, mean, std, err_mean))
            if corr is not None:
                print('Correlation coefficients:')
                for row in corr:
                    buff = '   '
                    for value in row:
                        buff += ' {0: .3f}'.format(value)
                    print(buff)

            values = {}
            for fit_stat in self.optimizer.fit_stat_list:
                for stat in ['chi2_c', 'chi2', 'cov', 'acor']:
                    if stat not in values:
                        values[stat] = []
                    values[stat].append(fit_stat[stat])

            print('Fit statistics: Data | simulations')
            print('  chi2_c = {0:0.1f} | mean = {1:0.1f} std = {2:0.1f}, err_mean = {3:0.1f}'.format(
                self.data_fit_statistics['chi2_c'], np.mean(values['chi2_c']), np.std(values['chi2_c']),
                np.std(values['chi2_c'])/np.sqrt(n_rep)))

            print('  ndof = {0:d} | {1:d}'.format(self.data_fit_statistics['ndof'],
                                                  self.optimizer.fit_stat_list[0]['ndof']))

            fs = {'chi2':1, 'cov':2, 'acor':4}
            for stat in ['chi2', 'cov', 'acor']:
                data_val = self.data_fit_statistics[stat]
                mean = np.mean(values[stat])
                std = np.std(values[stat])
                err_mean = std / np.sqrt(n_rep)
                print('  '+stat+' = {0:0.{i}f} | mean = {1:0.{i}f} std = {2:0.{i}f}, err_mean = {3:0.{i}f}'.format(
                    data_val, mean, std, err_mean, i=fs[stat]))

    def save_sims(b):
    # Save the last standard deviations of the estimators
        results = []
        for result in self.optimizer.opt_lists['opt']:
            results.append(result)
        transposed = np.array(results).T

        output.clear_output(True)
        with output:
            print('Saved estimator standard deviations:')
            for i, par_name in enumerate(self.optimizer.variable_names):
                std = np.std(transposed[i])
                self.model.parameters[par_name].std_estimator = std
                print('  '+par_name, ': std = {0:0.4f}'.format(std))

    fit_sims_button = widgets.Button(
        description='  Fit simulations', button_style='', tooltip='Fit simulations', icon='check',
                    disabled=True)
    fit_sims_button.on_click(fit_sims)

    save_sims_button = widgets.Button(
        description='  Save est std', button_style='', tooltip='Save standard deviations of estimators',
                    disabled=True)
    save_sims_button.on_click(save_sims)

    n_day_tran_widget = widgets.IntText(value=10, description='Days back:',
                                   continuous_update=False, disabled=False)

    def mod_trans_date(b):
        # calculate changes to final transition rate if transition date is adjusted by +/- 2 days
        output.clear_output(True)

        # find last alpha transition
        last_transition = {'trans_date':0}
        for trans_name in self.model.transitions:
            if 'rate' in trans_name:
                trans = self.model.transitions[trans_name]
                if trans.enabled:
                    trans_date = trans.transition_time.get_value()
                    if trans_date > last_transition['trans_date']:
                        last_transition['trans_date'] = trans_date
                        last_transition['trans_name'] = trans_name
                        last_transition['alpha_name'] = str(trans.parameter_after)

        range_list = get_range_list()
        delta_days = [-2, +2]
        mod_alphas = []
        for delta_day in delta_days:
            model = copy.deepcopy(self.model)
            new_date = last_transition['trans_date'] + delta_day
            model.transitions[last_transition['trans_name']].transition_time.set_value(new_date)
            optimizer = Optimizer(model, self.full_pop_name, self.pop_data[self.full_pop_name], range_list,
                                  cumul_reset=self.cumul_reset, skip_data=self.skip_data_text.value)
            popt, pcov = optimizer.fit()
            mod_alpha = model.parameters[last_transition['alpha_name']].get_value()
            mod_alphas.append(mod_alpha)

        # while the following should be divided by 2, leave as is to account for larger delta_day possibility
        self.mod_alphas_std = np.abs(mod_alphas[0] - mod_alphas[1])
        self.mod_last_transition = last_transition
        apply_mod_trans_button.disabled = False

        with output:
            print('Final transition:',last_transition['trans_name'],'on day',last_transition['trans_date'])
            print('alpha values: \n  nom = {0:0.4f} +/- {1:0.4f} \n  {2:+d} days = {3:0.4f} \n  {4:+d} days = {5:0.4f}'.format(
                self.model.parameters[last_transition['alpha_name']].get_value(),
                self.model.parameters[last_transition['alpha_name']].std_estimator,
                delta_days[0], mod_alphas[0], delta_days[1], mod_alphas[1]
            ))
            print('additional error to include in final alpha: {0:0.4f}'.format(self.mod_alphas_std))

    def apply_mod_trans_date(b):
        last_transition = self.mod_last_transition
        current_std = self.model.parameters[last_transition['alpha_name']].std_estimator
        new_std = np.sqrt(current_std**2 + self.mod_alphas_std**2)
        self.model.parameters[last_transition['alpha_name']].std_estimator = new_std
        apply_mod_trans_button.disabled = True
        with output:
            print('\nAdditional error applied to',last_transition['alpha_name'],':')
            print('was: {0:0.4f}, now: {1:0.4f}'.format(current_std,new_std))

    mod_trans_button = widgets.Button(
        description='Modify trans dates', button_style='', tooltip='Evaluate error from trans date',
                    disabled=True)
    mod_trans_button.on_click(mod_trans_date)

    apply_mod_trans_button = widgets.Button(
        description='Apply additional error', button_style='', tooltip='Apply error from trans date',
                    disabled=True)
    apply_mod_trans_button.on_click(apply_mod_trans_date)

    def check_trans(b):
        # Look to see if there is evidence that a recent transition should be added
        plot_output.clear_output(True)

        n_day = n_day_tran_widget.value

        # look at fit result with n_day removed from end
        range_list = get_range_list()
        range_list_reduced = copy.copy(range_list)
        range_list_reduced[1] -= n_day

        model = copy.deepcopy(self.model)
        optimizer = Optimizer(model, self.full_pop_name, self.pop_data[self.full_pop_name], range_list_reduced,
                              cumul_reset=self.cumul_reset, skip_data=self.skip_data_text.value)
        popt, pcov = optimizer.fit()
        chi2_c_reduced = optimizer.fit_statistics['chi2_c']
        chi2_reduced = optimizer.fit_statistics['chi2']
        ndof_reduced = optimizer.fit_statistics['ndof']

        model = copy.deepcopy(self.model)
        optimizer = Optimizer(model, self.full_pop_name, self.pop_data[self.full_pop_name], range_list,
                              cumul_reset=self.cumul_reset, skip_data=self.skip_data_text.value)
        popt, pcov = optimizer.fit()
        chi2_c_full = optimizer.fit_statistics['chi2_c']
        chi2_full = optimizer.fit_statistics['chi2']
        ndof_full = optimizer.fit_statistics['ndof']

        with plot_output:
            print('Comparison of goodness of fit with/without last '+str(n_day)+' days removed:')
            print('  ndof={0:d}, chi2 (cumul) = {1:0.1f} chi2 (daily) = {2:0.1f}'.format(
                ndof_full, chi2_c_full, chi2_full))
            print('  ndof={0:d}, chi2 (cumul) = {1:0.1f} chi2 (daily) = {2:0.1f}'.format(
                ndof_reduced, chi2_c_reduced, chi2_reduced))

        # copy model and add a transition in alpha
        model_mod = copy.deepcopy(self.model)

        # look for first available alpha transition
        rate_modifier = None
        for trans_name in model_mod.transitions:
            if 'rate' in trans_name:
                trans = model_mod.transitions[trans_name]
                if not trans.enabled:
                    rate_modifier = trans
                    break
        if rate_modifier is not None:
            rate_modifier.enabled = True
            rate_time = rate_modifier.transition_time
            new_rate = rate_modifier.parameter_after

            new_rate.set_variable(None, None)
            rate_time.set_variable(None, None)
            rate_time.set_min(range_list[1]-2*n_day)
            rate_time.set_max(range_list[1]-n_day)

            optimizer_mod = Optimizer(model_mod, self.full_pop_name, self.pop_data[self.full_pop_name], range_list,
                                      cumul_reset=self.cumul_reset, skip_data=self.skip_data_text.value)
            scan_dict = optimizer_mod.i_fit()
            with plot_output:
                val_list = scan_dict['val_list']
                print('Scan performed over integer variable:' + scan_dict['name'] +' range: {0:d}:{1:d}'.format(
                    val_list[0], val_list[-1]))
                chi2_list = scan_dict['chi2_list']
                buff=[]
                for chi2 in chi2_list:
                    buff.append('{0:0.1f}'.format(chi2))
                print(','.join(buff))

                rate_time.set_fixed()
                popt, pcov = optimizer_mod.fit()
                print('Possible rate transition:')
                print('  '+rate_time.name+'='+str(rate_time.get_value()))
                print('  '+new_rate.name+'= {0:0.4f}'.format(new_rate.get_value()))

                chi2_c_full = optimizer_mod.fit_statistics['chi2_c']
                chi2_full = optimizer_mod.fit_statistics['chi2']
                ndof_full = optimizer_mod.fit_statistics['ndof']
                print('  ndof={0:d}, chi2 (cumul) = {1:0.1f} chi2 (daily) = {2:0.1f}'.format(
                    ndof_full, chi2_c_full, chi2_full))

            rate_modifier.enabled = False

        # look for first available outbreak
        model_mod = copy.deepcopy(self.model)
        injector = None
        duplicate = False
        for trans_name in model_mod.transitions:
            if 'outbreak' in trans_name:
                trans = model_mod.transitions[trans_name]
                if not trans.enabled and injector is None:
                    injector = trans
                elif trans.enabled:
                    time = trans.transition_time.get_value()
                    if time >= range_list[1] - 2 * n_day - 4:
                        duplicate = True
                        with plot_output:
                            print('An injector already exists in the time range under consideration')
                            print('  '+str(trans)+' time ='+str(time))

        if injector is not None and not duplicate:
            injector.enabled = True
            injector_time = injector.transition_time
            injector_number = injector.injection

            injector_number.set_variable(None, None)
            injector_time.set_variable(None, None)
            injector_time.set_min(range_list[1] - 2 * n_day - 4)
            injector_time.set_max(range_list[1] - n_day - 4)

            optimizer_mod = Optimizer(model_mod, self.full_pop_name, self.pop_data[self.full_pop_name],
                                      range_list, cumul_reset=self.cumul_reset, skip_data=self.skip_data_text.value)
            scan_dict = optimizer_mod.i_fit()
            with plot_output:
                val_list = scan_dict['val_list']
                print('Scan performed over integer variable:' + scan_dict['name'] +' range: {0:d}:{1:d}'.format(
                    val_list[0], val_list[-1]))
                chi2_list = scan_dict['chi2_list']
                buff=[]
                for chi2 in chi2_list:
                    buff.append('{0:0.1f}'.format(chi2))
                print(','.join(buff))

                injector_time.set_fixed()
                popt, pcov = optimizer_mod.fit()
                print('Possible outbreak:')
                print('  ' + injector_time.name + '=' + str(injector_time.get_value()))
                print('  ' + injector_number.name + '= {0:0.1f}'.format(injector_number.get_value()))

                chi2_c_full = optimizer_mod.fit_statistics['chi2_c']
                chi2_full = optimizer_mod.fit_statistics['chi2']
                ndof_full = optimizer_mod.fit_statistics['ndof']
                print('  ndof={0:d}, chi2 (cumul) = {1:0.1f} chi2 (daily) = {2:0.1f}'.format(
                    ndof_full, chi2_c_full, chi2_full))

    check_trans_button = widgets.Button(
        description='Check transitions', button_style='', tooltip='Look for evidence of transitions',
                    disabled=True)
    check_trans_button.on_click(check_trans)

    def show_vars(b):
        plot_output.clear_output(True)

        with plot_output:
            print(ptt.variable_parameter_table(self.model, width=110))

    show_vars_button = widgets.Button(
        description='  Show variables', button_style='', tooltip='Show a table of variable parameters', icon='')
    show_vars_button.on_click(show_vars)

    hspace = widgets.HTML(
        value="&nbsp;" * 24,
        placeholder='Some HTML',
        description='')

    header_html = widgets.VBox([
        widgets.HTML(
            value="<h1><a href:='https://www.pypm.ca'>pyPM.ca</a></h1><p style='font-size: 26px;'>analyze</p>",
            placeholder='',
            description='')])

    header_hbox = widgets.HBox([header_html, hspace, show_vars_button])

    left_box = widgets.VBox([self.pop_dropdown,
                             self.date_range_text,
                             self.skip_data_text,
                             self.cumul_reset_checkbox,
                             self.full_par_dropdown,
                             variable_checkbox,
                             variable_bound_text,
                             widgets.HBox([fit_button, fix_button]),
                             n_rep_widget,
                             widgets.HBox([fit_sims_button, save_sims_button]),
                             widgets.HBox([mod_trans_button, apply_mod_trans_button])
#                             n_day_tran_widget, check_trans_button
                             ])

    return AppLayout(header=header_hbox,
                     left_sidebar=left_box,
                     center=output,
                     right_sidebar=None,
                     pane_widths=[2,2,0],
                     footer=plot_output,
                     pane_heights=[1, 2, '460px'])
