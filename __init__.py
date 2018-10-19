# This file is part of the project_helpdesk module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import helpdesk
from . import work
from . import getmail


def register():
    Pool.register(
        configuration.HelpdeskConfiguration,
        helpdesk.Helpdesk,
        helpdesk.ProjectHelpdeskCreateTask,
        helpdesk.ProjectHelpdeskAddTimesheet,
        work.ProjectWork,
        module='project_helpdesk', type_='model')
    Pool.register(
        getmail.GetmailServer,
        depends=['getmail'],
        module='project_helpdesk', type_='model')
    Pool.register(
        helpdesk.ProjectHelpdeskTask,
        helpdesk.ProjectHelpdeskTimesheet,
        module='project_helpdesk', type_='wizard')
