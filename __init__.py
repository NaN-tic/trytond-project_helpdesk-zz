# This file is part of the project_helpdesk module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .configuration import *
from .helpdesk import *
from .work import *

def register():
    Pool.register(
        HelpdeskConfiguration,
        Helpdesk,
        ProjectHelpdeskCreateTask,
        ProjectHelpdeskAddTimesheet,
        ProjectWork,
        module='project_helpdesk', type_='model')
    Pool.register(
        ProjectHelpdeskTask,
        ProjectHelpdeskTimesheet,
        module='project_helpdesk', type_='wizard')
