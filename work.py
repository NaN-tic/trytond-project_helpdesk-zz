# This file is part of project_helpdesk module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['ProjectWork']


class ProjectWork:
    __metaclass__ = PoolMeta
    __name__ = 'project.work'
    close_helpdesk = fields.Boolean('Close',
        help='Close project/task when close a helpdesk')

    @staticmethod
    def default_close_helpdesk():
        return True
