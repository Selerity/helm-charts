{{- define "auto.home" -}}
{{- if .Values.nfs.enabled -}}
/home -fstype=nfs4,proto=tcp,port={{ .Values.nfs.port | int }} {{ .Values.nfs.server }}:{{ .Values.nfs.homePath }}
{{- end }}
{{- end }}

{{- define "auto.master" -}}
{{- if .Values.nfs.enabled -}}
/-      /etc/auto.home
{{- end }}
{{- end }}