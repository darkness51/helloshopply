import boto
from os import path, pardir
from fabric.api import env, sudo, cd, local, run, settings, prefix, task
from fabric.operations import get, put, open_shell
from fabric.colors import green, red
from pprint import pprint

AMI = 'ami-ac9943c5'
KEYPAIR = 'darkangel51'
key_path = path.join(pardir, pardir, "claves_amazon/darkangel51.pem")
env.user = "ubuntu"
env.key_filename = key_path

@task
def create_security_group():
    """
    Create an EC2 Security Group
    """
    conn = boto.connect_ec2()
    sec_group = conn.create_security_group("shopply", "Shopply servers security group")
    sec_group.authorize('tcp', 80, 80, '0.0.0.0/0')
    sec_group.authorize('tcp', 22, 22, '0.0.0.0/0')
    sec_group.authorize('tcp', 8080, 8080, '0.0.0.0/0')
    sec_group.authorize('tcp', 9001, 9001, '0.0.0.0/0')

@task
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
    
@task
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
    
@task
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

@task    
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
        sudo('apt-get install -y python-pycurl python-setuptools jenkins git gcc')
        sudo('apt-get build-dep python-crypto')
        # Install pip
        sudo("easy_install pip")
        # Install virtualenv
        sudo("pip install virtualenv")
        # Install supervisor to manage process
        sudo("pip install supervisor")
 
@task   
def create_virtualenv(name):
    """
    Create a new virtualenv
    """
    instance = get_instance(name)
    with settings(host_string=instance.public_dns_name):
        run("virtualenv --distribute venv")

@task    
def install_requirements(name):
    """
    Install project requirements using pip
    """
    instance = get_instance(name)
    with settings(host_string=instance.public_dns_name):
        with cd("helloshopply"):
            with prefix('source ~/venv/bin/activate'):
                run("pip install -r requirements/requirements.txt")
                
@task
def create_ssh_key(name):
    """
    Create ssh rsa key
    """
    instance = get_instance(name)
    with settings(host_string=instance.public_dns_name):
        run('ssh-keygen -C "caguilar@dwdandsolutions.com" -t rsa')
        print "Authorize this on github \n"
        run("cat ~/.ssh/id_rsa.pub")

@task           
def config_repo(name):
    """
    Config git repo as ubuntu user
    """
    instance = get_instance(name)
    with settings(host_string=instance.public_dns_name):
        run('git config --global user.name "Carlos aguilar"')
        run('git config --global user.email caguilar@dwdandsolutions.com')
        run('git clone git@github.com:darkness51/helloshopply.git')

@task    
def configure_supervisord(instance_name):
    """
    Configure supervisord to daemonize the tornado script
    """
    instance = get_instance(instance_name)
    with settings(host_string=instance.public_dns_name):
        sudo("cp ~/helloshopply/configs/supervisord /etc/init.d/")
        sudo("chmod +x /etc/init.d/supervisord")
        sudo("cp ~/helloshopply/configs/supervisord.conf /etc/")
        run("mkdir -p ~/helloshopply/logs/")
        sudo("update-rc.d supervisord defaults")
        sudo("service supervisord start")
     
@task   
def update_supervisord_config(instance_name):
    """
    Update supervisord config file
    """
    instance = get_instance(instance_name)
    with settings(host_string=instance.public_dns_name):
        sudo("cp ~/helloshopply/configs/supervisord.conf /etc/")
        sudo("service supervisord stop")
        sudo("service supervisord start")
     
@task   
def install_nginx(instance_name):
    """
    Install and configure Nginx
    """
    instance = get_instance(instance_name)
    with settings(host_string=instance.public_dns_name):
        sudo("apt-get install -y nginx")
        sudo("apt-get install libcurl4-openssl-dev")
        sudo("cp ~/helloshopply/configs/shopply /etc/nginx/sites-available/")
        with cd("/etc/nginx/sites-enabled/"):
            sudo("ln -s /etc/nginx/sites-available/shopply")
            
        sudo("service nginx restart")
    
@task
def update_repo(instance_name):
    """
    Update the repo and restart supervisord service
    """
    instance = get_instance(instance_name)
    with settings(host_string=instance.public_dns_name):
        with cd("helloshopply"):
            run("git pull")
            sudo("supervisorctl restart shopply")
     
@task       
def configure_elasticsearch(instance_name):
    """
    Replace configuration for elasticsearch
    """
    instace = get_instance(instance_name)
    with settings(host_string=instance.public_dns_name):
        sudo("service elasticsearch stop")
        sudo("cp ~/helloshopply/configs/elasticsearch /etc/init.d/")
        sudo("chmod +x /etc/init.d/elasticsearch")
        sudo("cp ~/helloshopply/configs/elasticsearch.yml /etc/elasticsearch/")
        sudo("service elasticsearch start")
     
@task   
def install_mongodb(instance_name):
    """
    Install mongodb on server
    """
    instance = get_instance(instance_name)
    with settings(host_string=instance.public_dns_name):
        sudo("apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10")
        sudo('echo "\ndeb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen" >> /etc/apt/sources.list')
        sudo("apt-get update")
        sudo("apt-get install mongodb-10gen")
        
@task
def install_graylog2(instance_name):
    """
    Install graylog2 server and web interface
    """
    instance = get_instance(instance_name)
    with settings(host_string=instance.public_dns_name):
        # Installing Graylog2 server
        with cd("/opt"):
            sudo("curl  http://cloud.github.com/downloads/Graylog2/graylog2-server/graylog2-server-0.9.6.tar.gz | tar zxv")
            sudo("ln -s graylog2-server-0.9.6 graylog2-server")
            sudo("cp /opt/graylog2-server/graylog2.conf{.example,}")
            
        with cd("/etc"):
            sudo("ln -s /opt/graylog2-server/graylog2.conf graylog2.conf")
            
        sudo("sed -i -e 's|mongodb_useauth = true|mongodb_useauth = false|' /opt/graylog2-server/graylog2.conf")
        sudo("cp ~/helloshopply/configs/graylog2-server /etc/init.d/")
        sudo("chmod +x /etc/init.d/graylog2-server")
        sudo("update-rc.d graylog2-server defaults")
        
        # Installing Graylog2 Web Interface
        with cd("/opt"):
            sudo("curl  http://cloud.github.com/downloads/Graylog2/graylog2-web-interface/graylog2-web-interface-0.9.6.tar.gz | tar zxv")
            sudo("ln -s graylog2-web-interface-0.9.6 graylog2-web-interface")
            sudo("apt-get install ruby1.9.3")
            sudo("useradd graylog2 -d /opt/graylog2-web-interface")
            sudo("chown -R graylog2:graylog2 /opt/graylog2-web-interface*")
            sudo("usermod -G admin graylog2")
            with cd("/opt/graylog2-web-interface"):
                sudo("gem install bundler --no-ri --no-rdoc")
                sudo("bundle install")
        