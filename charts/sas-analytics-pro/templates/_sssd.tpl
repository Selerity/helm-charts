{{- define "sssd.conf" -}}
{{- if .Values.sssd.enabled -}}
[sssd]
domains = {{ .Values.sssd.domain }}
config_file_version = 2
services = nss, pam

[domain/{{ .Values.sssd.domain }}]
id_provider = ldap
access_provider = ldap
cache_credentials = True
default_shell = /bin/bash
ldap_id_mapping = True
use_fully_qualified_names = False
fallback_homedir = /home/%u

ldap_uri = {{ .Values.sssd.ldapUri }}
ldap_search_base = {{ .Values.sssd.ldapSearchBase }}
ldap_default_bind_dn = {{ .Values.sssd.ldapDefaultBindDn }}
ldap_default_authtok_type = password
ldap_default_authtok = {{ .Values.sssd.ldapPassword }}
ldap_schema = ad
ldap_tls_reqcert = never
{{- if .Values.sssd.ldapAccessFilter }}
ldap_access_filter = {{.Values.sssd.ldapAccessFilter }}
{{- end }}

{{- end }}
{{- end }}