# -*- coding: utf-8 -*-
import sublime, sublime_plugin
import os, sys, threading, zipfile, re, pprint, subprocess
if sys.version_info[0] == 3:
	from .wordpress_xmlrpc import *
	from .wordpress_xmlrpc.methods.posts import *
	from .wordpress_xmlrpc.methods.taxonomies import *
	from .wordpress_xmlrpc.methods.users import *
	from . import *
else:
	from wordpress_xmlrpc import *
	from wordpress_xmlrpc.methods.posts import *
	from wordpress_xmlrpc.methods.taxonomies import *
	from wordpress_xmlrpc.methods.users import *
	import common, plugin, command

class WordpressInsertCommand(sublime_plugin.TextCommand):
	""" Sublime Text Command to insert content into the active view """
	def __init__(self, *args, **kwargs):
		super(WordpressInsertCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressTextCommand()

	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		return self.wc.is_enabled()

	""" Called when the command is ran """
	def run(self, edit, *args, **kwargs):
		# grab the status keys and view data from the passed args
		title = kwargs.get('title', 'Unknown')
		content = kwargs.get('content', 'No Content')
		status = kwargs.get('status', {})
		syntax = kwargs.get('syntax', 'Packages/HTML/HTML.tmLanguage')

		# create a new file
		self.file = sublime.active_window().new_file()

		# set some initial data
		self.file.set_name(title)
		self.file.set_syntax_file(syntax) # HTML syntax
		self.file.set_scratch(True)

		# loop through the and set the status keys
		for k, v in status.items():	
			self.file.set_status(k, v)

		# insert the content into the new view
		self.file.insert(edit, 0, content)

class WordpressActionsCommand(sublime_plugin.WindowCommand):
	""" Sublime command to display the initial WordPress control panel """
	def __init__(self, *args, **kwargs):
		super(WordpressActionsCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressCommand()

	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		return self.wc.is_enabled()

	""" Called when the command is ran """
	def run(self, *args, **kwargs):
		# initialize anything we need for this command
		self.setup_command(*args, **kwargs)

	""" Called right before the rest of the command runs """
	def setup_command(self, *args, **kwargs):
		self.options = ['Edit Settings', 'Manage all Pages', 'Manage all Posts', 'Manage all Taxonomies', 'Manage a Custom Post Type']
		self.wc.show_quick_panel(self.options, self.panel_callback)

	""" Called when the quick panel has finished """
	def panel_callback(self, index):

		# the user cancelled the panel
		if index == -1:
			return 

		# settings
		if index == 0:
			self.window.run_command('wordpress_edit_settings')

		# manage Pages
		if index == 1:
			self.window.run_command('wordpress_manage_posts', {'post_type': 'page'})
			return

		# manage Posts
		if index == 2:
			self.window.run_command('wordpress_manage_posts', {'post_type': 'post'})

		# manage Taxonomies
		if index == 3:
			self.window.run_command('wordpress_manage_taxes')

		# manage a Custom Post Type
		if index == 4:
			self.window.run_command('wordpress_manage_custom_posts')

class WordpressConnectCommand(sublime_plugin.WindowCommand):
	""" Sublime command to display the list of sites we can connect to """
	def __init__(self, *args, **kwargs):
		super(WordpressConnectCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressCommand()

	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		if common.sp_wp == None:
			return True

		return False

	""" Called when the command is ran """
	def run(self, *args, **kwargs):
		# initialize anything we need for this command
		self.setup_command(*args, **kwargs)

	""" Called right before the rest of the command runs """
	def setup_command(self, *args, **kwargs):
		self.sites = []
		self.options = [] 
		
		# check if we have valid sublpress settings, reload if not
		if common.sp_settings == None:
			common.sp_settings = sublime.load_settings('Wordpress.sublime-settings')
		
		if not common.sp_settings.has('sites') or len(common.sp_settings.get('sites')) <= 0:
			sublime.error_message('No sites configured.')
			return

		# loop through all the sites 
		for name, site in common.sp_settings.get('sites').items():

			# and add them to the quick panel options and our sites container
			self.options.append([name, site['username'] + '@' + site['host']], )
			self.sites.append(site)

		# show the quick panel
		self.wc.show_quick_panel(self.options, self.panel_callback)


	""" Called when the quick panel has finished """
	def panel_callback(self, index):

		# the user cancelled the panel
		if index == -1:
			return 
		site = self.sites[index]

		url = 'http://' + site['host'] + '/xmlrpc.php'

		# create threaded API call because the http connections could take awhile
		thread = plugin.WordpressConnectCall(url, site['username'], site['password'])

		# add the thread to the list
		self.wc.add_thread(thread)

		# initiate any threads we have
		self.wc.init_threads(self.thread_callback)

	""" Called when the thread has finished executing """
	def thread_callback(self, result):
		#pprint.pprint(vars(result))
		# display a status message
		sublime.status_message('Connected to ' + common.sp_wp.url + ' successfully.')

		# show the wordpress actions panel
		self.window.run_command('wordpress_actions')

class WordpressDisconnectCommand(sublime_plugin.WindowCommand):
	def is_enabled(self):
		if common.sp_wp == None:
			return False

		return True

	def run(self, *args, **kwargs):
		common.sp_wp = None
		common.sp_settings = sublime.load_settings('Wordpress.sublime-settings')
