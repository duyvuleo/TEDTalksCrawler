#!/usr/bin/env python2
# -*- coding: utf8 -*-

'''
Script to crawl all TED talks (incl. HD videos, subtitles in multiple languages, and rich meta infos)
Author: Vu (Cong Duy) Hoang (vhoang2@student.unimelb.edu.au, duyvuleo@gmail.com)
'''

import json
import os
import optparse
import platform
import re
import sys
import urllib
import urllib2
from subprocess import Popen, PIPE

FOUND = True

Subtitles_Folder_Path = 'Subtitles/'
Videos_Folder_Path = 'Videos/'
Metas_Folder_Path = 'Metas/'

#==============================================================================
#   	Copyright 2010 Joe Di Castro <joe@joedicastro.com>
# 	adapted by Cong Duy Vu Hoang
def Get_Subtitle(tt_id, tt_intro, sub, lang):
	"""Get TED Subtitle in JSON format & convert it to SRT Subtitle."""

	def srt_time(tst):
		"""Format Time from TED Subtitles format to SRT time Format."""
		secs, mins, hours = ((tst / 1000) % 60), (tst / 60000), (tst / 3600000)
		right_srt_time = ("{0:02d}:{1:02d}:{2:02d},{3:3.0f}".format(int(hours), int(mins), int(secs), divmod(secs, 1)[1] * 1000))
		return right_srt_time

	srt_content = ''
	tt_url = 'http://www.ted.com/talks'
	sub_url = '{0}/subtitles/id/{1}/lang/{2}'.format(tt_url, tt_id, lang)
	print sub_url
	# Get JSON sub
	if FOUND:
		json_file = Popen(['wget', '-q', '-O', '-', sub_url], stdout=PIPE).stdout.readlines()

		if json_file:
			for line in json_file:
				if line.find('captions') == -1 and line.find('status') == -1:
					json_file.remove(line)
		else:
			print("Subtitle '{0}' not found.".format(sub))
	else:
		json_file = urllib2.urlopen(sub_url).readlines()
	if json_file:
		try:
			json_object = json.loads(json_file[0])
			if 'captions' in json_object:
				caption_idx = 1
				if not json_object['captions']:
					print("Subtitle '{0}' not available.".format(sub))
				for caption in json_object['captions']:
					start = tt_intro + caption['startTime']
					end = start + caption['duration']
					idx_line = '{0}'.format(caption_idx)
					time_line = '{0} --> {1}'.format(srt_time(start), srt_time(end))
					text_line = '{0}'.format(caption['content'].encode("utf-8"))
					srt_content += '\n'.join([idx_line, time_line, text_line, '\n'])
					caption_idx += 1
			elif 'status' in json_object:
				print("This is an error message returned by TED:{0}{0} - "
					  "{1}{0}{0}Probably because the subtitle '{2}' is not "
					  "available.{0}".format(os.linesep, json_object['status']['message'], sub))
		except ValueError:
			print("Subtitle '{0}' it's a malformed json file.".format(sub))
	return srt_content

def Check_Subtitles(tt_id, tt_intro, tt_video, avail_langs):
    	"""Check if the subtitles for the talk exists and try to get them. Checks
    	it for english and spanish languages."""
    	# Get the names for the subtitles (for english and spanish languages) only
    	# if they not are already downloaded
    	#subs = ("{0}.{1}.srt".format(tt_video[:-4], lang) for lang in avail_langs) #('eng', 'spa'))
	subs = ("{0}.{1}.srt".format(tt_id, lang) for lang in avail_langs)
    	i = 0
    	for sub in subs:
		#print sub
		if os.path.exists(Subtitles_Folder_Path + sub):
			continue
        	subtitle = Get_Subtitle(tt_id, tt_intro, sub, avail_langs[i])
        	if subtitle:
            		with open(Subtitles_Folder_Path + sub, 'w') as srt_file:
                		srt_file.write(subtitle)
            		print("Subtitle '{0}' downloaded.".format(sub))
		i = i + 1
    	return

def Get_Video(vid_name, vid_url, ttalk_id):
    	"""Gets the TED Talk video."""
    	print("Downloading video...")
    	#print vid_name
    	print vid_url

	if os.path.exists(Videos_Folder_Path + ttalk_id + '.mp4'):
		return
	    
	if FOUND:
        	#Popen(['wget', '-q', '-O', vid_name, vid_url],
        	#stdout=PIPE).stdout.read()
		Popen(['wget', '-q', '-O', Videos_Folder_Path + ttalk_id + ".mp4", vid_url], stdout=PIPE).stdout.read()
	else:
        	#urllib.urlretrieve(vid_url, vid_name
		urllib.urlretrieve(vid_url, Videos_Folder_Path + ttalk_id + ".mp4")
    	#print("Video {0} downloaded.".format(vid_name))
    	print("Video {0} downloaded.".format(Videos_Folder_Path + ttalk_id + ".mp4"))
    	return
#==============================================================================

#--------------------------------------------------------------------------------------------------
# Step 1: parse page of language info (https://www.ted.com/participate/translate/our-languages)
# Output: list of languages to be crawled (e.g., https://www.ted.com/talks?language=ky, ...)
''' Example:
<div class='languages__list__language'>
<div class='h9'><a href="/talks?language=ko">Korean</a></div>
1937 talks
</div>
'''
langinfo_url = 'https://www.ted.com/participate/translate/our-languages'
langinfo_url_str = Popen(['wget', '-q', '-O', '-', langinfo_url], stdout=PIPE).stdout.read()

langlink_list = [] #tuple (link,language_name,num_talks)
lines = langinfo_url_str.split('\n')
for i in range(0, len(lines)):
	l = lines[i].strip()
	if l.find("<div class='h9'><a ") != -1:
		l = l.replace("<div class='h9'><a href=\"", "")
		l = l.replace(' ', '#')
		l = l.replace("\">", " ")
		l = l.replace('</a></div>', '')
		l = l + ' ' + lines[i + 1]
		l = l.replace(' talks', '')
		linfos = l.split(' ')
		#if linfos[1].replace('#', ' ') != 'Albanian': continue
		langlink_list.append(('https://www.ted.com' + linfos[0], linfos[1].replace('#', ' '), linfos[2]))
		print langlink_list[len(langlink_list) - 1]	
#-------------------------------------------------------------------------------------------------- 

#--------------------------------------------------------------------------------------------------
# Step 2: parse all items from the list from Step 1
# Output: list of ted talk links associated with each of items
''' Example: 
</div>
</div>
<div class='col'>
<div class='m3'>
<div class='talk-link'>
<div class='media media--sm-v'>
<div class='media__image media__image--thumb talk-link__image'>
<a class='' href='/talks/greg_gage_how_to_control_someone_else_s_arm_with_your_brain?language=vi' language='vi'>
<span class="thumb thumb--video thumb--crop-top"><span class="thumb__sizer"><span class="thumb__tugger"><img alt="" class=" thumb__image" crop="top" play="352" src="https://tedcdnpi-a.akamaihd.net/r/tedcdnpe-a.akamaihd.net/images/ted/16565cf6939650dbd2041621c744d049820c1130_2880x1620.jpg?quality=89&amp;w=320" /><span class="thumb__aligner"></span></span></span><span class="thumb__duration">05:52</span></span>
<span class='talk-link__image__message'>
Under 6 minutes
</span>
</a>
</div>
<div class='media__message'>
<h4 class='h12 talk-link__speaker'>Greg Gage</h4>
<h4 class='h9 m5'>
<a class='' href='/talks/greg_gage_how_to_control_someone_else_s_arm_with_your_brain?language=vi' lang='vi'>
Làm thế nào điều khiển tay người khác bằng não của bạn
</a>
</h4>
<div class='meta'>
<span class='meta__item'>
Posted
<span class='meta__val'>
Apr 2015
</span>
</span>
<span class='meta__row'>
Rated
<span class='meta__val'>
Fascinating, Informative
</span>
</span>
</div>
</div>
</div>
</div>
'''
''' Note for the continuous pages:
<div class="pagination"><span class="pagination__prev pagination__flipper pagination__flipper--disabled">Previous</span><span class=pagination__separator>|</span><span class="pagination__item pagination__current">1</span><span class=pagination__separator>|</span><a rel="next" class="pagination__item pagination__link" href="/talks?language=vi&amp;page=2">2</a><span class=pagination__separator>|</span><a class="pagination__item pagination__link" href="/talks?language=vi&amp;page=3">3</a><span class=pagination__separator>|</span><a class="pagination__item pagination__link" href="/talks?language=vi&amp;page=4">4</a><span class=pagination__separator>|</span><a class="pagination__item pagination__link" href="/talks?language=vi&amp;page=5">5</a><span class="pagination__item pagination__gap">&hellip;</span><a class="pagination__item pagination__link" href="/talks?language=vi&amp;page=40">40</a><span class=pagination__separator>|</span><a class="pagination__next pagination__flipper pagination__link" rel="next" href="/talks?language=vi&amp;page=2">Next</a></div>
'''
mlinks = {}
for i in range(0, len(langlink_list)):
	link,lang_name,num_talks = langlink_list[i]
	print 'Processing ' + link + ' ...'
	num_pages = 1
	c = 0
	talklinks = []
	while c < num_pages:
		clink = link
		if c >= 1: clink = clink + '&page=' + str(c + 1)		
		link_url_str = Popen(['wget', '-q', '-O', '-', clink], stdout=PIPE).stdout.read()
		#print link_url_str
	
		lines = link_url_str.split('\n')
		for line in lines:
			if line.find("<a class='' href='/talks/") != -1 and line.find("language='") != -1:
				talklink = line.replace("<a class='' href='", "")
				talklink = "https://www.ted.com" + talklink.split(' ')[0].replace("'", "")
				#print talklink
				talklinks.append(talklink)
			if line.find('<div class="pagination">') != -1 and num_pages == 1:
				lpp = line.rfind('href="/talks?language=', 0, line.rfind('href="/talks?language='))
				lppb = line.find('page=', lpp)
				num_pages = int(line[lppb + 5:line.find('"', lppb)])
		c = c + 1

	print num_talks, len(talklinks)
	mlinks[i] = talklinks
	#break
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Step 3: download all links in the list from Step 2
# Output: all related infos for each of links
''' Available languages and meta infos
<meta content="Pamela Ronald: Ứng dụng kĩ thuật để tạo thức ăn | TED Talk | TED.com" name="title" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=vi" rel="canonical" />
<meta content="app-id=376183339,app-argument=https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=vi" name="apple-itunes-app" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food" hreflang="x-default" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=ar" hreflang="ar" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=bg" hreflang="bg" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=zh-cn" hreflang="zh-cn" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=zh-tw" hreflang="zh-tw" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=hr" hreflang="hr" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=nl" hreflang="nl" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=en" hreflang="en" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=fr" hreflang="fr" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=de" hreflang="de" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=he" hreflang="he" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=it" hreflang="it" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=ja" hreflang="ja" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=ko" hreflang="ko" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=fa" hreflang="fa" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=pt-br" hreflang="pt-br" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=ru" hreflang="ru" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=sr" hreflang="sr" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=sk" hreflang="sk" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=es" hreflang="es" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=sv" hreflang="sv" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=th" hreflang="th" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=tr" hreflang="tr" rel="alternate" />
<link href="https://www.ted.com/talks/pamela_ronald_the_case_for_engineering_our_food?language=vi" hreflang="vi" rel="alternate" />
<meta content="Pamela Ronald nghiên cứu gen giúp cây kháng lại bệnh và áp lực tốt hơn. Trong bài thuyết trình, bà mô tả cuộc tìm kiếm dài cả thập kỉ để giúp tạo ra nhiều giống gạo có thể sống sót khi bị ngập úng nhiều ngày. Bà biết rằng gen cải biến trong hạt giống có thể cứu vụ mùa đu đủ Hawai trong những năm 1950- khiến chúng trở thành cách hữu hiệu nhất để đảm bảo an ninh lương thực cho hành tinh này, khi mà dân số ngày càng tăng.  " name="description" />
<meta content="TED, talks, agriculture, food, global issues, sustainability" name="keywords" />
<meta content="video" name="medium" />
<meta content="Pamela Ronald" name="author" />
...
<meta content="ted://x-callback-url/talk?talkID=2241&amp;source=twitter" name="twitter:app:url:ipad" />
'''
#regex_intro = re.compile('"introDuration":(\d+\.?\d+),')
regex_intro = re.compile('"introDuration":(\d+\.\d+|\d+),')
regex_url = re.compile('"nativeDownloads":.*"high":"(.+)\?.+},"sub')
regex_vid = re.compile('http://.+\/(.*\.mp4)')		
regex_id = re.compile('"id":(\d+),')
for index,talklinks in mlinks.iteritems():
	for talklink in talklinks:
		#print talklink
		link_talklink_str = Popen(['wget', '-q', '-O', '-', talklink], stdout=PIPE).stdout.read()
		#print link_talklink_str
		lines = link_talklink_str.split('\n')
		avail_langs = []
		title = '';keywords = ''; description = ''; author = ''#; talkID = ''
		for line in lines:
			if line.find("<meta content=") != -1 and line.find('name="title"') != -1: #title
				beg = line.find('"') + 1
				end = line.find('"', beg)
				title = line[beg:end].replace(' | TED Talk | TED.com', '').strip() #FIXME: recover XML code
			if line.find("<meta content=") != -1 and line.find('name="keywords"') != -1: #keywords
				beg = line.find('"') + 1
				end = line.find('"', beg)
				keywords = line[beg:end].replace('TED,','').replace('talks,','').replace('conference,','').replace('TED Brain Trust,','').replace('TED Conference,','').replace('Google,','').replace(', ',',').strip() #FIXME: recover XML code
			if line.find("<meta content=") != -1 and line.find('name="description"') != -1: #description
				beg = line.find('"') + 1
				end = line.find('"', beg)
				description = line[beg:end].strip() #FIXME: recover XML code
			if line.find("<meta content=") != -1 and line.find('name="author"') != -1: #author
				beg = line.find('"') + 1
				end = line.find('"', beg)
				author = line[beg:end].strip() #FIXME: recover XML code
			#if line.find("<meta content=") != -1 and line.find('talk?talkID=') != -1 and line.find('name="twitter:app:url:ipad"') != -1: #talkID
			#	talkID = line.split(' ')[1].replace('content="ted://x-callback-url/talk?talkID=', '').replace('&amp;source=twitter"', '')
			if line.find("<link href=") != -1 and line.find("hreflang=") != -1 and line.find('rel="alternate"') !=-1:
				lang = line.split(' ')[2].replace("hreflang=",'').replace('"','')
				if lang != 'x-default':
					avail_langs.append(lang)
		#print talkID
		#print author
		#print title
		#print keywords
		#print description
		#print avail_langs

		curlang = talklink[talklink.rfind('=')+1:]
		print "Current language: " + curlang
		
		#download high quality video and corresponding subtitles
		talklink = talklink[0:talklink.find('?language=')]
		print talklink

		ttalk_webpage = Popen(['wget', '-q', '-O', '-', talklink], stdout=PIPE).stdout.read()	
		try:
			if ttalk_webpage:
				ttalk_intro = ((float(regex_intro.findall(ttalk_webpage)[0]) + 1) * 1000)
				ttalk_id = regex_id.findall(ttalk_webpage)[0]
				ttalk_url = regex_url.findall(ttalk_webpage)[0]
				ttalk_vid = regex_vid.findall(ttalk_url)[0]
			else:
				print "Cannot read the context of webpage from the link: " + talklink
		except IndexError:
			print('This video (' + talklink + ') is not available for download.')
			continue

		if not os.path.exists(Metas_Folder_Path + ttalk_id + "." + curlang + '.meta'):
			metaf = open(Metas_Folder_Path + ttalk_id + "." + curlang + '.meta', 'wb')
			print >>metaf, 'TALKID\t' + ttalk_id
			print >>metaf, 'LANGUAGE\t' + curlang + '\t' + langlink_list[index][1]
			#print >>metaf, 'NUM_TALKS\t' + langlink_list[index][2] 
			print >>metaf, 'AUTHOR\t' + author
			print >>metaf, 'TITLE\t' + title
			print >>metaf, 'KEYWORDS\t' + keywords
			print >>metaf, 'DESCRIPTION\t' + description
			print >>metaf, 'LANGUAGES\t' + ' '.join(avail_langs)
			metaf.close()

		#exit()

		#print talklink, ttalk_intro, ttalk_id, ttalk_url, ttalk_vid
		
		Check_Subtitles(ttalk_id, ttalk_intro, ttalk_vid, avail_langs)
		Get_Video(ttalk_vid, ttalk_url, ttalk_id)

		#break
		
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Step 4: additional step if required
#--------------------------------------------------------------------------------------------------

