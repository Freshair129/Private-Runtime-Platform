First datastore-scan of the EV08 source container (2026-09-22 15:42Z).

Kept because it is a real observation, but it is not the one the run record cites. The probe then
searched only the first 500 of 11875 `docker diff` paths for the marker, and did not record the
marker it used. The probe was changed to search a minimal covering set of added and changed paths
(1292 roots) and to record the marker (see ../test-design.md, "Change during the run"). The scan
was then repeated on the same container; the file one level up is the cited one.

Both scans found the marker in no file and not in docker logs.
