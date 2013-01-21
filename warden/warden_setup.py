import os
import imp

from django.core import management
import warden_utils
import sys


def main():



    setup_and_check_gentry()
#    # test adding a user
#    # this is the recommended method
#    from sentry.models import User
#
#    from sentry.models import Project, ProjectKey, Team, TeamMember
#    import random
#
#    rid = (random.random()*1000)
#
#    user = User.objects.create(username=('user%d' % rid), password='password')
#    project = Project.objects.create(name=('test%d'%rid), owner=user)
#    print project.key_set.filter(user=user).exists()
#
#    for k in project.key_set.filter(user=user):
#        print k.get_dsn()

def setup_and_check_gentry():
    # get settings module
    n = 'j5_warden_gentry_settings'
    os.environ['DJANGO_SETTINGS_MODULE'] = n
    if not sys.modules.has_key(n):
        imp.load_source(n, warden_utils.normalize_path('~/settings.py'))
    from django.conf import settings


    dbpath = settings.DATABASES['default']['NAME']

    #if file exists:
    try:
        with open(dbpath) as f: pass
        c = raw_input('Database "%s" already exists, shall I delete it? (yes/no): ' % dbpath)
        if c.lower() == 'yes':
            os.remove(dbpath)
        else:
            return
    except IOError:
        pass

    management.execute_from_command_line(['manage.py', 'syncdb','--noinput'])
    management.execute_from_command_line(['manage.py', 'migrate'])

    from sentry.models import Project, ProjectKey, Team, TeamMember, User

    # make a project
    user = User.objects.create_superuser('bob','','bob')
    team = Team.objects.create(name='Test', slug='test', owner=user)
    project = Project.objects.create(name='Test', slug='test', owner=user, team=team)
    print project.key_set.filter(user=user)[0].get_dsn()





if __name__ == '__main__':
    main()