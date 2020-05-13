
from sys import version_info

if version_info.major >= 3:
    from ipypm import (open_tab, settings_tab, explore_tab, analyze_tab, mcmc_tab,
                       compare_tab, edit_tab, main_tab, edit_connectors_tab)
else:
    raise NotImplementedError('pyPM.ca requires Python 3 or higher. Please upgrade!')

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
