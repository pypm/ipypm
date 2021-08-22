=======
History
=======

0.1 (2020-05-13)
------------------

* First release on PyPI.
* 0.1.1 : prevent long scans for integers. Add easier startup, run_gui()
* 0.1.2 : move from port 8080 to 80 on the data.ipypm.ca server so tha this package will work with binder
* 0.1.3 : prevent models with time_step !=1 from being loaded (not yet supported in ipypm)
* 0.1.3 : change Simulation on explore tab: if seed is set to zero (default) then new simulation is done each time a plot is produced
* 0.1.4 : revise MCMC tab

0.2 (2020-05-19)
----------------

* First beta release on PyPI
* 0.2.1 : feature update (2020-06-16)
* 0.2.2 : minor fixes (2020-07-24)
* 0.2.3 : allow cumulative to start from zero (2020-07-30)
* 0.2.4 : fix analyze plot when cumulative reset selected (2020-07-31)
* 0.2.5 : minor bug fix (2020-09-11)
* 0.2.6 : increase max days to 500 (2020-10-4)
* 0.2.7 : allow start date for plots to be specified (2020-11-21)
* 0.2.8 : add trans date error and improve new model loading (2020-12-06)
* 0.2.9 : allow dates to be skipped in fitting (2021-01-31)
* 0.2.10 : fixes to compare and MCMC tabs
* 0.2.11 : increase maximum # of days to show (2021-03-10)
* 0.2.12 : fixes for edit and explore tabs, local fit default (2021-08-22)
