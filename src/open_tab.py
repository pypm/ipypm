# -*- coding: utf-8 -*-
"""
Defines the open tab for reading models and data

It consists of two tabs: Model and Data

@author: karlen
"""

from __future__ import print_function
import ipywidgets as widgets

from IPython.display import display

import os
import sys
import pandas as pd

# TEMPORARY HACK - PROPER DISTRIBUTION REQUIRED
sys.path.insert(1, '/Users/karlen/pypm/src')
from Model import Model


def get_tab(self):

    open_tab = widgets.Tab()    
    model_tab = get_model_tab(self)
    data_tab = get_data_tab(self)

    open_tab.children = [model_tab, data_tab]
    open_tab.set_title(0, 'Model')
    open_tab.set_title(1, 'Data')
    
    return open_tab

def get_model_tab(self):
        
    return get_open_save_widget(self)
    
def get_data_tab(self):
    
    return get_data_folder_select(self)

def get_open_save_widget(self):
  
    self.model_folder_text_widget = widgets.Text(
        value='/Users/karlen/pypm/src/test',
        placeholder='Enter folder name',
        description='Folder:',
        disabled=False, continuous_update=False)
    
    file_list = os.listdir(self.model_folder_text_widget.value)
    pypm_list = []
    for fname in file_list:
        if '.pypm' in fname:
            pypm_list.append(fname)

    filename_dropdown = widgets.Dropdown(
        options=pypm_list,
        description='File:',
        disabled=False)

    output_filename_text = widgets.Text(
        value='',
        placeholder='Enter file name',
        description='Filename:',
        disabled=False)

    output_model_name_text = widgets.Text(
        value='',
        placeholder='Enter model name',
        description='Model name:',
        disabled=False)

    open_button = widgets.Button(
        description='  Open',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Open pypm model file: filetype is .pypm',
        icon='file')

    save_button = widgets.Button(
        description='  Save',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Save pypm model to a .pypm file',
        icon='file')

    output = widgets.Output()
    output2 = widgets.Output()

    def open_file(b):
        no_model = self.model is None
        output.clear_output(True)
        output2.clear_output()
        filename = self.model_folder_text_widget.value+'/'+filename_dropdown.value
        self.model = Model.open_file(filename)
        with output:
            print('Success. Model name = ' + self.model.name)
        # if this is first model to be read, create the other tabs
        if no_model:
            self.all_tabs()
        self.new_model_opened()
        
    def save_file(b):
        output.clear_output()
        output2.clear_output(True)
        ofn = output_filename_text.value
        if '.pypm' not in ofn:
            ofn = ofn+'.pypm'
        filename = self.model_folder_text_widget.value+'/'+ofn
        self.model.name = output_model_name_text.value
        self.model.save_file(filename)
        # update dropdown so that the new file is included
        file_list = os.listdir(self.model_folder_text_widget.value)
        pypm_list = []
        for fname in file_list:
            if '.pypm' in fname:
                pypm_list.append(fname)
        filename_dropdown.options = pypm_list
    
        with output2:
            print('Success. Model saved')
        

    def folder_eventhandler(change):
        file_list = os.listdir(change['new'])
        pypm_list = []
        for fname in file_list:
            if '.pypm' in fname:
                pypm_list.append(fname)
        filename_dropdown.options = pypm_list

    self.model_folder_text_widget.observe(folder_eventhandler, names='value')
    open_button.on_click(open_file)

    v_box1 = widgets.VBox([self.model_folder_text_widget, filename_dropdown, open_button, output])

    save_button.on_click(save_file)

    v_box2 = widgets.VBox([output_filename_text, output_model_name_text, save_button, output2])

    items = [v_box1, v_box2]
    grid_box = widgets.GridBox(items, layout=widgets.Layout(grid_template_columns="repeat(2, 400px)"))

    return grid_box

def get_data_folder_select(self):

    parent_folder_text = widgets.Text(
        value='/Users/karlen/pypm-data/data/covid19',
        placeholder='Enter folder name',
        description='Parent Folder:',
        disabled=False, continuous_update=False
    )
    
    file_list = os.listdir(parent_folder_text.value)
    
    folder_dropdown = widgets.Dropdown(
        options=file_list,
        description='Data Folder:',
        disabled=False,
    )
    
    open_button = widgets.Button(
        description='  Open',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Open data folder',
        icon='folder'
    )
            
    output = widgets.Output()
    output_region = widgets.Output()
    
    def open_folder(b):
        output.clear_output(True)
        output_region.clear_output(True)
        data_folder = parent_folder_text.value+'/'+folder_dropdown.value
        sys.path.insert(1, data_folder)
        import data
        self.data_description = data.get_data_description()
        self.data_description['folder'] = data_folder
        
        with output:
            print(self.data_description['description'])
            print('Source: '+self.data_description['source'])
            print('URL: '+self.data_description['source_url'])
        with output_region:
            for region_name in list(self.data_description['regional_data'].keys()):
                print(region_name)

        #tell the explorer that a new data file was loaded
        self.new_data_opened()
            
        #load the data into a panda dictionary
        self.pd_dict = {}
        for filename in self.data_description['files']:
            self.pd_dict[filename] = pd.read_csv(data_folder+'/'+filename)
    
    def folder_eventhandler(change):
        file_list = os.listdir(change['new'])
        folder_dropdown.options = file_list
    
    parent_folder_text.observe(folder_eventhandler, names='value')
    open_button.on_click(open_folder)
    
    v_box1 = widgets.VBox([parent_folder_text, folder_dropdown, open_button, output])
    
    items = [v_box1, output_region]
    #grid_box = widgets.GridBox(items, layout=widgets.Layout(grid_template_columns="repeat(3, 320px)"))
    h_box = widgets.HBox(items)
    return h_box