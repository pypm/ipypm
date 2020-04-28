# -*- coding: utf-8 -*-
"""
This tab allows the user to compare two scenarios, either side by side
or overlayed.

The A and B models are loaded on this page. These are independent of the
model in the explore page.

The purpose is to make compelling figures that show the consequences of
making changes in public policy.

@author: karlen
"""

from __future__ import print_function
import ipywidgets as widgets
from ipywidgets import AppLayout

import copy
from datetime import date

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms

import pickle

def get_region_list(self):
    region_list = ['None', 'Simulation']
    region_selected = 'None'
    if self.data_description is not None:
        region_list += list(self.data_description['regional_data'].keys())
        if 'selected_region' in self.data_description:
            region_selected = self.data_description['selected_region']
    return region_list, region_selected

def new_data_opened(self):
    # update the region choosers
    region_list, region_selected = get_region_list(self)
    for region_dropdown in self.region_dropdowns:
        region_dropdown.options = region_list
        region_dropdown.value = region_selected

def get_tab(self):
    
    # keys for the two models in self.models_compare dictionary
    m_ids = ['a','b']
    
    def delta(cumul):
        diff = []
        for i in range(1,len(cumul)):
            diff.append(cumul[i] - cumul[i-1])
        return diff
    
    def plot_total(self, model, sim_model, region, axis, y_axis_type='linear', y_max=0.):
     
        region_data = None
        if region != 'None' and region != 'Simulation':
            region_data = self.data_description['regional_data'][region]
        
        for pop_name in model.populations:
            pop = model.populations[pop_name]
            if not pop.hidden:
                t = range(len(pop.history))
                axis.plot(t, pop.history, lw=2, label=pop_name, color=pop.color)
                
                if region_data is not None:
                    if pop_name in region_data:
                        if 'total' in region_data[pop_name]:
                            filename = region_data[pop_name]['total']['filename']
                            header = region_data[pop_name]['total']['header']
                            data = self.pd_dict[filename][header].values
                            td = range(len(data))
                            axis.scatter(td, data, color=pop.color)
                            
                if region == 'Simulation':
                    sim_pop = sim_model.populations[pop_name]
                    if hasattr(sim_pop,'show_sim') and sim_pop.show_sim:
                        st = range(len(sim_pop.history))
                        axis.scatter(st, sim_pop.history, color=sim_pop.color)
                            
        title = 'Totals'
        if region_data is not None:
            title += ' - ' + region
        if region == 'Simulation':
            title += ' - Simulation'
        axis.set_title(title)
        axis.legend()
        axis.set_yscale(y_axis_type)
        #axis.set_xlim(left=-1, right=n_days_widget.value)
        if y_axis_type == 'log':
            axis.set_ylim(bottom=3)
        else:
            axis.set_ylim(bottom=0)
        if (y_max > 0.):
            axis.set_ylim(top=y_max)
            
    def plot_daily(self, model, sim_model, region, axis, y_axis_type='linear', y_max=0.):
                
        region_data = None
        if region != 'None' and region != 'Simulation':
            region_data = self.data_description['regional_data'][region]
        
        for pop_name in model.populations:
            pop = model.populations[pop_name]
            if not pop.hidden and pop.monotonic:
                daily = delta(pop.history)
                t = range(len(daily))
                axis.step(t, daily, lw=2, label=pop_name, color=pop.color)
                
                if region_data is not None:
                    if pop_name in region_data:
                        if 'daily' in region_data[pop_name]:
                            filename = region_data[pop_name]['daily']['filename']
                            header = region_data[pop_name]['daily']['header']
                            data = self.pd_dict[filename][header].values
                            td = range(len(data))
                            axis.scatter(td, data, color=pop.color)

                if region == 'Simulation':
                    sim_pop = sim_model.populations[pop_name]
                    if hasattr(sim_pop,'show_sim') and sim_pop.show_sim:
                        sim_daily = delta(sim_pop.history)
                        st = range(len(sim_daily))
                        axis.scatter(st, sim_daily.history, color=sim_pop.color)

        title = 'Daily'
        if region_data is not None:
            title += ' - ' + region
        if region == 'Simulation':
            title += ' - Simulation'
        axis.set_title(title)
        axis.legend()
        axis.set_yscale(y_axis_type)
        #axis.set_xlim(left=-1, right=n_days_widget.value)
        if y_axis_type == 'log':
            axis.set_ylim(bottom=3)
        else:
            axis.set_ylim(bottom=0)
        if (y_max > 0.):
            axis.set_ylim(top=y_max)

    t0_widget = widgets.DatePicker(
        description='t_0:', value = date(2020,3,1), tooltip='Defines day 0 on plots',)
            
    n_days_widget = widgets.BoundedIntText(
        value=60, min=10, max=300, step=1, description='n_days:',
        tooltip='number of days to model: sets the upper time range of plots')
    
    plot_type = widgets.Dropdown(
        options=['linear total', 'log total', 'linear daily', 'log daily'],
        value='linear total', description='Plot Type:', tooltip='Type of plot to show')
    
    plot_scaled = widgets.Dropdown(
        options=['People', 'per 1000 pop', 'per 1M pop'],
        value='People', description='Plot scaling:', 
        tooltip='Raw numbers or scaled to population?', disabled=True)
    
    plot_compare = widgets.Dropdown(
        options=['Side by side', 'Overlay'],
        value='Side by side', description='Compare:', 
        tooltip='Select how you would like to make the comparison', disabled=True)
    
    y_max_compare = widgets.BoundedFloatText(
        value=0., min=0., max=1.E8, step=100., description='y_max:',
        tooltip='maximum of vertical axis for Plots (0 -> autoscale)')
    
    plot_output = widgets.Output()
    
    plot_button = widgets.Button(
        description='  Plot', button_style='', tooltip='Run model and plot result', icon='check')
    
    def make_plot(b):
        plot_output.clear_output(True)
        for i in range(2):
            m_id = m_ids[i]
            self.models_compare[m_id].reset()
            self.models_compare[m_id].evolve_expectations(n_days_widget.value)
            
        with plot_output:
    
            if plot_compare.value == 'Side by side':
            
                fig, axes = plt.subplots(1, 2, figsize=(16,7))
                y_axis_type = 'linear'
                if 'linear' not in plot_type.value:
                    y_axis_type = 'log'
                y_max = y_max_compare.value
                
                for i in range(2):
                    axis = axes[i]
                    m_id = m_ids[i]
                    model = self.models_compare[m_id]
                    region_dropdown = self.region_dropdowns[i]
                    region = region_dropdown.value
                    
                    sim_model = None
                    if region == 'Simulation':
                        sim_model = copy.deepcopy(self.model)
                        sim_model.reset()
                        sim_model.generate_data(n_days_widget.value)

                    if 'total' in plot_type.value:
                        plot_total(self, model, sim_model, region, axis, y_axis_type, y_max)
                    else:
                        plot_daily(self, model, sim_model, region, axis, y_axis_type, y_max)
                        
                    plot_improvements(axis)

            else:
                pass
                # to be implemented!

                
            plt.suptitle(comparison_notes.value,x=0.1,size='small',ha='left')
            self.last_plot = plt.gcf()
            plt.show()
            
    def plot_improvements(axis):
        t0text = t0_widget.value.strftime("%b %d")
        axis.set_xlabel('days since '+t0text,
                           horizontalalignment='right', position = (1.,-0.1))
        axis.set_ylabel('Number of people')
           
        pypm_props = dict(boxstyle='round', facecolor='blue', alpha=0.1)
        axis.text(0.01, 1.02, 'pyPM.ca', transform=axis.transAxes, fontsize=10,
                     verticalalignment='bottom', bbox=pypm_props)

    plot_button.on_click(make_plot)
     
    # This will generally be called before data has been read, but will
    # be populated once the datafile is read
    
    region_list, region_selected = get_region_list(self)
    self.region_dropdowns = [widgets.Dropdown(options=region_list,description='Region data:'),
                        widgets.Dropdown(options=region_list,description='Region data:')]
            
    def save_plot_file(b):
        mfn = model_filename.value
        if len(mfn) > 0:
            plot_filename = self.model_folder_text_widget.value+'/'+mfn
            mfolder = model_folder.value
            if mfolder not in ['','.']:
                plot_filename = self.model_folder_text_widget.value+\
                    '/'+mfolder+'/'+mfn
            self.last_plot.savefig(plot_filename)
            model_filename.value = ''         

    header_html = widgets.HTML(
        value="<h1><a href:='https://www.pypm.ca'>pyPM</a> compare</h1>",
        placeholder='Some HTML',
        description='')
    
    hspace = widgets.HTML(
        value="&nbsp;"*24,
        placeholder='Some HTML',
        description='')
    
    model_uploads = [widgets.FileUpload(accept='.pypm',multiple=False),
                     widgets.FileUpload(accept='.pypm',multiple=False)]
    
    model_names = [widgets.Text(value='',description='Model A:', disabled=True),
                   widgets.Text(value='',description='Model B:', disabled=True)]
    
    model_descriptions = [widgets.Textarea(value='',description='Description:', disabled=True),
                          widgets.Textarea(value='',description='Description:', disabled=True)]
    
    model_blocks = [widgets.VBox([model_uploads[0], model_names[0], model_descriptions[0]]),
                    widgets.VBox([model_uploads[1], model_names[1], model_descriptions[1]])]
    
    def model0_upload_eventhandler(change):    
        filename = list(model_uploads[0].value.keys())[0]
        my_pickle = model_uploads[0].value[filename]['content']
        self.models_compare['a'] = pickle.loads(my_pickle)
        model_names[0].value = self.models_compare['a'].name
        model_descriptions[0].value = self.models_compare['a'].description
    def model1_upload_eventhandler(change):    
        filename = list(model_uploads[1].value.keys())[0]
        my_pickle = model_uploads[1].value[filename]['content']
        self.models_compare['b'] = pickle.loads(my_pickle)
        model_names[1].value = self.models_compare['b'].name
        model_descriptions[1].value = self.models_compare['b'].description
    
    model_uploads[0].observe(model0_upload_eventhandler, names='value')
    model_uploads[1].observe(model1_upload_eventhandler, names='value')
    
    header_save_hspace = widgets.HTML(
        value="&nbsp;"*8,
        placeholder='Some HTML',
        description='')
    # these are only used for plots - keeping same name from explore tab
    model_folder = widgets.Text(
        value='.',
        placeholder='relative to current model folder',
        description='Folder:')
    
    model_filename = widgets.Text(
        value='',
        tooltip='name',
        placeholder='filename',
        description='Filename:')
    
    plot_save_button = widgets.Button(
        description='  Save plot', button_style='', tooltip='Save plot to the specified file', icon='image')
    
    plot_save_button.on_click(save_plot_file)
    
    plot_save = widgets.VBox([widgets.HBox([plot_button, plot_save_button]),
                               model_folder, model_filename])
    
    comparison_notes = widgets.Textarea(value='',
    tooltip='Notes on the comparison', placeholder='Notes on the comparison, to be printed on saved plot')
    
    header_hbox = widgets.HBox([header_html, hspace, comparison_notes,header_save_hspace,
                                plot_save])
    
    left_box = widgets.VBox([model_blocks[0], self.region_dropdowns[0]])
    center_box = widgets.VBox([t0_widget,n_days_widget, plot_type, plot_scaled, plot_compare, y_max_compare])
    right_box = widgets.VBox([model_blocks[1], self.region_dropdowns[1]])
    
    return AppLayout(header=header_hbox,
              left_sidebar=left_box,
              center=center_box,
              right_sidebar=right_box,
              footer=plot_output,
              pane_widths=[2, 2, 2],
              pane_heights=[1, 2, '470px'])
    