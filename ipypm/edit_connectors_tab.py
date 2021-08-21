# -*- coding: utf-8 -*-
"""
Tabs for editing connectors

@author: karlen
"""

from __future__ import print_function
import ipywidgets as widgets

from pypmca import Model, Population, Delay, Parameter, Multiplier, Propagator, \
    Splitter, Adder, Subtractor, Chain, Modifier, Injector

import pypmca.tools.table as ptt

def get_conn_tab(self):

    connectors_tab = widgets.Tab()
    adder_tab = get_adder_tab(self)
    chain_tab = get_chain_tab(self)
    multiplier_tab = get_multiplier_tab(self)
    propagator_tab = get_propagator_tab(self)
    splitter_tab = get_splitter_tab(self)
    subtractor_tab = get_subtractor_tab(self)

    connectors_tab.children = [adder_tab, chain_tab, multiplier_tab, propagator_tab,
                               splitter_tab, subtractor_tab]
    connectors_tab.set_title(0, 'Adder')
    connectors_tab.set_title(1, 'Chain')
    connectors_tab.set_title(2, 'Multiplier')
    connectors_tab.set_title(3, 'Propagator')
    connectors_tab.set_title(4, 'Splitter')
    connectors_tab.set_title(5, 'Subtractor')
    
    table_output = widgets.Output()
    con_table = widgets.Button(description='Connector Table', tooltip='Show all connectors in a table')
    def con_table_handler(b):
        table_output.clear_output(True)
        with table_output:
            print(ptt.connector_table(self.edit_model, width=110))
    con_table.on_click(con_table_handler)

    return widgets.VBox([con_table,connectors_tab,table_output])

def get_adder_tab(self):
        
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    add_dropdown = widgets.Dropdown(description='Adder:', disabled=False)
    
    add_name = widgets.Text(description='Name:')

    add_from_population = widgets.Dropdown(description='From pop:', disabled=False, 
                                           tooltip='Add from population') 
    add_to_population = widgets.Dropdown(description='To pop:', disabled=False, 
                                         tooltip='Add to population')
    add_location = widgets.Dropdown(description='After:', disabled=False, 
                                         tooltip='Insert after this connector')
    add_save = widgets.Button(description='Save changes', tooltip='Save changes to loaded model')
    add_new = widgets.Button(description='Insert adder', tooltip='Create new adder and insert into model')
    add_delete = widgets.Button(description='Delete adder', tooltip='Remove from model',
                                button_style='warning', icon='warning')

    def refresh(b):
        # Remember that connector order is important - do not sort them!
        if self.edit_model is not None:
            
            connector_name_list = ['AT TOP']
            for con_name in self.edit_model.connector_list:
                connector_name_list.append(con_name)
            add_location.options = connector_name_list

            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            add_from_population.options = pop_name_list
            add_to_population.options = pop_name_list
            
            adder_name_list = []
            for con_name in self.edit_model.connector_list:
                con = self.edit_model.connectors[con_name]
                if isinstance(con,Adder):
                    adder_name_list.append(str(con))
            add_dropdown.options = adder_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        adder_name = add_dropdown.value
        adder = self.edit_model.connectors[adder_name]
        add_name.value = adder.name
        add_from_population.value = str(adder.from_population)
        add_to_population.value = str(adder.to_population)

        with output:
            print('Adder options loaded')

    add_dropdown.observe(dropdown_eventhandler, names='value')

    # This function should not be used: considered risky to allow to modify
    # connectors - maintaining the list of parameters etc.    
    def add_save_handler(b):        
        output.clear_output(True)
        adder_name = add_dropdown.value
        if add_name.value != adder_name:
            with output:
                print('You are not allowed to change the name of an existing adder.')
                print('You click the "new adder" button to create a new adder')
                print('with this name.')
        else:
            adder = self.edit_model.connectors[adder_name]
            from_pop_name = add_from_population.value
            from_pop = None
            if from_pop_name in self.edit_model.populations:
                from_pop = self.edit_model.populations[from_pop_name]
            else:
                from_pop = self.new_populations[from_pop_name]
            adder.from_population = from_pop

            to_pop_name = add_to_population.value
            to_pop = None
            if to_pop_name in self.edit_model.populations:
                to_pop = self.edit_model.populations[to_pop_name]
            else:
                to_pop = self.new_populations[to_pop_name]
            adder.to_population = to_pop            
            
            # after modifying a connector, it is necessary for the model to
            # update its lists of populations etc.
        
            self.edit_model.update_lists()

            with output:
                print('Changes saved to adder.')
                print('You must save model to disk to make this permanent.')

    add_save.on_click(add_save_handler)    

    def add_new_handler(b):
        output.clear_output(True)
              
        from_pop_name = add_from_population.value
        from_pop = None
        if from_pop_name in self.edit_model.populations:
            from_pop = self.edit_model.populations[from_pop_name]
        else:
            from_pop = self.new_populations[from_pop_name]

        to_pop_name = add_to_population.value
        to_pop = None
        if to_pop_name in self.edit_model.populations:
            to_pop = self.edit_model.populations[to_pop_name]
        else:
            to_pop = self.new_populations[to_pop_name]           

        adder = Adder(add_name.value, from_pop, to_pop)
        
        loc_name = add_location.value
        loc_con = None
        if loc_name != 'AT TOP':
            loc_con = self.edit_model.connectors[loc_name]
        else:
            top_con_name = self.edit_model.connector_list[0]
            loc_con = self.edit_model.connectors[top_con_name]
            
        with output:
            if adder.name in self.edit_model.connectors:
                print('Connector with this name already exists.')
                print('Please change the name and try again.')
            else:
                print('New adder created and added')
                if loc_name != 'AT TOP':
                    self.edit_model.add_connector(adder, after_connector=loc_con)
                    print('after connector: '+loc_name)
                else:
                    self.edit_model.add_connector(adder, before_connector=loc_con)
                    print('at the top.')
                print('You must save the model to disk')
                print('to make this permanent.')

    add_new.on_click(add_new_handler)
    
    def add_delete_handler(b):
        output.clear_output(True)
        adder_name = add_dropdown.value
        if add_name.value != adder_name:
            with output:
                print('You changed the name of an existing adder before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            adder = self.edit_model.connectors[adder_name]
        
            self.edit_model.remove_connector(adder)
            with output:
                print('Adder '+str(adder)+' removed from model.')
                print('You must save the model to disk')
                print('to make this permanent.')
                
    add_delete.on_click(add_delete_handler)
 
    v_box1 = widgets.VBox([
        refresh_button,
        add_dropdown, 
        add_name,
        add_from_population,
        add_to_population,
        widgets.HBox([add_new, add_location]),
        add_delete
        ])
    
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])

def get_propagator_tab(self):
        
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    prop_dropdown = widgets.Dropdown(description='Propagator:', disabled=False)
    
    prop_name_widget = widgets.Text(description='Name:')

    prop_from_population = widgets.Dropdown(description='From pop:', disabled=False, 
                                            tooltip='Add from population') 
    prop_to_population = widgets.Dropdown(description='To pop:', disabled=False, 
                                          tooltip='Add to population')
    fraction_dropdown = widgets.Dropdown(description='Fraction:', disabled=False, 
                                         tooltip='Fraction to be propagated')
    delay_dropdown = widgets.Dropdown(description='Delay:', disabled=False, 
                                      tooltip='Delay in propagation')
    prop_location = widgets.Dropdown(description='After:', disabled=False, 
                                     tooltip='Insert after this connector')

    prop_new = widgets.Button(description='Insert new', tooltip='Create new propagator and insert into model')
    prop_delete = widgets.Button(description='Delete', tooltip='Remove propagator from model',
                                 button_style='warning', icon='warning')

    def refresh(b):
        # Remember that connector order is important - do not sort them!
        if self.edit_model is not None:
            
            connector_name_list = ['AT TOP','DO NOT INSERT']
            for con_name in self.edit_model.connector_list:
                connector_name_list.append(con_name)
            prop_location.options = connector_name_list

            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            prop_from_population.options = pop_name_list
            prop_to_population.options = pop_name_list
            
            par_name_list = list(self.edit_model.parameters.keys()) + \
                list(self.new_parameters.keys())
            par_name_list.sort()
            fraction_dropdown.options = par_name_list
            
            self.delays = self.get_model_delays()
            delay_name_list =  list(self.delays.keys()) + list(self.new_delays.keys())
            delay_name_list.sort()
            
            delay_dropdown.options = delay_name_list
            
            prop_name_list = []
            for con_name in self.edit_model.connector_list:
                con = self.edit_model.connectors[con_name]
                if isinstance(con,Propagator):
                    prop_name_list.append(str(con))
            prop_dropdown.options = prop_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        prop_name = prop_dropdown.value
        prop = self.edit_model.connectors[prop_name]
        prop_name_widget.value = prop.name
        prop_from_population.value = str(prop.from_population)
        prop_to_population.value = str(prop.to_population)
        fraction_dropdown.value = str(prop.fraction)
        delay_dropdown.value = str(prop.delay)

        with output:
            print('Propagator options loaded')

    prop_dropdown.observe(dropdown_eventhandler, names='value')

    def prop_new_handler(b):
        output.clear_output(True)
              
        from_pop_name = prop_from_population.value
        from_pop = None
        if from_pop_name in self.edit_model.populations:
            from_pop = self.edit_model.populations[from_pop_name]
        else:
            from_pop = self.new_populations[from_pop_name]

        to_pop_name = prop_to_population.value
        to_pop = None
        if to_pop_name in self.edit_model.populations:
            to_pop = self.edit_model.populations[to_pop_name]
        else:
            to_pop = self.new_populations[to_pop_name]
            
        fraction_name = fraction_dropdown.value
        fraction = None
        if fraction_name in self.edit_model.parameters:
            fraction = self.edit_model.parameters[fraction_name]
        else:
            fraction = self.new_parameters[fraction_name]

        self.delays = self.get_model_delays()
        delay_name = delay_dropdown.value
        delay = None
        if delay_name in self.delays:
            delay = self.delays[delay_name]
        else:
            delay = self.new_delays[delay_name]

        propagator = Propagator(prop_name_widget.value, from_pop, to_pop, fraction, delay)
        
        loc_name = prop_location.value
        loc_con = None
        if loc_name == 'AT TOP':
            top_con_name = self.edit_model.connector_list[0]
            loc_con = self.edit_model.connectors[top_con_name]
        elif loc_name =='DO NOT INSERT':
            loc_con = None
        else: 
            loc_con = self.edit_model.connectors[loc_name]

            
        with output:
            if propagator.name in self.edit_model.connectors:
                print('Connector with this name already exists.')
                print('Please change the name and try again.')
                print('If you want to modify this connector,')
                print('delete this one and add a new one with this name.')  
            else:
                print('New propagator created')
                if loc_name == 'AT TOP':
                    self.edit_model.add_connector(propagator, before_connector=loc_con)
                    print('and added at the top.')
                elif loc_name =='DO NOT INSERT':
                    self.new_propagators[propagator.name] = propagator
                    print('but not added to model.')
                    print('You can include this propagator in a chain.')
                else:
                    self.edit_model.add_connector(propagator, after_connector=loc_con)
                    print('and added after connector: '+loc_name)

                print('You must save the model to disk')
                print('to make this permanent.')

    prop_new.on_click(prop_new_handler)
    
    def prop_delete_handler(b):
        output.clear_output(True)
        prop_name = prop_dropdown.value
        if prop_name_widget.value != prop_name:
            with output:
                print('You changed the name of an existing propagator before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            prop = self.edit_model.connectors[prop_name]
        
            self.edit_model.remove_connector(prop)
            with output:
                print('Propagator '+str(prop)+' removed from model.')
                print('You must save the model to disk')
                print('to make this permanent.')
                
    prop_delete.on_click(prop_delete_handler)
 
    v_box1 = widgets.VBox([
        refresh_button,
        prop_dropdown, 
        prop_name_widget,
        prop_from_population,
        prop_to_population,
        fraction_dropdown,
        delay_dropdown,
        widgets.HBox([prop_new, prop_location]),
        widgets.HBox([prop_delete])
        ])
        
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])

def get_chain_tab(self):
        
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    chain_dropdown = widgets.Dropdown(description='Chain:', disabled=False)
    
    chain_name_widget = widgets.Text(description='Name:')

    chain_from_population = widgets.Dropdown(description='From pop:', disabled=False, 
                                             tooltip='Add from population') 
    chain_to_population = widgets.Dropdown(description='To pop:', disabled=False, 
                                           tooltip='Add to population')
    chain_list_text = widgets.Textarea(description='Prop list:', disabled=False,
                                       tootip = 'ordered list of one-to-one norm propagators',
                                       placeholder = 'ordered list of one-to-one norm propagators')
    fraction_dropdown = widgets.Dropdown(description='Fraction:', disabled=False, 
                                         tooltip='Fraction remaining to be propagated')
    delay_dropdown = widgets.Dropdown(description='Delay:', disabled=False, 
                                      tooltip='Delay in propagation of remainder')
    chain_location = widgets.Dropdown(description='After:', disabled=False, 
                                      tooltip='Insert after this connector')

    chain_new = widgets.Button(description='Insert new', tooltip='Create new chain and insert into model')
    chain_delete = widgets.Button(description='Delete', tooltip='Remove chain from model',
                                 button_style='warning', icon='warning')

    def refresh(b):
        # Remember that connector order is important - do not sort them!
        if self.edit_model is not None:
            
            connector_name_list = ['AT TOP']
            for con_name in self.edit_model.connector_list:
                connector_name_list.append(con_name)
            chain_location.options = connector_name_list

            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            chain_from_population.options = pop_name_list
            chain_to_population.options = pop_name_list
            
            par_name_list = list(self.edit_model.parameters.keys()) + \
                list(self.new_parameters.keys())
            par_name_list.sort()
            fraction_dropdown.options = par_name_list
            
            self.delays = self.get_model_delays()
            delay_name_list =  list(self.delays.keys()) + list(self.new_delays.keys())
            delay_name_list.sort()
            
            delay_dropdown.options = delay_name_list
            
            chain_name_list = []
            for con_name in self.edit_model.connector_list:
                con = self.edit_model.connectors[con_name]
                if isinstance(con,Chain):
                    chain_name_list.append(str(con))
            chain_dropdown.options = chain_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        chain_name = chain_dropdown.value
        chain = self.edit_model.connectors[chain_name]
        chain_name_widget.value = chain.name
        chain_from_population.value = str(chain.from_population)
        chain_to_population.value = str(chain.to_population)
        prop_name_list = []
        for prop in chain.chain:
            prop_name_list.append(str(prop))
        chain_list_text.value = ','.join(prop_name_list)
        fraction_dropdown.value = str(chain.fraction)
        delay_dropdown.value = str(chain.delay)

        with output:
            print('Chain options loaded')

    chain_dropdown.observe(dropdown_eventhandler, names='value')

    def chain_new_handler(b):
        output.clear_output(True)
              
        from_pop_name = chain_from_population.value
        from_pop = None
        if from_pop_name in self.edit_model.populations:
            from_pop = self.edit_model.populations[from_pop_name]
        else:
            from_pop = self.new_populations[from_pop_name]

        to_pop_name = chain_to_population.value
        to_pop = None
        if to_pop_name in self.edit_model.populations:
            to_pop = self.edit_model.populations[to_pop_name]
        else:
            to_pop = self.new_populations[to_pop_name]

        prop_list = []
        prop_name_list = chain_list_text.value.split(',')
        for prop_name in prop_name_list:
            name = prop_name.strip()
            if len(name) > 0:
                prop = None
                if name in self.edit_model.connectors:
                    prop = self.edit_model.connectors[name]
                elif name in self.new_propagators:
                    prop = self.new_propatators[name]
                else:
                    raise ValueError('Cannot find propagator with name:'+name)
                prop_list.append(prop)
        if len(prop_list) == 0:
            raise ValueError('List of propagators missing')

        fraction_name = fraction_dropdown.value
        fraction = None
        if fraction_name in self.edit_model.parameters:
            fraction = self.edit_model.parameters[fraction_name]
        else:
            fraction = self.new_parameters[fraction_name]

        self.delays = self.get_model_delays()
        delay_name = delay_dropdown.value
        delay = None
        if delay_name in self.delays:
            delay = self.delays[delay_name]
        else:
            delay = self.new_delays[delay_name]

        chain = Chain(chain_name_widget.value, from_pop, to_pop, prop_list, fraction,
                      delay, self.edit_model)
        
        loc_name = chain_location.value
        loc_con = None
        if loc_name == 'AT TOP':
            top_con_name = self.edit_model.connector_list[0]
            loc_con = self.edit_model.connectors[top_con_name]
        else: 
            loc_con = self.edit_model.connectors[loc_name]

        with output:
            if chain.name in self.edit_model.connectors:
                print('Connector with this name already exists.')
                print('Please change the name and try again.')
                print('If you want to modify this connector,')
                print('delete this one and add a new one with this name.')  
            else:
                print('New chain created')
                if loc_name == 'AT TOP':
                    self.edit_model.add_connector(chain, before_connector=loc_con)
                    print('and added at the top.')
                else:
                    self.edit_model.add_connector(chain, after_connector=loc_con)
                    print('and added after connector: '+loc_name)

                print('You must save the model to disk')
                print('to make this permanent.')

                match = False
                for prop in prop_list:
                    if prop in self.edit_model.connectors:
                        match = True
                if match:
                    print()
                    print('*** Warning: a propagator in the chain is also')
                    print('used in the model itself. Double check! ***')

    chain_new.on_click(chain_new_handler)
    
    def chain_delete_handler(b):
        output.clear_output(True)
        chain_name = chain_dropdown.value
        if chain_name_widget.value != chain_name:
            with output:
                print('You changed the name of an existing chain before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            chain = self.edit_model.connectors[chain_name]
        
            self.edit_model.remove_connector(chain)
            with output:
                print('Chain '+str(chain)+' removed from model.')
                print('You must save the model to disk')
                print('to make this permanent.')
            
    chain_delete.on_click(chain_delete_handler)
 
    v_box1 = widgets.VBox([
        refresh_button,
        chain_dropdown, 
        chain_name_widget,
        chain_from_population,
        chain_to_population,
        chain_list_text,
        fraction_dropdown,
        delay_dropdown,
        widgets.HBox([chain_new, chain_location]),
        widgets.HBox([chain_delete])
        ])
        
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])


def get_multiplier_tab(self):
        
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    mult_dropdown = widgets.Dropdown(description='Multiplier:', disabled=False)
    
    mult_name_widget = widgets.Text(description='Name:')

    mult_from_population0 = widgets.Dropdown(description='From pop1:', disabled=False, 
                                             tooltip='Mult from population0')
    mult_from_population1 = widgets.Dropdown(description='From pop2:', disabled=False, 
                                             tooltip='Mult from population1')
    mult_has_divider = widgets.Checkbox(description='Has divider', disabled=False,
                                        tooltip='Include a divider')
    mult_from_population2 = widgets.Dropdown(description='From pop3:', disabled=False, 
                                             tooltip='Divider population') 
    mult_to_population = widgets.Dropdown(description='To pop:', disabled=False, 
                                          tooltip='Add to population')
    scale_parameter_dropdown = widgets.Dropdown(description='Scale par:', disabled=False, 
                                         tooltip='Scaling parameter')
    delay_dropdown = widgets.Dropdown(description='Delay:', disabled=False, 
                                      tooltip='Delay in propagation')
    distribution_dropdown = widgets.Dropdown(description='Distribution:', disabled=False,
                                             options=['poisson','nbinom'],
                                             tooltip='Newly infected distribution')
    nbinom_par_dropdown = widgets.Dropdown(description='nbinom p', disabled=True, 
                                           tooltip='Negative binomial parameter p')    
    mult_location = widgets.Dropdown(description='After:', disabled=False, 
                                     tooltip='Insert after this connector')

    mult_save = widgets.Button(description='Save', tooltip='Save changes to Multiplier')
    mult_new = widgets.Button(description='Insert new', tooltip='Create new propagator and insert into model')
    mult_delete = widgets.Button(description='Delete', tooltip='Remove multiplier from model',
                                 button_style='warning', icon='warning')

    def refresh(b):
        # Remember that connector order is important - do not sort them!
        if self.edit_model is not None:
            
            connector_name_list = ['AT TOP']
            for con_name in self.edit_model.connector_list:
                connector_name_list.append(con_name)
            mult_location.options = connector_name_list

            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            mult_from_population0.options = pop_name_list
            mult_from_population1.options = pop_name_list
            mult_from_population2.options = pop_name_list
            mult_to_population.options = pop_name_list
            
            par_name_list = list(self.edit_model.parameters.keys()) + \
                list(self.new_parameters.keys())
            par_name_list.sort()
            scale_parameter_dropdown.options = par_name_list
            nbinom_par_dropdown.options = par_name_list
            
            self.delays = self.get_model_delays()
            delay_name_list =  list(self.delays.keys()) + list(self.new_delays.keys())
            delay_name_list.sort()
            
            delay_dropdown.options = delay_name_list
            
            mult_name_list = []
            for con_name in self.edit_model.connector_list:
                con = self.edit_model.connectors[con_name]
                if isinstance(con,Multiplier):
                    mult_name_list.append(str(con))
            mult_dropdown.options = mult_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        mult_name = mult_dropdown.value
        mult = self.edit_model.connectors[mult_name]
        mult_name_widget.value = mult.name
        from_populations = mult.from_population        
        mult_from_population0.value = str(from_populations[0])
        mult_from_population1.value = str(from_populations[1])
        if len(from_populations) == 3:
            mult_from_population2.value = str(from_populations[2])
            mult_has_divider.value = True
        mult_to_population.value = str(mult.to_population)
        scale_parameter_dropdown.value = str(mult.scale_parameter)
        delay_dropdown.value = str(mult.delay)
        distribution, nbinom_par = mult.get_distribution()
        distribution_dropdown.value = distribution
        if distribution == 'nbinom':
            nbinom_par_dropdown.value = str(nbinom_par)
            nbinom_par_dropdown.disabled = False
        else:
            nbinom_par_dropdown.disabled = True

        with output:
            print('Multiplier options loaded')

    mult_dropdown.observe(dropdown_eventhandler, names='value')

    def mult_has_divider_checkbox_eventhandler(change):
        mult_from_population2.disabled = not mult_has_divider.value
            
    mult_has_divider.observe(mult_has_divider_checkbox_eventhandler, names='value')

    def distribution_dropdown_eventhandler(change):
        nbinom_par_dropdown.disabled = distribution_dropdown.value != 'nbinom'
    
    distribution_dropdown.observe(distribution_dropdown_eventhandler, names='value')

    # allow the multiplier to be modified (changing the distribution)
    def mult_save_handler(b):        
        output.clear_output(True)
        mult_name = mult_dropdown.value
        if mult_name.value != mult_name:
            with output:
                print('You are not allowed to change the name of an existing multiplier.')
                print('You click the "Insert new" button to create a new multiplier')
                print('with this name.')
        else:
            mult = self.edit_model.connectors[mult_name]
            from_pop_names = [mult_from_population0.value,mult_from_population1.value]
            if mult_has_divider.value:
                from_pop_names.append(mult_from_population2.value)
            from_pops = []
            for from_pop_name in from_pop_names:
                from_pop = None
                if from_pop_name in self.edit_model.populations:
                    from_pop = self.edit_model.populations[from_pop_name]
                else:
                    from_pop = self.new_populations[from_pop_name]
                from_pops.append(from_pop)
            mult.from_population = from_pops

            to_pop_name = mult_to_population.value
            to_pop = None
            if to_pop_name in self.edit_model.populations:
                to_pop = self.edit_model.populations[to_pop_name]
            else:
                to_pop = self.new_populations[to_pop_name]
            mult.to_population = to_pop

            scale_parameter_name = scale_parameter_dropdown.value
            scale_parameter = None
            if scale_parameter_name in self.edit_model.parameters:
                scale_parameter = self.edit_model.parameters[scale_parameter_name]
            else:
                scale_parameter = self.new_parameters[scale_parameter_name]
            mult.scale_parameter =  scale_parameter
            
            self.delays = self.get_model_delays()
            delay_name = delay_dropdown.value
            delay = None
            if delay_name in self.delays:
                delay = self.delays[delay_name]
            else:
                delay = self.new_delays[delay_name]
            mult.delay = delay

            nbinom_par_name = nbinom_par_dropdown.value
            nbinom_par = None
            if distribution_dropdown.value == 'nbinom':
                if nbinom_par_name in self.edit_model.parameters:
                    nbinom_par = self.edit_model.parameters[nbinom_par_name]
                else:
                    nbinom_par = self.new_parameters[nbinom_par_name]
            mult.set_distribution(distribution_dropdown.value, nbinom_par)

            # after modifying a connector, it is necessary for the model to
            # update its lists of populations etc.
        
            self.edit_model.update_lists()

            with output:
                print('Changes saved to multiplier.')
                print('You must save model to disk to make this permanent.')

    mult_save.on_click(mult_save_handler)    

    def mult_new_handler(b):
        output.clear_output(True)

        from_pop_names = [mult_from_population0.value,mult_from_population1.value]
        if mult_has_divider.value:
            from_pop_names.append(mult_from_population2.value)
        from_pops = []
        for from_pop_name in from_pop_names:
            from_pop = None
            if from_pop_name in self.edit_model.populations:
                from_pop = self.edit_model.populations[from_pop_name]
            else:
                from_pop = self.new_populations[from_pop_name]
            from_pops.append(from_pop)

        to_pop_name = mult_to_population.value
        to_pop = None
        if to_pop_name in self.edit_model.populations:
            to_pop = self.edit_model.populations[to_pop_name]
        else:
            to_pop = self.new_populations[to_pop_name]
            
        scale_parameter_name = scale_parameter_dropdown.value
        scale_parameter = None
        if scale_parameter_name in self.edit_model.parameters:
            scale_parameter = self.edit_model.parameters[scale_parameter_name]
        else:
            scale_parameter = self.new_parameters[scale_parameter_name]

        self.delays = self.get_model_delays()
        delay_name = delay_dropdown.value
        delay = None
        if delay_name in self.delays:
            delay = self.delays[delay_name]
        else:
            delay = self.new_delays[delay_name]
            
        nbinom_par_name = nbinom_par_dropdown.value
        nbinom_par = None
        if distribution_dropdown.value == 'nbinom':
            if nbinom_par_name in self.edit_model.parameters:
                nbinom_par = self.edit_model.parameters[nbinom_par_name]
            else:
                nbinom_par = self.new_parameters[nbinom_par_name]

        multiplier = Multiplier(mult_name_widget.value, from_pops, to_pop, scale_parameter, delay,
                                self.edit_model, distribution=distribution_dropdown.value,
                                nbinom_par=nbinom_par)

        loc_name = mult_location.value
        loc_con = None
        if loc_name == 'AT TOP':
            top_con_name = self.edit_model.connector_list[0]
            loc_con = self.edit_model.connectors[top_con_name]
        else: 
            loc_con = self.edit_model.connectors[loc_name]

            
        with output:
            if multiplier.name in self.edit_model.connectors:
                print('Connector with this name already exists.')
                print('Please change the name and try again.')
  
            else:
                print('New multiplier created')
                if loc_name == 'AT TOP':
                    self.edit_model.add_connector(multiplier, before_connector=loc_con)
                    print('and added at the top.')
                else:
                    self.edit_model.add_connector(multiplier, after_connector=loc_con)
                    print('and added after connector: '+loc_name)

                print('You must save the model to disk')
                print('to make this permanent.')

    mult_new.on_click(mult_new_handler)
    
    def mult_delete_handler(b):
        output.clear_output(True)
        mult_name = mult_dropdown.value
        if mult_name_widget.value != mult_name:
            with output:
                print('You changed the name of an existing multiplier before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            mult = self.edit_model.connectors[mult_name]
        
            self.edit_model.remove_connector(mult)
            with output:
                print('Multiplier '+str(mult)+' removed from model.')
                print('You must save the model to disk')
                print('to make this permanent.')
            
    mult_delete.on_click(mult_delete_handler)
 
    v_box1 = widgets.VBox([
        refresh_button,
        mult_dropdown, 
        mult_name_widget,
        mult_from_population0,
        mult_from_population1,
        mult_has_divider,
        mult_from_population2,
        mult_to_population,
        scale_parameter_dropdown,
        delay_dropdown,
        distribution_dropdown,
        nbinom_par_dropdown,
        widgets.HBox([mult_new, mult_location]),
        widgets.HBox([mult_save, mult_delete])
        ])
        
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])



    """
    Splitter distributes its incoming population to other populations,
    either in the next time step or distributed in time:
        - connector_name: string, short descriptor
        - from_population: Population object, source of population to be
        propagated
        - to_population: list of two or more Population objects,
        the destination populations.
        - fractions: list of Parameter object with expected
        fraction of population to be propagated to the first to_population,
        the second is the fraction of the remaining to go to the next to_population
        and so on, with the remainder going to the other population
        The fractions must be in the range (0.,1.)
        - delay: Delay object or list of the Delay objects that define how
        propagation is spread over time.


    def __init__(self, connector_name, from_population, to_population,
                 fractions, delay):
        
            """
            
def get_splitter_tab(self):
        
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    splitter_dropdown = widgets.Dropdown(description='Splitter:', disabled=False)
    
    splitter_name_widget = widgets.Text(description='Name:')

    splitter_from_population = widgets.Dropdown(description='From pop:', disabled=False, 
                                             tooltip='Add from population') 
    splitter_to_list_text = widgets.Textarea(description='To pops:', disabled=False,
                                       tootip = 'commma separated list of populations',
                                       placeholder = 'commma separated list of populations')
    fractions_list_text = widgets.Textarea(description='Fractions:', disabled=False, 
                                          tooltip= 'comma separated list of fraction parameters',
                                          placeholder = 'comma separated list of fraction parameters')
    delay_list_text = widgets.Textarea(description='Delay(s):', disabled=False, 
                                      tooltip='Delay(s) in propagation')
    splitter_location = widgets.Dropdown(description='After:', disabled=False, 
                                      tooltip='Insert after this connector')

    splitter_new = widgets.Button(description='Insert new', tooltip='Create new splitter and insert into model')
    splitter_delete = widgets.Button(description='Delete', tooltip='Remove splitter from model',
                                 button_style='warning', icon='warning')

    def refresh(b):
        # Remember that connector order is important - do not sort them!
        if self.edit_model is not None:
            
            connector_name_list = ['AT TOP']
            for con_name in self.edit_model.connector_list:
                connector_name_list.append(con_name)
            splitter_location.options = connector_name_list

            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            splitter_from_population.options = pop_name_list
            
            splitter_name_list = []
            for con_name in self.edit_model.connector_list:
                con = self.edit_model.connectors[con_name]
                if isinstance(con,Splitter):
                    splitter_name_list.append(str(con))
            splitter_dropdown.options = splitter_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        splitter_name = splitter_dropdown.value
        splitter = self.edit_model.connectors[splitter_name]
        splitter_name_widget.value = splitter.name
        splitter_from_population.value = str(splitter.from_population)
        pop_name_list = []
        for pop in splitter.to_population:
            pop_name_list.append(str(pop))
        splitter_to_list_text.value = ','.join(pop_name_list)
        par_name_list = []
        for par in splitter.fractions:
            par_name_list.append(str(par))
        fractions_list_text.value = ','.join(par_name_list)

        delay_name_list =[]
        if isinstance(splitter.delay, list):
            for delay in splitter.delay:
                delay_name_list.append(str(delay))
        else:
            delay_name_list.append(str(splitter.delay))
        delay_list_text.value = ','.join(delay_name_list)

        with output:
            print('Splitter options loaded')

    splitter_dropdown.observe(dropdown_eventhandler, names='value')

    def splitter_new_handler(b):
        output.clear_output(True)
              
        from_pop_name = splitter_from_population.value
        from_pop = None
        if from_pop_name in self.edit_model.populations:
            from_pop = self.edit_model.populations[from_pop_name]
        else:
            from_pop = self.new_populations[from_pop_name]

        to_pops = []
        to_pop_names = splitter_to_list_text.value.split(',')
        for to_pop_name in to_pop_names:
            to_pop = None
            if to_pop_name in self.edit_model.populations:
                to_pop = self.edit_model.populations[to_pop_name]
            else:
                to_pop = self.new_populations[to_pop_name]
            to_pops.append(to_pop)

        fractions = []
        fraction_names = fractions_list_text.value.split(',')
        for fraction_name in fraction_names:
            fraction = None
            if fraction_name in self.edit_model.parameters:
                fraction = self.edit_model.parameters[fraction_name]
            else:
                fraction = self.new_parameters[fraction_name]
            fractions.append(fraction)

        self.delays = self.get_model_delays()
        delays = []
        delay_names = delay_list_text.value.split(',')
        for delay_name in delay_names:
            delay = None
            if delay_name in self.delays:
                delay = self.delays[delay_name]
            else:
                delay = self.new_delays[delay_name]
            delays.append(delay)
        if len(delays) == 1:
            delays = delays[0]

        splitter = Splitter(splitter_name_widget.value, from_pop, to_pops, fractions,
                      delays)
                
        loc_name = splitter_location.value
        loc_con = None
        if loc_name == 'AT TOP':
            top_con_name = self.edit_model.connector_list[0]
            loc_con = self.edit_model.connectors[top_con_name]
        else: 
            loc_con = self.edit_model.connectors[loc_name]

        with output:
            if splitter.name in self.edit_model.connectors:
                print('Connector with this name already exists.')
                print('Please change the name and try again.')
                print('If you want to modify this connector,')
                print('delete this one and add a new one with this name.')  
            else:
                print('New splitter created')
                if loc_name == 'AT TOP':
                    self.edit_model.add_connector(splitter, before_connector=loc_con)
                    print('and added at the top.')
                else:
                    self.edit_model.add_connector(splitter, after_connector=loc_con)
                    print('and added after connector: '+loc_name)

                print('You must save the model to disk')
                print('to make this permanent.')

    splitter_new.on_click(splitter_new_handler)
    
    def splitter_delete_handler(b):
        output.clear_output(True)
        splitter_name = splitter_dropdown.value
        if splitter_name_widget.value != splitter_name:
            with output:
                print('You changed the name of an existing splitter before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            splitter = self.edit_model.connectors[splitter_name]
        
            self.edit_model.remove_connector(splitter)
            with output:
                print('Splitter '+str(splitter)+' removed from model.')
                print('You must save the model to disk')
                print('to make this permanent.')
            
    splitter_delete.on_click(splitter_delete_handler)
 
    v_box1 = widgets.VBox([
        refresh_button,
        splitter_dropdown, 
        splitter_name_widget,
        splitter_from_population,
        splitter_to_list_text,
        fractions_list_text,
        delay_list_text,
        widgets.HBox([splitter_new, splitter_location]),
        widgets.HBox([splitter_delete])
        ])
        
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])

def get_subtractor_tab(self):
        
    output = widgets.Output()
    
    refresh_button = widgets.Button(description='Refresh', tooltip='Refresh dropdown menus')
    subtract_dropdown = widgets.Dropdown(description='Subtractor:', disabled=False)
    
    subtract_name = widgets.Text(description='Name:')

    subtract_from_population = widgets.Dropdown(description='From pop:', disabled=False, 
                                           tooltip='Subtract from population') 
    subtract_to_population = widgets.Dropdown(description='To pop:', disabled=False, 
                                         tooltip='Subtract to population')
    subtract_location = widgets.Dropdown(description='After:', disabled=False, 
                                         tooltip='Insert after this connector')
    subtract_save = widgets.Button(description='Save changes', tooltip='Save changes to loaded model')
    subtract_new = widgets.Button(description='Insert subtractor', tooltip='Create new subtractor and insert into model')
    subtract_delete = widgets.Button(description='Delete subtractor', tooltip='Remove from model',
                                button_style='warning', icon='warning')

    def refresh(b):
        # Remember that connector order is important - do not sort them!
        if self.edit_model is not None:
            
            connector_name_list = ['AT TOP']
            for con_name in self.edit_model.connector_list:
                connector_name_list.append(con_name)
            subtract_location.options = connector_name_list

            pop_name_list = list(self.edit_model.populations.keys()) + \
                list(self.new_populations.keys())
            pop_name_list.sort()
            subtract_from_population.options = pop_name_list
            subtract_to_population.options = pop_name_list
            
            subtractor_name_list = []
            for con_name in self.edit_model.connector_list:
                con = self.edit_model.connectors[con_name]
                if isinstance(con,Subtractor):
                    subtractor_name_list.append(str(con))
            subtract_dropdown.options = subtractor_name_list

    refresh_button.on_click(refresh)

    def dropdown_eventhandler(change):
        output.clear_output(True)
        subtractor_name = subtract_dropdown.value
        subtractor = self.edit_model.connectors[subtractor_name]
        subtract_name.value = subtractor.name
        subtract_from_population.value = str(subtractor.from_population)
        subtract_to_population.value = str(subtractor.to_population)

        with output:
            print('Subtractor options loaded')

    subtract_dropdown.observe(dropdown_eventhandler, names='value')

    # This function should not be used: considered risky to allow to modify
    # connectors - maintaining the list of parameters etc.    
    def subtract_save_handler(b):        
        output.clear_output(True)
        subtractor_name = subtract_dropdown.value
        if subtract_name.value != subtractor_name:
            with output:
                print('You are not allowed to change the name of an existing subtractor.')
                print('You click the "new subtractor" button to create a new subtractor')
                print('with this name.')
        else:
            subtractor = self.edit_model.connectors[subtractor_name]
            from_pop_name = subtract_from_population.value
            from_pop = None
            if from_pop_name in self.edit_model.populations:
                from_pop = self.edit_model.populations[from_pop_name]
            else:
                from_pop = self.new_populations[from_pop_name]
            subtractor.from_population = from_pop

            to_pop_name = subtract_to_population.value
            to_pop = None
            if to_pop_name in self.edit_model.populations:
                to_pop = self.edit_model.populations[to_pop_name]
            else:
                to_pop = self.new_populations[to_pop_name]
            subtractor.to_population = to_pop            
            
            # after modifying a connector, it is necessary for the model to
            # update its lists of populations etc.
        
            self.edit_model.update_lists()

            with output:
                print('Changes saved to subtractor.')
                print('You must save model to disk to make this permanent.')

    subtract_save.on_click(subtract_save_handler)    

    def subtract_new_handler(b):
        output.clear_output(True)
              
        from_pop_name = subtract_from_population.value
        from_pop = None
        if from_pop_name in self.edit_model.populations:
            from_pop = self.edit_model.populations[from_pop_name]
        else:
            from_pop = self.new_populations[from_pop_name]

        to_pop_name = subtract_to_population.value
        to_pop = None
        if to_pop_name in self.edit_model.populations:
            to_pop = self.edit_model.populations[to_pop_name]
        else:
            to_pop = self.new_populations[to_pop_name]           

        subtractor = Subtractor(subtract_name.value, from_pop, to_pop)
        
        loc_name = subtract_location.value
        loc_con = None
        if loc_name != 'AT TOP':
            loc_con = self.edit_model.connectors[loc_name]
        else:
            top_con_name = self.edit_model.connector_list[0]
            loc_con = self.edit_model.connectors[top_con_name]
            
        with output:
            if subtractor.name in self.edit_model.connectors:
                print('Connector with this name already exists.')
                print('Please change the name and try again.')
            else:
                print('New subtractor created and added')
                if loc_name != 'AT TOP':
                    self.edit_model.add_connector(subtractor, after_connector=loc_con)
                    print('after connector: '+loc_name)
                else:
                    self.edit_model.add_connector(subtractor, before_connector=loc_con)
                    print('at the top.')
                print('You must save the model to disk')
                print('to make this permanent.')

    subtract_new.on_click(subtract_new_handler)
    
    def subtract_delete_handler(b):
        output.clear_output(True)
        subtractor_name = subtract_dropdown.value
        if subtract_name.value != subtractor_name:
            with output:
                print('You changed the name of an existing subtractor before asking to remove it.')
                print('Restore the name before trying to remove it.')
        else:
            subtractor = self.edit_model.connectors[subtractor_name]
        
            self.edit_model.remove_connector(subtractor)
            with output:
                print('Subtractor '+str(subtractor)+' removed from model.')
                print('You must save the model to disk')
                print('to make this permanent.')
            
    subtract_delete.on_click(subtract_delete_handler)
 
    v_box1 = widgets.VBox([
        refresh_button,
        subtract_dropdown, 
        subtract_name,
        subtract_from_population,
        subtract_to_population,
        widgets.HBox([subtract_new, subtract_location]),
        subtract_delete
        ])
    
    hspace = widgets.HTML(
        value="&nbsp;"*4,
        placeholder='Some HTML',
        description='')

    return widgets.HBox([v_box1, hspace, output])