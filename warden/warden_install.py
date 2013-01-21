import os
import imp
import warden_utils
import sys


def main():


    # assume installation has happened before this

    n = 'j5_warden_gentry_settings'
    os.environ['DJANGO_SETTINGS_MODULE'] = n
    if not sys.modules.has_key(n):
        imp.load_source(n, warden_utils.normalize_path('~/settings.py'))
    from django.conf import settings

    print settings.DATABASES['default']['NAME']

    # test adding a user
    # this is the recommended method
    from sentry.models import User

    try:
        User.objects.using('default').get(username='user')
    except User.DoesNotExist:
        User.objects.db_manager('default').create_user('user','','password')
    else:
        print("Error: 'user' username is already taken.")

    from sentry.models import Project, ProjectKey
    import random

    pname = 'Project%d' % random.random()*100

    try:
        Project.objects.using('default').get(name=pname)
    except Project.DoesNotExist:
        Project.objects.using('default').create(name=pname)
    else:
        print("Error: Project name is already taken.")




if __name__ == '__main__':
    main()