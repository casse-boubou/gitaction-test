{{- /* Template for generating a json with distro info */ -}}
{{- /* with syft scan from his complete outpout */ -}}
{{- /* updated on 06/08/2026 from */ -}}
{{- /* https://github.com/anchore/syft/blob/main/schema/json/schema-latest.json */ -}}
{
  "distro": {
    "prettyName": "{{.distro.prettyName}}",
    "name": "{{.distro.name}}",
    "id": "{{.distro.id}}",
    "versionID": "{{.distro.versionID}}",
    "homeURL": "{{.distro.homeURL}}",
    "bugReportURL": "{{.distro.bugReportURL}}"
  }
} 
