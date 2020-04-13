# -*- coding: utf-8 -*-
"""
Testing ipython calls from Jupyter notebook

@author: karlen
"""
from __future__ import print_function
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets

import matplotlib.pyplot as plt
import numpy as np

import sys
sys.path.insert(1, '/Users/karlen/pypm/src')
from Model import Model

import main_tab
import open_tab

class ipypm_test:
    
    def __init__(self):
        
        self.model = None
        self.data_description = None

    def test(self):
        
        my_model = Model.open_file('/Users/karlen/pypm/src/test/model.pypm')
        self.model = my_model
        
        pars = list(my_model.parameters.keys())
        pars.sort()
        
        main_t = main_tab.get_tab(self)
        
        output = widgets.Output()
        plot_output = widgets.Output()
        par_sel = widgets.Dropdown(options=pars, value=pars[0], description='Parameter:', disabled=False,)
        val_sel = widgets.FloatSlider(value=5., min=0, max=10.0, step=0.001, description='value', disabled=False,
                                      continuous_update=False, orientation='horizontal', readout=True, readout_format='.3f')
        
        def dropdown_eventhandler(change):
            val_sel.value = my_model.parameters[change['new']].get_value()
            val_sel.description = change['new']
            val_sel.min = val_sel.value/5.
            val_sel.max = val_sel.value*5.
            
        def slider_eventhandler(change):
            output.clear_output(True)
            plot_output.clear_output(True)
            my_model.reset()
            my_model.boot(True)
            if val_sel.description in pars:
                my_model.parameters[val_sel.description].set_value(change['new'])
            my_model.evolve_expectations(60)
            
            with plot_output:
                print(change['new'],my_model.parameters[val_sel.description].get_value())
                plt.plot(my_model.populations['contagious'].history)
                plt.show()
        
        par_sel.observe(dropdown_eventhandler, names='value')
        val_sel.observe(slider_eventhandler, names='value')
        
        return main_t,par_sel,val_sel,output,plot_output
    
    def open_model(self,chooser):
        self.model = Model.open_file(chooser.selected)
        chooser.default_path = chooser.selected_path
        