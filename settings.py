# -*- coding: utf-8 -*-
import sublime, sublime_plugin
import os, sys, threading, zipfile, re, pprint, subprocess
if sys.version_info[0] == 3:
	from .wordpress_xmlrpc import *
	from .wordpress_xmlrpc.methods.posts import *
	from .wordpress_xmlrpc.methods.taxonomies import *
	from .wordpress_xmlrpc.methods.users import *
	from .wordpress_xmlrpc.methods.options import *
	from . import *
else:
	from wordpress_xmlrpc import *
	from wordpress_xmlrpc.methods.posts import *
	from wordpress_xmlrpc.methods.taxonomies import *
	from wordpress_xmlrpc.methods.users import *
	from wordpress_xmlrpc.methods.options import *
	import common, plugin, command



class WordpressEditSettingsCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that shows the user a list of WordPress settings, allowing the user to cahnge """
	def __init__(self, *args, **kwargs):
		super(WordpressEditSettingsCommand, self).__init__(*args, **kwargs)
		self.wc = command.WordpressCommand()

	""" Called to determine if the command should be enabled """
	def is_enabled(self):
		return self.wc.is_enabled()

	""" Called when the command is ran """
	def run(self, *args, **kwargs):  
		# initialize anything we need for this command
		self.setup_command(*args, **kwargs)

		# initiate any threads we have
		self.wc.init_threads(self.thread_callback)

	""" Called right before the rest of the command runs """
	def setup_command(self, *args, **kwargs):
		# create threaded API call because the http connections could take awhile
		thread = plugin.WordpressApiCall(GetOptions([]))

		# add the thread to the list
		self.wc.add_thread(thread)

	""" Called when a thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		if type(result) is list:
			if len(result) <= 3:
				sublime.status_message('Successfully updated ' + result[0].name + '!')
				return

			self.options = result
			self.panel_options = []

			for option in self.options:
				if not option.read_only:
					self.panel_options.append([option.name, str(option.value) + ' | ' + option.description])

			self.wc.show_quick_panel(self.panel_options, self.panel_callback)

	""" Called when the input panel has received input """
	def doDone(self, value):
		to_update = {self.cur_option.name: value}

		# create threaded API call because the http connections could take awhile
		thread = plugin.WordpressApiCall(SetOptions(to_update))

		# add the thread to the list
		self.wc.add_thread(thread)

		# initialize the threads since we added them after run_command
		self.wc.init_threads(self.thread_callback)

	""" Called when the quick panel is closed """
	def panel_callback(self, index):
		# the user cancelled the panel
		if index == -1:
			return 

		#if index == 0:
			#self.window.run_command('wordpress_new_term')
			#return

		# loop through all of the retreived options
		for option in self.options:

			# check for a matching option name for the selected quick panel option
			if option.name == self.panel_options[index][0]:
				# allow the user to input the new option value
				self.cur_option = option
				self.window.show_input_panel('Change ' + option.name + ' to:', option.value, self.doDone, None, None)
				pass