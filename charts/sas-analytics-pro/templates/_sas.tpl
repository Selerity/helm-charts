{{/*
Define the User ID
*/}}
{{- define "sas-analytics-pro.sasUser" }}
{{- default "sasdemo" .Values.sas.user }}
{{- end }}

{{/*
Define the User Password
*/}}
{{- define "sas-analytics-pro.sasUserPassword" }}
{{- if .Values.sas.password }}
{{- .Values.sas.password }}
{{- else }}
{{- $secretObj := (lookup "v1" "Secret" .Release.Namespace "goodly-guppy-sas-analytics-pro-authconfig" | default dict) }}
{{- $secretData := (get $secretObj "data") | default dict }}
{{- $secret := (get $secretData "password" | b64dec) | default "" }}
{{- $secret }}
{{- end }}
{{- end }}

{{/*
Define Lockdown Mode
*/}}
{{- define "sas-analytics-pro.lockdown" -}}
{{- if eq .Values.sas.lockdown true -}}
"1"
{{- else -}}
"0"
{{- end -}}
{{- end -}}

{{/*
Define RUN_HTTPD value
*/}}
{{- define "sas-analytics-pro.runHttpd" -}}
{{- if .Values.sas.runHttpd -}}
"true"
{{- else -}}
"false"
{{- end -}}
{{- end -}}

{{/*
Define init_usermods.properties
*/}}
{{- define "sas-analytics-pro.initUsermods" -}}
sas.studio.allowGitPassword=True
{{- end -}}

{{/*
Define spawner_usermods.sh
*/}}
{{- define "sas-analytics-pro.spawnerUsermods" -}}
USERMODS=-allowxcmd
{{- end -}}