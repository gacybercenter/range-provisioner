
"""
Class for connection groups
"""
import openstack.connection
import yaml
import openstack
import guacamole
from objects.connections import NewConnections, ConnectionGroup
from objects.users import NewUsers

with open('clouds.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)['clouds']['guac']

with open('templates/guac.yaml', 'r', encoding='utf-8') as file:
    guac = yaml.safe_load(file)

ostack_conn = openstack.connect('gcr')

# for ip in local_ip_associations:
#     print(ip)

session = guacamole.session(config['host'],
                            config['data_source'],
                            config['username'],
                            config['password'])

# instances = HeatInstances(ostack_conn, 'zeroday')

# print(instances.addresses)

# conn_group = ConnectionGroup(session, 'group1', 'ROOT', 'ORGANIZATIONAL')
# print(conn_group)
# print(conn_group.create())
# time.sleep(1)
# conn = ConnectionInstance(session, 'ssh', 'ssh', conn_group.identifier)
# time.sleep(1)
# print(conn.create())
# time.sleep(1)
# share = SharingProfile(session, 'ssh', conn.identifier)
# time.sleep(1)
# print(share.create())
# time.sleep(10)
# print(conn_group.delete())

# print(tree.connections)

# print(HeatInstances(ostack_conn, 'playground').addresses)

root_name = 'cyber-range-testing'

new_data = NewConnections(session, ostack_conn, guac, root_name, debug=True)
# new_data.update()
# print(new_data.connections)
# print(new_data.addresses)
# print(new_data.current_connections)

# new_data.update()

# current = CurrentUsers(session, 'CFIC-Capstone')
# print(current.users)

new = NewUsers(session, guac, 'cyber-range-testing', new_data.connections, debug=True)

# new.update()
# print()
# print(new.current_users[1])
# print(new.users[0] == new.current_users[1])

# response = session.update_connection_permissions(
#         'test',
#         '6909',
#         "add",
#         "connection"
# )
# print(response)d
