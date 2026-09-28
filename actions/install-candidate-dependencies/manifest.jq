type == "array" and length > 0 and all(.[];
  (.repository | IN("rptadv-samplerate-adapter", "rate_adjusting_pcm_ring", "librptadvradio")) and
  (.sha | test("^[0-9a-f]{40}$")) and
  (.packages | type == "array" and length > 0 and all(.[]; test("^lib[a-z0-9][a-z0-9+.-]*$"))))
