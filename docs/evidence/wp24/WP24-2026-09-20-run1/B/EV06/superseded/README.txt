First runs of the restart and kill-engine cases (2026-09-22 14:09Z and 14:11Z).

Both are kept because they are real observations, but they were taken before the probe recorded
`error` chunks inside a stream. The tool was then changed to capture them (see ../test-design.md,
"Change during the run"), and both cases were run again. The files one level up are the ones the
run record cites.

What these first runs add:
- the restart case ended with `data: [DONE]` here, but without it in the re-run. The client-visible
  ending of a restart varies from run to run;
- `docker restart` returned in 1.6 s here and in 10.7 s in the re-run, where SIGTERM did not end
  the container within Docker's 10 s grace period;
- ready times of 98.1 s (restart) and 78.6 s (kill, measured from docker start) sit close to the
  re-run's 93.2 s and 73.2 s.
