from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView


class CustomLoginView(LoginView):
    def form_valid(self, form):
        print('Redicionamento de Login')
        usuario = self.request.user.usuario
        if usuario.funcionario:
            return redirect('home:painel')
        elif usuario.doutor:
            return redirect('home:painel')
        elif usuario.adm:
            return redirect('home:painel')
        else:
            return redirect('home:indice')
