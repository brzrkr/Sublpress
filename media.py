# -*- coding: utf-8 -*-
import sublime, sublime_plugin
import os, sys, threading, zipfile, re, pprint, subprocess, webbrowser, mimetypes
from wordpress_xmlrpc import *
from wordpress_xmlrpc.methods.posts import *
from wordpress_xmlrpc.methods.taxonomies import *
from wordpress_xmlrpc.methods.users import *  
from wordpress_xmlrpc.methods.media import *  
import common, sublpress, command


class WordpressUploadMediaCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that uploads an image as a WordPress Media Attachment """
	def __init__(self, *args, **kwargs):
		super(WordpressUploadMediaCommand, self).__init__(*args, **kwargs)
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
		# grab the active view
		self.view = self.window.active_view()

		# grab the id and title from the commands arguments, or the current view's status keys
		self.id = kwargs.get('id', self.view.get_status('Post ID'))
		self.title = kwargs.get('title', self.view.get_status('Post Title'))
		self.post_type = kwargs.get('post_type', self.view.get_status('Post Type'))

		# show the input panel to input the name
		self.window.show_input_panel('Path to File', '', self.doDone, None, None)

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		self.attachment = result

		# Display a successful status message
		sublime.status_message('Successfully uploaded ' + self.path + ' to an attachment with id of: ' + self.attachment.id + '.')

	""" Called when the input panel has received input """
	def doDone(self, path):
		self.path = path

		if not os.path.exists(self.path):
			sublime.error_message('Invalid path.')
			return

		data = {}
		data['name'] = os.path.basename(self.path)
		data['type'] = mimetypes.read_mime_types(self.path) or mimetypes.guess_type(self.path)[0]

		# read the binary file and let the XMLRPC library encode it into base64
		with open(self.path, 'rb') as img:
			data['bits'] = xmlrpc_client.Binary(img.read())

		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(UploadFile(data))

		# add the thread to the list
		self.wc.add_thread(thread)

		# initialize the threads since we added them after run_command
		self.wc.init_threads(self.thread_callback)