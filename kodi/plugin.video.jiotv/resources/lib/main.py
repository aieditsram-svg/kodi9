from __future__ import unicode_literals
_A6='isCatchupAvailable'
_A5='channel_order'
_A4='channelIdForRedirect'
_A3='episode_desc'
_A2='description'
_A1='showGenre'
_A0='mediatype'
_z='episodeguide'
_y='tvshowtitle'
_x='originaltitle'
_w='clearlogo'
_v='clearart'
_u='Languages'
_t='Genres'
_s='/resources/lib/main:show_featured'
_r='utf-8'
_q='JioTV'
_p='headers'
_o='channel_name'
_n='languageIdMapping'
_m='channelCategoryMapping'
_l='end'
_k='begin'
_j='programId'
_i=' %I:%M %p ]   %a'
_h='    [ %I:%M %p -'
_g='genre'
_f='enabled'
_e='addonid'
_d='Addons.SetAddonEnabled'
_c='mobile'
_b='channelCategoryId'
_a='Extra'
_Z='%Y%m%dT%H%M%S'
_Y='episode_num'
_X='duration'
_W='director'
_V='episode'
_U='showtime'
_T='title'
_S='info'
_R='channelLanguageId'
_Q='endEpoch'
_P='fanart'
_O=True
_N=None
_M='thumb'
_L='art'
_K='srno'
_J='logoUrl'
_I='icon'
_H='showname'
_G='episodePoster'
_F='params'
_E='startEpoch'
_D=False
_C='callback'
_B='label'
_A='channel_id'
from xbmcaddon import Addon
from xbmc import executebuiltin,log,LOGINFO
from xbmcgui import Dialog,DialogProgress
from codequick import Route,run,Listitem,Resolver,Script
from codequick.utils import keyboard
from codequick.script import Settings
from codequick.storage import PersistentDict
from resources.lib.utils import getTokenParams,getHeaders,isLoggedIn,login as ULogin,logout as ULogout,check_addon,sendOTPV2,get_local_ip,getChannelHeaders,getChannelHeadersWithHost,quality_to_enum,_setup,kodi_rpc,Monitor,getCachedChannels,getCachedDictionary,cleanLocalCache,getFeatured
from resources.lib.constants import GET_CHANNEL_URL,IMG_CATCHUP,PLAY_URL,IMG_CATCHUP_SHOWS,CATCHUP_SRC,M3U_SRC,EPG_SRC,M3U_CHANNEL,IMG_CONFIG,EPG_PATH,ADDON,ADDON_ID
import urlquick
from uuid import uuid4
from urllib.parse import urlencode
import inputstreamhelper
from time import time,sleep
from datetime import datetime,timedelta,date
import m3u8,requests,gzip,xml.etree.ElementTree as ET,os
monitor=Monitor()
@Route.register
def root(plugin):
	A='cms/TKSS_Carousal1.jpg';yield Listitem.from_dict(**{_B:'Featured',_L:{_M:IMG_CATCHUP_SHOWS+A,_I:IMG_CATCHUP_SHOWS+A,_P:IMG_CATCHUP_SHOWS+A},_C:Route.ref(_s)})
	for B in[_t,_u]:yield Listitem.from_dict(**{_B:B,_C:Route.ref('/resources/lib/main:show_listby'),_F:{'by':B}})
@Route.register
def show_featured(plugin,id=_N):
	G='showStatus';F='id';D='data'
	for C in getFeatured():
		if id:
			if int(C.get(F,0))==int(id):
				H=C.get(D,[])
				for A in H:
					B={_L:{_M:IMG_CATCHUP_SHOWS+A.get(_G,''),_I:IMG_CATCHUP_SHOWS+A.get(_G,''),_P:IMG_CATCHUP_SHOWS+A.get(_G,''),_v:IMG_CATCHUP+A.get(_J,''),_w:IMG_CATCHUP+A.get(_J,'')},_S:{_x:A.get(_H),_y:A.get(_H),_g:A.get(_A1),'plot':A.get(_A2),_z:A.get(_A3),_V:0 if A.get(_Y)==-1 else A.get(_Y),'cast':A.get('starCast','').split(', '),_W:A.get(_W),_X:A.get(_X)*60,'tag':A.get('keywords'),_A0:'movie'if A.get('channel_category_name')=='Movies'else _V}}
					if A.get(G)=='Now':B[_B]=B[_S][_T]=A.get(_H,'')+' [COLOR red] [ LIVE ] [/COLOR]';B[_C]=play;B[_F]={_A:A.get(_A)};yield Listitem.from_dict(**B)
					elif A.get(G)=='future':E=datetime.fromtimestamp(int(A.get(_E,0)*.001)).strftime(_h)+datetime.fromtimestamp(int(A.get(_Q,0)*.001)).strftime(_i);B[_B]=B[_S][_T]=A.get(_H,'')+' [COLOR green]%s[/COLOR]'%E;B[_C]='';yield Listitem.from_dict(**B)
					elif A.get(G)=='catchup':E=datetime.fromtimestamp(int(A.get(_E,0)*.001)).strftime(_h)+datetime.fromtimestamp(int(A.get(_Q,0)*.001)).strftime(_i);B[_B]=B[_S][_T]=A.get(_H,'')+' [COLOR yellow]%s[/COLOR]'%E;B[_C]=play;B[_F]={_A:A.get(_A),_U:A.get(_U,'').replace(':',''),_K:datetime.fromtimestamp(int(A.get(_E,0)*.001)).strftime('%Y%m%d'),_j:A.get(_K,''),_k:datetime.utcfromtimestamp(int(A.get(_E,0)*.001)).strftime(_Z),_l:datetime.utcfromtimestamp(int(A.get(_Q,0)*.001)).strftime(_Z)};yield Listitem.from_dict(**B)
		else:yield Listitem.from_dict(**{_B:C.get('name'),_L:{_M:IMG_CATCHUP_SHOWS+C.get(D,[{}])[0].get(_G),_I:IMG_CATCHUP_SHOWS+C.get(D,[{}])[0].get(_G),_P:IMG_CATCHUP_SHOWS+C.get(D,[{}])[0].get(_G)},_C:Route.ref(_s),_F:{F:C.get(F)}})
@Route.register
def show_listby(plugin,by):
	B=getCachedDictionary();E=B.get(_m);F=B.get(_n);C=list(F.values());C.append(_a);G={_t:E.values(),_u:C}
	for A in G[by]:D=IMG_CONFIG[by].get(A,{}).get('tvImg','');H=IMG_CONFIG[by].get(A,{}).get('promoImg','');yield Listitem.from_dict(**{_B:A,_L:{_M:D,_I:D,_P:H},_C:Route.ref('/resources/lib/main:show_category'),_F:{'categoryOrLang':A,'by':by}})
def is_lang_allowed(langId,langMap):
	B=langMap;A=langId
	if A in B.keys():return Settings.get_boolean(B[A])
	else:return Settings.get_boolean(_a)
def is_genre_allowed(id,map):
	if id in map.keys():return Settings.get_boolean(map[id])
	else:return _D
def isPlayAbleLang(each,LANG_MAP):return not each.get(_A4)and is_lang_allowed(str(each.get(_R)),LANG_MAP)
def isPlayAbleGenre(each,GENRE_MAP):return not each.get(_A4)and is_genre_allowed(str(each.get(_b)),GENRE_MAP)
@Route.register
def show_category(plugin,categoryOrLang,by):
	C=categoryOrLang;I=getCachedChannels();E=getCachedDictionary();D=E.get(_m);B=E.get(_n)
	def J(x):
		A=by.lower()[:-1]
		if A==_g:return D[str(x.get(_b))]==C and isPlayAbleLang(x,B)
		elif C==_a:return str(x.get(_R))not in B.keys()and isPlayAbleGenre(x,D)
		else:
			if str(x.get(_R))not in B.keys():return _D
			return B[str(x.get(_R))]==C and isPlayAbleGenre(x,D)
	try:
		F=list(filter(J,I))
		if len(F)<1:yield Listitem.from_dict(**{_B:'No Results Found, Go Back',_C:show_listby,_F:{'by':by}})
		else:
			for A in F:
				if Settings.get_boolean('number_toggle'):K=int(A.get(_A5))+1;G=str(K)+' '+A.get(_o)
				else:G=A.get(_o)
				H=Listitem.from_dict(**{_B:G,_L:{_M:IMG_CATCHUP+A.get(_J),_I:IMG_CATCHUP+A.get(_J),_P:IMG_CATCHUP+A.get(_J),_w:IMG_CATCHUP+A.get(_J),_v:IMG_CATCHUP+A.get(_J)},_C:play,_F:{_A:A.get(_A)}})
				if A.get(_A6):H.context.container(show_epg,'Catchup',0,A.get(_A))
				yield H
	except Exception as L:Script.notify('Error',L);monitor.waitForAbort(1);return _D
@Route.register
def show_epg(plugin,day,channel_id):
	D=channel_id;F=urlquick.get(CATCHUP_SRC.format(day,D),verify=_D,max_age=-1).json();G=sorted(F['epg'],key=lambda show:show[_E],reverse=_D);H='[COLOR red] [ LIVE ] [/COLOR]'
	for A in G:
		B=int(time()*1000)
		if not A['stbCatchupAvailable']or A[_E]>B:continue
		I=A[_E]<B and A[_Q]>B;E='   '+H if I else datetime.fromtimestamp(int(A[_E]*.001)).strftime(_h)+datetime.fromtimestamp(int(A[_Q]*.001)).strftime(_i);yield Listitem.from_dict(**{_B:A[_H]+E,_L:{_M:IMG_CATCHUP_SHOWS+A[_G],_I:IMG_CATCHUP_SHOWS+A[_G],_P:IMG_CATCHUP_SHOWS+A[_G]},_C:play,_S:{_T:A[_H]+E,_x:A[_H],_y:A[_H],_g:A[_A1],'plot':A[_A2],_z:A.get(_A3),_V:0 if A[_Y]==-1 else A[_Y],'cast':A['starCast'].split(', '),_W:A[_W],_X:A[_X]*60,'tag':A['keywords'],_A0:_V},_F:{_A:A.get(_A),_U:A.get(_U,'').replace(':',''),_K:datetime.fromtimestamp(int(A.get(_E,0)*.001)).strftime('%Y%m%d'),_j:A.get(_K,''),_k:datetime.utcfromtimestamp(int(A.get(_E,0)*.001)).strftime(_Z),_l:datetime.utcfromtimestamp(int(A.get(_Q,0)*.001)).strftime(_Z)}})
	if int(day)==0:
		for C in range(-1,-7,-1):J='Yesterday'if C==-1 else(date.today()+timedelta(days=C)).strftime('%A %d %B');yield Listitem.from_dict(**{_B:J,_C:Route.ref('/resources/lib/main:show_epg'),_F:{'day':C,_A:D}})
@Resolver.register
@isLoggedIn
def play(plugin,channel_id,showtime=_N,srno=_N,programId=_N,begin=_N,end=_N):
	a='user-agent';Z='Manual';Y='__hdnea__';X='stream_type';W='com.widevine.alpha';R=showtime;Q=channel_id;P='cookie';K='?';J='result';F='mpd'
	try:
		b=inputstreamhelper.Helper(F,drm=W);c=b.check_inputstream()
		if not c:return
		A={_A:int(Q),X:'Seek'};S=_D
		if R and srno:S=_O;A[_U]=R;A[_K]=srno;A[X]='Catchup';A[_j]=programId;A[_k]=begin;A[_l]=end;Script.log(str(A),lvl=Script.INFO)
		C=getHeaders();C['channelid']=str(Q);C[_K]=str(uuid4())if _K not in A else A[_K];d=Settings.get_boolean('enablehost');e=urlquick.post(GET_CHANNEL_URL,json=A,verify=_D,headers=getChannelHeadersWithHost()if d else getChannelHeaders(),max_age=-1,raise_for_status=_O);D=e.json();L={};G=D.get(J,'').split(K)[0].split('/')[-1];L[_M]=L[_I]=IMG_CATCHUP+G.replace('.m3u8','.png');T=Y+D.get(J,'').split(Y)[-1];C[P]=T;B=D.get(J,'');H=Settings.get_string('quality');M='adaptive';I=Settings.get_boolean('usempd')and D.get(F,_D)
		if I:
			U=C;U['Content-type']='application/octet-stream'
			if Settings.get_boolean('mpdnotice'):Script.notify('Notice!','Using the Experimental MPD URL',icon=Script.NOTIFY_INFO)
			B=D.get(F,'').get(J,'');f={'license_server_url':D.get(F,'').get('key',''),_p:urlencode(U),'post_data':'H{SSM}','response_data':''}
		if H=='Ask-me':M='ask-quality'
		if H==Z:M='manual-osd'
		if not I and not H==Z:
			N={};N[a]=C[a];N[P]=T;g=urlquick.get(B,headers=N,verify=_D,max_age=-1,raise_for_status=_O);h=g.text;E=m3u8.loads(h)
			if E.is_variant and(E.version is _N or E.version<7):
				V=quality_to_enum(H,len(E.playlists))
				if S:
					O=E.playlists[V].uri
					if K in O:B=B.split(K)[0].replace(G,O)
					else:B=B.replace(G,O.split(K)[0])
					del C[P]
				else:B=B.replace(G,E.playlists[V].uri)
		Script.log(B,lvl=Script.INFO);return Listitem().from_dict(**{_B:plugin._title,_L:L,_C:B+'|verifypeer=false','properties':{'IsPlayable':_O,'inputstream':'inputstream.adaptive','inputstream.adaptive.stream_selection_type':M,'inputstream.adaptive.chooser_resolution_secure_max':'4K','inputstream.adaptive.manifest_headers':urlencode(C),'inputstream.adaptive.manifest_type':F if I else'hls','inputstream.adaptive.license_type':W,'inputstream.adaptive.license_key':'|'.join(f.values())if I else'|'+urlencode(C)+'|R{SSM}|'}})
	except Exception as i:Script.notify('Error while playback , Check connection',i);return _D
@Script.register
def login(plugin):
	F='Login';C=Dialog().yesno(F,'Select Login Method',yeslabel='Keyboard',nolabel='WEB')
	if C==1:
		D=Dialog().yesno(F,'Select Login Type',yeslabel='OTP',nolabel='Password')
		if D==1:
			A=Settings.get_string(_c)
			if not A or len(A)!=10:A=Dialog().numeric(0,'Enter your Jio mobile number');ADDON.setSetting(_c,A)
			E=sendOTPV2(A)
			if E:Script.notify('Login Error',E);return
			G=Dialog().numeric(0,'Enter OTP');ULogin(A,G,mode='otp')
		elif D==0:H=keyboard('Enter your Jio mobile number or email');I=keyboard('Enter your password',hidden=_O);ULogin(H,I)
	elif C==0:
		B=DialogProgress();B.create(_q,'Visit [B]http://%s:48996/[/B] to login'%get_local_ip())
		for J in range(120):
			sleep(1)
			with PersistentDict(_p)as K:L=K.get(_p)
			if L or B.iscanceled():break
			B.update(J)
		B.close()
@Script.register
def setmobile(plugin):A=Settings.get_string(_c);B=Dialog().numeric(0,'Update Jio mobile number',A);kodi_rpc(_d,{_e:ADDON_ID,_f:_D});ADDON.setSetting(_c,B);kodi_rpc(_d,{_e:ADDON_ID,_f:_O});monitor.waitForAbort(1);Script.notify('Jio number set','')
@Script.register
def applyall(plugin):kodi_rpc(_d,{_e:ADDON_ID,_f:_D});monitor.waitForAbort(1);kodi_rpc(_d,{_e:ADDON_ID,_f:_O});monitor.waitForAbort(1);Script.notify('All settings applied','')
@Script.register
def logout(plugin):ULogout()
@Script.register
def m3ugen(plugin,notify='yes'):
	I=getCachedChannels();C=getCachedDictionary();D=C.get(_m);E=C.get(_n);F='#EXTM3U x-tvg-url="%s"'%EPG_SRC
	for(J,A)in enumerate(I):
		if str(A.get(_R))not in E.keys():B=_a
		else:B=E[str(A.get(_R))]
		if str(A.get(_b))not in D.keys():G='Extragenre'
		else:G=D[str(A.get(_b))]
		if not Settings.get_boolean(B):continue
		K=B+';'+G;L=PLAY_URL+'channel_id={0}'.format(A.get(_A));H=''
		if A.get(_A6):H=' catchup="vod" catchup-source="{0}channel_id={1}&showtime={{H}}{{M}}{{S}}&srno={{Y}}{{m}}{{d}}&programId={{catchup-id}}" catchup-days="7"'.format(PLAY_URL,A.get(_A))
		F+=M3U_CHANNEL.format(tvg_id=A.get(_A),channel_name=A.get(_o),group_title=K,tvg_chno=int(A.get(_A5,J))+1,tvg_logo=IMG_CATCHUP+A.get(_J,''),catchup=H,play_url=L)
	with open(M3U_SRC,'w+')as M:M.write(F.replace('\xa0',' ').encode(_r).decode(_r))
	if notify=='yes':Script.notify(_q,'Playlist updated.')
@Script.register
def epg_setup(plugin):
	H='Epg setup in progress';E='UTF-8';Script.notify('Please wait',H);A=DialogProgress();A.create(H);C=Settings.get_string('epgurl')
	if not C or len(C)<5:C='https://cdn.jsdelivr.net/gh/mitthu786/tvepg/epg.xml.gz'
	I={};J={};K=requests.request('GET',C,headers=J,data=I)
	with open(EPG_PATH,'wb')as B:B.write(K.content)
	A.update(20)
	with gzip.open(EPG_PATH,'rb')as B:L=B.read();M=L.decode(_r);F=ET.fromstring(M)
	A.update(30);A.update(35);A.update(45)
	for D in F.iterfind('.//programme'):N=D.find(_I);O=N.get('src');P=O.rsplit('/',1)[-1];Q=os.path.splitext(P)[0];D.set('catchup-id',Q);G=D.find(_T);G.text=G.text.strip()
	A.update(60);R='<?xml version="1.0" encoding="UTF-8"?>\n';S='<!DOCTYPE tv SYSTEM "xmltv.dtd">\n';T=R.encode(E)+S.encode(E)+ET.tostring(F,encoding=E);U=gzip.compress(T);A.update(80)
	with open(EPG_PATH,'wb')as B:B.write(U)
	A.update(100);A.close();Script.notify(_q,'Epg generated')
@Script.register
def pvrsetup(plugin):
	D='true';C='0';executebuiltin('RunPlugin(plugin://plugin.video.jiotv/resources/lib/main/m3ugen/)');B='pvr.iptvsimple'
	def A(id,value):
		A=value
		if Addon(B).getSetting(id)!=A:Addon(B).setSetting(id,A)
	if check_addon(B):A('m3uPathType',C);A('m3uPath',M3U_SRC);A('epgPathType','1');A('epgUrl',EPG_SRC);A('epgCache','false');A('useInputstreamAdaptiveforHls',D);A('catchupEnabled',D);A('catchupWatchEpgBeginBufferMins',C);A('catchupWatchEpgEndBufferMins',C)
	_setup(M3U_SRC,EPG_SRC)
@Script.register
def cleanup(plugin):urlquick.cache_cleanup(-1);cleanLocalCache();Script.notify('Cache Cleaned','')