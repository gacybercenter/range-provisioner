from guacamole import session
from objects.users import CurrentUsers

orgs_to_delete = [
    'comp1313',
    'ncu',
    'ncu_test',
    'netw2334',
]

gconn = session(
    host='https://ncu.gacyberrange.org',
    data_source='mysql',
    username='range_provisioner',
    password='REDACTED'
)

for org in orgs_to_delete:
    current_users = CurrentUsers(gconn, org)
    for user in current_users.users:
        user.delete()
