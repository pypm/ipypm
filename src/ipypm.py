# -*- coding: utf-8 -*-
"""
Testing ipython calls from Jupyter notebook

@author: karlen
"""

#import sys
#sys.path.insert(1, '/Users/karlen/pypm/src')

import main_tab
import explore_tab
import analyze_tab
import compare_tab

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
        self.last_plot = None
        self.transitions_chooser = None
        self.region_dropdown = None
        self.region_dropdowns = []
        self.model_name = None
        self.model_description = None
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

    def get_display(self):
        """ Returns widget that can be displayed in a Jupyter notebook cell
        """

        main_tab.init_tab(self)

        return self.main_tab_widget

    def all_tabs(self):
        """ Updates the tab once a model has been defined (readin or created)
        """

        main_tab.all_tabs(self)
        
    def new_model_opened(self):
        explore_tab.new_model_opened(self)
        
    def new_data_opened(self):
        explore_tab.new_data_opened(self)
        compare_tab.new_data_opened(self)
        
    def new_region_opened(self):
        analyze_tab.new_region_opened(self)
