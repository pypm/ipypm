# -*- coding: utf-8 -*-
"""
Defines the open tab for reading models and data

It consists of two tabs: Model and Data

@author: karlen
"""

from __future__ import print_function
import ipywidgets as widgets

from datetime import date

import os
import sys
import pandas as pd

def get_tab(self):

    open_tab = widgets.Tab()    
    model_tab = get_model_tab(self)
    data_tab = get_data_tab(self)

    open_tab.children = [model_tab, data_tab]
    open_tab.set_title(0, 'Model')
    open_tab.set_title(1, 'Data')
    
    return open_tab

def get_model_tab(self):

    self.open_output = widgets.Output()
    model_upload = widgets.FileUpload(decription='Open model', accept='.pypm',
                                      multiple=False)

    self.model_name = widgets.Text(description='Name:')
    self.model_description = widgets.Textarea(description='Description:')
    self.model_t0 = widgets.DatePicker(description='t_0:', value = date(2020,3,1), 
                                  tooltip='Defines day 0 on plots', disabled=True)
    self.model_time_step = widgets.FloatText(description='time_step:', value = 1., disabled=True,
                                        tooltip='Duration of one time step. Units: days')

    def model_upload_eventhandler(change):
        filename = list(model_upload.value.keys())[0]
        my_pickle = model_upload.value[filename]['content']
        self.open_model(filename, my_pickle)

    model_upload.observe(model_upload_eventhandler, names='value')

    open_label = widgets.Label(value='Open model for data analysis:')
    
    v_box1 = widgets.VBox([
        widgets.HBox([open_label, model_upload]),
        self.model_name,
        self.model_description,
        self.model_t0,
        self.model_time_step
        ])

    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')
    
    return widgets.HBox([v_box1, hspace, self.open_output])  

def get_data_tab(self):
    
    return get_data_folder_select(self)

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