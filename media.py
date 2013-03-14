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
		if type(result) is dict:
			self.attachment = result
			#pprint.pprint(vars(result))

			# Display a successful status message
			sublime.status_message('Successfully uploaded ' + self.path + ' to an attachment with id of: ' + self.attachment['id'] + '.')

			#if self.id != "":
			options = ["Assign as Featured Image to Post", "Assign as Featured Image to Page", ]
			self.wc.show_quick_panel(options, self.assign_callback)

		if type(result) is list:
			# save the retreived posts
			self.posts = result
			self.post_options = []

			# loop through all of the retreived posts
			for post in self.posts:
				prefix = 'ID: ' + post.id

				# add the post title the quick panel options
				self.post_options.append([post.title[:50], prefix + post.content[:40]])

			# show the quick panel
			self.wc.show_quick_panel(self.post_options, self.post_panel_callback)

	def assign_callback(self, index):
		if index == -1:
			return
		elif index == 0:
			self.post_type = 'post'
			thread = sublpress.WordpressApiCall(GetPosts({ 'number': 200, 'post_type': 'post' }))
		elif index == 1:
			self.post_type = 'page'
			thread = sublpress.WordpressApiCall(GetPosts({ 'number': 200, 'post_type': 'page' }))

		# add the thread to the list
		self.wc.add_thread(thread)
		self.wc.init_threads(self.thread_callback)

	def post_panel_callback(self, index):
		if index == -1:
			return

		# loop through all of the retreived posts
		for post in self.posts:

			# check for a matching title for the selected quick panel option
			if post.title[:50] == self.post_options[index][0]:

				# show the user actions for this posts
				self.window.run_command('wordpress_assign_featured_image', {'post_id': post.id, 'attachment_id': self.attachment['id'], 'post_type': self.post_type, 'post_title': post.title})

	""" Called when the input panel has received input """
	def doDone(self, path):
		self.path = path

		if not os.path.exists(self.path):
			sublime.error_message('Invalid path.')
			return

		data = {}
		data['name'] = os.path.basename(self.path)
		data['type'] = mimetypes.guess_type(self.path)[0]

		# read the binary file and let the XMLRPC library encode it into base64
		with open(self.path, 'rb') as img:
			data['bits'] = xmlrpc_client.Binary(img.read())

		pprint.pprint(data)

		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(UploadFile(data))

		# add the thread to the list
		self.wc.add_thread(thread)

		# initialize the threads since we added them after run_command
		self.wc.init_threads(self.thread_callback)

class WordpressAssignFeaturedImageCommand(sublime_plugin.WindowCommand):
	""" Sublime Command that renames a WordPress post """
	def __init__(self, *args, **kwargs):
		super(WordpressAssignFeaturedImageCommand, self).__init__(*args, **kwargs)
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
		self.post_id = kwargs.get('post_id')
		self.attachment_id = kwargs.get('attachment_id')
		self.post_type = kwargs.get('post_type')
		self.post_title = kwargs.get('post_title')

		post = WordPressPost()
		post.title = None
		post.thumbnail = self.attachment_id
		post.id = self.post_id
		post.post_type = None

		# create threaded API call because the http connections could take awhile
		thread = sublpress.WordpressApiCall(EditPost(post.id, post))

		# add the thread to the list
		self.wc.add_thread(thread)

		# initialize the threads since we added them after run_command
		self.wc.init_threads(self.thread_callback)

	""" Called when the thread is finished executing """
	def thread_callback(self, result, *args, **kwargs):
		sublime.status_message('Successfully attached the uploaded media.')

		