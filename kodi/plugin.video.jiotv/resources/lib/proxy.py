from __future__ import unicode_literals
_B='Content-Length'
_A='File not found'
from http.server import SimpleHTTPRequestHandler
import os
from urllib.parse import parse_qs,urlparse
from xbmcvfs import translatePath
import xbmcaddon
from resources.lib.utils import login,sendOTPV2
from codequick import Script
ADDON=xbmcaddon.Addon()
ADDON_PATH=ADDON.getAddonInfo('path')
class JioTVProxy(SimpleHTTPRequestHandler):
	def do_GET(A):
		C=urlparse(A.path).path
		if C=='/':
			A.send_response(200);D=os.path.join(translatePath(ADDON_PATH),'resources','login.html')
			try:B=open(D,'rb')
			except IOError:A.send_error(404,_A);return
			A.send_header('Content-type','text/html');E=os.fstat(B.fileno());A.send_header(_B,str(E.st_size));A.end_headers();A.wfile.write(bytes(B.read()));B.close();return
		else:A.send_error(404,_A)
	def do_POST(B):
		J='mobile';I='password';F='type';D='otp'
		if B.path=='/login':
			K=B.rfile.read(int(B.headers[_B]));A=parse_qs(K.decode('utf-8'));C=None;Script.log(A,lvl=Script.INFO)
			try:
				if A.get(F)[0]==I:C=login(A.get('username')[0],A.get(I)[0])
				elif A.get(F)[0]==D:
					G=A.get(J)[0]
					if A.get(D):C=login(G,A.get(D)[0],mode=D)
					else:C=sendOTPV2(G)
				else:C='Invalid Type'
			except Exception as H:Script.log(H,lvl=Script.ERROR);C=str(H)
			if C:E='/?error='+str(C)
			elif A.get(F)[0]==D and A.get(D)is None:E='/?otpsent='+A.get(J)[0]
			else:E='/?success'
			B.send_response(302);B.send_header('Location',E);B.end_headers()
		else:B.send_error(404,_A)