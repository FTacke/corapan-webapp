# D2 Results

Command output collected on 2026-03-22 from the server.

```text
=== WEB ===
/srv/webapps/corapan/runtime/corapan/config  ->  /app/config
/srv/webapps/corapan/runtime/corapan/data  ->  /app/data
/srv/webapps/corapan/data/blacklab/export  ->  /app/data/blacklab/export
/srv/webapps/corapan/runtime/corapan/media  ->  /app/media
/srv/webapps/corapan/runtime/corapan/logs  ->  /app/logs


=== BLACKLAB ===
--- corapan-blacklab ---
/var/lib/docker/volumes/b8a349f36655dbb40616377a84f81ae51ff309b0d927b2e1f4849ce2b3ba1bc1/_data  ->  /data
/srv/webapps/corapan/data/blacklab_index  ->  /data/index/corapan
/srv/webapps/corapan/app/config/blacklab  ->  /etc/blacklab


=== DB ===
--- corapan-web-prod ---
bind :  : /srv/webapps/corapan/runtime/corapan/data  ->  /app/data
bind :  : /srv/webapps/corapan/data/blacklab/export  ->  /app/data/blacklab/export
bind :  : /srv/webapps/corapan/runtime/corapan/media  ->  /app/media
bind :  : /srv/webapps/corapan/runtime/corapan/logs  ->  /app/logs
bind :  : /srv/webapps/corapan/runtime/corapan/config  ->  /app/config

--- corapan-db-prod ---
volume : corapan_postgres_prod : /var/lib/docker/volumes/corapan_postgres_prod/_data  ->  /var/lib/postgresql/data

--- corapan-blacklab ---
bind :  : /srv/webapps/corapan/app/config/blacklab  ->  /etc/blacklab
volume : b8a349f36655dbb40616377a84f81ae51ff309b0d927b2e1f4849ce2b3ba1bc1 : /var/lib/docker/volumes/b8a349f36655dbb40616377a84f81ae51ff309b0d927b2e1f4849ce2b3ba1bc1/_data  ->  /data
bind :  : /srv/webapps/corapan/data/blacklab_index  ->  /data/index/corapan

--- hedgedoc_db ---
volume : hedgedoc_hedgedoc_db : /var/lib/docker/volumes/hedgedoc_hedgedoc_db/_data  ->  /var/lib/postgresql/data


=== SIZE runtime/corapan ===
0	/srv/webapps/corapan/runtime/corapan/config
1.8G	/srv/webapps/corapan/runtime/corapan/data
52K	/srv/webapps/corapan/runtime/corapan/docmeta.jsonl
163M	/srv/webapps/corapan/runtime/corapan/exports
3.0M	/srv/webapps/corapan/runtime/corapan/logs
15G	/srv/webapps/corapan/runtime/corapan/media

=== SIZE data ===
0	/srv/webapps/corapan/data/blacklab
279M	/srv/webapps/corapan/data/blacklab_index
279M	/srv/webapps/corapan/data/blacklab_index.bad_2026-01-19_104135
279M	/srv/webapps/corapan/data/blacklab_index.bak_2026-01-16_003920
0	/srv/webapps/corapan/data/blacklab_index.new.leftover_2026-01-15_193558
0	/srv/webapps/corapan/data/public
0	/srv/webapps/corapan/data/stats_temp
9.3M	/srv/webapps/corapan/data/tsv_json_test

=== DISK ===
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        50G   38G   13G  76% /srv
```