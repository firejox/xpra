#!/usr/bin/env python
# This file is part of Xpra.
# Copyright (C) 2016 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os
import shutil
import unittest
import tempfile
from xpra.exit_codes import EXIT_OK, EXIT_CONNECTION_LOST
from tests.unit.server_test_util import ServerTestUtil, log


class ServerSocketsTest(ServerTestUtil):

	@classmethod
	def start_server(cls, *args):
		server_proc = cls.run_xpra(["xpra", "start", "--no-daemon"]+list(args))
		assert cls.pollwait(server_proc, 5) is None, "server failed to start, returned %s" % server_proc.poll()
		return server_proc

	def _test_connect(self, server_args=[], auth="none", client_args=[], password=None, uri_prefix=":", exit_code=0):
		display_no = self.find_free_display_no()
		display = ":%s" % display_no
		log("starting test server on %s", display)
		server = self.start_server(display, "--auth=%s" % auth, *server_args)
		#we should always be able to get the version:
		uri = uri_prefix + str(display_no)
		client = self.run_xpra(["xpra", "version", uri] + server_args)
		assert self.pollwait(client, 5)==0, "version client failed to connect"
		if client.poll() is None:
			client.terminate()
		#try to connect
		cmd = ["xpra", "info", uri] + client_args
		f = None
		if password:
			f = self._temp_file(password)
			cmd += ["--password-file=%s" % f.name]
		client = self.run_xpra(cmd)
		r = self.pollwait(client, 5)
		if f:
			f.close()
		assert r==exit_code, "expected info client to return %s but got %s" % (exit_code, client.poll())
		if client.poll() is None:
			client.terminate()
		server.terminate()

	def Xtest_default_socket(self):
		self._test_connect([], "allow", [], "hello", "", EXIT_OK)

	def test_bind_tmpdir(self):
		try:
			tmpdir = tempfile.mkdtemp(suffix='xpra')
			#run with this extra socket-dir:
			args = ["--socket-dir=%s" % tmpdir]
			#tell the client about it, or don't - both cases should work:
			#(it will also use the default socket dirs)
			self._test_connect(args, "none", args, None, ":", EXIT_OK)
			self._test_connect(args, "none", [], None, ":", EXIT_OK)
			#now run with ONLY this socket dir:
			args = ["--socket-dirs=%s" % tmpdir]
			#tell the client:
			self._test_connect(args, "none", args, None, ":", EXIT_OK)
			#if the client doesn't know about the socket location, it should fail:
			self._test_connect(args, "none", [], None, ":", EXIT_CONNECTION_LOST)
			#use the exact path to the socket:
			from xpra.platform.dotxpra_common import PREFIX
			self._test_connect(args, "none", [], None, "socket:"+os.path.join(tmpdir, PREFIX))
		finally:
			shutil.rmtree(tmpdir)


def main():
	if os.name=="posix":
		unittest.main()


if __name__ == '__main__':
	main()
