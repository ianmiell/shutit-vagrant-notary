"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule

class vagrant_notary(ShutItModule):


	def build(self, shutit):
		# Some useful API calls for reference. See shutit's docs for more info and options:
		#
		# ISSUING BASH COMMANDS
		# shutit.send(send,expect=<default>) - Send a command, wait for expect (string or compiled regexp)
		#                                      to be seen before continuing. By default this is managed
		#                                      by ShutIt with shell prompts.
		# shutit.multisend(send,send_dict)   - Send a command, dict contains {expect1:response1,expect2:response2,...}
		# shutit.send_and_get_output(send)   - Returns the output of the sent command
		# shutit.send_and_match_output(send, matches) 
		#                                    - Returns True if any lines in output match any of 
		#                                      the regexp strings in the matches list
		# shutit.send_until(send,regexps)    - Send command over and over until one of the regexps seen in the output.
		# shutit.run_script(script)          - Run the passed-in string as a script
		# shutit.install(package)            - Install a package
		# shutit.remove(package)             - Remove a package
		# shutit.login(user='root', command='su -')
		#                                    - Log user in with given command, and set up prompt and expects.
		#                                      Use this if your env (or more specifically, prompt) changes at all,
		#                                      eg reboot, bash, ssh
		# shutit.logout(command='exit')      - Clean up from a login.
		# 
		# COMMAND HELPER FUNCTIONS
		# shutit.add_to_bashrc(line)         - Add a line to bashrc
		# shutit.get_url(fname, locations)   - Get a file via url from locations specified in a list
		# shutit.get_ip_address()            - Returns the ip address of the target
		# shutit.command_available(command)  - Returns true if the command is available to run
		#
		# LOGGING AND DEBUG
		# shutit.log(msg,add_final_message=False) -
		#                                      Send a message to the log. add_final_message adds message to
		#                                      output at end of build
		# shutit.pause_point(msg='')         - Give control of the terminal to the user
		# shutit.step_through(msg='')        - Give control to the user and allow them to step through commands
		#
		# SENDING FILES/TEXT
		# shutit.send_file(path, contents)   - Send file to path on target with given contents as a string
		# shutit.send_host_file(path, hostfilepath)
		#                                    - Send file from host machine to path on the target
		# shutit.send_host_dir(path, hostfilepath)
		#                                    - Send directory and contents to path on the target
		# shutit.insert_text(text, fname, pattern)
		#                                    - Insert text into file fname after the first occurrence of 
		#                                      regexp pattern.
		# shutit.delete_text(text, fname, pattern)
		#                                    - Delete text from file fname after the first occurrence of
		#                                      regexp pattern.
		# shutit.replace_text(text, fname, pattern)
		#                                    - Replace text from file fname after the first occurrence of
		#                                      regexp pattern.
		# ENVIRONMENT QUERYING
		# shutit.host_file_exists(filename, directory=False)
		#                                    - Returns True if file exists on host
		# shutit.file_exists(filename, directory=False)
		#                                    - Returns True if file exists on target
		# shutit.user_exists(user)           - Returns True if the user exists on the target
		# shutit.package_installed(package)  - Returns True if the package exists on the target
		# shutit.set_password(password, user='')
		#                                    - Set password for a given user on target
		shutit.send('mkdir -p ' + shutit.cfg[self.module_id]['vagrant_dir'])
		shutit.send('cd ' + shutit.cfg[self.module_id]['vagrant_dir'])
		if shutit.file_exists('shutit-vagrant-notary',directory=True):
			shutit.send('cd shutit-vagrant-notary')
			shutit.send('git pull')
		else:
			shutit.send('git clone --recursive https://github.com/ianmiell/shutit-vagrant-notary')
			shutit.send('cd shutit-vagrant-notary')
		shutit.send('vagrant destroy -f || /bin/true')
		shutit.send('vagrant up')
		shutit.login(command='vagrant ssh')
		shutit.login(command='sudo su -')
		shutit.install('git curl')
		shutit.send('curl -sSL https://experimental.docker.com/ | sh')
		shutit.send('curl -L https://github.com/docker/compose/releases/download/1.4.0/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose')
		shutit.send('chmod +x /usr/local/bin/docker-compose')
		shutit.send('''sh -c 'echo "127.0.0.1 notaryserver" >> /etc/hosts' ''',note='Adding an entry for the notaryserver to /etc/hosts')
		shutit.send('''sh -c 'echo "127.0.0.1 sandboxregistry" >> /etc/hosts' ''',note='Adding an entry for the sandboxregistry to /etc/hosts')
		shutit.send('mkdir -p notarysandbox')
		shutit.send('cd notarysandbox')
		shutit.send('mkdir -p notarytest')
		shutit.send('cd notarytest')
		shutit.send_file('Dockerfile','''FROM debian:jessie
ADD https://master.dockerproject.org/linux/amd64/docker /usr/bin/docker
RUN chmod +x /usr/bin/docker && apt-get update && apt-get install -y tree vim git ca-certificates --no-install-recommends
WORKDIR /root
RUN git clone -b trust-sandbox https://github.com/docker/notary.git
RUN cp /root/notary/fixtures/root-ca.crt /usr/local/share/ca-certificates/root-ca.crt
RUN update-ca-certificates
ENTRYPOINT ["bash"]''',note='Creating dockerfile for sandbox build')
		shutit.send('docker build -t notarysandbox .',note='Building notarysandbox')
		shutit.send('cd ../../notarysandbox')
		if shutit.file_exists('notary',directory=True):
			shutit.send('rm -rf notary')
		shutit.send('git clone -b trust-sandbox https://github.com/docker/notary.git',note='Getting trust-sandbox notary code')
		if shutit.file_exists('distribution',directory=True):
			shutit.send('rm -rf distribution')
		shutit.send('git clone https://github.com/docker/distribution.git',note='Getting registry/distribution code')
		shutit.send('cd notary')
		shutit.send('docker-compose build',note='Building notary using docker-compose')
		shutit.send('docker-compose up -d',note='Bringing up notary')
		shutit.send('cd ../../notarysandbox/distribution')
		shutit.send('docker build -t sandboxregistry .',note='Building the registry for the sandbox')
		shutit.send('docker rm -f sandboxregistry || /bin/true')
		shutit.send('docker run -d -p 5000:5000 --name sandboxregistry sandboxregistry',note='Running the sandbox registry')
		shutit.send('docker rm -f notarysandbox || /bin/true')
		shutit.send("""docker run -d --name notarysandbox -v /var/run/docker.sock:/var/run/docker.sock --link notary_notaryserver_1:notaryserver --link sandboxregistry:sandboxregistry notarysandbox -c 'sleep infinity'""",note='Logging into the notary sandbox, linked to the notary server')
		shutit.login(command='docker exec -ti notarysandbox bash')
		shutit.send('docker pull alpine',note='Pulling an image to sign')
		shutit.send('docker tag -f alpine sandboxregistry:5000/test/alpine:latest',note='Tagging the image ready to push and sign')
		shutit.send('export DOCKER_CONTENT_TRUST=1',note='Enable the docker trust env variable')
		shutit.send('export DOCKER_CONTENT_TRUST_SERVER=https://notaryserver:4443',note='Telling Docker which server we are trusting (normally defaults to the Docker Hub)')
		sha256 = shutit.send_and_get_output('docker push sandboxregistry:5000/test/alpine:latest',expect='passphrase for new offline key')
		shutit.send('D0ck3rSh0ck3rOFFLINE',expect='passphrase for new offline key')
		shutit.send('D0ck3rSh0ck3rOFFLINE',expect='passphrase for new tagging key')
		shutit.send('D0ck3rSh0ck3rTAGGING',expect='passphrase for new tagging key')
		shutit.send('D0ck3rSh0ck3rTAGGING')
		shutit.send('docker pull sandboxregistry:5000/test/alpine:latest',note='Pulling the image with new metadata from the local registry')
		shutit.logout()
		shutit.login(command='docker exec -it sandboxregistry bash')
		# Can't get output ok into sha256, so let's just poison them all!
		shutit.send('for f in $(ls /var/lib/registry/docker/registry/v2/blobs/sha256); do echo "Evil data" > /var/lib/registry/docker/registry/v2/blobs/sha256/$f/data; done',note='Placing bad data into the registry!')
		shutit.logout()
		shutit.send('docker rmi -f sandboxregistry:5000/test/alpine:latest',note='Removing the image we have locally, just rmi does not work')
		shutit.login(command='docker exec -ti notarysandbox bash')
		shutit.send('export DOCKER_CONTENT_TRUST=1',note='Enable the docker trust env variable')
		shutit.send('export DOCKER_CONTENT_TRUST_SERVER=https://notaryserver:4443',note='Telling Docker which server we are trusting (normally defaults to the Docker Hub)')
		shutit.send('export DOCKER_CONTENT_TRUST=1',note='Enable the docker trust env variable')
		shutit.send('export DOCKER_CONTENT_TRUST_SERVER=https://notaryserver:4443',note='Telling Docker which server we are trusting (normally defaults to the Docker Hub)')
		shutit.send('docker pull sandboxregistry:5000/test/alpine:latest',note='Pulling the image again, it will fail to verify!')
		shutit.logout()
		shutit.logout()
		shutit.logout()
		return True

	def get_config(self, shutit):
		# CONFIGURATION
		# shutit.get_config(module_id,option,default=None,boolean=False)
		#                                    - Get configuration value, boolean indicates whether the item is 
		#                                      a boolean type, eg get the config with:
		# shutit.get_config(self.module_id, 'myconfig', default='a value')
		#                                      and reference in your code with:
		# shutit.cfg[self.module_id]['myconfig']
		import os
		shutit.get_config(self.module_id, 'vagrant_dir', os.path.expanduser('~'), hint='Location of build')
		return True

	def test(self, shutit):
		# For test cycle part of the ShutIt build.
		return True

	def finalize(self, shutit):
		# Any cleanup required at the end.
		return True
	
	def is_installed(self, shutit):
		return False


def module():
	return vagrant_notary(
		'tk.shutit.vagrant_notary.vagrant_notary', 1845506479.00,
		description='',
		maintainer='ian.miell@gmail.com',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','tk.shutit.vagrant.vagrant.vagrant','shutit-library.virtualbox.virtualbox.virtualbox']
	)

