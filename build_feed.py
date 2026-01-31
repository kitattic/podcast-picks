#!/usr/bin/env python3
"""
Kit's Podcast Picks - RSS Feed Generator
Curates podcast episodes from various shows into one feed
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import requests
import json
import os
from datetime import datetime
import hashlib

# Feed metadata
FEED_TITLE = "🦊 Kit's Podcast Picks"
FEED_DESCRIPTION = "Curated podcast episodes for people who love crafted storytelling, investigative journalism, and shows that respect your time. No algorithms. No ads. Just Kit's taste."
FEED_AUTHOR = "Kit (kitattic.com)"
FEED_URL = "https://kitattic.github.io/podcast-picks/feed.xml"
FEED_LINK = "https://github.com/kitattic/podcast-picks"
FEED_IMAGE = "https://kitattic.github.io/podcast-picks/artwork.jpg"

def fetch_rss(url):
    """Fetch and parse an RSS feed"""
    try:
        resp = requests.get(url, timeout=15, headers={'User-Agent': 'KitPodcastCurator/1.0'})
        return ET.fromstring(resp.content)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_episodes(rss_root, limit=5):
    """Extract episode info from RSS"""
    episodes = []
    channel = rss_root.find('channel')
    if channel is None:
        return episodes
    
    show_title = channel.findtext('title', 'Unknown Show')
    
    for item in channel.findall('item')[:limit]:
        enclosure = item.find('enclosure')
        if enclosure is None:
            continue
            
        episode = {
            'show': show_title,
            'title': item.findtext('title', 'Untitled'),
            'description': item.findtext('description', ''),
            'url': enclosure.get('url'),
            'type': enclosure.get('type', 'audio/mpeg'),
            'length': enclosure.get('length', '0'),
            'pub_date': item.findtext('pubDate', ''),
            'duration': item.findtext('{http://www.itunes.com/dtds/podcast-1.0.dtd}duration', ''),
            'guid': item.findtext('guid', enclosure.get('url')),
        }
        episodes.append(episode)
    
    return episodes

def generate_feed(curated_episodes, output_path='feed.xml'):
    """Generate the curated RSS feed"""
    
    rss = ET.Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    
    channel = ET.SubElement(rss, 'channel')
    
    # Feed metadata
    ET.SubElement(channel, 'title').text = FEED_TITLE
    ET.SubElement(channel, 'description').text = FEED_DESCRIPTION
    ET.SubElement(channel, 'link').text = FEED_LINK
    ET.SubElement(channel, 'language').text = 'en-us'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # iTunes tags
    ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}author').text = FEED_AUTHOR
    ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}summary').text = FEED_DESCRIPTION
    ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text = 'no'
    
    image = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}image')
    image.set('href', FEED_IMAGE)
    
    category = ET.SubElement(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}category')
    category.set('text', 'Society &amp; Culture')
    
    # Atom self link
    atom_link = ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link')
    atom_link.set('href', FEED_URL)
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    # Add episodes
    for ep in curated_episodes:
        item = ET.SubElement(channel, 'item')
        
        # Prefix title with show name
        full_title = f"[{ep['show']}] {ep['title']}"
        ET.SubElement(item, 'title').text = full_title
        ET.SubElement(item, 'description').text = ep.get('description', '')
        
        enclosure = ET.SubElement(item, 'enclosure')
        enclosure.set('url', ep['url'])
        enclosure.set('type', ep.get('type', 'audio/mpeg'))
        enclosure.set('length', str(ep.get('length', 0)))
        
        ET.SubElement(item, 'guid').text = ep.get('guid', ep['url'])
        
        if ep.get('pub_date'):
            ET.SubElement(item, 'pubDate').text = ep['pub_date']
        
        if ep.get('duration'):
            ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = ep['duration']
    
    # Pretty print
    xml_str = ET.tostring(rss, encoding='unicode')
    pretty = minidom.parseString(xml_str).toprettyxml(indent='  ')
    
    # Remove extra declaration line
    lines = pretty.split('\n')
    if lines[0].startswith('<?xml'):
        pretty = '\n'.join(lines[1:])
    
    with open(output_path, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(pretty)
    
    print(f"Generated {output_path} with {len(curated_episodes)} episodes")

if __name__ == '__main__':
    # Curated podcast RSS feeds - shows that match Oscar's taste
    PODCAST_FEEDS = {
        # Narrative/investigative (S-Town vibes)
        'Serial': 'https://feeds.simplecast.com/xl36XBC2',
        'Darknet Diaries': 'https://feeds.megaphone.fm/darknetdiaries',
        'Radiolab': 'https://feeds.simplecast.com/EmVW7VGp',
        '99% Invisible': 'https://feeds.simplecast.com/BqbsxVfO',
        'Criminal': 'https://feeds.megaphone.fm/criminal',
        'Heavyweight': 'https://feeds.megaphone.fm/heavyweight',
        'Reply All': 'https://feeds.megaphone.fm/replyall',
        'The Lazarus Heist': 'https://podcasts.files.bbci.co.uk/w13xttx2.rss',
        
        # Tech/business (Darknet Diaries adjacent)
        'Acquired': 'https://feeds.megaphone.fm/acquired',
        'Lex Fridman': 'https://lexfridman.com/feed/podcast/',
        
        # High production storytelling
        'This American Life': 'https://www.thisamericanlife.org/podcast/rss.xml',
        'Revisionist History': 'https://feeds.megaphone.fm/revisionisthistory',
    }
    
    print("🦊 Kit's Podcast Picks - Building Feed")
    print("=" * 50)
    
    all_episodes = []
    
    for name, url in PODCAST_FEEDS.items():
        print(f"Fetching: {name}...")
        rss = fetch_rss(url)
        if rss:
            eps = extract_episodes(rss, limit=2)  # 2 recent eps per show
            all_episodes.extend(eps)
            print(f"  Got {len(eps)} episodes")
    
    print(f"\nTotal episodes: {len(all_episodes)}")
    
    # Sort by pub date (newest first)
    all_episodes.sort(key=lambda x: x.get('pub_date', ''), reverse=True)
    
    # Generate feed
    generate_feed(all_episodes)
    print("\n✅ Feed ready!")
