# -*- coding: utf-8 -*-
"""
Defines the open tab for reading models and data

It consists of two tabs: Model and Data

@author: karlen
"""

from __future__ import print_function
import ipywidgets as widgets

from datetime import date

import requests
import os
import sys
import pandas as pd

def get_tab(self):

    open_tab = widgets.Tab()    
    model_tab_net = get_model_tab_net(self)
    model_tab_local = get_model_tab_local(self)
    data_tab_net = get_data_tab_net(self)
    data_tab_local = get_data_tab_local(self)

    open_tab.children = [model_tab_net, model_tab_local, data_tab_net, data_tab_local]
    open_tab.set_title(0, 'Model - network')
    open_tab.set_title(1, 'Model - local')
    open_tab.set_title(2, 'Data - network')
    open_tab.set_title(3, 'Data - local')
    
    return open_tab

def get_model_tab_net(self):

    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh region dropdown menu')
    region_dropdown = widgets.Dropdown(description='Region:', options=['None'], disabled=False)
    model_dropdown = widgets.Dropdown(description='Model:', options=['None'], disabled=False)
    download_button = widgets.Button(description='Download', optiona=['None'], tooltip='Download and load model')

    def refresh(b):
        self.open_model_output.clear_output()
        success = True
        try:
            folders_resp = requests.get('http://data.ipypm.ca:8080/list_model_folders/covid19')
        except requests.exceptions.RequestException as error:
            with self.open_model_output:
                print('Error retrieving model folders over network:')
                print()
                print(error)
            success = False
        if success:
            self.region_model_folders = folders_resp.json()
            region_list = list(self.region_model_folders.keys())
            region_list.sort()
            region_dropdown.options = ['None']+region_list
    refresh_button.on_click(refresh)

    def region_dropdown_eventhandler(change):
        self.open_model_output.clear_output()
        region = region_dropdown.value
        if region != 'None':
            folder = self.region_model_folders[region]
            success = True
            try:
                models_resp = requests.get('http://data.ipypm.ca:8080/list_models/'+folder)
            except requests.exceptions.RequestException as error:
                with self.open_model_output:
                    print('Error retrieving model list over network:')
                    print()
                    print(error)
                success = False
            if success:
                self.model_filenames = models_resp.json()
                model_list = list(self.model_filenames.keys())
                model_list.sort()
                model_dropdown.options = model_list
    region_dropdown.observe(region_dropdown_eventhandler, names='value')

    def download(b):
        self.open_model_output.clear_output()
        model = model_dropdown.value
        if model != 'None':
            model_fn = self.model_filenames[model]
            success = True
            try:
                pypm_resp = requests.get('http://data.ipypm.ca:8080/get_pypm/'+model_fn, stream=True)
            except requests.exceptions.RequestException as error:
                with self.open_model_output:
                    print('Error retrieving model over network:')
                    print()
                    print(error)
                success = False
            if success:
                my_pickle = pypm_resp.content
                filename = model_fn.split('/')[-1]
                self.open_model(filename, my_pickle)
    download_button.on_click(download)

    v_box1 = widgets.VBox([
        refresh_button,
        region_dropdown,
        model_dropdown,
        download_button,
        self.model_name,
        self.model_description,
        self.model_t0,
        self.model_time_step
        ])

    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')
    
    return widgets.HBox([v_box1, hspace, self.open_model_output])

def get_model_tab_local(self):
    model_upload = widgets.FileUpload(decription='Open model', accept='.pypm',
                                      multiple=False)

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
        value="&nbsp;" * 4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, self.open_model_output])

def get_data_tab_net(self):

    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh region dropdown menu')
    region_dropdown = widgets.Dropdown(description='Region:', options=['None'], disabled=False)
    download_button = widgets.Button(description='Download', optiona=['None'], tooltip='Download and load model')

    def refresh(b):
        self.open_data_output.clear_output()
        success = True
        try:
            folders_resp = requests.get('http://data.ipypm.ca:8080/list_data_folders/covid19')
        except requests.exceptions.RequestException as error:
            with self.open_data_output:
                print('Error retrieving data folder list over network:')
                print()
                print(error)
            success = False
        if success:
            self.region_data_folders = folders_resp.json()
            region_list = list(self.region_data_folders.keys())
            region_list.sort()
            region_dropdown.options = ['None']+region_list
    refresh_button.on_click(refresh)

    def download(b):
        self.open_data_output.clear_output()
        region = region_dropdown.value
        if region != 'None':
            data_folder = self.region_data_folders[region]
            success = True
            try:
                data_desc_resp = requests.get('http://data.ipypm.ca:8080/get_data_desc/'+data_folder)
            except requests.exceptions.RequestException as error:
                with self.open_data_output:
                    print('Error retrieving data description over network:')
                    print()
                    print(error)
                success = False
            if success:
                self.data_description = data_desc_resp.json()
                self.data_description['folder'] = data_folder

                with self.open_data_output:
                    print(self.data_description['description'])
                    print('Source: ' + self.data_description['source'])
                    print('URL: ' + self.data_description['source_url'])
                with self.region_data_output:
                    for region_name in list(self.data_description['regional_data'].keys()):
                        print(region_name)

                # tell the explorer that a new data file was loaded
                self.new_data_opened()

                # load the data into a panda dictionary
                self.pd_dict = {}
                for filename in self.data_description['files']:
                    path = data_folder + '/' + filename
                    success = True
                    try:
                        csv_resp = requests.get('http://data.ipypm.ca:8080/get_csv/'+path, stream=True)
                    except requests.exceptions.RequestException as error:
                        with self.open_data_output:
                            print('Error retrieving data over network:')
                            print()
                            print(error)
                        success = False
                    if success:
                        self.pd_dict[filename] = pd.read_csv(csv_resp.raw)

    download_button.on_click(download)

    v_box1 = widgets.VBox([refresh_button, region_dropdown, download_button, self.open_data_output])

    items = [v_box1, self.region_data_output]
    h_box = widgets.HBox(items)
    return h_box

def get_data_tab_local(self):

    parent_folder_text = widgets.Text(
        value='/',
        placeholder='Enter folder path to data area',
        description='Parent Folder:',
        disabled=False, continuous_update=False
    )

    folder_dropdown = widgets.Dropdown(
        description='Data Folder:',
        disabled=False,
    )

    def folder_text_eventhandler(change):
        folder_list = os.listdir(parent_folder_text.value)
        folder_dropdown.options = folder_list
    parent_folder_text.observe(folder_text_eventhandler, names='value')
    
    open_button = widgets.Button(
        description='  Open',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Open data folder',
        icon='folder'
    )
    
    def open_folder(b):
        self.open_data_output.clear_output(True)
        self.region_data_output.clear_output(True)
        data_folder = parent_folder_text.value+'/'+folder_dropdown.value
        sys.path.insert(1, data_folder)
        import data
        self.data_description = data.get_data_description()
        self.data_description['folder'] = data_folder
        
        with self.open_data_output:
            print(self.data_description['description'])
            print('Source: '+self.data_description['source'])
            print('URL: '+self.data_description['source_url'])
        with self.region_data_output:
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
    
    v_box1 = widgets.VBox([parent_folder_text, folder_dropdown, open_button, self.open_data_output])
    
    items = [v_box1,self.region_data_output]
    h_box = widgets.HBox(items)
    return h_box