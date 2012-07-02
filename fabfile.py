import boto
from os import path, pardir
from fabric.api import env, sudo, cd, local, run, settings
from fabric.operations import get, put, open_shell
from fabric.colors import green, red
from pprint import pprint

AMI = 'ami-ac9943c5'
KEYPAIR = 'darkangel51'
key_path = path.join(pardir, pardir, "claves_amazon/darkangel51.pem")
env.user = "ubuntu"
env.key_filename = key_path

def create_security_group():
    conn = boto.connect_ec2()
    sec_group = conn.create_security_group("shopply", "Shopply servers security group")
    sec_group.authorize('tcp', 80, 80, '0.0.0.0/0')
    sec_group.authorize('tcp', 22, 22, '0.0.0.0/0')
    sec_group.authorize('tcp', 8080, 8080, '0.0.0.0/0')

def create_ec2_instace(name="shopply", security_group="dwd"):
    """
    Create new instance of AWS EC2
    """
    conn = boto.connect_ec2()
    reservation = conn.run_instances(
        AMI,
        key_name = KEYPAIR,
        instance_type = 't1.micro',
        security_groups = [security_group],
        instance_initiated_shutdown_behavior = "stop"
    )
    
    instance = reservation.instances[0]
    instance.add_tag("Name", name)
    
    
    print "Launching instance: ", instance.public_dns_name
    
def get_instance(name):
    """
    Get an instance using his tag name
    """
    instance = None
    conn = boto.connect_ec2()
    reservations = conn.get_all_instances()
    
    for reservation in reservations:
        if reservation.instances[0].tags['Name'] == name:
            instance = reservation.instances[0]
            
    return instance
    
#env.hosts = ["64.22.109.92"]
    
def install_elasticsearch(name):
    """
    Install elastic search on EC2 instance
    """
    instance = get_instance(name)
    with settings(host_string=instance.public_dns_name):
        # Download the deb package
        run("wget https://github.com/downloads/elasticsearch/elasticsearch/elasticsearch-0.19.7.deb")
        # Installing
        sudo("apt-get -f install")
        sudo("apt-get install openjdk-7-jre")
        sudo("dpkg -i elasticsearch-0.19.7.deb")
        sudo("rm -r elasticsearch-0.19.7.deb")
    
def install_jenkins(name):
    """
    Install Jenkins
    """
    instance = get_instance(name)
    with settings(host_string=instance.public_dns_name):
        # Added to apt-get lists
        sudo('wget -q -O - http://pkg.jenkins-ci.org/debian/jenkins-ci.org.key | sudo apt-key add -')
        sudo("sh -c 'echo deb http://pkg.jenkins-ci.org/debian binary/ > /etc/apt/sources.list.d/jenkins.list'")
        sudo('apt-get -y update')
        sudo('apt-get install -y python-pycurl python-setuptools jenkins git')
        # Install pip
        sudo("easy_install pip")
        # Install virtualenv
        sudo("pip install virtualenv")
        # Install supervisor to manage process
        sudo("pip install supervisor")
    
def create_virtualenv(name):
    """
    Create a new virtualenv
    """
    instance = get_instance(name)
    with settings(host_string=instance.public_dns_name):
        run("virtualenv --distribute venv")
    
def install_requirements():
    instance = get_instance(name)
    with settings(host_string=instance.public_dns_name):
        with cd("helloshopply"):
            with prefix('source ~/venv/bin/activate'):
                run("pip install -r requirements/requirements.txt")
    
    