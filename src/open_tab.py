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
  
    folder_text = widgets.Text(
        value='/Users/karlen/pypm/src/test',
        placeholder='Enter folder name',
        description='Folder:',
        disabled=False, continuous_update=False)
    
    file_list = os.listdir(folder_text.value)

    filename_dropdown = widgets.Dropdown(
        options=file_list,
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
        output.clear_output(True)
        output2.clear_output()
        filename = folder_text.value+'/'+filename_dropdown.value
        self.my_model = Model.open_file(filename)
        # my_list[0] = my_model
        with output:
            print('Success. Model name = ' + self.my_model.name)
        
    def save_file(b):
        output.clear_output()
        output2.clear_output(True)
        ofn = output_filename_text.value
        if '.pypm' not in ofn:
            ofn = ofn+'.pypm'
        filename = folder_text.value+'/'+ofn
        #my_model = my_list[0]
        self.my_model.name = output_model_name_text.value
        self.my_model.save_file(filename)
        #my_list[0] = my_model
        # update dropdown so that the new file is included
        file_list = os.listdir(folder_text.value)
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

    folder_text.observe(folder_eventhandler, names='value')
    open_button.on_click(open_file)

    v_box1 = widgets.VBox([folder_text, filename_dropdown, open_button, output])

    save_button.on_click(save_file)

    v_box2 = widgets.VBox([output_filename_text, output_model_name_text, save_button, output2])

    items = [v_box1, v_box2]
    grid_box = widgets.GridBox(items, layout=widgets.Layout(grid_template_columns="repeat(2, 400px)"))

    return grid_box

def get_data_folder_select(self):

    parent_folder_text = widgets.Text(
        value='/Users/karlen/pypm-data/data/covid19',
        placeholder='Enter folder name',
        description='Folder:',
        disabled=False, continuous_update=False
    )
    
    file_list = os.listdir(parent_folder_text.value)
    
    folder_dropdown = widgets.Dropdown(
        options=file_list,
        description='File:',
        disabled=False,
    )
    
    open_button = widgets.Button(
        description='  Open',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Open data folder',
        icon='folder'
    )
    
    region_select = widgets.RadioButtons(
        options=[],
        description='Region:',
        disabled=False)
    
    
    output = widgets.Output()
    output2 = widgets.Output()
    output3 = widgets.Output()
    
    def open_folder(b):
        output.clear_output(True)
        output2.clear_output(True)
        data_folder = parent_folder_text.value+'/'+folder_dropdown.value
        sys.path.insert(1, data_folder)
        import data
        self.data_description = data.get_data_description()
        self.data_description['folder'] = data_folder
        region_select.options = list(self.data_description['regional_data'].keys())
        
        with output:
            print(self.data_description['description'])
            print('Source: '+self.data_description['source'])
            print('URL: '+self.data_description['source_url'])
        with output2:
            display(region_select)
    
    def folder_eventhandler(change):
        file_list = os.listdir(change['new'])
        folder_dropdown.options = file_list
        
    def region_eventhandler(change):
        output3.clear_output(True)
        choices = []
        self.data_description['selected_region'] = region_select.value
        pops_data = self.data_description['regional_data'][region_select.value]
        for pop in pops_data:
            pop_data = pops_data[pop]
            for datatype in ['daily','total']:
                if datatype in pop_data:
                    choices.append(datatype+' '+pop)
                    
        with output3:
            ws = []
            for choice in choices:
                ws.append(widgets.Checkbox(
                    value=True,
                    description=choice,
                    disabled=False))
            display(widgets.VBox(ws))
    
    parent_folder_text.observe(folder_eventhandler, names='value')
    open_button.on_click(open_folder)
    region_select.observe(region_eventhandler, names='value')
    
    v_box1 = widgets.VBox([parent_folder_text, folder_dropdown, open_button, output])
    
    items = [v_box1, output2, output3]
    #grid_box = widgets.GridBox(items, layout=widgets.Layout(grid_template_columns="repeat(3, 320px)"))
    h_box = widgets.HBox(items)
    return h_box