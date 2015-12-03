# This file is part of the project_helpdesk module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Not, Equal
from trytond.transaction import Transaction

__all__ = ['Helpdesk', 'ProjectHelpdeskCreateTask',
    'ProjectHelpdeskAddTimesheet', 'ProjectHelpdeskTask',
    'ProjectHelpdeskTimesheet']
__metaclass__ = PoolMeta


class Helpdesk:
    __name__ = 'helpdesk'
    work_domain = fields.Function(fields.One2Many('project.work', None,
            'Work Domain', depends=['party']),
        'on_change_with_work_domain')
    work = fields.Many2One('project.work', 'Work',
        states={
            'readonly': Eval('state').in_(['cancel', 'done']),
            },
        domain=[('id', 'in', Eval('work_domain', []))],
        depends=['state', 'work_domain'])
    timesheet_lines = fields.Function(fields.One2Many('timesheet.line', 'work',
        'Timesheet Lines'), 'get_timesheet_lines')

    @classmethod
    def __setup__(cls):
        super(Helpdesk, cls).__setup__()
        value = ('project', 'Project')
        if not value in cls.kind.selection:
            cls.kind.selection.append(value)
        cls._buttons.update({
            'create_task': {
                'invisible': (Eval('work', False)
                    | (Eval('state').in_(['cancel', 'done']))),
                },
            'add_timesheet': {
                'invisible': (~Eval('work', False)
                    | (Eval('state').in_(['cancel', 'done']))),
                },
            })

    @classmethod
    def view_attributes(cls):
        return super(Helpdesk, cls).view_attributes() + [
            ('//page[@id="project"]', 'states', {
                    'invisible': Not(Equal(Eval('kind'), 'project')),
                    })]

    @fields.depends('party')
    def on_change_with_work_domain(self, name=None):
        Work = Pool().get('project.work')
        domain = set()
        if self.party:
            works = Work.search([
                    ('party', '=', self.party.id),
                    ('state', '=', 'opened')
                    ])
            childs = Work.search([
                    ('parent', 'child_of', [w.id for w in works]),
                    ('state', '=', 'opened')
                    ])
            domain = set(c.id for c in childs)
        return list(domain)

    @classmethod
    @ModelView.button_action('project_helpdesk.wizard_task')
    def create_task(cls, helpdesks):
        pass

    @classmethod
    @ModelView.button_action('project_helpdesk.wizard_timesheet')
    def add_timesheet(cls, helpdesks):
        pass

    @classmethod
    def create_work(cls, helpdesk, project):
        '''
        Create a work from helpdesk
        :param helpdesk: helpdesk
        :param project: project
        '''
        pool = Pool()
        Timesheet = pool.get('timesheet.work')
        ProjectWork = pool.get('project.work')

        timesheet = Timesheet()
        timesheet.name = helpdesk.name
        timesheet.save()

        if helpdesk.employee and (helpdesk.employee not in project.employees):
            ProjectWork.write([project], {
                'employees': [('add', [helpdesk.employee.id])],
                'employee': helpdesk.employee.id,
                })

        # Create a new task parent to project
        work = ProjectWork()
        work.name = helpdesk.name
        work.type = 'task'
        work.work = timesheet
        work.parent = project if project else None
        work.state = 'opened'
        work.party = helpdesk.party
        if helpdesk.employee:
            work.employees = [helpdesk.employee.id]
            work.employee = helpdesk.employee
        work.save()

        return work


class ProjectHelpdeskCreateTask(ModelView):
    'Project Helpdesk Create Task'
    __name__ = 'project_helpdesk.project.helpdesk.task.ask'
    party = fields.Many2One('party.party', 'Party', readonly=True)
    project = fields.Many2One('project.work', 'Project', required=True,
        domain=[
            ('party', '=', Eval('party')),
            ('state', '=', 'opened'),
            ('type', '=', 'project')
        ], depends=['party'])

    @staticmethod
    def default_party():
        Helpdesk = Pool().get('helpdesk')

        helpdesk = Transaction().context.get('active_id')
        if helpdesk:
            helpdesk = Helpdesk(helpdesk)
            if helpdesk.party:
                return helpdesk.party.id

    @classmethod
    def default_project(cls):
        ProjectWork = Pool().get('project.work')

        domain = [d for d in cls.project.domain if d[0] != 'party']
        party = cls.default_party()
        if party:
            domain += [('party', '=', party)]
        project_works = ProjectWork.search(domain)
        if len(project_works) == 1:
            return project_works[0].id


class ProjectHelpdeskTask(Wizard):
    'Project Helpdesk Task'
    __name__ = 'project_helpdesk.project.helpdesk.task'
    start_state = 'ask'
    ask = StateView('project_helpdesk.project.helpdesk.task.ask',
        'project_helpdesk.wizard_task_ask_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Ok', 'handle', 'tryton-ok', default=True),
            ])
    handle = StateTransition()

    def transition_handle(self):
        Helpdesk = Pool().get('helpdesk')

        helpdesk = Helpdesk(Transaction().context['active_id'])
        project = self.ask.project

        work = Helpdesk.create_work(helpdesk, project)
        helpdesk.work = work
        helpdesk.save()

        return 'end'


class ProjectHelpdeskAddTimesheet(ModelView):
    'Project Helpdesk Add Timesheet'
    __name__ = 'project_helpdesk.project.helpdesk.timesheet.ask'
    duration = fields.TimeDelta('Duration', 'company_work_time', required=True)
    description = fields.Char('Description')


class ProjectHelpdeskTimesheet(Wizard):
    'Project Helpdesk Timesheet'
    __name__ = 'project_helpdesk.project.helpdesk.timesheet'
    start_state = 'ask'
    ask = StateView('project_helpdesk.project.helpdesk.timesheet.ask',
        'project_helpdesk.wizard_timesheet_ask_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Ok', 'handle', 'tryton-ok', default=True),
            ])
    handle = StateTransition()

    @classmethod
    def __setup__(cls):
        super(ProjectHelpdeskTimesheet, cls).__setup__()
        cls._error_messages.update({
            'no_employee': 'You must select a employee in yours user '
                'preferences!',
            'no_work': 'You must select a work in your task or parent.',
        })

    def transition_handle(self):
        pool = Pool()
        Helpdesk = pool.get('helpdesk')
        Line = pool.get('timesheet.line')
        User = pool.get('res.user')
        Date = pool.get('ir.date')

        user = User(Transaction().user)
        if not user.employee:
            self.raise_user_error('no_employee')

        helpdesk = Helpdesk(Transaction().context['active_id'])
        
        work = helpdesk.work.work if helpdesk.work.work else helpdesk.work.parent.work
        if not work:
            self.raise_user_error('no_work')

        line = Line()
        line.employee = user.employee
        line.date = Date.today()
        line.duration = self.ask.duration
        line.work = work
        line.description = self.ask.description
        line.save()

        return 'end'
