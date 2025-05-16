from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from app.models import Tag, Profile
from users.forms import LoginUserForm, RegisterUserForm, ProfileUserForm

def global_context():
    return {
        "popular_tags": Tag.popular_tags_manager.popular_tags(),
        "top_users": Profile.top_users_manager.top_users(),
        "menu": {
            "index": "Главная",
            "ask": "Задать вопрос",
            "hot": "Популярное",
        }
    }

# Create your views here.
class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(global_context())
        context.update({"title": "Войти"})
        return context

class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'signup.html'

    success_url = reverse_lazy('index')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(global_context())
        context.update({"title": "Регистрация"})
        return context

class ProfileUser(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileUserForm
    template_name = 'settings.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(global_context())
        context.update({"title": "Настройки профиля"})
        return context

