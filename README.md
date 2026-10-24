# Live TV playlists, Kodi add-on and web player

A GitHub Actions workflow rebuilds the playlists every 5 minutes. Each run fetches the channel sources in `sources.txt`, tests every stream, and keeps the working ones, grouped by language. Dead links drop out after 3 failed checks in a row and come back automatically once they work again.

## Playlist files

All files are at `https://raw.githubusercontent.com/aieditsram-svg/kodi9/main/<file>`.

| File | Use it for |
|------|-----------|
| `channels_pvr.m3u` | **Kodi IPTV Simple Client** (what the add-on sets up for you): one link per channel, including channels that only work inside India. `telugu_pvr.m3u` is the Telugu-only version |
| `epg_telugu.xml.gz`, `epg_pvr.xml.gz` | **TV guide (XMLTV)** for the `*_pvr.m3u` playlists: Telugu only, or every language. Rebuilt daily from a public guide and matched to our channels by name, so only channels the guide knows have programme data |
| `channels_best.m3u` | Same idea, verified links only |
| `channels_hd.m3u` | Same, HD channels only (720p and up) |
| `channels.m3u` | Every working link (several per channel), all languages |
| `channels_all.m3u` | Everything found, including links the server could not check (some only work inside India). The web player and the Kodi add-on use this one |
| `languages/<language>.m3u` | Working links for one language (`telugu.m3u`, `hindi.m3u`, ...) |
| `status.json` | Counts per language and the list of dead links with reasons |

Channels are grouped by language (`group-title` is the language name), so players show a folder per language.

## 1. Kodi: IPTV Simple Client (PVR, normal TV guide and channel zapping)

1. Add-ons > Install from repository > **PVR clients** > **PVR IPTV Simple Client** > Install.
2. Open its settings > **General**: Location = **Remote path (Internet address)**, M3U play list URL = `https://raw.githubusercontent.com/aieditsram-svg/kodi9/main/channels_pvr.m3u`.
3. Turn off "Cache m3u at local storage" if shown, and set the playlist refresh to repeat (for example hourly) so new links are picked up.
4. Optional TV guide: in the same settings, **EPG settings** > Location = **Remote path (Internet address)**, XMLTV URL = `https://raw.githubusercontent.com/aieditsram-svg/kodi9/main/epg_pvr.xml.gz` (Telugu only: `epg_telugu.xml.gz`). Turn off "Cache XML at local storage".
5. Restart Kodi. Live TV > Channels shows the channels, and Channel groups shows one group per language.

For HD only, use `channels_hd.m3u`. For a single language, use `languages/telugu.m3u` and so on.

The PVR client plays the link it was given and cannot switch to another one if it dies. If a channel stops, wait for the next refresh, or use the Telugu Live add-on (below) which tests links on your device and switches by itself.

## 2. Kodi: Telugu Live add-on (instant failover)

1. Kodi: Settings > System > Add-ons > allow **Unknown sources**.
2. Download `https://raw.githubusercontent.com/aieditsram-svg/kodi9/main/repository.telugulive.zip` to the device.
3. Add-ons > Install from zip file > pick `repository.telugulive.zip`.
4. Add-ons > Install from repository > Telugu Live Repository > Video add-ons > **Telugu Live** > Install.

The repository is read from `raw.githubusercontent.com`, so GitHub Pages is not needed for Kodi.

After installing, Telugu Live offers (once, about 20 seconds after Kodi starts) to **load all channels into Kodi's TV section**. If you accept, it installs IPTV Simple Client if needed and points it at `channels_pvr.m3u` and the TV guide `epg_pvr.xml.gz`, so every channel appears under TV > Channels with one group per language and programme info where the guide has it. You can run this again any time from the add-on menu, and change the playlist and guide addresses in the add-on settings.

Menu: **HD channels** (split by language), **All channels**, then a folder per language. In the add-on settings, "HD means at least" switches between 720p and 1080p, and "Also show channels the server could not verify" keeps links that only work from India visible.

## JioTV with your own Jio login (optional)

Telugu Live does not log in to Jio and never sees your number, OTP or tokens. If you want Jio's channels as well:

1. In Telugu Live, open **JioTV: use your own Jio login** and accept the install. JioTV is a separate, unofficial
   add-on (not made by Jio) hosted in this repository, so it installs from the Telugu Live Repository. By hand:
   Add-ons > Install from repository > Telugu Live Repository > Video add-ons > JioTV.
2. Open JioTV settings, log in with your own Jio number and the OTP, and turn on its playlist generation.
3. In Telugu Live, open the same entry again and choose **Use JioTV channels in Telugu Live**.

JioTV channels are then tried first and the public links stay as the backup. The JioTV add-on was last updated in
2023 and may not work with Jio's current service, and its login requests skip certificate checking, so log in only on
a network you trust. Do not put a playlist generated by it into a public repository, and do not use JioTV's own
"PVR setup" and the Telugu Live setup on the same IPTV Simple Client entry (run JioTV's first).

JioTV's code is unchanged from the original MIT-licensed add-on by tobalan and botallen (see
`kodi/plugin.video.jiotv/LICENSE` and `NOTICE.txt`); only its metadata, default guide address and README were adapted.

## 3. Web player for a blog or website

`player.html` is a ready-made player: language filter, HD filter, search, and automatic switching to the next link when one fails. It is published at `https://aieditsram-svg.github.io/kodi9/player.html` once GitHub Pages is on.

**Embed it anywhere** (Blogger, WordPress, any site that accepts HTML):

```html
<iframe src="https://aieditsram-svg.github.io/kodi9/player.html"
        style="width:100%;height:720px;border:0" allow="autoplay; fullscreen" allowfullscreen></iframe>
```

On Blogger: Pages > New page > switch the editor to **HTML view** > paste the iframe > Publish.

Options go on the address: `player.html?lang=Telugu&hd=1`, or `?list=<another .m3u address>`. Change the default list at the top of the `<script>` in `player.html`.

Limits of playing in a browser:
- Browsers block `http://` streams on `https://` pages, and many stream servers refuse web players (CORS). Those channels will not play on the website but will play in Kodi or VLC. The player tries every link of a channel before giving up.
- Some channels are geo-restricted to India.

## Adding sources

Edit `sources.txt`, one playlist per line. Options after `|`: `language=Tamil`, `group=India`, `keywords=a,b`, `enrich=iptv-org`. Sources are merged, de-duplicated by stream URL and tested together.

Run it locally with `python scripts/build_playlist.py` (Python 3.9+, no dependencies).

## Notes

- GitHub starts scheduled runs a few minutes late, so a 5-minute schedule often means 5 to 15 minutes in practice.
- Only use sources that carry free-to-air or officially public streams. You are responsible for the sources you add.
