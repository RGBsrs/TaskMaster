import operator

from django.http.response import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db.models import Count, Q

from .models import Task, UserProfile
from .forms import TaskForm


class CustomLoginView(LoginView):
    template_name = 'base/login.html'
    fields = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('tasks')


class RegisterPage(FormView):
    template_name = 'base/register.html'
    form_class = UserCreationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('tasks')

    def form_valid(self, form):
        user = form.save()
        if user is not None:
            login(self.request, user)
        return super(RegisterPage, self).form_valid(form)
        if User.objects.filter(username = request.POST['username']).exists():
              print('Already taken')


    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('tasks')
        return super(RegisterPage, self).get(*args, **kwargs)


class TaskList(LoginRequiredMixin, ListView):
    model = Task
    context_object_name = 'tasks'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = context['tasks'].filter(user=self.request.user)
        context['count'] = context['tasks'].filter(complete=False).count()
        context['k'] = context['tasks'].filter(complete=True).count()

        search_input = self.request.GET.get('search-area') or ''
        if search_input:
            context['tasks'] = context['tasks'].filter(title__icontains=search_input)
        context['search_input'] = search_input

        return context


class TaskDetail(LoginRequiredMixin, DetailView):
    model = Task
    context_object_name = 'task'
    template_name = 'base/task.html'

    def dispatch(self, request, *args, **kwargs):
        task=self.get_object()
        if task.user != self.request.user:
            raise Http404("You don't have permission to view this Task")
        return super().dispatch(request, *args, **kwargs)


class TaskCreate(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    success_url = reverse_lazy('tasks')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(TaskCreate, self).form_valid(form)


class TaskUpdate(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    success_url = reverse_lazy('tasks')

    def dispatch(self, request, *args, **kwargs):
        task=self.get_object()
        if task.user != self.request.user:
            raise Http404("You don't have permission to edit this Task")
        return super().dispatch(request, *args, **kwargs)


class DeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    context_object_name = 'task'
    success_url = reverse_lazy('tasks')


class About(ListView):
    model= Task
    template_name = 'base/about.html'


class TopUsersView(View):
    def get(self, request):
        template = 'base/top-users.html'
        context = {'top_users': self.get_top_users()}
        return render(request, template, context)

    def get_top_users(self):
        top_users = User.objects.annotate(task_completed=Count(
            'tasks', filter=Q(tasks__complete=True))).order_by('-task_completed')
        return top_users


class UserProfileDetailView(DetailView):
    model = User
    context_object_name = "user"
    template_name = "base/profile_detail.html"

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, username=self.kwargs['username'])


class UserProfileEditView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    fields = ["first_name", "last_name", "profile_picture", "bio"]
    template_name = "base/profile_edit.html"

    def get_object(self, queryset=None):
        return self.model.objects.get(user__username=self.request.user)

    def get_success_url(self):
        return reverse_lazy("profile-detail", kwargs={'username':self.object.user.username})
