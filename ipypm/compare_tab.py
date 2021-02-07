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
    m_ids = ['a', 'b']

    def delta(cumul):
        diff = []
        for i in range(1, len(cumul)):
            diff.append(cumul[i] - cumul[i - 1])
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

    def plot_total(self, model, sim_model, region, axis, y_axis_type='linear', y_max=0., scale=1.):

        start_day = (day0_widget.value - date(2020, 3, 1)).days

        region_data = None
        if region != 'None' and region != 'Simulation':
            region_data = self.data_description['regional_data'][region]

        for pop_name in model.populations:
            pop = model.populations[pop_name]
            if not pop.hidden:
                t = range(len(pop.history))
                axis.plot(t, np.array(pop.history)*scale, lw=2, label=pop_name, color=pop.color)

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
            title += ' - Simulation'
        axis.set_title(title)
        axis.legend()
        axis.set_yscale(y_axis_type)

        day_offset = (day0_widget.value - model.t0).days
        axis.set_xlim(left=day_offset, right=n_days_widget.value)
        if y_axis_type == 'log':
            axis.set_ylim(bottom=3)
        else:
            axis.set_ylim(bottom=0)
        if (y_max > 0.):
            axis.set_ylim(top=y_max)

    def plot_daily(self, model, sim_model, region, axis, y_axis_type='linear', y_max=0., scale=1.):

        start_day = (day0_widget.value - date(2020, 3, 1)).days

        region_data = None
        if region != 'None' and region != 'Simulation':
            region_data = self.data_description['regional_data'][region]

        for pop_name in model.populations:
            pop = model.populations[pop_name]
            if not pop.hidden and pop.monotonic:
                daily = delta(pop.history)
                t = range(len(daily))
                axis.step(t, np.array(daily)*scale, lw=2, label=pop_name, color=pop.color)

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
            title += ' - Simulation'
        axis.set_title(title)
        axis.legend()
        axis.set_yscale(y_axis_type)
        day_offset = (day0_widget.value - model.t0).days
        axis.set_xlim(left=day_offset, right=n_days_widget.value)
        if y_axis_type == 'log':
            axis.set_ylim(bottom=3)
        else:
            axis.set_ylim(bottom=0)
        if (y_max > 0.):
            axis.set_ylim(top=y_max)

    day0_widget = widgets.DatePicker(
        description='day_0:', value=date(2020, 3, 1), tooltip='First day to show on plots')

    n_days = (date.today() - self.model_t0.value).days
    n_days = n_days - n_days % 10 + 10

    n_days_widget = widgets.BoundedIntText(
        value=n_days, min=10, max=600, step=1, description='n_days:',
        tooltip='number of days to model: sets the upper time range of plots')

    plot_type = widgets.Dropdown(
        options=['linear total', 'log total', 'linear daily', 'log daily'],
        value='linear total', description='Plot Type:', tooltip='Type of plot to show')

    plot_scaled = widgets.Dropdown(
        options=['People', 'per 1000 people', 'per 1M people'],
        value='People', description='Plot scaling:',
        tooltip='Raw numbers or scaled?', disabled=False)

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
        if len(self.models_compare) < 2:
            with plot_output:
                print('You must first load comparison models A and B. Go to the "Open" tab.')
        else:
            for i in range(2):
                m_id = m_ids[i]
                self.models_compare[m_id].reset()
                self.models_compare[m_id].evolve_expectations(n_days_widget.value)

            with plot_output:

                if plot_compare.value == 'Side by side':

                    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
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

                        scale = 1.
                        scale_text = 'Number of People'
                        if plot_scaled.value in ['per 1000 people', 'per 1M people']:
                            if m_id in self.models_total_population:
                                if self.models_total_population[m_id] is not None:
                                    tot_pop = self.models_total_population[m_id]
                                    if tot_pop > 0:
                                        if plot_scaled.value == 'per 1000 people':
                                            scale = 1000. / tot_pop
                                        else:
                                            scale = 1000000. / tot_pop
                                        scale_text = plot_scaled.value

                        t0text = model.t0.strftime("%b %d")

                        sim_model = None
                        if region == 'Simulation':
                            sim_model = copy.deepcopy(model)
                            sim_model.reset()
                            sim_model.generate_data(n_days_widget.value)

                        if 'total' in plot_type.value:
                            plot_total(self, model, sim_model, region, axis, y_axis_type, y_max, scale)
                        else:
                            plot_daily(self, model, sim_model, region, axis, y_axis_type, y_max, scale)

                        plot_improvements(axis, t0text, scale_text)

                else:
                    pass
                    # to be implemented!

                plt.suptitle(comparison_notes.value, x=0.1, size='small', ha='left')
                self.last_plot = plt.gcf()
                plt.show()

    def plot_improvements(axis, t0text, scale_text):
        axis.set_xlabel('days since ' + t0text,
                        horizontalalignment='right', position=(1., -0.1))
        axis.set_ylabel(scale_text)

        pypm_props = dict(boxstyle='round', facecolor='blue', alpha=0.1)
        axis.text(0.01, 1.02, 'pyPM.ca', transform=axis.transAxes, fontsize=10,
                  verticalalignment='bottom', bbox=pypm_props)

    plot_button.on_click(make_plot)

    # This will generally be called before data has been read, but will
    # be populated once the datafile is read

    region_list, region_selected = get_region_list(self)
    self.region_dropdowns = [widgets.Dropdown(options=region_list, description='Region data:'),
                             widgets.Dropdown(options=region_list, description='Region data:')]

    plot_folder = widgets.Text(
        value='.',
        placeholder='relative to current folder',
        description='Folder:')

    plot_filename = widgets.Text(
        value='',
        tooltip='name',
        placeholder='filename',
        description='Filename:')

    def save_plot_file(b):
        pfn = plot_filename.value
        if len(pfn) > 0:
            # plot_filename = self.plot_folder_text_widget.value+'/'+pfn
            p_filename = pfn
            pfolder = plot_folder.value
            if pfolder not in ['', '.']:
                # plot_filename = self.plot_folder_text_widget.value+\
                #    '/'+pfolder+'/'+pfn
                p_filename = pfolder + '/' + pfn
            self.last_plot.savefig(p_filename)
            plot_filename.value = ''

    header_html = widgets.VBox([
        widgets.HTML(
            value="<h1><a href:='https://www.pypm.ca'>pyPM.ca</a></h1><p style='font-size: 26px;'>compare</p>",
            placeholder='',
            description='')])

    hspace = widgets.HTML(
        value="&nbsp;" * 24,
        placeholder='Some HTML',
        description='')

    model_blocks = [widgets.VBox([self.model_names[0], self.model_descriptions[0]]),
                    widgets.VBox([self.model_names[1], self.model_descriptions[1]])]

    header_save_hspace = widgets.HTML(
        value="&nbsp;" * 8,
        placeholder='Some HTML',
        description='')

    plot_save_button = widgets.Button(
        description='  Save plot', button_style='', tooltip='Save plot to the specified file', icon='image')

    plot_save_button.on_click(save_plot_file)

    plot_save = widgets.VBox([widgets.HBox([plot_button, plot_save_button]),
                              plot_folder, plot_filename])

    comparison_notes = widgets.Textarea(value='',
                                        tooltip='Notes on the comparison',
                                        placeholder='Notes on the comparison, to be printed on saved plot')

    header_hbox = widgets.HBox([header_html, hspace, comparison_notes, header_save_hspace,
                                plot_save])

    left_box = widgets.VBox([model_blocks[0], self.region_dropdowns[0]])
    center_box = widgets.VBox([day0_widget, n_days_widget, plot_type, plot_scaled, y_max_compare])
    right_box = widgets.VBox([model_blocks[1], self.region_dropdowns[1]])

    return AppLayout(header=header_hbox,
                     left_sidebar=left_box,
                     center=center_box,
                     right_sidebar=right_box,
                     footer=plot_output,
                     pane_widths=[2, 2, 2],
                     pane_heights=[1, 2, '470px'])
