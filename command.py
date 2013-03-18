# -*- coding: utf-8 -*-
import sublime, sublime_plugin
import os, sys, threading, zipfile, re, pprint, subprocess
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


class WordpressCommand():
	def __init__(self, *args, **kwargs):
		#super(WordpressCommand, self).__init__(*args, **kwargs)

		# initialize empty threads list
		self.threads = []

		# initialize callback
		self.callback = None

		self.prefix = '✓   '

	def is_enabled(self):
		if common.sp_wp == None:
			return False

		return True

	def update_keys(self):
		return
		
	def init_threads(self, callback):
		if not self.threads:
			return 

		self.callback = callback

		# start any threads that may have been added
		for thread in self.threads: 
			if not thread.is_alive():
				thread.start()

		# handle the threads, this is where our callback will be caled
		self.handle_threads(self.threads)

		# reset threads
		self.threads = []

	def add_thread(self, thread):
		self.threads.append(thread)
		
	def unslugify(self, value):
		return ' '.join([s.capitalize() for s in value.split('-')])

	def show_quick_panel(self, options, done):
		sublime.set_timeout(lambda: sublime.active_window().show_quick_panel(options, done), 30)

	def handle_threads(self, threads, i = 0, dir = 1):
		next_threads = []

		# loop through existing threads
		for thread in threads:
			if thread.is_alive():
				next_threads.append(thread)
				continue
			if thread.result == False or thread.result == None:
				continue

			# the thread is finished
			self.callback(thread.result)

		threads = next_threads

		if len(threads):
			# This animates a little activity indicator in the status area
			before = i % 8
			after = (7) - before
			if not after:
				dir = -1
			if not before:
				dir = 1

			i += dir

			sublime.active_window().active_view().set_status('sublpress', 'Sublpress [%s=%s]' % (' ' * before, ' ' * after))

			sublime.set_timeout(lambda: self.handle_threads(threads, i, dir), 100)
			return

		sublime.active_window().active_view().erase_status('sublpress')
  
class WordpressTextCommand():
	def __init__(self, *args, **kwargs):
		#super(WordpressTextCommand, self).__init__(*args, **kwargs)

		# initialize empty threads list
		self.threads = []

		# initialize callback
		self.callback = None

	def is_enabled(self):
		if common.sp_wp == None:
			return False

		return True

	def init_threads(self, callback):
		if not self.threads:
			return 

		self.callback = callback
		
		# start any threads that may have been added
		for thread in self.threads:
			if not thread.is_alive():
				thread.start()

		# handle the threads, this is where our callback will be caled
		self.handle_threads(self.threads)

	def run(self, edit, *args, **kwargs):
		# initialize anything we need for this command
		self.run_command(edit, *args, **kwargs)

		# if we have some threads
		if self.threads:
			self.init_threads()

	def run_command(self, edit, *args, **kwargs):
		return

	def thread_callback(self, result, *args, **kwargs):
		return

	def panel_callback(self, index):
		return

	def handle_threads(self, threads, i = 0, dir = 1):
		next_threads = []

		# loop through existing threads
		for thread in threads:
			if thread.is_alive():
				next_threads.append(thread)
				continue
			if thread.result == False or thread.result == None:
				continue

			# the thread is finished
			self.callback(thread.result)

		threads = next_threads

		if len(threads):
			# This animates a little activity indicator in the status area
			before = i % 8
			after = (7) - before
			if not after:
				dir = -1
			if not before:
				dir = 1

			i += dir

			sublime.active_window().active_view().set_status('sublpress', 'Sublpress [%s=%s]' % (' ' * before, ' ' * after))

			sublime.set_timeout(lambda: self.handle_threads(threads, i, dir), 100)
			return

		sublime.active_window().active_view().erase_status('sublpress')