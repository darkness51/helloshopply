import boto
from os import path, pardir
from fabric.api import env, sudo, cd, local
from fabric.operations import get, put, open_shell
from fabric.colors import green, red
from pprint import pprint

AMI = 'ami-ac9943c5'
KEYPAIR = 'darkangel51'
key_path = path.join(pardir, pardir, "claves_amazon/darkangel51.pem")
env.user = "ubuntu"
env.key_filename = key_path

def create_ec2_instace(name="shopply"):
    """
    Create new instance of AWS EC2
    """
    conn = boto.connect_ec2()
    reservation = conn.run_instances(
        AMI,
        key_name = KEYPAIR,
        instance_type = 't1.micro',
        security_groups = ["dwd"],
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
    
def install_elasticsearch():
    """
    Install elastic search on EC2 instance
    """
    # Get instance first
    instance = get_instance("shopply")
    # Add instance public dns to hosts environment
    env.hosts.append(instance.public_dns_name)
    # Download the deb package
    run("wget https://github.com/downloads/elasticsearch/elasticsearch/elasticsearch-0.19.7.deb")
    # Installing
    sudo("dpkg -i elasticsearch-0.19.7.deb")
    
def install_jenkins():
    """
    Install Jenkins
    """
    sudo('wget -q -O - http://pkg.jenkins-ci.org/debian/jenkins-ci.org.key | sudo apt-key add -')
    sudo("sh -c 'echo deb http://pkg.jenkins-ci.org/debian binary/ > /etc/apt/sources.list.d/jenkins.list'")
    sudo('apt-get -y update')
    sudo('apt-get install -y python-pycurl python-setuptools jenkins git')
    sudo("easy_install pip")
    sudo("pip install virtualenv")
    
def create_virtualenv():
    run("virtualenv --distribute venv")
    
def install_requirements():
    with cd("helloshopply"):
        with prefix('source ~/venv/bin/activate'):
            run("pip install -r requirements/requirements.txt")
    
    
    
    