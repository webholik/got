from fabric.contrib.files import append, exists, sed
from fabric.api import env, local, run
import random

REPO_URL = 'https://github.com/webholik/got.git'


def deploy():
    site_folder = f'/home/{env.user}/sites/{env.host}'
    source_folder = site_folder + '/source'
    _create_directory_substructure_if_necessary(site_folder)
    _get_latest_source(source_folder)
    _update_settings(source_folder, env.host)
    _update_virtualenv(source_folder)
    _update_static_files(source_folder)
    _update_database(source_folder)
    _restart_gunicorn(env.host)


def _create_directory_substructure_if_necessary(site_folder):
    for folder in ('database', 'static', 'source', 'virtualenv'):
        run(f'mkdir -p {site_folder}/{folder}')


def _get_latest_source(source_folder):
    if exists(source_folder + '/.git'):
        run(f'cd {source_folder} && git fetch')
    else:
        run(f'git clone {REPO_URL} {source_folder}')

    current_commit = local('git log -n 1 --format="%H"', capture=True)
    run(f'cd {source_folder} && git reset --hard {current_commit}')


def _update_settings(source_folder, site_url):
    settings_path = source_folder + '/got/settings.py'
    sed(settings_path, 'DEBUG = True', 'DEBUG = False')
    sed(settings_path, 'ALLOWED_HOSTS = .+$',
        f'ALLOWED_HOSTS = ["{site_url}"]')
    secret_key_file = source_folder + '/got/secret_key.py'
    if not exists(secret_key_file):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
        append(secret_key_file, f'SECRET_KEY = "{key}"')
    append(settings_path, '\nfrom .secret_key import SECRET_KEY')


def _update_virtualenv(source_folder):
    venv_folder = source_folder + '/../virtualenv'
    if not exists(venv_folder + '/bin/pip'):
        run(f'python3 -m venv {venv_folder}')
    run(f'{venv_folder}/bin/pip install -r {source_folder}/requirements.txt')


def _update_static_files(source_folder):
    run(f'cd {source_folder}'
        '&& ../virtualenv/bin/python manage.py collectstatic --noinput')


def _update_database(source_folder):
    run(f'cd {source_folder}'
        '&& ../virtualenv/bin/python manage.py migrate --noinput')

def _restart_gunicorn(site_url):
    service_name = 'gunicorn-' + site_url + '.service'
    run(f'sudo systemctl restart {service_name}')
