from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, ListView, DetailView, UpdateView, FormView
from .models import Usuario, Endereco
from .forms import CriarUsuarioForm, EnderecoForm
from .permissoes import PermissaoFuncionariosMixin


class Home(TemplateView):
    template_name = 'core/inicio.html'


class Painel(PermissaoFuncionariosMixin, TemplateView):
    template_name = 'core/painel.html'


class Cadastrar(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Usuario
    form_class = CriarUsuarioForm
    template_name = 'core/cadastrar.html'
    success_message = 'Cadastro realizado com sucesso!'

    def form_valid(self, form):
        pessoa = form.save(commit=False)
        cpf = pessoa.cpf.replace('.', '').replace('-', '')
        user = User.objects.create_user(username=cpf, password=form.cleaned_data['password1'])
        pessoa.usuario = user
        pessoa.paciente = True
        pessoa.save()
        self.user_id = user.id
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('home:endereco', kwargs={'id': self.user_id})


class EnderecoCad(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Endereco
    form_class = EnderecoForm
    template_name = 'core/endereco.html'
    success_message = 'Endereço cadastrado com sucesso!'
    success_url = reverse_lazy('home:painel')

    def form_valid(self, form):
        endereco = form.save(commit=False)
        user = User.objects.get(id=self.kwargs['id'])
        usuario = Usuario.objects.get(usuario=user)
        endereco.pessoa = usuario
        endereco.save()
        return super().form_valid(form)


def custom_login_redirect(request):
    user = request.user
    if user.is_authenticated:
        usuario = user.usuario
        if usuario.funcionario:
            return redirect('home:painel')
        elif usuario.adm:
            return redirect('home:painel')
        elif usuario.doutor:
            return redirect('home:painel')
    return redirect(reverse_lazy('home:indice'))


class Pacientes(LoginRequiredMixin, ListView):
    model = Usuario
    template_name = 'core/pacientes.html'
    context_object_name = 'pacientes'
    paginate_by = 10

    def get_queryset(self):
        return Usuario.objects.filter(funcionario=False, status=True, adm=False, doutor=False).order_by('nome')


class BuscarAtendimentoPaciente(LoginRequiredMixin, TemplateView):
    template_name = 'core/buscar_paciente.html'


class MostrarPerfil(LoginRequiredMixin, DetailView):
    model = Usuario
    template_name = 'core/perfil.html'

    def get_context_data(self, **kwargs):
      context = super().get_context_data(**kwargs)
      paciente = Usuario.objects.get(pk=self.kwargs['pk'])
      endereco = None
      try:
        endereco = Endereco.objects.get(pessoa=paciente)
      except:
          print('')

      atendimentos = paciente.r_paciente.all().order_by('-data_cadastro')
      context['atendimentos'] = atendimentos
      context['paciente'] = paciente
      context['endereco'] = endereco
      return context


class AtualizarPerfil(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Usuario
    fields = ('nome', 'cpf', 'rg', 'sexo', 'data_nascimento', 'telefone')
    template_name = 'core/atualizar_perfil.html'
    context_object_name = 'form'
    success_message = 'Informações atualizadas com sucesso!'

    def get_success_url(self):
        return reverse_lazy('home:perfil', kwargs={'pk': self.kwargs['pk']})


class AtualizarEndereco(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Endereco
    fields = ('rua', 'numero', 'complemento', 'bairro', 'cep', 'cidade', 'estado')
    template_name = 'core/atualizar_endereco.html'
    context_object_name = 'form'
    success_message = 'Endereço atualizado com sucesso!'

    def get_success_url(self):
        return reverse_lazy('home:atualizar', kwargs={'pk': self.get_object.pessoa.pk})


def buscar_atendimento_paciente(request):
    if request.POST.get('ajax_request') == 'true':
        res = None
        nomes = request.POST.get('nomes')
        query_se = Usuario.objects.filter(nome__icontains=nomes)

        if len(query_se) > 0 and len(nomes) > 0:
            data = []
            for paciente in query_se:
                item = {
                    'pk': paciente.pk,
                    'nome': paciente.nome,
                    'cpf': paciente.cpf,
                }

                data.append(item)
            res = data
        else:
            res = 'Nenhum paciente encontrado'

        return JsonResponse({'data': res})
    return JsonResponse({})


class BuscarOpcoesPaciente(LoginRequiredMixin, TemplateView):
    template_name = 'core/perfil_paciente.html'


def buscar_paciente(request):
    if request.POST.get('ajax_request') == 'true':
        res = None
        nomes = request.POST.get('nomes')
        query_se = Usuario.objects.filter(nome__icontains=nomes)

        if len(query_se) > 0 and len(nomes) > 0:
            data = []
            for paciente in query_se:
                item = {
                    'pk': paciente.pk,
                    'nome': paciente.nome,
                    'cpf': paciente.cpf,
                }

                data.append(item)
            res = data
        else:
            res = 'Nenhum paciente encontrado'

        return JsonResponse({'data': res})
    return JsonResponse({})


class OpcoesPaciente(LoginRequiredMixin, TemplateView):
    template_name = 'core/opcoes_paciente.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        paciente = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        contexto['paciente'] = paciente
        return contexto


class AtualizarSenha(LoginRequiredMixin, FormView):
    template_name = 'core/atualizar_senha.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('home:perfil')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.get_user()
        kwargs['user'] = user
        return kwargs

    def get_user(self):
        pk = self.kwargs.get('pk')
        return User.objects.get(pk=pk)

    def form_valid(self, form):
        form.save()
        user = self.get_user()
        messages.success(self.request, 'Senha atualizada com sucesso!')
        return super().form_valid(form)

    def get_success_url(self):
        pk = self.kwargs.get('pk')
        user = User.objects.get(pk=pk)
        paciente = Usuario.objects.get(usuario=user)
        return reverse_lazy('home:perfil', kwargs={'pk': paciente.pk})

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        user = User.objects.get(pk=pk)
        paciente = Usuario.objects.get(usuario=user)
        contexto['paciente'] = paciente
        return contexto

