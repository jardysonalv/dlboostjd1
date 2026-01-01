[app]
title = DLBoost Lite
package.name = dlboostlite
package.domain = org.example
source.dir = .
version = 0.1
# O entrypoint padrão é main.py
requirements = python3,kivy==2.1.0,kivymd==1.1.1,supabase,requests,pyjnius
orientation = portrait

# Permissões (algumas requerem consentimento do usuário ou são normais)
android.permissions = INTERNET,ACCESS_NETWORK_STATE,KILL_BACKGROUND_PROCESSES,WRITE_EXTERNAL_STORAGE

# APIs / SDK
android.minapi = 21
android.sdk = 24
android.ndk = 23b
android.arch = armeabi-v7a, arm64-v8a

# Inclua assets se tiver
source.include_exts = py,png,jpg,kv,txt