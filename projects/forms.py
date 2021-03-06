from django import forms
from django.utils.translation import gettext as _
# from django.utils.translation import get_language
from django.utils.text import slugify
# from django.core.exceptions import ValidationError

from rules.contrib.views import AutoPermissionRequiredMixin

from tempus_dominus.widgets import DateTimePicker, DatePicker

import projects.models as _model
from accounts.models import User
from projects.templatetags.projects_tags import leva


PROJECT_ACTIVYTY_TYPES = [
    ('Creativity', 'Наука и творчество'),
    ('Education', 'Просвета и възпитание'),
    ('Art', 'Култура и артистичност'),
    ('Administration', 'Администрация и финанси'),
    ('Willpower', 'Спорт и туризъм'),
    ('Health', 'Бит и здравеопазване'),
    ('Food', 'Земеделие и изхранване')
]


class ProjectForm(forms.ModelForm):

    class Meta:
        model = _model.Project
        fields = [
            'name',
            'category',
            'location',
            'description',
            'goal',
            'text',
            'start_date',
            'end_date',
            'end_date_tasks',
            'report_period',
        ]
        widgets = {
            'end_date': DatePicker(
                attrs={
                    'required': True
                },
                options={
                    'useCurrent': True,
                    'collapse': False,
                }
            ),
            'start_date': DatePicker(
                attrs={
                    'required': True
                },
                options={
                    'useCurrent': True,
                    'collapse': False,
                }
            ),
            'end_date_tasks': DatePicker(
                attrs={
                    'required': True
                },
                options={
                    'useCurrent': True,
                    'collapse': True,
                }
            ),
            'category': forms.RadioSelect(
                attrs=None, choices=PROJECT_ACTIVYTY_TYPES
            )
        }
        labels = {
            'goal1': 'Goal 1 ',
            'goal2': 'Goal 2',
            'goal3': 'Goal 3',
            'text': _('Text(5000 characters)')
        }

    def clean_end_date(self):
        startDate = self.cleaned_data['start_date']
        endDate = self.cleaned_data['end_date']
        if endDate <= startDate:
            raise forms.ValidationError(_(
                'End date must be after  start date'), code='invalid')

        return endDate

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        self.author_admin = user
        super().__init__(*args, **kwargs)
        # self.fields['project'].queryset = user.projects


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = _model.Announcement
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
        }


def question_key(question):
    return 'question_%d' % question.pk


class QuestionTextForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions')
        self.user = kwargs.pop('user')
        if 'answers' in kwargs:
            answers = kwargs.pop('answers')
        else:
            answers = []
        super(QuestionTextForm, self).__init__(*args, **kwargs)

        self.answer_values = {}
        self.questions = {}
        for question in questions:
            self.fields['question_text'] = forms.CharField(
                label=question.question_text,
                required=False
            )

    def save(self, project):
        for question in self.fields.keys():
            if 'question' in question:
                value = self.cleaned_data[question]

                if value is None:
                    value = ''
                answer, created = _model.QuestionText.objects.update_or_create(
                    project=project,
                    question_text=_model.QuestionText,
                    defaults={'answer': value}
                )


class PaymentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        payment_method = kwargs.pop('payment_method')
        payment_amount = kwargs.pop('payment_amount')
        project = kwargs.pop('project')
        super(PaymentForm, self).__init__(*args, **kwargs)

        self.unsupported = False

        self.template = 'projects/payment/' + slugify(payment_method) + '.html'
        self.payment_data = project
        pledge_action_text = _('Pledge to donate') + ' ' + leva(payment_amount)

        if payment_method == _model.MoneySupport.PAYMENT_METHODS.BankTransfer:
            if not project.bank_account_iban:
                self.unsupported = True

            self.fields['accept'] = forms.BooleanField(label=_(
                '''I will send the money to the provided bank account within
                the next 3 days'''
            ),
                disabled=self.unsupported,
                help_text=_("Otherwise the support will be marked invalid")
            )
            self.action_text = pledge_action_text
        elif payment_method == _model.MoneySupport.PAYMENT_METHODS.Revolut:
            if not project.revolut_phone:
                self.unsupported = True

            self.fields['accept'] = forms.BooleanField(label=_(
                '''I will send the money to the provided Revolut account
                within the next 3 days'''
            ),
                disabled=self.unsupported,
                help_text=_("Otherwise the support will be marked invalid")
            )
            self.action_text = pledge_action_text

        if self.unsupported:
            self.template = 'projects/payment/unsupported.html'


class MoneySupportForm(forms.ModelForm):
    class Meta:
        model = _model.MoneySupport
        fields = ['leva', 'necessity', 'comment',
                  'payment_method']
        widgets = {
            'payment_method': forms.RadioSelect()
        }

    def __init__(self, *args, **kwargs):
        if 'project' in kwargs:
            project = kwargs.pop('project')
        else:
            project = None

        super().__init__(*args, **kwargs)

        if not project:
            project = kwargs.get('instance').project

        self.fields['necessity'].queryset = project.thingnecessity_set
        self.fields['necessity'].empty_label = _('Any will do')


class ProjectUpdateSlackForm(forms.ModelForm):
    class Meta:
        model = _model.Project
        fields = ['slack_channel']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)


class ProjectUpdateTextForm(forms.ModelForm):
    class Meta:
        model = _model.Project
        fields = ['text']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)


class ProjectUpdatePresentationForm(forms.ModelForm):
    class Meta:
        model = _model.Project
        fields = ['presentation']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)


class ProjectUpdateAdministratorsForm(forms.ModelForm):
    administrators = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = _model.Project
        fields = ['administrators']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def save(self):
        project = super().save(commit=False)
        original_administrators = project.administrators.all()
        new_administrators = self.cleaned_data.get('administrators')
        remove_a = original_administrators.exclude(
            id__in=new_administrators.values('id')
        )
        add_a = new_administrators.exclude(
            id__in=original_administrators.values('id')
        )
        project.save()

        if new_administrators:
            for administrator in new_administrators.all():
                if administrator.is_administrator is False:
                    administrator.is_administrator = True
                    administrator.save()

        if remove_a:
            project.administrators.remove(*remove_a)
        if add_a:
            project.administrators.add(*add_a)
        return project


class ProjectUpdateMembersForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = _model.Project
        fields = ['members']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def save(self):
        project = super().save(commit=False)
        project.save()
        original_members = project.members.all()
        new_members = self.cleaned_data.get('members')
        remove_m = original_members.exclude(id__in=new_members.values('id'))
        # add_m = new_members.exclude(id__in=original_members.values('id'))
        project.save()

        project.members.remove(*remove_m)

        return project


class ReportForm(AutoPermissionRequiredMixin, forms.ModelForm):
    class Meta:
        model = _model.Report
        fields = ['name', 'text', 'published_at']
        widgets = {
            'published_at': DateTimePicker(
                options={
                    'useCurrent': True,
                    'collapse': False,
                },
            )
        }


class BugReportForm(forms.ModelForm):

    class Meta:
        model = _model.BugReport
        fields = ['email', 'message']


class EpayMoneySupportForm(forms.ModelForm):

    class Meta:
        model = _model.MoneySupport
        fields = ['leva', 'supportType']


class TimeSupportForm(AutoPermissionRequiredMixin, forms.ModelForm):
    class Meta:
        model = _model.TimeSupport
        fields = ['comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


TimeNecessityFormset = forms.inlineformset_factory(
    _model.Project,
    _model.TimeNecessity,
    fields=['name', 'description', 'count', 'price', 'start_date', 'end_date'],
    widgets={
        'count': forms.TextInput({
            'style': 'width: 60px'
        }
        ),
        'price': forms.TextInput({
            'style': 'width: 60px'
        }
        ),
        'description': forms.Textarea({
            'rows': 1,
            'cols': 30
        }
        ),
        'start_date': DatePicker(
            attrs={
                'style': 'width:120px',
                'required': True
            },
            options={
                'useCurrent': True,
                'collapse': False,
            },
        ),
        'end_date': DatePicker(
            attrs={
                'style': 'width:120px',
                'required': True
            },
            options={
                'useCurrent': True,
                'collapse': False,
            },
        )
    },
    extra=0)

TimeNecessityFormsetWithRow = forms.inlineformset_factory(
    _model.Project,
    _model.TimeNecessity,
    fields=['name', 'description', 'count', 'price', 'start_date', 'end_date'],
    widgets={
        'count': forms.TextInput({
            'style': 'width: 60px'
        }
        ),
        'price': forms.TextInput({
            'style': 'width: 60px'
        }
        ),
        'description': forms.Textarea({
            'rows': 1,
            'cols': 30
        }
        ),
        'start_date': DatePicker(
            attrs={
                'style': 'width:120px',
                'required': True
            },
            options={
                'useCurrent': True,
                'collapse': False,
            },
        ),
        'end_date': DatePicker(
            attrs={
                'style': 'width:120px',
                'required': True
            },
            options={
                'useCurrent': True,
                'collapse': False,
            },
        )
    },
    extra=1)

ThingNecessityFormset = forms.inlineformset_factory(
    _model.Project,
    _model.ThingNecessity,
    fields=['name', 'description', 'count', 'price'],
    widgets={
        'count': forms.TextInput({
            'style': 'width: 60px'
        }
        ),
        'price': forms.TextInput({
            'style': 'width: 60px'
        }
        ),
        'description': forms.Textarea({
            'rows': 1,
        }
        ),
    },
    extra=0)

ThingNecessityFormsetWithRow = forms.inlineformset_factory(
    _model.Project,
    _model.ThingNecessity,
    fields=['name', 'description', 'count', 'price'],
    widgets={
        'count': forms.TextInput({
            'style': 'width: 60px'
        }
        ),
        'price': forms.TextInput({
            'style': 'width: 60px'
        }
        ),
        'description': forms.Textarea({
            'rows': 1,
        }
        ),
    },
    extra=1)
