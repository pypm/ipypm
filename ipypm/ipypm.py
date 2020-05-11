# -*- coding: utf-8 -*-
"""
Testing ipython calls from Jupyter notebook

@author: karlen
"""

#import sys
#sys.path.insert(1, '/Users/karlen/pypm/src')

import pickle

from ipypm import analyze_tab, compare_tab, explore_tab, main_tab


class ipypm:
    """ GUI for pyPM engine based on ipywidgets for use with Jupyter notebook
    """

    def __init__(self):

        self.model = None
        self.sim_model = None
        self.models_compare = {}
        self.data_description = None
        self.pd_dict = None
        self.model_folder_text_widget = None
        self.main_tab_widget = None
        self.open_tab_widget = None
        self.edit_tab_widget = None
        self.last_plot = None
        self.transitions_chooser = None
        self.region_dropdown = None
        self.region_dropdowns = []
        self.model_name = None
        self.model_description = None
        self.model_t0 = None
        self.model_time_step = None
        self.open_output = None
        self.param_dropdown = None
        self.val_text_widget = None
        self.seed_text_widget = None
        self.n_days_widget = None
        self.pop_data = None
        self.pop_dropdown = None
        self.date_range_text = None
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

    def get_display(self):
        """ Returns widget that can be displayed in a Jupyter notebook cell
        """

        main_tab.init_tab(self)

        return self.main_tab_widget

    def all_tabs(self):
        """ Updates the tab once a model has been defined (readin or created)
        """

        main_tab.all_tabs(self)
        
#    def new_model_opened(self):
        # repopulate the data analysis tabs
#        self.all_tabs()
        #explore_tab.new_model_opened(self)
        
    def new_data_opened(self):
        explore_tab.new_data_opened(self)
        compare_tab.new_data_opened(self)
        
    def new_region_opened(self):
        analyze_tab.new_region_opened(self)
        
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
    
    def open_model(self, filename, my_pickle):
        self.open_output.clear_output(True)
        self.model = pickle.loads(my_pickle)
        self.model_name.value = self.model.name
        self.model_description.value = self.model.description
        self.model_t0.value = self.model.t0
        self.model_time_step.value = self.model.get_time_step()

        self.all_tabs()
        with self.open_output:
            print('Filename: '+filename)
            print('Model loaded for data analysis. It has:')
            print(len(self.model.populations), ' Populations')
            print(len(self.model.connectors), ' Connectors')
            print(len(self.model.parameters), ' Parameters')
            print(len(self.model.transitions), ' Transitions')