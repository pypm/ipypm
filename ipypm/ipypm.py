# -*- coding: utf-8 -*-
"""
Testing ipython calls from Jupyter notebook

@author: karlen
"""

import pickle
import ipywidgets as widgets
from datetime import date
from scipy.stats import randint

from ipypm import analyze_tab, compare_tab, explore_tab, main_tab


def run_gui():
    """ simple startup"""
    return ipypm().get_display()


class ipypm:
    """ GUI for pyPM.ca engine based on ipywidgets for use with Jupyter notebook
    """

    def __init__(self):

        self.model = None
        self.sim_model = None
        self.models_compare = {}
        self.models_total_population = {}
        self.data_description = None
        self.pd_dict = None
        self.model_folder_text_widget = None
        self.main_tab_widget = None
        self.open_tab_widget = None
        self.edit_tab_widget = None
        self.last_plot = None
        self.transitions_chooser = None
        self.region_dropdowns = []
        self.param_dropdown = None
        self.val_text_widget = None
        self.seed_text_widget = None
        self.seed_value = None
        self.pop_data = None
        self.pop_dropdown = None
        self.date_range_text = None
        self.skip_data_text = None
        self.full_par_dropdown = None
        self.full_pop_name = None
        self.optimizer = None
        self.chain = None
        self.edit_model = None
        self.new_parameters = {}
        self.delays = {}
        self.new_delays = {}
        self.new_populations = {}
        self.new_propagators = {}
        self.region_model_folders = None
        self.model_filenames = None
        self.region_data_folders = None
        self.data_fit_statistics = None
        self.cumul_reset = True
        self.cumul_reset_checkbox = None
        self.mod_last_transition = None
        self.mod_alphas_std = None

        # widgets shared on more than one tab:

        self.model_name = widgets.Text(description='Name:')
        self.model_description = widgets.Textarea(description='Description:')
        self.model_t0 = widgets.DatePicker(description='t_0:', value=date(2020, 3, 1),
                                           tooltip='Defines day 0 on plots', disabled=True)
        self.model_time_step = widgets.FloatText(description='time_step:', value=1., disabled=True,
                                                 tooltip='Duration of one time step. Units: days')
        self.open_model_output = widgets.Output(layout={'width': '60%'})
        self.open_data_output = widgets.Output()
        self.region_data_output = widgets.Output(layout={'width': '60%'})
        self.region_dropdown = widgets.Dropdown(description='Region data:', options=['None', 'Simulation'])
        n_days = (date.today() - self.model_t0.value).days
        n_days = n_days - n_days % 10 + 10
        self.n_days_widget = widgets.BoundedIntText(
            value=n_days, min=10, max=700, step=1, description='n_days:',
            tooltip='number of days to model: sets the upper time range of plots')
        # Compare A and B
        self.model_names = [widgets.Text(value='', description='Model A:', disabled=True),
                            widgets.Text(value='', description='Model B:', disabled=True)]
        self.model_descriptions = [widgets.Textarea(value='', description='Description:', disabled=True),
                                   widgets.Textarea(value='', description='Description:', disabled=True)]

    def get_display(self):
        """ Returns widget that can be displayed in a Jupyter notebook cell
        """

        main_tab.init_tab(self)

        return self.main_tab_widget

    def all_tabs(self):
        """ Updates the tab once a model has been defined (read in or created)
        """

        main_tab.all_tabs(self)

    def new_data_opened(self):
        explore_tab.new_data_opened(self)
        compare_tab.new_data_opened(self)
        analyze_tab.new_region_opened(self)

    # update transition chooser etc
    def new_model_opened(self):
        explore_tab.new_model_opened(self)
        analyze_tab.new_region_opened(self)

    def new_region_opened(self):
        analyze_tab.new_region_opened(self)

    def get_model_delays(self):
        # return a dictionary of model delays indexed by delay_name
        delays = {}
        for key in self.edit_model.connectors:
            con = self.edit_model.connectors[key]
            if hasattr(con, 'delay'):
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

    def open_model(self, filename, my_pickle):
        self.open_model_output.clear_output(True)
        model = pickle.loads(my_pickle)

        time_step = model.get_time_step()
        if time_step > 1.001 or time_step < 0.999:
            with self.open_model_output:
                print('Filename: ' + filename)
                print('*** Model NOT loaded ***')
                print('Currently, ipypm only supports models with time_step = 1 day.')
            return None

        with self.open_model_output:
            print('Filename: ' + filename)
            print('Model loaded. It has:')
            print(len(model.populations), ' Populations')
            print(len(model.connectors), ' Connectors')
            print(len(model.parameters), ' Parameters')
            print(len(model.transitions), ' Transitions')

        return model

    def get_seed_value(self, new_seed = False):
        # returns value of seed specified in the text_widget
        # if that value is zero, return the seed stored in self.seed_value
        # if that value is zero, produce a new seed if new_seed is true
        value = self.seed_text_widget.value
        if value == 0:
            if new_seed:
                self.seed_value = randint.rvs(100000,999999)
            value = self.seed_value
        return value
