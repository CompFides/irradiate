# IRRADIATE
Run Atomic Red Team techniques from Ansible against Linux or Windows based systems to test detection capabilities.

## Setup
Copy irradiate directory to /etc/ansible/roles/<br>
Copy irradiate.yml playbook to /etc/ansible/<br>
Copy irradiate_hosts file to /etc/ansible/<br>
Pull Atomic Red Team git and save to /etc/ansible/roles/irradiate/files/<br>

## Configure Hosts to Test
Edit irradiate_hosts<br>

## Customize Techniques
Techniques can have thier input_arguments and executors customized. <br>
Create / edit technique yaml file and save ../etc/ansible/roles/irradiate/files/custom/ <br>
2 example customizations are included



