# -*- coding: utf-8 -*-
import sublime, sublime_plugin
import os, sys, threading, zipfile, re, pprint, subprocess, binascii, hashlib, shutil
if sys.version_info[0] == 3:
	from .wordpress_xmlrpc import *
	from .wordpress_xmlrpc.methods.posts import *
	from .wordpress_xmlrpc.methods.taxonomies import *
	from .wordpress_xmlrpc.methods.users import *
	from . import common
else:
	from wordpress_xmlrpc import *
	from wordpress_xmlrpc.methods.posts import *
	from wordpress_xmlrpc.methods.taxonomies import *
	from wordpress_xmlrpc.methods.users import *
	import common


ran = False

""" Called by Sublime after Sublime has loaded and is ready to load Sublpress """
def plugin_loaded():
	# log commands for debugging  
	#sublime.log_commands(True)
   
	# show console for debugging      
	#sublime.active_window().run_command("show_panel", { "panel": "console", "toggle": True })
 
	if not os.path.exists(sublime.packages_path() + "/User/Wordpress.sublime-settings"):
		shutil.copyfile(sublime.packages_path() + "/Sublpress/Default Wordpress.sublime-settings", sublime.packages_path() + "/User/Wordpress.sublime-settings")
		sublime.active_window().open_file(sublime.packages_path() + "/User/Wordpress.sublime-settings")

	# initialize some default values
	common.sp_wp = None
	common.sp_settings = sublime.load_settings('Wordpress.sublime-settings')

	#for name, site in common.sp_settings.get('sites').items():
		#if site['salt'] == "":
			#site['salt'] = binascii.b2a_hex(os.urandom(15))

		#matches = re.findall(r'(?i)(?<![a-z0-9])[a-f0-9]{32}(?![a-z0-9])', site['password'])

	global ran
	ran = True

	#print("Sublpress loaded.")


class WordpressManageSites(sublime_plugin.WindowCommand):
	def run(self, *args, **kwargs):
		if not os.path.exists(sublime.packages_path() + "/User/Wordpress.sublime-settings"):
			shutil.copyfile(sublime.packages_path() + "/Sublpress/Default Wordpress.sublime-settings", sublime.packages_path() + "/User/Wordpress.sublime-settings")
			
		self.window.open_file(sublime.packages_path() + "/User/Wordpress.sublime-settings")

class WordpressConnectCall(threading.Thread):
	""" Used to connect Sublime's Wordpress Connect command to wordpress_xmlrpc via theads """
	def __init__(self, url, username, password):
		# initialize some stuff
		self.url = url
		self.username = username
		self.password = password
		self.result = None    
 
		# make sure to initialize the thread
		threading.Thread.__init__(self)

	""" Called by the threading module after being started """
	def run(self):
		# make sure we have a valid wordpress client object
		if common.sp_wp == None:
			common.sp_wp = Client(self.url, self.username, self.password)
			self.result = common.sp_wp
			return
		
		# display an error message
		sublime.error_message('Already connected.')

		# and make sure the result gets set again
		self.result = common.sp_wp

class WordpressApiCall(threading.Thread):  
	""" Used to connect Sublime's Wordpress API commands to wordpress_xmlrpc via theads """
	def __init__(self, method):
		# initialize some stuff
		self.method = method
		self.result = None

		# make sure to initialize the thread
		threading.Thread.__init__(self)     

	""" Called by the threading module after being started """
	def run(self):
		# make sure we have a valid wordpress client object
		if common.sp_wp != None:
			self.result = common.sp_wp.call(self.method)
			return

		# display an error message
		sublime.error_message('Not connected')

		# make sure we don't execute the callback
		self.result = False

if not ran:
	sublime.set_timeout(plugin_loaded, 100)
	ran = True