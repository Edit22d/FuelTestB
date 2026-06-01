from django.shortcuts import render
from .permissions import role_required


@role_required('super_admin', 'sub_admin')
def dashboard_home(request):
    return render(request, 'dashboard/pages/home.html', {
        'page': 'dashboard',
    })


@role_required('super_admin', 'sub_admin')
def dashboard_stations(request):
    return render(request, 'dashboard/pages/stations.html', {
        'page': 'stations',
    })


@role_required('super_admin')
def dashboard_users(request):
    return render(request, 'dashboard/pages/users.html', {
        'page': 'users',
    })


def station_table_partial(request):
    return render(request, 'dashboard/partials/table_body.html', {
        'stations': [],
    })


def toast_message(request, message_type='success', message=''):
    return render(request, 'dashboard/partials/toast.html', {
        'type': message_type,
        'message': message,
    })