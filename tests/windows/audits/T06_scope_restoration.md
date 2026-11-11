# T06 compatibility-only scope

Current scope, clarified by the user on 11 November 2026: **address Windows
porting differences; record and defer inherited Linux bugs**. Matching Linux
behavior takes precedence over repairing its statistical or interface defects
during this stage.

The T06 inherited-bug changes were removed from active qpF4ratio and qpsubs.
Source was restored from the original audited port snapshot after verifying that
the files had no intervening user changes. The only remaining T06 production
diff is the four-line Windows getopt guard; Unix keeps upstream getopt.
Earlier T01-T05 changes were left untouched. This does not establish full-suite
parity with pristine upstream, especially where earlier shared repairs differ.

All 37 supported executables were rebuilt from this restored source. The
installed 131-case rerun has exactly the original scientific rows; 129/131 full
comparisons match, with two absolute fixture-path differences. At printed
precision, 76 finite-result cases match the retained current-Linux reference
and 73 match the pristine reference. Inherited nonfinite results and NaN-sign
differences remain visible. Native PowerShell/redirection/Tee/gzip/cleanup pass.
See [restoration evidence](T06_scope_restoration.evidence.json).

Population limiting/seeds, X counting, malformed lists, undefined estimates,
duplicate-ID handling, inactive output controls and version-exit behavior retain
the original Linux behavior. The [original findings](T06_qpF4ratio.md) are
deferred upstream issues, not fixes applied by this Windows porting step.

The [corrected-Linux experiment](T06_qpF4ratio.corrections.md) and its evidence
remain historical and unapplied. Its source and installed binaries were backed
up under validation-results/hard-check/T06/scope-restoration before restoration.
Those experimental passing results do not describe current binaries. No old
evidence, commits or upstream-tracking history was rewritten.

T06 is recorded as compatibility reviewed with deferred upstream defects; it
is not an unqualified hard-audit pass. Full-suite parity and independent module
coverage remain open. No commit, push or release was made.
