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
import imp
import pandas as pd


def get_tab(self,sub_tabs):
    if sub_tabs == 'model':
        open_tab = widgets.Tab()
        model_tab_net = get_model_tab_net(self)
        model_tab_local = get_model_tab_local(self)
        open_tab.children = [model_tab_net, model_tab_local]
        open_tab.set_title(0, 'Model - network')
        open_tab.set_title(1, 'Model - local')
    elif sub_tabs == 'all':
        open_tab = self.open_tab_widget
        data_tab_net = get_data_tab_net(self)
        data_tab_local = get_data_tab_local(self)
        open_tab.children = [open_tab.children[0], open_tab.children[1], data_tab_net,data_tab_local]
        open_tab.set_title(2, 'Data - network')
        open_tab.set_title(3, 'Data - local')

    return open_tab


def get_total_population(model):
    # Assume the pop at t=0 with the most members is the total population
    max_pop = 0.
    for pop_name in model.populations:
        pop = model.populations[pop_name]
        if pop.history is not None and len(pop.history) > 0:
            start_pop = pop.history[0]
            if start_pop > max_pop:
                max_pop = start_pop
    return max_pop


def get_model_tab_net(self):
    refresh_button = widgets.Button(description='Refresh Regions', tooltip='Refresh region dropdown menu')
    region_dropdown = widgets.Dropdown(description='Region:', options=['None'], disabled=False)
    model_dropdown = widgets.Dropdown(description='Model:', options=['None'], disabled=False)
    download_button = widgets.Button(description='Download', tooltip='Load model for explore/analysis')

    def refresh(b):
        self.open_model_output.clear_output()
        success = True
        try:
            folders_resp = requests.get('http://data.ipypm.ca/list_model_folders/covid19')
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
            region_dropdown.options = ['None'] + region_list

    refresh_button.on_click(refresh)

    def region_dropdown_eventhandler(change):
        self.open_model_output.clear_output()
        region = region_dropdown.value
        if region != 'None':
            folder = self.region_model_folders[region]
            success = True
            try:
                models_resp = requests.get('http://data.ipypm.ca/list_models/' + folder)
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
                pypm_resp = requests.get('http://data.ipypm.ca/get_pypm/' + model_fn, stream=True)
            except requests.exceptions.RequestException as error:
                with self.open_model_output:
                    print('Error retrieving model over network:')
                    print()
                    print(error)
                success = False
            if success:
                my_pickle = pypm_resp.content
                filename = model_fn.split('/')[-1]
                model = self.open_model(filename, my_pickle)
                if model is not None:
                    self.model = model
                    self.model_name.value = self.model.name
                    self.model_description.value = self.model.description
                    self.model_t0.value = self.model.t0
                    self.model_time_step.value = self.model.get_time_step()
                    self.all_tabs()

    download_button.on_click(download)
    download_label = widgets.Label(value='Open model for analysis:')

    v_box_1 = widgets.VBox([
        refresh_button,
        region_dropdown,
        model_dropdown,
        widgets.HBox([download_label, download_button]),
        self.model_name,
        self.model_description
    ])

    # Compare A and B model loaded here:

    download_buttons = [widgets.Button(description='Download - A', tooltip='Load model for Compare A'),
                        widgets.Button(description='Download - B', tooltip='Load model for Compare B')]

    def download_0(b):
        self.open_model_output.clear_output()
        model = model_dropdown.value
        if model != 'None':
            model_fn = self.model_filenames[model]
            success = True
            try:
                pypm_resp = requests.get('http://data.ipypm.ca/get_pypm/' + model_fn, stream=True)
            except requests.exceptions.RequestException as error:
                with self.open_model_output:
                    print('Error retrieving model over network:')
                    print()
                    print(error)
                success = False
            if success:
                my_pickle = pypm_resp.content
                filename = model_fn.split('/')[-1]
                model = self.open_model(filename, my_pickle)
                if model is not None:
                    self.models_compare['a'] = model
                    self.model_names[0].value = self.models_compare['a'].name
                    self.model_descriptions[0].value = self.models_compare['a'].description
                    self.models_total_population['a'] = get_total_population(self.models_compare['a'])

    def download_1(b):
        self.open_model_output.clear_output()
        model = model_dropdown.value
        if model != 'None':
            model_fn = self.model_filenames[model]
            success = True
            try:
                pypm_resp = requests.get('http://data.ipypm.ca/get_pypm/' + model_fn, stream=True)
            except requests.exceptions.RequestException as error:
                with self.open_model_output:
                    print('Error retrieving model over network:')
                    print()
                    print(error)
                success = False
            if success:
                my_pickle = pypm_resp.content
                filename = model_fn.split('/')[-1]
                model = self.open_model(filename, my_pickle)
                if model is not None:
                    self.models_compare['b'] = model
                    self.model_names[1].value = self.models_compare['b'].name
                    self.model_descriptions[1].value = self.models_compare['b'].description
                    self.models_total_population['b'] = get_total_population(self.models_compare['b'])

    download_buttons[0].on_click(download_0)
    download_buttons[1].on_click(download_1)

    download_label_A = widgets.Label(value='Open model for compare A:')
    download_label_B = widgets.Label(value='Open model for compare B:')

    v_box_A = widgets.VBox([
        widgets.HBox([download_label_A, download_buttons[0]]),
        self.model_names[0],
        self.model_descriptions[0]
    ])

    v_box_B = widgets.VBox([
        widgets.HBox([download_label_B, download_buttons[1]]),
        self.model_names[1],
        self.model_descriptions[1]
    ])

    hspace = widgets.HTML(
        value="&nbsp;" * 4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([widgets.VBox([v_box_1, v_box_A, v_box_B]), hspace, self.open_model_output])


def get_model_tab_local(self):
    model_upload = widgets.FileUpload(decription='Open model', accept='.pypm',
                                      multiple=False)

    def model_upload_eventhandler(change):
        filename = list(model_upload.value.keys())[0]
        my_pickle = model_upload.value[filename]['content']
        model = self.open_model(filename, my_pickle)
        if model is not None:
            self.model = model
            self.model_name.value = self.model.name
            self.model_description.value = self.model.description
            self.model_t0.value = self.model.t0
            self.model_time_step.value = self.model.get_time_step()
            self.all_tabs()

    model_upload.observe(model_upload_eventhandler, names='value')

    open_label = widgets.Label(value='Open model for analysis:')

    v_box_1 = widgets.VBox([
        widgets.HBox([open_label, model_upload]),
        self.model_name,
        self.model_description
    ])

    # Compare A and B model loaded here:

    model_uploads = [widgets.FileUpload(accept='.pypm', multiple=False),
                     widgets.FileUpload(accept='.pypm', multiple=False)]

    def model0_upload_eventhandler(change):
        filename = list(model_uploads[0].value.keys())[0]
        my_pickle = model_uploads[0].value[filename]['content']
        model = self.open_model(filename, my_pickle)
        if model is not None:
            self.models_compare['a'] = model
            self.model_names[0].value = self.models_compare['a'].name
            self.model_descriptions[0].value = self.models_compare['a'].description
            self.models_total_population['a'] = get_total_population(self.models_compare['a'])

    def model1_upload_eventhandler(change):
        filename = list(model_uploads[1].value.keys())[0]
        my_pickle = model_uploads[1].value[filename]['content']
        model = self.open_model(filename, my_pickle)
        if model is not None:
            self.models_compare['b'] = model
            self.model_names[1].value = self.models_compare['b'].name
            self.model_descriptions[1].value = self.models_compare['b'].description
            self.models_total_population['b'] = get_total_population(self.models_compare['b'])

    model_uploads[0].observe(model0_upload_eventhandler, names='value')
    model_uploads[1].observe(model1_upload_eventhandler, names='value')

    open_label_A = widgets.Label(value='Open model for compare A:')
    open_label_B = widgets.Label(value='Open model for compare B:')

    v_box_A = widgets.VBox([
        widgets.HBox([open_label_A, model_uploads[0]]),
        self.model_names[0],
        self.model_descriptions[0]
    ])

    v_box_B = widgets.VBox([
        widgets.HBox([open_label_B, model_uploads[1]]),
        self.model_names[1],
        self.model_descriptions[1]
    ])

    hspace = widgets.HTML(
        value="&nbsp;" * 4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([widgets.VBox([v_box_1, v_box_A, v_box_B]), hspace, self.open_model_output])


def get_data_tab_net(self):
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh region dropdown menu')
    region_dropdown = widgets.Dropdown(description='Region:', options=['None'], disabled=False)
    download_button = widgets.Button(description='Download', optiona=['None'], tooltip='Download and load model')

    def refresh(b):
        self.open_data_output.clear_output()
        success = True
        try:
            folders_resp = requests.get('http://data.ipypm.ca/list_data_folders/covid19')
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
            region_dropdown.options = ['None'] + region_list

    refresh_button.on_click(refresh)

    def download(b):
        self.open_data_output.clear_output()
        self.region_data_output.clear_output()
        region = region_dropdown.value
        if region != 'None':
            data_folder = self.region_data_folders[region]
            success = True
            try:
                data_desc_resp = requests.get('http://data.ipypm.ca/get_data_desc/' + data_folder)
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
                        csv_resp = requests.get('http://data.ipypm.ca/get_csv/' + path, stream=True)
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
        button_style='',  # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Open data folder',
        icon='folder'
    )

    def open_folder(b):
        self.open_data_output.clear_output(True)
        self.region_data_output.clear_output(True)
        data_folder = parent_folder_text.value + '/' + folder_dropdown.value
        data_py = data_folder + '/data.py'
        module = imp.load_source('module_name', data_py)
        self.data_description = module.get_data_description()
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
            self.pd_dict[filename] = pd.read_csv(data_folder + '/' + filename)

    def folder_eventhandler(change):
        file_list = os.listdir(change['new'])
        folder_dropdown.options = file_list

    parent_folder_text.observe(folder_eventhandler, names='value')
    open_button.on_click(open_folder)

    v_box1 = widgets.VBox([parent_folder_text, folder_dropdown, open_button, self.open_data_output])

    items = [v_box1, self.region_data_output]
    h_box = widgets.HBox(items)
    return h_box
