# -*- coding: utf-8 -*-
"""
This tab allows the user to explore the current model by manually adjusting parameters

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
    pars = []
    for par_name in self.model.parameters:
        par = self.model.parameters[par_name]
        if not par.hidden:
            pars.append(par_name)
    pars.sort()
    return pars

def get_transitions_lists(self):
    trans_list = []
    trans_enabled = []
    for trans_name in self.model.transitions:
        trans = self.model.transitions[trans_name]
        trans_list.append(trans_name)
        if trans.enabled:
            trans_enabled.append(trans_name)
    trans_list.sort()
    return trans_list, trans_enabled

def get_region_list(self):
    region_list = ['None', 'Simulation']
    region_selected = 'None'
    if self.data_description is not None:
        region_list += list(self.data_description['regional_data'].keys())
        if 'selected_region' in self.data_description:
            region_selected = self.data_description['selected_region']
    return region_list, region_selected

def new_data_opened(self):
    # update the region chooser
    region_list, region_selected = get_region_list(self)
    self.region_dropdown.options = region_list
    self.region_dropdown.value = region_selected
    self.region_dropdown.disabled = False

def new_model_opened(self):
    # update the text widgets to show the current model
    self.model_name.value = self.model.name
    self.model_description.value = self.model.description
    
    # update the list of transitions
    trans_list, trans_enabled = get_transitions_lists(self)
    self.transitions_chooser.options = trans_list
    self.transitions_chooser.value = trans_enabled

    # update list of parameters
    pars = get_par_list(self)
    self.param_dropdown.options = pars
    par = self.model.parameters[self.param_dropdown.value]
    self.val_text_widget.value = par.get_value()

def get_tab(self):

    def delta(cumul):
        diff = []
        for i in range(1,len(cumul)):
            diff.append(cumul[i] - cumul[i-1])
        # first daily value is repeated since val(t0-1) is unknown
        diff.insert(0, diff[0])
        return diff

    def delta_weekly(cumul):
        diff = []
        for i in range(7,len(cumul),7):
            diff.append((cumul[i] - cumul[i-7])/7.)
        return diff

    def accum_weekly(daily):
        accum = []
        for i in range(7,len(daily),7):
            sum = 0
            for j in range(i-7,i):
                sum += daily[j]
            accum.append(sum/7.)
        return accum

    def plot_total(self, axis, y_axis_type='linear', y_max=0.):

        start_day = (t0_widget.value - date(2020,3,1)).days

        region = self.region_dropdown.value        
        region_data = None
        if self.region_dropdown.value != 'None' and self.region_dropdown.value != 'Simulation':
            region_data = self.data_description['regional_data'][region]
        
        for pop_name in self.model.populations:
            pop = self.model.populations[pop_name]
            if not pop.hidden:
                t = range(len(pop.history))
                axis.plot(t[start_day:], pop.history[start_day:], lw=2, label=pop_name, color=pop.color, zorder=2)
                
                if region_data is not None:
                    if pop_name in region_data:
                        if 'total' in region_data[pop_name]:
                            filename = region_data[pop_name]['total']['filename']
                            header = region_data[pop_name]['total']['header']
                            data = self.pd_dict[filename][header].values
                            td = range(len(data))
                            axis.scatter(td[start_day:], data[start_day:], color=pop.color, zorder=1)

                if region == 'Simulation':
                    if self.sim_model is not None:
                        sim_pop = self.sim_model.populations[pop_name]
                        if hasattr(sim_pop,'show_sim') and sim_pop.show_sim:
                            st = range(len(sim_pop.history))
                            axis.scatter(st[start_day:], sim_pop.history[start_day:], color=sim_pop.color, zorder=1)

        title = 'Totals'
        if region_data is not None:
            title += ' - ' + region
        if region == 'Simulation':
            title += ' - Simulation ('+str(self.get_seed_value())+')'
        axis.set_title(title)
        axis.legend()
        axis.set_yscale(y_axis_type)
        axis.set_xlim(left=start_day, right=self.n_days_widget.value)
        if y_axis_type == 'log':
            axis.set_ylim(bottom=3)
        else:
            axis.set_ylim(bottom=0)
        if (y_max > 0.):
            axis.set_ylim(top=y_max)

    def plot_residual(self, axis, y_max=0.):

        start_day = (t0_widget.value - date(2020, 3, 1)).days

        region = self.region_dropdown.value
        region_data = None
        if self.region_dropdown.value != 'None' and self.region_dropdown.value != 'Simulation':
            region_data = self.data_description['regional_data'][region]

        for pop_name in self.model.populations:
            pop = self.model.populations[pop_name]
            if not pop.hidden:
                #t = range(len(pop.history))
                #axis.plot(t, pop.history, lw=2, label=pop_name, color=pop.color, zorder=2)

                if region_data is not None:
                    if pop_name in region_data:
                        if 'total' in region_data[pop_name]:
                            filename = region_data[pop_name]['total']['filename']
                            header = region_data[pop_name]['total']['header']
                            data = self.pd_dict[filename][header].values
                            td = range(len(data))
                            residual = [data[i]-pop.history[i] for i in td]
                            axis.scatter(td[start_day:], residual[start_day:], label=pop_name, color=pop.color, zorder=1)

                if region == 'Simulation':
                    if self.sim_model is not None:
                        sim_pop = self.sim_model.populations[pop_name]
                        if hasattr(sim_pop, 'show_sim') and sim_pop.show_sim:
                            st = range(len(sim_pop.history))
                            residual = [sim_pop.history[i] - pop.history[i] for i in st]
                            axis.scatter(st[start_day:], residual[start_day:], label=pop_name, color=sim_pop.color, zorder=1)

        title = 'Residuals: Totals'
        if region_data is not None:
            title += ' - ' + region
        if region == 'Simulation':
            title += ' - Simulation (' + str(self.get_seed_value()) + ')'
        axis.set_title(title)
        axis.legend()
        axis.set_xlim(left=0, right=self.n_days_widget.value)
        if (y_max > 0.):
            axis.set_ylim(top=y_max)
            axis.set_ylim(bottom=-y_max)
            
    def plot_daily(self, axis, y_axis_type='linear', y_max=0.):

        start_day = (t0_widget.value - date(2020, 3, 1)).days
        
        region = self.region_dropdown.value        
        region_data = None
        if self.region_dropdown.value != 'None' and self.region_dropdown.value != 'Simulation':
            region_data = self.data_description['regional_data'][region]
        
        for pop_name in self.model.populations:
            pop = self.model.populations[pop_name]
            if not pop.hidden and pop.monotonic:
                daily = delta(pop.history)
                t = range(len(daily))
                axis.step(t[start_day:], daily[start_day:], lw=2, label=pop_name, color=pop.color, zorder=2)
                
                if region_data is not None:
                    if pop_name in region_data:
                        if 'daily' in region_data[pop_name]:
                            filename = region_data[pop_name]['daily']['filename']
                            header = region_data[pop_name]['daily']['header']
                            data = self.pd_dict[filename][header].values
                            td = range(len(data))
                            axis.scatter(td[start_day:], data[start_day:], color=pop.color, s=10, zorder=1)
                            weekly_data = accum_weekly(data[start_day:])
                            tw = [start_day + 3.5 + i*7 for i in range(len(weekly_data))]
                            axis.scatter(tw, weekly_data, color=pop.color, marker='*', s=100, zorder=1)
                        else:
                            filename = region_data[pop_name]['total']['filename']
                            header = region_data[pop_name]['total']['header']
                            data = self.pd_dict[filename][header].values
                            daily_data = delta(data)
                            td = range(len(daily_data))
                            axis.scatter(td[start_day:], daily_data[start_day:], color=pop.color, s=10, zorder=1)
                            weekly_data = delta_weekly(data[start_day:])
                            tw = [start_day + 3.5 + i*7 for i in range(len(weekly_data))]
                            axis.scatter(tw, weekly_data, color=pop.color, marker='*', s=100, zorder=1)

                if region == 'Simulation':
                    if self.sim_model is not None:
                        sim_pop = self.sim_model.populations[pop_name]
                        if hasattr(sim_pop,'show_sim') and sim_pop.show_sim:
                            sim_daily = delta(sim_pop.history)
                            st = range(len(sim_daily))
                            axis.scatter(st[start_day:], sim_daily[start_day:], color=sim_pop.color, s=10, zorder=1)
                            weekly_data = delta_weekly(sim_pop.history[start_day:])
                            tw = [start_day + 3.5 + i * 7 for i in range(len(weekly_data))]
                            axis.scatter(tw, weekly_data, color=pop.color, marker='*', s=100, zorder=1)
        
        title = 'Daily'
        if region_data is not None:
            title += ' - ' + region
        if region == 'Simulation':
            title += ' - Simulation ('+str(self.get_seed_value())+')'
        axis.set_title(title)
        axis.legend()
        axis.set_yscale(y_axis_type)
        axis.set_xlim(left=start_day, right=self.n_days_widget.value)
        if y_axis_type == 'log':
            axis.set_ylim(bottom=3)
        else:
            axis.set_ylim(bottom=0)
        if (y_max > 0.):
            axis.set_ylim(top=y_max)

# the t0 information needs to be propagated correctly before enabling this widget:
    t0_widget = widgets.DatePicker(
        description='t_0:', value = date(2020,3,1), tooltip='Defines day 0 on plots', disabled=False)
 
# Look into this later:
#    time_step_widget = widgets.BoundedFloatText(
#        value=1., min=0.02, max=2.0, step=0.05, description='time_step:',
#        tooltip='length of each step in the calculation: disabled for now', disabled=True)

    plot_1 = widgets.Dropdown(
        options=['linear total', 'log total', 'residual total', 'linear daily', 'log daily'],
        value='linear total', description='Plot #1:', tooltip='Plot on left if the second plot is not None')
    
    plot_2 = widgets.Dropdown(
        options=['linear total', 'log total', 'residual total', 'linear daily', 'log daily'],
        value='log total', description='Plot #2:', tooltip='Plot on the right')
    
    y_max_1 = widgets.BoundedFloatText(
        value=0., min=0., max=1.E8, step=100., description='y_max #1:',
        tooltip='maximum of vertical axis for Plot #1. (0 -> autoscale)', disabled=False)
    
    y_max_2 = widgets.BoundedFloatText(
        value=0., min=0., max=1.E8, step=100., description='y_max #2:',
        tooltip='maximum of vertical axis for Plot #2. (0 -> autoscale)', disabled=False)
    
    output = widgets.Output()
    plot_output = widgets.Output()
    #plot_output.layout.height = '50px'
    
    plot_button = widgets.Button(
        description='  Plot', button_style='', tooltip='Run model and plot result', icon='check')
    reset_button = widgets.Button(description='  Reset', button_style='warning', 
                                  tooltip='Undo all changes to parameters since loading model', icon='warning')
    
    def make_plot(b):
        output.clear_output(True)
        plot_output.clear_output(True)

        if self.region_dropdown.value == 'Simulation':
            self.sim_model = copy.deepcopy(self.model)
            # produce a new seed if the text_widget value is zero
            seed = self.get_seed_value(new_seed = True)
            np.random.seed(seed)
            self.sim_model.reset()
            self.sim_model.generate_data(self.n_days_widget.value, data_start = data_start_widget.value)
            # since there could be new simulation data:
            self.new_region_opened()
        
        #self.model.parameters[self.param_dropdown.value].set_value(self.val_text_widget.value)
        #run model with current parameters
        before = time.process_time()
        self.model.reset()
        self.model.evolve_expectations(self.n_days_widget.value)
        after = time.process_time()
        run_time = int(round((after-before)*1000.))
        with output:
            dash = '-' * 33
            print('Run time = '+str(run_time)+' ms')
            print()
            print('Max. expectations in the period:')
            print()
            print('population              max   day')
            print(dash)
            for pop_name in self.model.populations:
                pop = self.model.populations[pop_name]
                if not pop.hidden:
                    print('{:<22s}{:>5d}{:>5d}'\
                          .format(pop_name,int(round(np.max(pop.history))),
                                  int(round(np.argmax(pop.history))))) 
        with plot_output:
    
            fig, axes = plt.subplots(1, 2, figsize=(16,7))

            axis = axes[0]
            y_axis_type = 'linear'
            if 'linear' not in plot_1.value:
                y_axis_type = 'log'
            y_max = y_max_1.value
            if 'total' in plot_1.value:
                if 'residual' in plot_1.value:
                    plot_residual(self, axis, y_max)
                else:
                    plot_total(self, axis, y_axis_type, y_max)
            else:
                plot_daily(self, axis, y_axis_type, y_max)
            plot_improvements(axis)

    
            axis = axes[1]
            y_axis_type = 'linear'
            if 'linear' not in plot_2.value:
                y_axis_type = 'log'
            y_max = y_max_2.value
            if 'total' in plot_2.value:
                if 'residual' in plot_2.value:
                    plot_residual(self, axis, y_max)
                else:
                    plot_total(self, axis, y_axis_type, y_max)
            else:
                plot_daily(self, axis, y_axis_type, y_max)
            plot_improvements(axis)
    
            self.last_plot = plt.gcf()
            plt.show()
            
    def plot_improvements(axis):
        t0text = date(2020,3,1).strftime("%b %d")
        axis.set_xlabel('days since '+t0text,
                           horizontalalignment='right', position = (1.,-0.1))
        axis.set_ylabel('Number of people')
           
        pypm_props = dict(boxstyle='round', facecolor='blue', alpha=0.1)
        axis.text(0.01, 1.02, 'pyPM.ca', transform=axis.transAxes, fontsize=10,
                     verticalalignment='bottom', bbox=pypm_props)

        start_day = (t0_widget.value - date(2020, 3, 1)).days

        # indicate times of transitions
        x_transform = transforms.blended_transform_factory(axis.transData, axis.transAxes)
        trans_list, trans_enabled = get_transitions_lists(self)
        i = 0
        n_mod = 0
        # multiple bands if multiple parameters to be changed
        prefix = 8
        tran_dict = {}
        for tran_name in trans_enabled:
            tran = self.model.transitions[tran_name]
            if hasattr(tran, 'parameter_after'):
                if tran_name[0:prefix] not in tran_dict:
                    tran_dict[tran_name[0:prefix]] = {'y_min': 0., 'y_max': 1., 'n_mod':0, 'last_mod':0}

        n_bands = len(tran_dict)
        if n_bands > 1.:
            d_band = 1./n_bands
            low = 0.
            for key in tran_dict:
                tran_dict[key]['y_min'] = low
                tran_dict[key]['y_max'] = low + d_band
                low += d_band

        for tran_name in trans_enabled:
            tran = self.model.transitions[tran_name]
            if hasattr(tran,'parameter_after'):
                # a modifier changes a parameter - use a color band to distinguish regions
                tran_dict[tran_name[0:prefix]]['n_mod'] += 1
                n_mod = tran_dict[tran_name[0:prefix]]['n_mod']
                last_mod = tran_dict[tran_name[0:prefix]]['last_mod']
                y_min = tran_dict[tran_name[0:prefix]]['y_min']
                y_max = tran_dict[tran_name[0:prefix]]['y_max']
                axis.axvspan(last_mod, tran.trigger_step, facecolor='papayawhip', 
                             edgecolor='tan', alpha=0.1*(n_mod+1), zorder=0, ymin=y_min, ymax=y_max)
                tran_dict[tran_name[0:prefix]]['last_mod'] = tran.trigger_step
            else:
                # an injector adds population - use an circle to show times (delayed by a week?)
                i+=1
                x_text = 'X'+str(i)
                x_props = dict(boxstyle='circle', facecolor='red', alpha=0.3)
                # a hack to put it in the right place (since a 1 week delay - need to get 7 from somewhere)
                delay = 7./self.model.get_time_step()
                if tran.trigger_step+delay > start_day and tran.trigger_step+delay < self.n_days_widget.value:
                    axis.text(tran.trigger_step+delay, -0.1, x_text , transform=x_transform, fontsize=10,
                              verticalalignment='top', horizontalalignment='center', bbox=x_props)
            
    def reset_parameters(b):
        output.clear_output(True)
        self.model.reset()
        for par_name in self.model.parameters:
            par = self.model.parameters[par_name]
            par.reset()
        par_down = self.param_dropdown
        if par_down.value in self.model.parameters:
            reset_value = self.model.parameters[par_down.value].get_value()
            self.val_text_widget.value = reset_value
        with output:
            print('All parameters reset')
            print('to their initial values!')
        
    plot_button.on_click(make_plot)
    reset_button.on_click(reset_parameters)
    
    pars = get_par_list(self)    
    self.param_dropdown = widgets.Dropdown(options=pars, description='Parameter:', disabled=False)
    
    par = self.model.parameters[pars[0]]
    #Bug in BoundedFloatText - regularly incorrect read back 
    #val_text = widgets.BoundedFloatText(min=par.get_min(), max=par.get_max(), value = par.get_value())
    
    #similar bug in the slide
    #val_slide = widgets.FloatSlider(min=par.get_min(), max=par.get_max(), value = par.get_value(),
    #        continuous_update=False, orientation='horizontal', readout=True, readout_format='.3f')
    self.val_text_widget = widgets.FloatText(value = par.get_value(), description='Value:', 
                                             continuous_update=False)
    #widgets.link((val_slide, 'value'), (val_text, 'value'))
    
    def dropdown_eventhandler(change):
        # update list of visible parameters in case it has changed
        pars = get_par_list(self)
        self.param_dropdown.options = pars
        par = self.model.parameters[self.param_dropdown.value]
        self.val_text_widget.value = par.get_value()
    
    def val_change_eventhandler(change):
        if self.param_dropdown.value in self.model.parameters:
            par = self.model.parameters[self.param_dropdown.value]
            if par.parameter_type == 'float':
                par.set_value(change['new'])
            else:
                par.set_value(int(change['new']))
                
            b=[]
            make_plot(b)
    
    self.param_dropdown.observe(dropdown_eventhandler, names='value')
    self.val_text_widget.observe(val_change_eventhandler, names='value')

    trans_list, trans_enabled = get_transitions_lists(self)
        
    self.transitions_chooser = widgets.SelectMultiple(
        options=trans_list, value=trans_enabled, rows=1,
        description='Transitions:')
    
    def tran_choo_eventhandler(change):    
        output.clear_output(True)
        trans_enabled = self.transitions_chooser.value
        with output:
            print('Changes made to transition status:')
            for tran_name in self.model.transitions:
                tran = self.model.transitions[tran_name]
                prev_enabled = tran.enabled
                was_enabled = ' was disabled'
                if tran.enabled:
                    was_enabled = ' was enabled'
                # set the bit in the model:
                tran.enabled = tran_name in trans_enabled
                now_enabled = 'and is now disabled.'
                if tran.enabled:
                    now_enabled = 'and is now enabled.'
                if prev_enabled != tran.enabled:
                    print(tran_name+was_enabled)
                    print(now_enabled)

    self.transitions_chooser.observe(tran_choo_eventhandler, names='value')

    def region_dropdown_eventhandler(change):    
        output.clear_output(True)
        region_selected = self.region_dropdown.value
        if self.data_description is not None:
            self.data_description['selected_region'] = region_selected
        if region_selected == 'Simulation':
            self.seed_text_widget.disabled = False
            data_start_widget.disabled = False
        else:
            self.seed_text_widget.disabled = True
            data_start_widget.disabled = True
        with output:
            print('Changed data region to: '+region_selected)
        self.new_region_opened()
                
    self.region_dropdown.observe(region_dropdown_eventhandler, names='value')
    
    self.seed_text_widget = widgets.IntText(value=0, description='Seed:',
                                            disabled=True,
                                            tooltip='To use a fixed seed for simulation, enter an integer',
                                            continuous_update=False)

    data_start_widget = widgets.IntText(value=0, description='Data start:',
                                            disabled=True,
                                            tooltip='Enter step for simulation to start',
                                            continuous_update=False)

    def save_model_file(b):
        output.clear_output(True)
        mfn = model_filename.value
        if len(mfn) > 0:
            if '.pypm' not in mfn:
                mfn = mfn + '.pypm'
            #filename = self.model_folder_text_widget.value+'/'+mfn
            filename = mfn
            mfolder = model_folder.value
            if mfolder not in ['','.']:
            #    filename = self.model_folder_text_widget.value+\
            #        '/'+mfolder+'/'+mfn
                filename = mfolder+'/'+mfn
            self.model.name = self.model_name.value
            self.model.description = self.model_description.value
            self.model.save_file(filename)
        
            with output:
                print('Success. Model saved to:')
                print(filename)
                model_filename.value=''

        else:
            with output:
                print(' Model not saved: Missing filename.')
            
    def save_plot_file(b):
        # use the same widgets for filename as model
        output.clear_output(True)
        with output:
            mfn = model_filename.value
            if len(mfn) > 0:
                #plot_filename = self.model_folder_text_widget.value+'/'+mfn
                plot_filename = mfn
                mfolder = model_folder.value
                if mfolder not in ['','.']:
                    #plot_filename = self.model_folder_text_widget.value+\
                    #    '/'+mfolder+'/'+mfn
                    plot_filename = mfolder+'/'+mfn
                self.last_plot.savefig(plot_filename)
                print('The plot was saved to:')
                print(plot_filename)
                model_filename.value = ''
            else:
                print('No filename provided.')
                print('Please try again.')                
    
    hspace = widgets.HTML(
        value="&nbsp;"*12,
        placeholder='Some HTML',
        description='')
    
    model_id = widgets.VBox([self.model_name, self.model_description])
    
    header_save_hspace = widgets.HTML(
        value="&nbsp;"*16,
        placeholder='Some HTML',
        description='')
    
    model_folder = widgets.Text(
        value='.',
        placeholder='relative to current model folder',
        description='Folder:')
    
    model_filename = widgets.Text(
        value='',
        tooltip='name',
        placeholder='filename',
        description='Filename:')
    
    model_save_button = widgets.Button(
        description='  Save model', button_style='', 
        tooltip='Save model as currently defined to the specified file', icon='file')
    
    plot_save_button = widgets.Button(
        description='  Save plot', button_style='', tooltip='Save plot to the specified file', icon='image')
    
    model_save = widgets.VBox([widgets.HBox([model_save_button, plot_save_button]),
                               model_folder, model_filename])
    
    #model_upload = widgets.FileUpload(accept='.pypm',multiple=False)
    #def model_upload_eventhandler(change):
    #    filename = list(model_upload.value.keys())[0]
    #    my_pickle = model_upload.value[filename]['content']
    #    self.open_model(filename, my_pickle)

    #model_upload.observe(model_upload_eventhandler, names='value')

    header_html = widgets.VBox([
        widgets.HTML(
            value="<h1><a href:='https://www.pypm.ca'>pyPM.ca</a></h1><p style='font-size: 26px;'>explore</p>",
            placeholder='',
            description='')])

    header_hbox = widgets.HBox([header_html, hspace, model_id, header_save_hspace,
                                model_save])
    
    model_save_button.on_click(save_model_file)
    plot_save_button.on_click(save_plot_file)
        
    left_box = widgets.VBox([t0_widget, self.n_days_widget, plot_1, plot_2, y_max_1, y_max_2])
    right_box = widgets.VBox([widgets.HBox([plot_button, reset_button]), 
                              self.param_dropdown, self.val_text_widget, self.transitions_chooser, 
                              self.region_dropdown, self.seed_text_widget, data_start_widget])
    
    return AppLayout(header=header_hbox,
              left_sidebar=left_box,
              center=output,
              right_sidebar=right_box,
              footer=plot_output,
              pane_widths=[2, 2, 2],
              pane_heights=[1, 2, '460px'])
