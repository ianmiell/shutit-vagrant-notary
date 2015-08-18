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
		shutit.send('vagrant destroy -f')
		shutit.send('vagrant up')
		shutit.login(command='vagrant ssh')
		shutit.login(command='sudo su -')
		shutit.install('git curl')
		shutit.send('curl -sSL https://get.docker.com/ | sh')
		shutit.send('curl -L https://github.com/docker/compose/releases/download/1.4.0/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose')
		shutit.send('chmod +x /usr/local/bin/docker-compose')
		shutit.send('''sh -c 'echo "127.0.0.1 notaryserver" >> /etc/hosts' ''',note='Add an entry for the notaryserver to /etc/hosts')
		shutit.send('''sh -c 'echo "127.0.0.1 sandboxregistry" >> /etc/hosts' ''',note='Add an entry for the sandboxregistry to /etc/hosts')
		shutit.send('mkdir notarysandbox')
		shutit.send('cd notarysandbox')
		shutit.send('mkdir notarytest')
		shutit.send('cd notarytest')
		shutit.send_file('Dockerfile','''FROM debian:jessie
ADD https://master.dockerproject.org/linux/amd64/docker /usr/bin/docker
RUN chmod +x /usr/bin/docker && apt-get update && apt-get install -y tree vim git ca-certificates --no-install-recommends
WORKDIR /root
RUN git clone -b trust-sandbox https://github.com/docker/notary.git
RUN cp /root/notary/fixtures/root-ca.crt /usr/local/share/ca-certificates/root-ca.crt
RUN update-ca-certificates
ENTRYPOINT ["bash"]''',note='Create dockerfile for sandbox build')
		shutit.send('docker build -t notarysandbox .',note='Build notarysandbox')
		shutit.send('cd ../../notarysandbox')
		shutit.send('git clone -b trust-sandbox https://github.com/docker/notary.git')
		shutit.send('git clone https://github.com/docker/distribution.git')
		shutit.send('cd notary')
		shutit.send('docker-compose build')
		shutit.send('docker-compose up -d')
		shutit.send('cd ../../notarysandbox/distribution')
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

