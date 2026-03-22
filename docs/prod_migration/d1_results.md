# D1 Results

Command output collected on 2026-03-22 from `/srv/webapps/corapan`.

```text
=== TOP LEVEL ===
total 0
drwxr-xr-x  1 root     root      70 Jan 19 18:51 .
drwxr-xr-x  1 root     root      94 Feb  6 09:26 ..
drwxr-xr-x  1 root     root     854 Mar 22 17:46 app
drwxr-xr-x  1 root     root      26 Dec  2 23:40 config
drwxr-xr-x  1 root     root     336 Mar 20 22:11 data
drwxr-xr-x  1 hrzadmin hrzadmin  22 Dec  2 12:04 logs
drwxr-xr-x  1 root     root       0 Jan 19 10:01 media
drwxr-xr-x  1     1001     1001 600 Mar 22 12:28 runner
drwxrwxr-x+ 1 hrzadmin hrzadmin  14 Jan 19 09:55 runtime

=== DATA ===
total 0
drwxr-xr-x 1 root     root      336 Mar 20 22:11 .
drwxr-xr-x 1 root     root       70 Jan 19 18:51 ..
drwxr-xr-x 1 root     root       56 Mar 20 22:16 blacklab
drwxr-xr-x 1 hrzadmin hrzadmin 1.7K Jan 15 18:41 blacklab_index
drwxrwxrwx 1 hrzadmin hrzadmin 1.7K Jan 16 00:24 blacklab_index.bad_2026-01-19_104135
drwxr-xr-x 1 hrzadmin hrzadmin 1.7K Jan 15 18:41 blacklab_index.bak_2026-01-16_003920
drwxr-xr-x 1 root     root        0 Jan 19 10:26 blacklab_index.new.leftover_2026-01-15_193558
drwxrwsr-x 1 hrzadmin hrzadmin   36 Jan 19 13:34 public
drwxrwsr-x 1 hrzadmin hrzadmin    0 Jan 19 13:33 stats_temp
drwxr-xr-x 1 hrzadmin hrzadmin  148 Dec  2 13:03 tsv_json_test

=== DATA (deep) ===
data
data/tsv_json_test
data/tsv_json_test/tsv_for_index
data/blacklab_index.bak_2026-01-16_003920
data/blacklab_index.new.leftover_2026-01-15_193558
data/blacklab_index.bad_2026-01-19_104135
data/blacklab_index
data/stats_temp
data/public
data/public/metadata
data/public/statistics
data/blacklab
data/blacklab/export
data/blacklab/index
data/blacklab/backups
data/blacklab/quarantine

=== RUNTIME ===
total 0
drwxrwxr-x+ 1 hrzadmin hrzadmin 14 Jan 19 09:55 .
drwxr-xr-x  1 root     root     70 Jan 19 18:51 ..
drwxrwxr-x+ 1 hrzadmin hrzadmin 78 Jan 19 13:08 corapan

=== RUNTIME (deep) ===
runtime
runtime/corapan
runtime/corapan/exports
runtime/corapan/exports/tsv
runtime/corapan/exports/.sync_state
runtime/corapan/logs
runtime/corapan/media
runtime/corapan/media/mp3-full
runtime/corapan/media/mp3-split
runtime/corapan/media/mp3-temp
runtime/corapan/media/transcripts
runtime/corapan/data
runtime/corapan/data/db
runtime/corapan/data/public
runtime/corapan/data/blacklab_export
runtime/corapan/data/blacklab_index.new.leftover_2026-01-15_193558
runtime/corapan/data/blacklab_index
runtime/corapan/data/counters
runtime/corapan/data/tsv_json_test
runtime/corapan/data/stats_temp
runtime/corapan/data/blacklab
runtime/corapan/config

=== MEDIA ===
total 0
drwxr-xr-x 1 root root  0 Jan 19 10:01 .
drwxr-xr-x 1 root root 70 Jan 19 18:51 ..

=== DOCKER MOUNTS ===
/srv/webapps/corapan/data/blacklab/export -> /app/data/blacklab/export
/srv/webapps/corapan/runtime/corapan/media -> /app/media
/srv/webapps/corapan/runtime/corapan/logs -> /app/logs
/srv/webapps/corapan/runtime/corapan/config -> /app/config
/srv/webapps/corapan/runtime/corapan/data -> /app/data
```