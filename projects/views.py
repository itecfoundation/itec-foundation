import os
import uuid
import base64
from hashlib import sha1
import hmac

from requests.exceptions import Timeout, ConnectionError

from django.utils import timezone
from django.core.mail import EmailMultiAlternatives

from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views import generic
from django.utils.text import slugify
from django.utils.html import format_html
from django.forms import modelformset_factory
from django.views.decorators.csrf import csrf_exempt

from django import forms

from django.urls import reverse_lazy
from django.utils.functional import lazy
from django.utils.safestring import mark_safe

from django.views.generic.edit import CreateView, DeleteView, UpdateView

from django.utils.translation import gettext as _

from rules.contrib.views import AutoPermissionRequiredMixin, permission_required, objectgetter, PermissionRequiredMixin

import projects.models as _model

import projects.forms as _form

from vote.models import UP, DOWN

from photologue.models import Photo, Gallery
from accounts.models import User, DonatorData, LegalEntityDonatorData

from dal import autocomplete

from stream_django.feed_manager import feed_manager
from stream_django.enrich import Enrich
from django.contrib.auth.mixins import UserPassesTestMixin

from notifications.signals import notify
from notifications.models import Notification
from django.db import IntegrityError
from datetime import datetime
from datetime import timedelta

from weasyprint import HTML as weasyHTML
from django.utils.crypto import get_random_string

from config import settings
mark_safe_lazy = lazy(mark_safe)


def short_random():
    return str(uuid.uuid4()).split('-')[0]


@login_required
@permission_required('projects.change_thingnecessity', fn=objectgetter(_model.Project, 'project_id'))
def thing_necessity_update(request, project_id):
    return necessity_update(request, project_id, 'thing')


@login_required
@permission_required('projects.change_timenecessity', fn=objectgetter(_model.Project, 'project_id'))
def time_necessity_update(request, project_id):
    return necessity_update(request, project_id, 'time')


def necessity_update(request, project_id, type):
    cls = _form.TimeNecessityFormset if type == 'time' else _form.ThingNecessityFormset
    template_name = 'projects/necessity_form.html'
    project = get_object_or_404(_model.Project, pk=project_id)

    if request.method == 'GET':
        if (type == 'time'):
            if(project.timenecessity_set.count() == 0):
                formset = _form.TimeNecessityFormsetWithRow
            else:
                formset = cls(instance=project)
        else:
            if(project.thingnecessity_set.count() == 0):
                formset = _form.ThingNecessityFormsetWithRow
            else:
                formset = cls(instance=project)

    elif request.method == 'POST':
        formset = cls(request.POST, instance=project)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data.get('DELETE'):
                    form.instance.delete()

                elif form.cleaned_data.get('name'):
                    form.instance.project = project
                    if(project.question_set.count() == 0):
                        prototypes = _model.QuestionPrototype.objects.all()
                        order = 1
                        for prototype in prototypes:
                            question = _model.Question(
                                prototype=prototype,
                                project=project,
                                order=order
                            )
                            question.save()
                            project.question_set.add(question)
                            order += 1
                    form.save()
            if 'add-row' in request.POST:
                if (type == 'thing'):
                    formset = _form.ThingNecessityFormsetWithRow(
                        instance=project)  # за да добави празен ред
                else:
                    formset = _form.TimeNecessityFormsetWithRow(instance=project)
            else:
                if type == 'time':
                    return redirect('projects:time_necessity_list', project.pk)
                else:
                    return redirect('projects:thing_necessity_list', project.pk)

    return render(request, 'projects/necessity_form.html', {
        'formset': formset,
        'project': project,
        'type': type
    })


class ProjectsList(generic.ListView):
    model = _model.Project
    paginate_by = 100
    template_name = 'projects/projects_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['now'] = timezone.now()
        print(context)
        return context


class ProjectDetails(AutoPermissionRequiredMixin, generic.DetailView):
    model = _model.Project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        show_admin = self.request.GET.get('show_admin', 'True') == 'True'
        print(show_admin)
        can_be_admin = self.request.user.is_authenticated
        context['admin'] = show_admin and can_be_admin
        context['can_be_admin'] = can_be_admin

        try:
            feed = feed_manager.get_feed('project', context['object'].id)
            enricher = Enrich()
            timeline = enricher.enrich_activities(
                feed.get(limit=25)['results'])
            context['timeline'] = timeline
        except (Timeout, ConnectionError):
            messages.error(_('Could not get timeline'))
            context['timeline'] = None

        context['announcement_form'] = _form.AnnouncementForm()

        return context


class ProjectCreate(AutoPermissionRequiredMixin, UserPassesTestMixin, CreateView):
    model = _model.Project
    form_class = _form.ProjectForm

    def handle_no_permission(self):
        return redirect('/projects/project/create')

    def test_func(self):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.author_admin = self.request.user
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        return context

    def form_valid(self, form):
        user = self.request.user
        form.instance.author_admin = self.request.user
        print("Project Author: ", self.author_admin)
        project = form.instance


        # Потребител 0 следва всички проекти
        user_follow_project(0, project)

        itec_admins = _model.User.objects.filter(is_superuser=True)
        notification_text = '%s подаде заявка за проектa %s ' % (
            user, project)
        notify.send(self.request.user, recipient=itec_admins,
                    verb=notification_text)
        form.save()
        return super().form_valid(form)


class ProjectUpdate(AutoPermissionRequiredMixin, UpdateView):
    model = _model.Project
    form_class = _form.ProjectUpdateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        return super().form_valid(form)


class ProjectTextUpdate(AutoPermissionRequiredMixin, UpdateView):
    model = _model.Project
    form_class = _form.ProjectUpdateTextForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        return super().form_valid(form)


class ProjectDelete(AutoPermissionRequiredMixin, DeleteView):
    model = _model.Project
    success_url = '/'


class ReportCreate(PermissionRequiredMixin, CreateView):
    model = _model.Report
    form_class = _form.ReportForm

    def get_permission_object(self):
        project_pk = self.kwargs['project']
        return get_object_or_404(_model.Project, pk=project_pk)

    permission_required = ('projects.add_report')

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs['project']
        self.project = get_object_or_404(_model.Project, pk=project_pk)
        context['project'] = self.project
        return context

    def form_valid(self, form):
        project_pk = self.kwargs['project']
        self.project = get_object_or_404(_model.Project, pk=project_pk)
        form.instance.project = self.project
        return super().form_valid(form)


# class ReportUpdate(AutoPermissionRequiredMixin, UpdateView):
#     model = Report
#     form_class = ReportForm

#     def get_context_data(self, **kwargs):

#         context = super().get_context_data(**kwargs)
#         context['project'] = self.object.project
#         return context


class ReportDelete(AutoPermissionRequiredMixin, DeleteView):
    model = _model.Report
    template_name = 'projects/project_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('projects:details', kwargs={'pk': self.object.project.pk})


class ReportDetails(AutoPermissionRequiredMixin, generic.DetailView):
    model = _model.Report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = kwargs['object']
        context['votes_up'] = report.votes.count(UP)
        context['votes_down'] = report.votes.count(DOWN)
        vote = report.votes.get(self.request.user.pk)

        not_voted_classes = 'btn-light'
        voted_classes = 'btn-primary'
        vote_up_classes = not_voted_classes
        vote_down_classes = not_voted_classes

        if vote:
            if vote.action == UP:
                vote_up_classes = voted_classes
            else:
                vote_down_classes = voted_classes

        context['vote_up_classes'] = vote_up_classes
        context['vote_down_classes'] = vote_down_classes

        return context


class ReportList(AutoPermissionRequiredMixin, generic.ListView):
    model = _model.Report
    permission_type = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        project_pk = self.kwargs['project']
        context['project'] = get_object_or_404(_model.Project, pk=project_pk)

        context['reports'] = _model.Report.objects.filter(
            project_id=project_pk, published_at__lte=now)
        context['unpublished_reports'] = _model.Report.objects.filter(
            project_id=project_pk, published_at__gt=now)

        return context


def report_vote_up(request, pk):
    return report_vote(request, pk, UP)


def report_vote_down(request, pk):
    return report_vote(request, pk, DOWN)


@login_required
# TODO must be a subscriber to vote
def report_vote(request, pk, action):
    user = request.user
    report = get_object_or_404(_model.Report, pk=pk)

    if report.votes.exists(user.pk, action=action):
        success = report.votes.delete(user.pk)
        if not success:
            messages.error(request, _('Could not delete vote'))

        else:
            messages.success(request, _('Deleted vote'))

    else:
        if action == UP:
            success = report.votes.up(user.pk)
        else:
            success = report.votes.down(user.pk)

        if not success:
            messages.error(request, _('Could not vote'))
        else:
            messages.success(request, _('Voted up')
                             if action == UP else _('Voted down'))

    return redirect(report)


@login_required
def money_support_create(request, project_id=None):
    supporterType = request.GET.get('supportertype')
    if(supporterType == 'donator'):
        if(request.user.donatorData):
            return create_epay_support(request, pk=project_id)
        else:
            return redirect('/projects/donator/create/?next=/projects/create_epay_support/%s' % (project_id))
    elif (supporterType == 'legalentitydonator'):
        if(request.user.legalEntityDonatorData):
            return create_epay_support(request, pk=project_id)
        else:
            return redirect('/projects/legalentitydonator/create/?next=/projects/create_epay_support/%s' % (project_id))


class MoneySupportUpdate(AutoPermissionRequiredMixin, UpdateView):
    model = _model.MoneySupport
    template_name = 'projects/support_form.html'
    form_class = _form.MoneySupportForm

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['project'] = self.object.project

        return context


@permission_required('projects.update_moneysupport', fn=objectgetter(_model.MoneySupport, 'support_id'))
def money_support_update(request, project_id=None, support_id=None):
    return money_support_crud(request, support_id=support_id)


def money_support_crud(request, project_id=None, support_id=None):
    Form = _form.MoneySupportForm
    template = 'projects/support_form.html'
    supportType = request.GET.get('supportertype')
    if project_id:
        project = get_object_or_404(_model.Project, pk=project_id)
        support = None
    else:
        support = get_object_or_404(_model.MoneySupport, pk=support_id)
        project = support.project

    payment_form = None
    action_text = _('Next step')
    if request.method == 'GET':
        form = Form(instance=support, project=project, prefix='step_1')

    elif request.method == 'POST':
        form = Form(request.POST, instance=support,
                    project=project, prefix='step_1')
        if form.is_valid():
            if 'go_back' in request.POST:
                payment_form = None
            elif 'step_2-accept' in request.POST:
                # We only validate data if this is a step_2 submit, if only a step_1 submit  validation on step_2 printed on the form may confuse the user
                payment_form = _form.PaymentForm(
                    request.POST,
                    payment_method=form.cleaned_data['payment_method'],
                    payment_amount=form.cleaned_data['leva'],
                    prefix='step_2'
                )
            else:
                payment_form = _form.PaymentForm(
                    payment_method=form.cleaned_data['payment_method'],
                    payment_amount=form.cleaned_data['leva'],
                    prefix='step_2'
                )

            if payment_form:
                action_text = payment_form.action_text
                if payment_form.is_valid():
                    form.instance.project = project
                    form.instance.user = request.user
                    support = form.save(commit=False)
                    support.supportType = supportType
                    support.save()

                    notification_message = '%s подаде заявка за парична подкрепа към %s' % (
                        request.user, project)
                    notify.send(request.user, verb=notification_message)

                    return redirect(form.instance)

    return render(request, template, {
        'form': form,
        'project': project,
        'action_text': action_text,
        'payment_form': payment_form
    })


class MoneySupportDetails(AutoPermissionRequiredMixin, generic.DetailView):
    model = _model.MoneySupport
    template_name = 'projects/support_detail.html'

# TODO only allow if support is not accepted


class MoneySupportDelete(AutoPermissionRequiredMixin, DeleteView):
    model = _model.MoneySupport
    template_name = 'projects/project_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('projects:details', kwargs={'pk': self.object.project.pk})


class TimeSupportDelete(AutoPermissionRequiredMixin, DeleteView):
    model = _model.TimeSupport
    template_name = 'projects/project_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('projects:details', kwargs={'pk': self.object.project.pk})


def get_support(pk, type):
    if type in ['money', 'm']:
        support = get_object_or_404(_model.MoneySupport, pk=pk)
    else:
        support = get_object_or_404(_model.TimeSupport, pk=pk)

    return support


def get_support_request(request, pk, type, *args, **kwargs):
    return get_support(pk, type)


def support_accept(request, pk, type):
    return support_change_accept(request, pk, type, True)


def support_decline(request, pk, type):
    return support_change_accept(request, pk, type, False)


@permission_required('projects.accept_support', fn=get_support_request)
def support_change_accept(request, pk, type, accepted):
    if type in ['money', 'm']:
        support = get_object_or_404(_model.MoneySupport, pk=pk)
    else:
        support = get_object_or_404(_model.TimeSupport, pk=pk)

    if support.STATUS == support.STATUS.accepted:
        messages.info(request, _('Support already accepted')
                      if accepted else _('Support already declined'))
    else:
        if type in ['money', 'm'] and not support.necessity:
            messages.info(request, _(
                'Select a necessity for the money support'))
            return redirect('projects:money_support_update', support.pk)

        user_recipient = get_object_or_404(_model.User, pk=support.user.id)
        project = get_object_or_404(_model.Project, pk=support.project.id)
        project_name = project.name

        if type == 'time':
            if support.STATUS == support.STATUS.accepted:
                notification_message = 'Вашата заявка за доброволстване към %s беше приета' % (
                    project_name)
                email_txt_filename = 'email/support-accepted-time.txt'
            else:
                notification_message = 'Вашата заявка за доброволстване към %s беше отхвърлена' % (
                    project_name)
                email_txt_filename = 'email/support-declined-time.txt'
        else:
            notification_message = 'Вашето дарение към %s беше прието' % (
                project_name)

        result = support.set_accepted(accepted)
        if result == accepted:
            notify.send(request.user, recipient=user_recipient,
                        verb=notification_message)
            if type == 'time':
                ctx = {
                    'project_name': project_name
                }
                txt_msg = render_to_string(email_txt_filename, context=ctx)
                email = EmailMultiAlternatives(notification_message,
                                               txt_msg,
                                               'no-reply@horodeya.com',
                                               [user_recipient.email])
                email.send()

            messages.success(request, _('Support accepted')
                             if accepted else _('Support declined'))
        else:
            messages.error(request, _('Support could not be accepted')
                           if accepted else _('Support could not be declined'))

    return redirect(support)


@permission_required('projects.mark_delivered_support', fn=get_support_request)
def support_delivered(request, pk, type):

    if type in ['money', 'm']:
        support = get_object_or_404(_model.MoneySupport, pk=pk)
    else:
        support = get_object_or_404(_model.TimeSupport, pk=pk)

    user_recipient = get_object_or_404(_model.User, pk=support.user.id)
    project = get_object_or_404(_model.Project, pk=support.project.id)
    project_name = project.name

    if type == 'time':
        notification_message = 'Поздравления за успешно изпълненото доброволстване към задругата %s' % (
            project_name)
    else:
        notification_message = 'Вашето дарение към %s беше получено' % (
            project_name)

    # support = get_support(pk, type)

    if support.status == support.STATUS.delivered:
        messages.info(request, _('Support already marked as delivered'))
    else:
        support.status = support.STATUS.delivered
        support.delivered_at = timezone.now()
        support.save()
        notify.send(request.user, recipient=user_recipient,
                    verb=notification_message)

        messages.success(request, _('Support marked as delivered'))

    return redirect(support)


@permission_required('projects.change_timesupport', fn=objectgetter(_model.TimeSupport, 'pk'))
def time_support_update(request, pk):
    time_support = get_object_or_404(_model.TimeSupport, pk=pk)
    return time_support_create_update(request, time_support.project, time_support)


class TimeSupportDetails(AutoPermissionRequiredMixin, generic.DetailView):
    model = _model.TimeSupport
    template_name = 'projects/support_detail.html'


def user_support_list(request, user_id, type):
    user = get_object_or_404(_model.User, pk=user_id)
    if type == 'time':
        support_list = user.timesupport_set.order_by('-status_since')

    else:
        support_list = user.moneysupport_set.order_by('-status_since')

    return render(request, 'projects/user_support_list.html', context={
        'account': user,
        'type': type,
        'support_list': support_list,
    }
    )


def user_vote_list(request, user_id):
    user = get_object_or_404(_model.User, pk=user_id)

    votes_up = _model.Report.votes.all(user_id, UP)
    votes_down = _model.Report.votes.all(user_id, DOWN)

    supported_projects = set()
    money_supported = user.moneysupport_set.all()
    time_supported = user.timesupport_set.all()

    awaiting_list = []
    # TODO use stream framework for this
    # for m in money_supported:
    #    supported_projects.add(m.project)

    # for t in time_supported:
    #    supported_projects.add(t.project)

    # for p in supported_projects:
    #    awaiting_list.extend(p.report_set.filter())

    return render(request, 'projects/user_vote_list.html', context={
        'account': user,
        'awaiting_list': awaiting_list,
        'votes_up': votes_up,
        'votes_down': votes_down
    }
    )


class UserAutocompleteForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=_model.User.objects.none(),
        label=_("Email:"),
        widget=autocomplete.ModelSelect2(
            url='projects:user_autocomplete',
            attrs={
                'data-html': True,
            }
        )
    )

# TODO authenticate with rules


class UserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return _model.User.objects.none()

        if self.q and '@' in self.q:
            qs = _model.User.objects.all()
            qs = qs.filter(email=self.q)
        else:
            qs = _model.User.objects.none()

        return qs

    def get_result_label(self, item):
        return format_html('%s %s' % (item.first_name, item.last_name))


@permission_required('projects.follow_project', fn=objectgetter(_model.Project, 'pk'))
def follow_project(request, pk):

    project = get_object_or_404(_model.Project, pk=pk)

    user = request.user

    user_follow_project(user.id, project)

    messages.success(request, "%s %s" % (_("Started following"), project))

    return redirect(project)


def user_follow_project(user_id, project):
    news_feeds = feed_manager.get_news_feeds(user_id)

    for feed in news_feeds.values():
        feed.follow('project', project.id)

    notification_feed = feed_manager.get_notification_feed(user_id)
    notification_feed.follow('project', project.id)


class AnnouncementCreate(PermissionRequiredMixin, CreateView):
    model = _model.Announcement
    fields = ['text']

    def get_permission_object(self):
        project_pk = self.kwargs['project']
        return get_object_or_404(_model.Project, pk=project_pk)

    permission_required = ('projects.add_announcement')

    def form_valid(self, form):
        project_pk = self.kwargs['project']
        self.project = get_object_or_404(_model.Project, pk=project_pk)
        form.instance.project = self.project
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:details', kwargs={'pk': self.object.project.pk})


class AnnouncementUpdate(AutoPermissionRequiredMixin, UpdateView):
    model = _model.Announcement
    fields = ['text']

    def get_success_url(self):
        return reverse_lazy('projects:details', kwargs={'pk': self.object.project.pk})


class AnnouncementDelete(AutoPermissionRequiredMixin, DeleteView):
    model = _model.Announcement

    def get_success_url(self):
        return reverse_lazy('projects:details', kwargs={'pk': self.object.project.pk})


class AnnouncementDetails(AutoPermissionRequiredMixin, generic.DetailView):
    model = _model.Announcement

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        return context


@permission_required('projects.add_timesupport', fn=objectgetter(_model.Project, 'project_id'))
def time_support_create(request, project_id):
    project = get_object_or_404(_model.Project, pk=project_id)
    if(request.user.donatorData or request.user.legalEntityDonatorData):
        return time_support_create_update(request, project)
    else:
        return redirect('/projects/donator/create/?next=/projects/%s/timesupport/create/' % (project_id))


def time_support_create_update(request, project, support=None):
    context = {}
    context['project'] = project
    queryset = _model.TimeSupport.objects.filter(project=project, user=request.user)
    applied_necessities = set(map(lambda ts: ts.necessity, queryset.all()))
    answers = project.answer_set.filter(user=request.user).all()

    necessity_list = project.timenecessity_set.all()
    necessity_list = list(
        filter(lambda n: n not in applied_necessities, necessity_list))

    TimeSupportFormset = modelformset_factory(
        _model.TimeSupport,
        fields=['necessity', 'comment', 'start_date', 'end_date', 'price'],
        labels={'comment': _(
                'Why do you apply for this position? List your relevant experience / skills')},
        widgets={
            'start_date': forms.HiddenInput(),
            'end_date': forms.HiddenInput(),
            'price': forms.HiddenInput(),
            'comment': forms.Textarea(
                attrs={
                    'rows': 1,
                    'cols': 30,
                },
            )},
        extra=len(necessity_list))

    initial = list(map(lambda n: {'necessity': n, 'start_date': n.start_date,
                                  'end_date': n.end_date, 'price': n.price}, necessity_list))
    questions = project.question_set.order_by('order').all()
    if request.method == 'GET':
        formset = TimeSupportFormset(
            queryset=queryset,
            initial=initial)
        question_form = _form.QuestionForm(
            questions=questions, answers=answers, user=request.user)

    elif request.method == 'POST':
        formset = TimeSupportFormset(
            request.POST,
            queryset=queryset,
            initial=None)

        question_form = _form.QuestionForm(
            request.POST, questions=questions, user=request.user)

        selected_necessities = request.POST.getlist('necessity')
        selected_necessities = list(map(int, selected_necessities))

        if not selected_necessities:
            messages.error(request, _(
                "Choose at least one volunteer position"))

        else:
            if question_form.is_valid():
                question_form.save(project)
            if formset.is_valid():
                saved = 0
                for form in formset:
                    necessity = form.cleaned_data.get('necessity')
                    if necessity and necessity.pk in selected_necessities:
                        form.instance.project = project
                        form.instance.user = request.user
                        form.save()
                        saved += 1

                messages.success(request, _(
                    'Applied to %d volunteer positions' % saved))

                notify.send(request.user,
                            verb='%s подаде заявка за доброволстване към %s' % (request.user, project))
                return redirect(project)

    context['formset'] = formset
    context['form'] = question_form
    context['update'] = support is not None

    return render(request, 'projects/time_support_create.html', context)


class TimeNecessityList(AutoPermissionRequiredMixin, generic.ListView):
    permission_type = 'view'
    model = _model.TimeNecessity

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project_pk = self.kwargs['project_id']
        project = get_object_or_404(_model.Project, pk=project_pk)
        context['project'] = project

        context['necessity_list'] = project.timenecessity_set.all()
        context['type'] = 'time'

        if self.request.user == project.author_admin:
            context['member'] = self.request.user

        return context


class ThingNecessityList(AutoPermissionRequiredMixin, generic.ListView):
    permission_type = 'view'
    model = _model.ThingNecessity

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project_pk = self.kwargs['project_id']
        project = get_object_or_404(_model.Project, pk=project_pk)
        context['project'] = project

        context['necessity_list'] = project.thingnecessity_set.all()
        context['type'] = 'thing'

        if self.request.user == project.author_admin:
            context['member'] = self.request.user


        # context['member'] = self.request.user.member_of(project.pk)

        return context


class TimeNecessityDetails(AutoPermissionRequiredMixin, generic.DetailView):
    model = _model.TimeNecessity

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['type'] = 'time'
        return context


class ThingNecessityDetails(AutoPermissionRequiredMixin, generic.DetailView):
    model = _model.ThingNecessity

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['type'] = 'thing'
        return context


PhotoFormset = modelformset_factory(
    Photo,
    fields=['image'],
    extra=1,
    can_delete=True,
    can_order=True)


def neat_photo(first_directory, second_directory, image):
    path, extension = os.path.splitext(image.name)
    image.name = short_random() + extension

    photo = Photo()
    photo.title = image.name
    photo.image = image
    photo.slug = slugify(image.name)

    # Нашият PHOTOLOGUE_PATH използва това за да реши къде да запише файла
    photo.first_directory = first_directory
    photo.second_directory = second_directory

    photo.save()

    return photo


def gallery_update(request, project_id):
    template_name = 'projects/photo_form.html'
    project = get_object_or_404(_model.Project, pk=project_id)

    # TODO make project.name unique
    gallery, created = Gallery.objects.get_or_create(
        title=project.name,
        defaults={
            'slug': slugify(project.name, allow_unicode=True)
        })

    if created:
        project.gallery = gallery
        project.save()

    if request.method == 'GET':
        # we don't want to display the already saved model instances
        formset = PhotoFormset(queryset=gallery.photos.all())

    elif request.method == 'POST':
        formset = PhotoFormset(request.POST, queryset=gallery.photos.all())
        if formset.is_valid():
            for form in formset:
                image = request.FILES.get("%s-image" % (form.prefix))
                order = form.cleaned_data.get('ORDER', len(formset))
                if form.instance.id and form.cleaned_data.get('DELETE'):
                    form.instance.delete()
                elif image:
                    photo = neat_photo('project', str(project_id), image)
                    photo.galleries.add(gallery)

                    through = gallery.photos.through.objects.get(
                        photo_id=photo.pk, gallery_id=gallery.pk)
                    through.sort_value = order
                    through.save()
                elif form.instance.image:
                    image = form.instance
                    through = gallery.photos.through.objects.get(
                        photo_id=image.pk, gallery_id=gallery.pk)
                    through.sort_value = order
                    through.save()

            return redirect(project)

    return render(request, 'projects/photo_form.html', {
        'formset': formset,
        'project': project,
    })


@permission_required('projects.change_question', fn=objectgetter(_model.Project, 'project_id'))
def questions_update(request, project_id):
    project = get_object_or_404(_model.Project, pk=project_id)
    if project.question_set is None:
        prototypes = _model.QuestionPrototype.objects.order_by('order').all()
    else:
        prototypes = []

    initial = list(
        map(lambda p: {
            'prototype': p[1],
            'required': p[1].required,
            'ORDER': p[0]+1
        }, enumerate(prototypes))
    )

    QuestionFormset = modelformset_factory(
        _model.Question,
        fields=['prototype', 'description', 'required'],
        widgets={
            'description': forms.Textarea({
                'rows': 1,
                'cols': 15
            }
            ),
        },
        can_order=True,
        can_delete=True,
        extra=len(prototypes))

    cls = QuestionFormset
    template_name = 'projects/questions_form.html'

    if request.method == 'GET':
        question_set = _model.Question.objects.filter(project=project).exclude(
            prototype__id=14).order_by('order')

        formset = cls(initial=initial, queryset=question_set)

    elif request.method == 'POST':
        formset = cls(request.POST)

        try:
            if formset.is_valid():
                for form in formset:
                    order = form.cleaned_data.get('ORDER', len(formset))
                    if form.cleaned_data.get('DELETE'):
                        form.instance.delete()

                    elif form.cleaned_data.get('prototype'):
                        form.instance.project = project

                        if order:
                            form.instance.order = order

                        form.save()

        except IntegrityError:
            error_message = 'Добавили сте някой от въпросите повече от веднъж'
            formset = cls(initial=initial, queryset=_model.Question.objects.filter(
                project=project).order_by('order'))
            return render(request, template_name, {'formset': formset,
                                                   'project': project,
                                                   'error_message': error_message})

        return redirect('projects:time_necessity_list', project.pk)

    return render(request, template_name, {
        'formset': formset,
        'project': project
    })


class DonatorDataCreate(AutoPermissionRequiredMixin, CreateView):
    model = DonatorData
    fields = ['phone', 'citizenship', 'postAddress',
              'TIN']
    redirectUrl = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        redirectUrl = self.request.GET.get('next')
        return context

    def form_valid(self, form):
        user = self.request.user
        data = form.save(commit=False)
        data.save()
        user.donatorData = data
        user.save()
        redirectUrl = self.request.GET.get('next')
        if(redirectUrl):
            return redirect(self.request.GET['next']+'?supportertype=donator')
        else:
            return redirect('/accounts/profile/')


class LegalEntityDataCreate(AutoPermissionRequiredMixin, CreateView):
    model = LegalEntityDonatorData
    fields = ['name', 'type', 'headquarters', 'EIK', 'postAddress', 'TIN',
              'DDORegistration', 'phoneNumber', 'website']

    def form_valid(self, form):
        user = self.request.user
        data = form.save(commit=False)
        data.save()
        user.legalEntityDonatorData = data
        user.save()
        redirectUrl = self.request.GET.get('next')
        if(redirectUrl):
            return redirect(self.request.GET['next']+'?supportertype=legalentitydonator')
        else:
            return redirect('/accounts/profile/')


def feed(request):
    user = request.user

    if user.is_authenticated:
        feed = feed_manager.get_feed('timeline', user.id)
    else:
        feed = feed_manager.get_feed('timeline', 0)

    enricher = Enrich()
    timeline = enricher.enrich_activities(feed.get(limit=25)['results'])

    return render(request, 'projects/feed.html', {'timeline': timeline})


def notifications_feed(request):
    user = request.user
    notifications = user.notifications.unread()

    return render(request, 'projects/notifications.html', {'notifications': notifications})


def notifications_read(request):
    user = request.user
    notifications_read = user.notifications.read()

    return render(request, 'projects/notifications_read.html', {'notifications': notifications_read})


def notifications_mark_as_read(request):
    user = request.user
    notifications = user.notifications.unread()
    notifications.mark_all_as_read()
    return redirect('/projects/notifications')


@user_passes_test(lambda u: u.is_superuser)
def unverified_cause_list(request):
    unverified_causes = _model.Project.objects.filter(verified_status='review')
    return render(request, 'projects/unverified_causes.html', {'items': unverified_causes})


class ProjectVerify(AutoPermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = _model.Project
    fields = ['verified_status']
    template_name_suffix = '_verify_form'

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        project = form.save(commit=False)
        project_members = User.objects.filter(is_active=True)

        ctx = {
            'project_name': project.name
        }
        if(project.verified_status == 'accepted'):
            notification_message = 'Задругата %s беше одобрена' % (project)
            txt_msg = render_to_string(
                'email/project-accepted.txt', context=ctx)

        elif(project.verified_status == 'rejected'):
            notification_message = 'Задругата %s беше отхвърлена' % (project)
            txt_msg = render_to_string(
                'email/project-rejected.txt', context=ctx)

        notify.send(self.request.user, recipient=project_members,
                    verb=notification_message)

        recipients_list = project_members.values_list('email', flat=True)
        email = EmailMultiAlternatives(notification_message,
                                       txt_msg,
                                       'no-reply@horodeya.com',
                                       recipients_list)
        email.send()

        return super().form_valid(form)


def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    notification.mark_as_read()
    return redirect('/projects/notifications')


def bug_report_create(request):

    if(request.method == "POST"):
        form = _form.BugReportForm(request.POST)
        redirect_url = request.POST.get('next')
        if form.is_valid():
            form.save()
            message = request.POST.get('message', '')
            user_email = request.POST.get('email', '')
            email = EmailMultiAlternatives(user_email, message, settings.SERVER_EMAIL, ['beglika@gmail.com'])
            email.send()
            messages.add_message(request, messages.SUCCESS,
                                 'Благодарим ви за обратната връзка')
            return redirect(redirect_url)
        else:
            messages.add_message(request, messages.ERROR,
                                 "Въведете валиден имейл адрес")
            return redirect(redirect_url)


@user_passes_test(lambda u: u.is_superuser)
def administration(request):
    return render(request, 'projects/administration.html')


@user_passes_test(lambda u: u.is_superuser)
def received_bug_reports(request):
    bug_reports = _model.BugReport.objects.all()
    return render(request, 'projects/bug_reports.html', {'reports': bug_reports})


def create_epay_support(request, pk):
    if(request.method == "GET"):
        supporterType = request.GET.get('supportertype')
        context = {}
        context['pk'] = pk
        context['supporterType'] = supporterType
        return render(request, 'projects/epaymoneysupport_form.html', {'context': context})

    if(request.method == "POST"):
        form = _form.EpayMoneySupportForm(request.POST)
        project = get_object_or_404(_model.Project, pk=pk)
        if form.is_valid():
            form.instance.project = project
            form.instance.user = request.user
            form.instance.payment_method = 'epay'
            support = form.save()
            supportId = support.id
            messages.add_message(request, messages.SUCCESS,
                                 'Благодарим ви за дарението')
            return redirect('/projects/pay_epay_support/%s' % (supportId))
        else:
            messages.add_message(request, messages.ERROR,
                                 'Въведете валидна сума')
            return redirect('/')


def pay_epay_support(request, pk):
    # if(request == 'GET'):

    support = get_object_or_404(_model.MoneySupport, pk=pk)
    context = {}

    context['PAGE'] = 'paylogin'
    context['MIN'] = os.getenv('EPAY_MIN')
    context['INVOICE'] = support.id
    context['AMOUNT'] = support.leva
    context['EXP_TIME'] = (
        datetime.today()+timedelta(days=3)).strftime('%d.%m.%Y')
    context['DESCR'] = support.project.name
    context['user_id'] = request.user.id
    context['project_id'] = support.project.id

    context['data'] = ('MIN='+context['MIN'] + '\nINVOICE='+str(context['INVOICE']) + '\nAMOUNT=' +
                       str(context['AMOUNT']) + '\nEXP_TIME='+context['EXP_TIME'] + '\nDESCR='+context['DESCR'])
    encoded = base64.b64encode(context['data'].encode())
    context['ENCODED'] = encoded.decode('utf-8')

    key = os.getenv('EPAY_KEY').encode()

    checksum = hmac.new(key, encoded, sha1)
    context['CHECKSUM'] = checksum.hexdigest()

    return render(request, 'projects/epay_form.html', {'context': context})


@csrf_exempt
def accept_epay_payment(request):

    encodedParam = request.POST.get('encoded')
    checksum = request.POST.get('checksum')

    encoded = base64.b64decode(encodedParam).decode('utf-8')

    epay_items = encoded.split(':')

    epay_item_currencies = []
    for item in epay_items:
        epay_item_currencies.append(item.split('=')[1])

    invoice_number_decoded = epay_item_currencies[0]
    status = epay_item_currencies[1]
    pay_time = epay_item_currencies[2]

    key = os.getenv('EPAY_KEY').encode()

    calc_checksum = hmac.new(key, encodedParam.encode(), sha1).hexdigest()

    ok_message_for_epay = "INVOICE=%s:STATUS=OK" % (invoice_number_decoded)
    err_message_for_epay = "INVOICE=%s:STATUS=ERR" % (invoice_number_decoded)

    support = get_object_or_404(_model.MoneySupport, pk=invoice_number_decoded)

    if(calc_checksum == checksum):
        if(status == 'PAID'):
            support.status = _model.MoneySupport.STATUS.delivered
            support.save()

            txt_subject = 'Вашето дарение към %s беше получено' % (
                support.project.name)
            txt_msg = render_to_string('email/support-delivered-money.txt',
                                       context={'project_name': support.project.name})
            email = EmailMultiAlternatives(txt_subject,
                                           txt_msg,
                                           'no-reply@horodeya.com',
                                           [support.user.email])

            # only send tickets for Beglika 2020 for now
            if (support.project.id == 34):
                ticket = _model.TicketQR(
                    project=support.project,
                    user=support.user,
                    validation_code=get_random_string(length=16)
                )
                ticket.save()
                ctx_pdf = {
                    'ticket_code': ticket.validation_code,
                    'url': request.build_absolute_uri('/check-qr?ticket=' + ticket.validation_code)
                }
                html_string = render_to_string(
                    'email/ticket-pdf.html', context=ctx_pdf)
                ticket_html = weasyHTML(
                    string=html_string, base_url=request.build_absolute_uri())
                email.attach('ticket.pdf', ticket_html.write_pdf(),
                             'application/pdf')

            email.send()

            return HttpResponse(ok_message_for_epay)
        elif(status == 'EXPIRED'):
            support.status = 'expired'
            support.save()
            return HttpResponse(ok_message_for_epay)
        else:
            support.status = 'declined'
            support.save()
    else:
        return HttpResponse(err_message_for_epay)
