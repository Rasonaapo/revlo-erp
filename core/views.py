from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from core.models import CustomUser
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required, permission_required

@never_cache
def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is None:
            try:
                # If user is None, check if the user exists for a better error message
                CustomUser.objects.get(email=email)
                return JsonResponse({'status': 'fail', 'message': "Sorry, email and password combination is incorrect"}, status=401)

            except CustomUser.DoesNotExist:
                return JsonResponse({'status': 'fail', 'message': "Oops, user does not exist"}, status=404)
        
        # Log the user in if authentication is successful
        login(request, user)  

        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return JsonResponse({'status': 'success', 'message': 'Login successful'}, status=200)


    return render(request, 'core/login.html')

@login_required
def dashboard(request):
    context = {
        'title':'Dashboard'
    }
    return render(request, 'core/dashboard.html', context)

def logout_user(request):
    logout(request)
    return redirect('login')

def change_password(request):
    return HttpResponse('Change here')

def user_profile(request):
    return HttpResponse('Profile here...')

def disclaimer(request):
    return HttpResponse('Disclaimer here')