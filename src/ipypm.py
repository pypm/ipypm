# -*- coding: utf-8 -*-
"""
Testing ipython calls from Jupyter notebook

@author: karlen
"""

#import sys
#sys.path.insert(1, '/Users/karlen/pypm/src')

import main_tab
import explore_tab
import compare_tab

class ipypm:
    """ GUI for pyPM engine based on ipywidgets for use with Jupyter notebook
    """

    def __init__(self):

        self.model = None
        self.models_compare = {}
        self.data_description = None
        self.pd_dict = None
        self.model_folder_text_widget = None
        self.main_tab_widget = None
        self.open_tab_widget = None
        self.last_plot = None

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
